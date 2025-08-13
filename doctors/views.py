# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm, DoctorProfileEditForm, DoctorSlotForm, DoctorAddPatientForm, DoctorScheduleForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser
from django.db.models import Q
import datetime

def doctor_list(request):
    doctors = Doctor.objects.filter(is_approved=True).prefetch_related('specialties')
    specialties = Specialty.objects.all()

    query = request.GET.get('q')
    if query:
        doctors = doctors.filter(full_name__icontains=query)

    specialty_filter = request.GET.get('specialty')
    if specialty_filter:
        doctors = doctors.filter(specialties__name=specialty_filter)

    context = {
        'doctors': doctors,
        'specialties': specialties,
        'current_query': query,
        'current_specialty': specialty_filter,
    }
    return render(request, 'doctors/doctor_list.html', context)

def doctor_detail(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)
    context = {'doctor': doctor}
    return render(request, 'doctors/doctor_detail.html', context)

def register_clinic(request):
    if request.method == 'POST':
        form = ClinicRegistrationForm(request.POST)
        if form.is_valid():
            try:
                doctor = form.save()
                messages.success(request, 'Your clinic registration has been submitted successfully! We will review your details soon.')
                form = ClinicRegistrationForm()
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClinicRegistrationForm()

    context = {
        'form': form,
        'specialties': Specialty.objects.all()
    }
    return render(request, 'doctors/clinic_registration_form.html', context)

def clinic_registration_success(request):
    return render(request, 'doctors/clinic_registration_success.html')

@login_required
def doctor_dashboard(request):
    try:
        doctor = request.user.doctor_login_profile
        if not doctor.is_approved:
            messages.warning(request, "Your doctor profile is pending approval. Please wait for an administrator to approve it.")
            return redirect('landing_page')
    except Doctor.DoesNotExist:
        messages.error(request, "You are not registered as a doctor, or your profile is incomplete. Please register your clinic.")
        return redirect('register_clinic')

    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')

    past_appointments = Appointment.objects.filter(
        doctor=doctor,
        status__in=['completed', 'cancelled']
    ).order_by('-appointment_date', '-appointment_time')

    patient_ids_with_appointments = Appointment.objects.filter(doctor=doctor).values_list('patient__id', flat=True).distinct()

    doctor_relevant_reports = Report.objects.filter(
        Q(doctor=doctor) | Q(patient__id__in=patient_ids_with_appointments)
    ).order_by('-uploaded_at').distinct()

    context = {
        'doctor': doctor,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'doctor_relevant_reports': doctor_relevant_reports,
    }
    return render(request, 'doctors/doctor_dashboard.html', context)

@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id, is_approved=True)

    try:
        if request.user.doctor_login_profile:
            messages.error(request, "Doctors cannot book appointments for themselves using this form.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        pass

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, doctor=doctor)
        if form.is_valid():
            selected_slot = form.cleaned_data['available_slot']

            if Appointment.objects.filter(
                appointment_slot=selected_slot,
                status__in=['pending', 'confirmed']
            ).exists():
                messages.error(request, "This slot is no longer available. Please select another time.")
                form = AppointmentBookingForm(doctor=doctor)
                context = {'doctor': doctor, 'form': form}
                return render(request, 'doctors/book_appointment.html', context)

            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.appointment_date = selected_slot.date
            appointment.appointment_time = selected_slot.start_time
            appointment.appointment_slot = selected_slot
            appointment.save()

            selected_slot.is_available = False
            selected_slot.save()

            messages.success(request, f"Your appointment with Dr. {doctor.full_name} on {appointment.appointment_date} at {appointment.appointment_time} has been requested. It is currently pending confirmation.")
            return redirect('appointment_success')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentBookingForm(doctor=doctor)

    context = {
        'doctor': doctor,
        'form': form,
    }
    return render(request, 'doctors/book_appointment.html', context)

def appointment_success(request):
    return render(request, 'doctors/appointment_success.html')

