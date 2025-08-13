# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
import calendar
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot
from .forms import (
    ClinicRegistrationForm,
    AppointmentBookingForm,
    ReportUploadForm,
    DoctorProfileEditForm,
    DoctorSlotForm,
    DoctorScheduleForm,
    DoctorAddPatientForm,
    FollowupAppointmentForm
)
from users.models import CustomUser


def landing_page(request):
    """Renders the landing page."""
    return render(request, 'index.html')


def about_us(request):
    """Renders the about us page."""
    return render(request, 'about_us.html')


def is_doctor(user):
    """Check if the user is a doctor and their profile is approved."""
    return user.is_authenticated and hasattr(user, 'doctor_login_profile') and user.doctor_login_profile.is_approved


def doctor_list(request):
    """
    Renders a list of approved doctors with search and filter functionality.
    """
    doctors = Doctor.objects.filter(is_approved=True)

    query = request.GET.get('q')
    specialty_name = request.GET.get('specialty')

    if query:
        doctors = doctors.filter(
            Q(full_name__icontains=query) |
            Q(clinic_name__icontains=query)
        )

    if specialty_name and specialty_name != 'All Specialties':
        doctors = doctors.filter(specialties__name__iexact=specialty_name)

    # Use prefetch_related for a single query to get all specialties
    doctors = doctors.prefetch_related('specialties').distinct()
    
    specialties = Specialty.objects.all().order_by('name')

    context = {
        'doctors': doctors,
        'specialties': specialties,
        'current_query': query,
        'current_specialty': specialty_name,
    }
    return render(request, 'doctors/doctor_list.html', context)


def doctor_detail(request, doctor_id):
    """
    Renders the public profile page for a single doctor.
    """
    doctor = get_object_or_404(Doctor, id=doctor_id, is_approved=True)
    context = {
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_detail.html', context)


def register_clinic(request):
    """
    Handles the clinic registration form display and submission.
    """
    if request.method == 'POST':
        form = ClinicRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your clinic has been registered! It will be listed after admin approval.")
            return redirect('landing_page')
    else:
        form = ClinicRegistrationForm()

    context = {'form': form}
    return render(request, 'doctors/clinic_registration_form.html', context)


@login_required
@user_passes_test(lambda u: not is_doctor(u))
def book_appointment(request, doctor_id):
    """
    Renders the appointment booking form for a patient.
    """
    doctor = get_object_or_404(Doctor, id=doctor_id, is_approved=True)
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, doctor=doctor)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.save()

            # Mark the selected DoctorSlot as unavailable
            appointment.appointment_slot.is_available = False
            appointment.appointment_slot.save()

            messages.success(request, "Your appointment request has been sent successfully!")
            return redirect('appointment_success')
    else:
        form = AppointmentBookingForm(doctor=doctor)

    context = {
        'form': form,
        'doctor': doctor,
    }
    return render(request, 'doctors/book_appointment.html', context)


@login_required
@user_passes_test(is_doctor)
def book_followup_appointment(request, doctor_id, patient_id):
    """
    A view for a doctor to book a follow-up appointment for a specific patient.
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)
    patient = get_object_or_404(CustomUser, id=patient_id)
    
    # Ensure the logged-in user is the doctor of this clinic
    if request.user != doctor.user:
        messages.error(request, "You are not authorized to book a follow-up appointment for this patient.")
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        form = FollowupAppointmentForm(request.POST, doctor=doctor)
        if form.is_valid():
            slot = form.cleaned_data['available_slot']
            comment = form.cleaned_data['comments']
            payment_status = form.cleaned_data['payment_status']
            reason = form.cleaned_data['reason']

            # Create the appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_slot=slot,
                status='confirmed', # Doctor-booked appointments are auto-confirmed
                comments=comment,
                payment_status=payment_status,
                reason=reason,
                appointment_date=slot.date,
                appointment_time=slot.start_time,
            )

            # Mark the selected DoctorSlot as unavailable
            slot.is_available = False
            slot.save()

            messages.success(request, f"Follow-up appointment for {patient.username} has been successfully booked.")
            return redirect('doctor_patient_detail', patient_id=patient.id)
    else:
        form = FollowupAppointmentForm(doctor=doctor)
        
    context = {
        'form': form,
        'doctor': doctor,
        'patient': patient,
        'title': 'Book Follow-up Appointment',
    }
    return render(request, 'doctors/book_followup.html', context)


def appointment_success(request):
    """Renders the success page after an appointment request."""
    return render(request, 'doctors/appointment_success.html')


@login_required
@user_passes_test(is_doctor)
def confirm_appointment(request, appointment_id):
    """
    Allows a doctor to confirm a pending appointment.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Security check: Ensure the doctor is the one for this appointment
    if request.user != appointment.doctor.user:
        messages.error(request, "You are not authorized to confirm this appointment.")
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(request, "Appointment has been confirmed.")

    return redirect('doctor_dashboard')