@login_required
def confirm_appointment(request, appointment_id):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)

        try:
            current_doctor = request.user.doctor_login_profile
            if appointment.doctor != current_doctor:
                messages.error(request, "You are not authorized to confirm this appointment.")
                return redirect('doctor_dashboard')
        except Doctor.DoesNotExist:
            messages.error(request, "You must be a registered doctor to perform this action.")
            return redirect('doctor_dashboard')

        if appointment.status == 'pending':
            appointment.status = 'confirmed'
            appointment.save()

            if appointment.appointment_slot:
                appointment.appointment_slot.is_available = False
                appointment.appointment_slot.save()
            else:
                messages.warning(request, "Associated time slot not found or already marked unavailable.")

            messages.success(request, f"Appointment with {appointment.patient.username} on {appointment.appointment_date} confirmed.")
        else:
            messages.warning(request, "Only pending appointments can be confirmed.")
        return redirect('doctor_dashboard')
    else:
        raise Http404("Only POST requests are allowed for this action.")

@login_required
def cancel_appointment(request, appointment_id):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)
        canceller_is_doctor = False

        try:
            current_doctor_profile = request.user.doctor_login_profile
            if appointment.doctor == current_doctor_profile:
                canceller_is_doctor = True
            else:
                if appointment.patient != request.user:
                    messages.error(request, "You are not authorized to cancel this appointment.")
                    return redirect('patient_dashboard')
        except Doctor.DoesNotExist:
            if appointment.patient != request.user:
                messages.error(request, "You are not authorized to cancel this appointment.")
                return redirect('patient_dashboard')

        if appointment.status in ['pending', 'confirmed']:
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, f"Appointment with {appointment.patient.username} on {appointment.appointment_date} has been cancelled.")

            if appointment.appointment_slot:
                appointment.appointment_slot.is_available = True
                appointment.appointment_slot.save()
            else:
                messages.warning(request, "Associated time slot not found or already available.")

            redirect_url = 'doctor_dashboard' if canceller_is_doctor else 'patient_dashboard'
            return redirect(redirect_url)
        else:
            messages.warning(request, "This appointment cannot be cancelled as it is already completed or cancelled.")
        return redirect('doctor_dashboard')
    else:
        raise Http404("Only POST requests are allowed for this action.")

@login_required
def patient_upload_report(request):
    try:
        if request.user.doctor_login_profile:
            messages.error(request, "Doctors upload reports via specific patient/appointment context.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        pass

    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = request.user
            report.save()
            messages.success(request, 'Your report has been uploaded successfully!')
            return redirect('patient_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReportUploadForm()

    context = {
        'form': form,
        'title': 'Upload Your Medical Report'
    }
    return render(request, 'doctors/report_upload_form.html', context)

@login_required
def doctor_upload_report(request, patient_id):
    try:
        current_doctor = request.user.doctor_login_profile
        if not current_doctor.is_approved:
            messages.error(request, "Your doctor profile is not approved.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        messages.error(request, "You must be a registered and approved doctor to perform this action.")
        return redirect('doctor_dashboard')

    patient = get_object_or_404(CustomUser, id=patient_id)

    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = patient
            report.doctor = current_doctor
            report.save()
            messages.success(request, f'Report for {patient.username} uploaded successfully by Dr. {current_doctor.full_name}!')
            return redirect('doctor_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReportUploadForm()

    context = {
        'form': form,
        'patient': patient,
        'title': f'Upload Report for {patient.username}'
    }
    return render(request, 'doctors/report_upload_form.html', context)

@login_required
def doctor_profile_edit(request):
    try:
        doctor = request.user.doctor_login_profile
        if not doctor.is_approved:
            messages.warning(request, "Your doctor profile is pending approval. You cannot edit it until approved.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        messages.error(request, "You are not registered as a doctor.")
        return redirect('register_clinic')

    if request.method == 'POST':
        form = DoctorProfileEditForm(request.POST, instance=doctor)
        if form.is_valid():
            doctor_instance = form.save(commit=False)
            doctor_instance.save()
            form.save_m2m()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('doctor_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorProfileEditForm(instance=doctor)

    context = {
        'form': form,
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_profile_edit.html', context)

@login_required
def doctor_slot_management(request):
    try:
        doctor = request.user.doctor_login_profile
        if not doctor.is_approved:
            messages.warning(request, "Your doctor profile is pending approval. You cannot manage slots until approved.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        messages.error(request, "You are not registered as a doctor.")
        return redirect('register_clinic')

    if request.method == 'POST':
        form = DoctorSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = doctor
            try:
                slot.save()
                messages.success(request, f"New slot created: {slot.date} {slot.start_time}-{slot.end_time}.")
                return redirect('doctor_slot_management')
            except Exception as e:
                messages.error(request, f"Error creating slot: {e}. (Perhaps an overlapping slot already exists?)")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorSlotForm()

    existing_slots = DoctorSlot.objects.filter(doctor=doctor).order_by('date', 'start_time')

    context = {
        'form': form,
        'existing_slots': existing_slots,
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_slot_management.html', context)

@login_required
def toggle_slot_availability(request, slot_id):
    if request.method == 'POST':
        try:
            slot = get_object_or_404(DoctorSlot, id=slot_id)
            
            try:
                current_doctor = request.user.doctor_login_profile
                if slot.doctor != current_doctor:
                    messages.error(request, "You are not authorized to modify this slot.")
                    return redirect('doctor_slot_management')
            except Doctor.DoesNotExist:
                messages.error(request, "You must be a registered doctor to perform this action.")
                return redirect('doctor_dashboard')
            
            if Appointment.objects.filter(
                appointment_slot=slot,
                status__in=['pending', 'confirmed']
            ).exists():
                messages.error(request, "Cannot block a slot that already has a booked appointment.")
                return redirect('doctor_slot_management')
            
            slot.is_available = not slot.is_available
            slot.save()
            
            status = "unblocked" if slot.is_available else "blocked"
            messages.success(request, f"Slot on {slot.date} at {slot.start_time} has been {status}.")
            
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
    
    return redirect('doctor_slot_management')

@login_required
def doctor_add_patient(request):
    try:
        doctor = request.user.doctor_login_profile
        if not doctor.is_approved:
            messages.warning(request, "Your doctor profile is pending approval. You cannot add patients until approved.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        messages.error(request, "You are not registered as a doctor.")
        return redirect('register_clinic')

    if request.method == 'POST':
        form = DoctorAddPatientForm(request.POST, doctor=doctor)
        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data
                
                patient_user = CustomUser.objects.create_user(
                    username=cleaned_data['patient_username'],
                    email=cleaned_data['patient_email'],
                    first_name=cleaned_data['patient_first_name'],
                    last_name=cleaned_data['patient_last_name'],
                    password='temp_password_123',
                    is_active=True
                )
                
                if hasattr(patient_user, 'phone'):
                    patient_user.phone = cleaned_data['patient_phone']
                    patient_user.save()
                
                selected_slot = cleaned_data['available_slot']
                
                if Appointment.objects.filter(
                    appointment_slot=selected_slot,
                    status__in=['pending', 'confirmed']
                ).exists():
                    patient_user.delete()
                    messages.error(request, "This slot is no longer available. Please select another time.")
                    form = DoctorAddPatientForm(doctor=doctor)
                    context = {'form': form, 'doctor': doctor}
                    return render(request, 'doctors/doctor_add_patient.html', context)
                
                appointment = Appointment.objects.create(
                    patient=patient_user,
                    doctor=doctor,
                    appointment_date=selected_slot.date,
                    appointment_time=selected_slot.start_time,
                    appointment_slot=selected_slot,
                    reason=cleaned_data.get('reason', ''),
                    appointment_type=cleaned_data.get('appointment_type', 'unpaid'),
                    status='confirmed'
                )
                
                selected_slot.is_available = False
                selected_slot.save()
                
                messages.success(
                    request, 
                    f"Patient {patient_user.get_full_name()} has been added successfully! "
                    f"Appointment booked for {appointment.appointment_date} at {appointment.appointment_time}. "
                    f"Patient username: {patient_user.username}, temporary password: temp_password_123"
                )
                
                return redirect('doctor_dashboard')
                
            except Exception as e:
                messages.error(request, f'An error occurred while adding the patient: {e}')
                if 'patient_user' in locals():
                    patient_user.delete()
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorAddPatientForm(doctor=doctor)

    context = {
        'form': form,
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_add_patient.html', context)

@login_required
def doctor_generate_slots(request):
    try:
        doctor = request.user.doctor_login_profile
        if not doctor.is_approved:
            messages.warning(request, "Your doctor profile is pending approval. You cannot generate slots until approved.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        messages.error(request, "You are not registered as a doctor.")
        return redirect('register_clinic')

    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            try:
                working_days = form.cleaned_data['working_days']
                start_time = form.cleaned_data['start_time']
                end_time = form.cleaned_data['end_time']
                slot_duration = form.cleaned_data['slot_duration']
                generate_for_weeks = form.cleaned_data['generate_for_weeks']
                
                doctor.working_days = working_days
                doctor.start_time = start_time
                doctor.end_time = end_time
                doctor.save()
                
                slots_created = generate_doctor_slots(doctor, slot_duration, generate_for_weeks)
                
                messages.success(
                    request, 
                    f"Working schedule updated and {slots_created} time slots generated successfully! "
                    f"Slots created for {generate_for_weeks} weeks ahead."
                )
                
                return redirect('doctor_slot_management')
                
            except Exception as e:
                messages.error(request, f'An error occurred while generating slots: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_data = {}
        if doctor.working_days:
            initial_data['working_days'] = doctor.working_days
        if doctor.start_time:
            initial_data['start_time'] = doctor.start_time
        if doctor.end_time:
            initial_data['end_time'] = doctor.end_time
        
        form = DoctorScheduleForm(initial=initial_data)

    context = {
        'form': form,
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_generate_slots.html', context)

def generate_doctor_slots(doctor, slot_duration, weeks_ahead):
    from datetime import timedelta
    
    slots_created = 0
    today = datetime.date.today()
    
    working_days = parse_working_days(doctor.working_days)
    
    slot_minutes = int(slot_duration)
    
    for week in range(weeks_ahead):
        for day_offset in range(7):
            current_date = today + timedelta(days=week * 7 + day_offset)
            
            if current_date.weekday() in working_days:
                day_slots = generate_slots_for_day(
                    doctor, current_date, doctor.start_time, 
                    doctor.end_time, slot_minutes
                )
                slots_created += day_slots
    
    return slots_created

def parse_working_days(working_days_str):
    working_days = []
    
    if working_days_str == 'Mon-Fri':
        working_days = [0, 1, 2, 3, 4]
    elif working_days_str == 'Mon-Sat':
        working_days = [0, 1, 2, 3, 4, 5]
    elif working_days_str == 'Mon-Sun':
        working_days = [0, 1, 2, 3, 4, 5, 6]
    elif working_days_str == 'Mon,Wed,Fri':
        working_days = [0, 2, 4]
    elif working_days_str == 'Tue,Thu,Sat':
        working_days = [1, 3, 5]
    elif working_days_str == 'Mon,Tue,Wed':
        working_days = [0, 1, 2]
    elif working_days_str == 'Thu,Fri,Sat':
        working_days = [3, 4, 5]
    elif working_days_str == 'Mon,Tue,Wed,Thu,Fri':
        working_days = [0, 1, 2, 3, 4]
    elif working_days_str == 'Mon,Tue,Wed,Thu,Fri,Sat':
        working_days = [0, 1, 2, 3, 4, 5]
    elif working_days_str == 'Mon,Tue,Wed,Thu,Fri,Sat,Sun':
        working_days = [0, 1, 2, 3, 4, 5, 6]
    
    return working_days

def generate_slots_for_day(doctor, date, start_time, end_time, slot_minutes):
    slots_created = 0
    
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    
    current_minutes = start_minutes
    while current_minutes + slot_minutes <= end_minutes:
        slot_start_hour = current_minutes // 60
        slot_start_minute = current_minutes % 60
        slot_start_time = datetime.time(slot_start_hour, slot_start_minute)
        
        slot_end_minutes = current_minutes + slot_minutes
        slot_end_hour = slot_end_minutes // 60
        slot_end_minute = slot_end_minutes % 60
        slot_end_time = datetime.time(slot_end_hour, slot_end_minute)
        
        if not DoctorSlot.objects.filter(
            doctor=doctor,
            date=date,
            start_time=slot_start_time,
            end_time=slot_end_time
        ).exists():
            DoctorSlot.objects.create(
                doctor=doctor,
                date=date,
                start_time=slot_start_time,
                end_time=slot_end_time,
                is_available=True
            )
            slots_created += 1
        
        current_minutes += slot_minutes
    
    return slots_created