@login_required
def cancel_appointment(request, appointment_id):
    """
    Allows a patient or a doctor to cancel an appointment.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Security check: Ensure the user is either the patient or the doctor
    if not (request.user == appointment.patient or (appointment.doctor and request.user == appointment.doctor.user)):
        messages.error(request, "You are not authorized to cancel this appointment.")
        if is_doctor(request.user):
            return redirect('doctor_dashboard')
        else:
            return redirect('patient_dashboard')

    if request.method == 'POST':
        if appointment.status in ['pending', 'confirmed']:
            appointment.status = 'cancelled'
            appointment.save()
            
            # If a slot was booked, make it available again
            if appointment.appointment_slot:
                appointment.appointment_slot.is_available = True
                appointment.appointment_slot.save()
            
            messages.success(request, "Appointment has been cancelled.")
        else:
            messages.warning(request, "This appointment cannot be cancelled.")
    
    if is_doctor(request.user):
        return redirect('doctor_dashboard')
    else:
        return redirect('patient_dashboard')


@login_required
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    """
    Renders the dashboard for an approved doctor.
    """
    doctor = get_object_or_404(Doctor, user=request.user)

    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')

    past_appointments_query = Q(appointment_date__lt=timezone.now().date()) | Q(appointment_date=timezone.now().date(), appointment_time__lte=timezone.now().time())
    past_appointments = Appointment.objects.filter(
        past_appointments_query,
        doctor=doctor,
        status__in=['confirmed', 'completed', 'cancelled']
    ).order_by('-appointment_date', '-appointment_time')
    
    # Corrected query: Get reports uploaded by this doctor OR reports belonging to patients of this doctor
    doctor_relevant_reports = Report.objects.filter(
        Q(doctor=doctor) | Q(patient__appointments__doctor=doctor)
    ).distinct().order_by('-uploaded_at').prefetch_related('patient', 'doctor')

    context = {
        'doctor': doctor,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'doctor_relevant_reports': doctor_relevant_reports,
    }
    return render(request, 'doctors/doctor_dashboard.html', context)


@login_required
@user_passes_test(is_doctor)
def doctor_profile_edit(request):
    """
    Allows a doctor to edit their profile details.
    """
    doctor = get_object_or_404(Doctor, user=request.user)
    if request.method == 'POST':
        form = DoctorProfileEditForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('doctor_dashboard')
    else:
        form = DoctorProfileEditForm(instance=doctor)
        
    context = {
        'form': form,
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_profile_edit.html', context)


@login_required
@user_passes_test(is_doctor)
def doctor_patient_detail(request, patient_id):
    """
    Allows a doctor to view a specific patient's details and history with them.
    """
    doctor = get_object_or_404(Doctor, user=request.user)
    patient = get_object_or_404(CustomUser, id=patient_id)
    
    if not Appointment.objects.filter(doctor=doctor, patient=patient).exists():
        messages.error(request, "You are not authorized to view this patient's details.")
        return redirect('doctor_dashboard')
    
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        patient=patient,
        appointment_date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')

    past_appointments_query = Q(appointment_date__lt=timezone.now().date()) | Q(appointment_date=timezone.now().date(), appointment_time__lte=timezone.now().time())
    past_appointments = Appointment.objects.filter(
        past_appointments_query,
        doctor=doctor,
        patient=patient,
        status__in=['confirmed', 'completed', 'cancelled']
    ).order_by('-appointment_date', '-appointment_time')
    
    reports = Report.objects.filter(patient=patient).order_by('-uploaded_at')

    context = {
        'doctor': doctor,
        'patient': patient,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'reports': reports,
    }
    return render(request, 'doctors/doctor_patient_detail.html', context)


@login_required
def patient_upload_report(request):
    """
    Allows a patient to upload a report for themselves.
    """
    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = request.user
            report.save()
            messages.success(request, "Your report has been uploaded successfully!")
            return redirect('patient_dashboard')
    else:
        form = ReportUploadForm()

    context = {
        'form': form,
        'title': 'Upload Your Medical Report',
    }
    return render(request, 'doctors/report_upload_form.html', context)


@login_required
@user_passes_test(is_doctor)
def doctor_upload_report(request, patient_id):
    """
    Allows a doctor to upload a report for a specific patient.
    """
    doctor = get_object_or_404(Doctor, user=request.user)
    patient = get_object_or_404(CustomUser, id=patient_id)

    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = patient
            report.doctor = doctor
            report.save()
            messages.success(request, f"Report for {patient.username} has been uploaded successfully!")
            return redirect('doctor_patient_detail', patient_id=patient.id)
    else:
        form = ReportUploadForm()

    context = {
        'form': form,
        'doctor': doctor,
        'patient': patient,
        'title': 'Upload Report for Patient',
    }
    return render(request, 'doctors/report_upload_form.html', context)


@login_required
@user_passes_test(is_doctor)
def doctor_slot_management(request):
    """
    Allows a doctor to manually add a single time slot.
    """
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if request.method == 'POST':
        form = DoctorSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = doctor
            slot.is_available = True
            slot.save()
            messages.success(request, "Time slot added successfully!")
            return redirect('doctor_slot_management')
    else:
        form = DoctorSlotForm()

    existing_slots = DoctorSlot.objects.filter(
        doctor=doctor,
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')

    context = {
        'form': form,
        'doctor': doctor,
        'existing_slots': existing_slots,
    }
    return render(request, 'doctors/doctor_slot_management.html', context)


@login_required
@user_passes_test(is_doctor)
def doctor_generate_slots(request):
    """
    Allows a doctor to automatically generate time slots based on a schedule.
    """
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            working_days = form.cleaned_data['working_days']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            slot_duration = int(form.cleaned_data['slot_duration'])
            generate_for_weeks = form.cleaned_data['generate_for_weeks']
            
            doctor.working_days = ','.join(working_days)
            doctor.start_time = start_time
            doctor.end_time = end_time
            doctor.save()
            
            today = timezone.now().date()
            end_date = today + timedelta(weeks=generate_for_weeks)
            
            day_names = {name: i for i, name in enumerate(calendar.day_name)}
            
            current_date = today + timedelta(days=1)
            
            while current_date <= end_date:
                if calendar.day_name[current_date.weekday()] in working_days:
                    
                    current_time = datetime.combine(current_date, start_time)
                    end_time_dt = datetime.combine(current_date, end_time)
                    
                    while current_time.time() < end_time_dt.time():
                        slot_end_time = (current_time + timedelta(minutes=slot_duration)).time()
                        
                        DoctorSlot.objects.get_or_create(
                            doctor=doctor,
                            date=current_date,
                            start_time=current_time.time(),
                            end_time=slot_end_time,
                        )
                        current_time += timedelta(minutes=slot_duration)
                        
                current_date += timedelta(days=1)
            
            messages.success(request, f"{DoctorSlot.objects.filter(doctor=doctor, date__gte=today).count()} slots generated successfully!")
            return redirect('doctor_slot_management')
    else:
        form = DoctorScheduleForm(initial={
            'working_days': doctor.working_days.split(',') if doctor.working_days else [],
            'start_time': doctor.start_time,
            'end_time': doctor.end_time,
        })
    
    context = {
        'form': form,
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_generate_slots.html', context)


@login_required
@user_passes_test(is_doctor)
def doctor_add_patient(request):
    """
    Allows a doctor to create a new patient account and book a confirmed appointment.
    """
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == 'POST':
        form = DoctorAddPatientForm(request.POST, doctor=doctor)
        if form.is_valid():
            patient_username = form.cleaned_data['patient_username']
            patient_email = form.cleaned_data['patient_email']
            patient_first_name = form.cleaned_data['patient_first_name']
            patient_last_name = form.cleaned_data['patient_last_name']
            patient_phone = form.cleaned_data['patient_phone']

            temp_password = CustomUser.objects.make_random_password()
            
            patient_user = CustomUser.objects.create_user(
                username=patient_username,
                password=temp_password,
                email=patient_email,
                first_name=patient_first_name,
                last_name=patient_last_name,
                phone_number=patient_phone
            )
            patient_user.save()

            slot = form.cleaned_data['available_slot']
            reason = form.cleaned_data['reason']
            appointment_type = form.cleaned_data['appointment_type']

            appointment = Appointment.objects.create(
                patient=patient_user,
                doctor=doctor,
                appointment_slot=slot,
                reason=reason,
                appointment_type=appointment_type,
                status='confirmed',
                appointment_date=slot.date,
                appointment_time=slot.start_time,
            )

            slot.is_available = False
            slot.save()

            messages.success(request, f"Patient {patient_username} has been added and appointment booked successfully!")
            messages.info(request, f"Temporary Password for {patient_username} is: {temp_password}. Please share it with them securely.")

            return redirect('doctor_dashboard')
    else:
        form = DoctorAddPatientForm(doctor=doctor)

    context = {
        'form': form,
        'doctor': doctor,
    }
    return render(request, 'doctors/doctor_add_patient.html', context)


@login_required
@user_passes_test(is_doctor)
def toggle_slot_availability(request, slot_id):
    """
    Allows a doctor to toggle the availability of a specific slot.
    """
    slot = get_object_or_404(DoctorSlot, id=slot_id)
    
    if request.user != slot.doctor.user:
        messages.error(request, "You are not authorized to modify this slot.")
        return redirect('doctor_slot_management')

    if request.method == 'POST':
        if slot.is_available:
            slot.is_available = False
            messages.info(request, f"Slot on {slot.date} at {slot.start_time.strftime('%I:%M %p')} has been blocked.")
        else:
            slot.is_available = True
            messages.success(request, f"Slot on {slot.date} at {slot.start_time.strftime('%I:%M %p')} has been unblocked.")
        slot.save()
    
    return redirect('doctor_slot_management')