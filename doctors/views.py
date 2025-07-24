# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render
from .models import Doctor, Specialty,models
from django.shortcuts import render, redirect

def doctor_list(request):
    doctors = Doctor.objects.filter(is_approved=True).prefetch_related('specialties')
    specialties = Specialty.objects.all() # For filter options

    # Basic search functionality
    query = request.GET.get('q') # <--- Check if 'q' is correctly retrieved
    if query:
        # Filter by full_name containing the query (case-insensitive)
        doctors = doctors.filter(full_name__icontains=query)

    # Basic filter by specialty
    specialty_filter = request.GET.get('specialty') # <--- Check if 'specialty' is correctly retrieved
    if specialty_filter:
        # Filter by specialties (ManyToManyField lookup)
        # This filters doctors who have a specialty with that exact name
        doctors = doctors.filter(specialties__name=specialty_filter)

    context = {
        'doctors': doctors,
        'specialties': specialties,
        'current_query': query, # <--- Pass back the current query for input field
        'current_specialty': specialty_filter, # <--- Pass back the current specialty for select field
    }
    return render(request, 'doctors/doctor_list.html', context)

def doctor_detail(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id) # Or use get_object_or_404
    context = {'doctor': doctor}
    return render(request, 'doctors/doctor_detail.html', context)
from .models import Doctor, Specialty
from .forms import ClinicRegistrationForm
from django.contrib import messages

def register_clinic(request):
    if request.method == 'POST':
        form = ClinicRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # The form's save method now handles CustomUser creation and Doctor saving
                doctor = form.save()
                messages.success(request, 'Your clinic registration has been submitted successfully! We will review your details soon.')
                return redirect('clinic_registration_success') # Redirect to a success page
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Populate specialties for the HTML form's dropdown
        specialties = Specialty.objects.all()
        # You can pass initial data to form if needed.
        form = ClinicRegistrationForm()

    context = {
        'form': form,
        'specialties': Specialty.objects.all() # Pass all specialties for the template
    }
    return render(request, 'doctors/clinic_registration_form.html', context)

def clinic_registration_success(request):
    return render(request, 'doctors/clinic_registration_success.html')
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment # Import Appointment
from .forms import ClinicRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required # Import login_required

# ... (existing doctor_list, doctor_detail, register_clinic, clinic_registration_success views) ...


# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm # Import new forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# ... (existing doctor_list, doctor_detail, register_clinic, clinic_registration_success, doctor_dashboard views) ...

@login_required # Only logged-in users (patients) can book appointments
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id, is_approved=True)

    # Ensure the logged-in user is not a doctor trying to book for themselves
    # Or, if a doctor is allowed to book for a patient, adjust this logic.
    # For now, assuming only patients book.
    try:
        if request.user.doctor_login_profile:
            messages.error(request, "Doctors cannot book appointments for themselves using this form.")
            return redirect('doctor_dashboard') # Or appropriate redirect
    except Doctor.DoesNotExist:
        pass # This user is not a doctor, proceed as patient

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False) # Don't save to DB yet
            appointment.patient = request.user # Link to the logged-in patient
            appointment.doctor = doctor # Link to the doctor from the URL
            appointment.save() # Now save the appointment

            messages.success(request, f"Your appointment with Dr. {doctor.full_name} on {appointment.appointment_date} at {appointment.appointment_time} has been requested. It is currently pending confirmation.")
            return redirect('appointment_success') # Redirect to a success page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentBookingForm()

    context = {
        'doctor': doctor,
        'form': form,
    }
    return render(request, 'doctors/book_appointment.html', context)

def appointment_success(request):
    """
    Simple success page after appointment booking.
    """
    return render(request, 'doctors/appointment_success.html')
# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404 # Import Http404

# ... (existing doctor_list, doctor_detail, register_clinic, clinic_registration_success, doctor_dashboard, book_appointment, appointment_success views) ...

@login_required
def confirm_appointment(request, appointment_id):
    """
    Allows a doctor to confirm a pending appointment.
    """
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)

        # Security check: Ensure the logged-in user is the doctor associated with this appointment
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
            messages.success(request, f"Appointment with {appointment.patient.username} on {appointment.appointment_date} confirmed.")
        else:
            messages.warning(request, "Only pending appointments can be confirmed.")
        return redirect('doctor_dashboard')
    else:
        raise Http404("Only POST requests are allowed for this action.")


@login_required
def cancel_appointment(request, appointment_id):
    """
    Allows a doctor (or potentially patient later) to cancel an appointment.
    """
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)

        # Security check: Ensure the logged-in user is the doctor associated with this appointment
        # Or if it's a patient cancelling their own appointment
        try:
            current_doctor = request.user.doctor_login_profile
            if appointment.doctor != current_doctor:
                messages.error(request, "You are not authorized to cancel this appointment.")
                return redirect('doctor_dashboard')
        except Doctor.DoesNotExist:
            # If not a doctor, check if it's the patient themselves
            if appointment.patient != request.user:
                messages.error(request, "You are not authorized to cancel this appointment.")
                return redirect('patient_dashboard') # Redirect to patient dashboard if not their appointment

        if appointment.status in ['pending', 'confirmed']: # Can cancel pending or confirmed
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, f"Appointment with {appointment.patient.username} on {appointment.appointment_date} has been cancelled.")
        else:
            messages.warning(request, "This appointment cannot be cancelled as it is already completed or cancelled.")
        return redirect('doctor_dashboard')
    else:
        raise Http404("Only POST requests are allowed for this action.")
# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report # Import Report
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm # Import ReportUploadForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser # Import CustomUser for doctor_upload_report

# ... (existing views: doctor_list, doctor_detail, register_clinic, clinic_registration_success,
#      doctor_dashboard, book_appointment, appointment_success, confirm_appointment, cancel_appointment) ...

@login_required
def patient_upload_report(request):
    """
    Allows a logged-in patient to upload their own medical report.
    """
    # Ensure this user is not a doctor trying to upload patient reports here
    try:
        if request.user.doctor_login_profile:
            messages.error(request, "Doctors upload reports via specific patient/appointment context.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        pass # This user is a patient, proceed.

    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES) # request.FILES is crucial for file uploads
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = request.user # Link report to the logged-in patient
            # doctor field will be null if patient uploads it themselves
            report.save()
            messages.success(request, 'Your report has been uploaded successfully!')
            return redirect('patient_dashboard') # Redirect to patient dashboard
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
    """
    Allows a logged-in doctor to upload a report for a specific patient.
    """
    # Security check: Ensure the logged-in user is a doctor
    try:
        current_doctor = request.user.doctor_login_profile
        if not current_doctor.is_approved:
            messages.error(request, "Your doctor profile is not approved.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        messages.error(request, "You must be a registered and approved doctor to perform this action.")
        return redirect('doctor_dashboard')

    # Get the patient for whom the report is being uploaded
    patient = get_object_or_404(CustomUser, id=patient_id)

    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = patient # Link report to the specified patient
            report.doctor = current_doctor # Link report to the logged-in doctor
            report.save()
            messages.success(request, f'Report for {patient.username} uploaded successfully by Dr. {current_doctor.full_name}!')
            # Redirect back to doctor dashboard or a patient's detail view for the doctor
            return redirect('doctor_dashboard') # For simplicity, redirect to doctor dashboard
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReportUploadForm()

    context = {
        'form': form,
        'patient': patient,
        'title': f'Upload Report for {patient.username}'
    }
    return render(request, 'doctors/report_upload_form.html', context) # Reusing the same template
# healthcare_app_motihari/users/views.py

# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report # Ensure Report is imported
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser
from django.db.models import Q # <--- Import Q object for complex queries

# ... (existing views) ...

@login_required
def doctor_dashboard(request):
    """
    Displays the dashboard for a logged-in doctor.
    Shows their profile and a list of their appointments and relevant reports.
    """
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

    # --- FIX/CONFIRMATION: Fetch reports for this doctor ---
    # Fetch reports where:
    # 1. The logged-in doctor is the uploader (report.doctor = current_doctor)
    # OR
    # 2. The patient associated with the report has an appointment with this doctor.
    #    We need to get all patient IDs that have appointments with this doctor first.

    # Get IDs of patients who have ever had an appointment with this doctor
    patient_ids_with_appointments = Appointment.objects.filter(doctor=doctor).values_list('patient__id', flat=True).distinct()

    doctor_relevant_reports = Report.objects.filter(
        Q(doctor=doctor) | Q(patient__id__in=patient_ids_with_appointments)
    ).order_by('-uploaded_at').distinct() # Use distinct to avoid duplicates if a report matches both Q objects
    # --------------------------------------------------------

    context = {
        'doctor': doctor,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'doctor_relevant_reports': doctor_relevant_reports, # Ensure this is passed to context
    }
    return render(request, 'doctors/doctor_dashboard.html', context)
# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser
from django.db.models import Q

# ... (existing views: doctor_list, doctor_detail, doctor_dashboard, book_appointment, appointment_success,
#      confirm_appointment, cancel_appointment, patient_upload_report, doctor_upload_report) ...

def register_clinic(request):
    if request.method == 'POST':
        form = ClinicRegistrationForm(request.POST)
        if form.is_valid():
            try:
                doctor = form.save()
                messages.success(request, 'Your clinic registration has been submitted successfully! We will review your details soon and notify you via email.')
                # --- CHANGE HERE: Re-render the form with a new, empty instance ---
                form = ClinicRegistrationForm() # Create a new, empty form instance to clear the form
                # ------------------------------------------------------------------
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClinicRegistrationForm()

    context = {
        'form': form,
        'specialties': Specialty.objects.all() # Pass all specialties for the template
    }
    return render(request, 'doctors/clinic_registration_form.html', context)

# --- REMOVE OR COMMENT OUT THIS VIEW if you want to show message on same page ---
# def clinic_registration_success(request):
#     return render(request, 'doctors/clinic_registration_success.html')
# ------------------------------------------------------------------------------
# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm, DoctorProfileEditForm # Import new form
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser
from django.db.models import Q

# ... (existing views) ...

@login_required
def doctor_profile_edit(request):
    """
    Allows a logged-in doctor to edit their profile information and availability.
    """
    try:
        doctor = request.user.doctor_login_profile
        if not doctor.is_approved:
            messages.warning(request, "Your doctor profile is pending approval. You cannot edit it until approved.")
            return redirect('doctor_dashboard') # Or landing_page
    except Doctor.DoesNotExist:
        messages.error(request, "You are not registered as a doctor.")
        return redirect('register_clinic')

    if request.method == 'POST':
        form = DoctorProfileEditForm(request.POST, instance=doctor)
        if form.is_valid():
            # Save the Doctor instance
            doctor_instance = form.save(commit=False)
            doctor_instance.save() # Save the doctor's non-M2M fields
            form.save_m2m() # Save the ManyToManyField (specialties)
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('doctor_dashboard') # Redirect back to doctor dashboard
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorProfileEditForm(instance=doctor) # Pre-populate form with current doctor data

    context = {
        'form': form,
        'doctor': doctor, # Pass doctor object for template title/context
    }
    return render(request, 'doctors/doctor_profile_edit.html', context)
# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm, DoctorProfileEditForm # Ensure DoctorProfileEditForm is imported
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser
from django.db.models import Q
import datetime # Ensure datetime is imported

# ... (existing views) ...

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
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment_date = form.cleaned_data.get('appointment_date')
            appointment_time = form.cleaned_data.get('appointment_time')

            # --- NEW: Check Doctor's Availability ---
            # Basic check: Is the requested day one of the doctor's working days?
            # And is the time within their working hours?
            if doctor.working_days and doctor.start_time and doctor.end_time:
                # Convert working_days string to a list of day names (e.g., "Mon-Fri" -> ["Monday", "Tuesday", ...])
                # This is a very basic parsing. For production, consider a more robust system.
                # For simplicity, let's assume working_days is comma-separated like "Monday,Tuesday" or "Mon-Fri"
                # A more robust solution would involve a dedicated parsing function or a better model field.

                # Let's assume working_days is a comma-separated list of 3-letter day abbreviations (e.g., "Mon,Tue,Wed")
                # Or a simple string like "Mon-Fri"
                # For this MVP, we'll do a simple check.
                day_of_week_abbr = appointment_date.strftime('%a') # e.g., 'Mon', 'Tue'
                day_of_week_full = appointment_date.strftime('%A') # e.g., 'Monday', 'Tuesday'

                is_working_day = False
                if doctor.working_days:
                    # Simple check for common patterns or comma-separated list
                    if 'Mon-Fri' in doctor.working_days and appointment_date.weekday() < 5: # 0=Mon, 4=Fri
                        is_working_day = True
                    elif 'Sat-Sun' in doctor.working_days and appointment_date.weekday() >= 5: # 5=Sat, 6=Sun
                        is_working_day = True
                    elif day_of_week_abbr in doctor.working_days or day_of_week_full in doctor.working_days:
                        is_working_day = True
                    elif ',' in doctor.working_days and day_of_week_abbr in doctor.working_days.split(','):
                        is_working_day = True
                    # Add more sophisticated parsing if working_days format is complex

                if not is_working_day:
                    messages.error(request, f"Dr. {doctor.full_name} does not typically work on {day_of_week_full}s.")
                    return render(request, 'doctors/book_appointment.html', {'doctor': doctor, 'form': form})

                if not (doctor.start_time <= appointment_time <= doctor.end_time):
                    messages.error(request, f"Dr. {doctor.full_name} is available between {doctor.start_time.strftime('%I:%M %p')} and {doctor.end_time.strftime('%I:%M %p')}.")
                    return render(request, 'doctors/book_appointment.html', {'doctor': doctor, 'form': form})
            else:
                # If doctor has not set availability, optionally warn or allow
                messages.warning(request, "Doctor's specific working hours are not set. Your request will be manually reviewed.")
            # --- END NEW: Check Doctor's Availability ---

            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.save()

            messages.success(request, f"Your appointment with Dr. {doctor.full_name} on {appointment.appointment_date} at {appointment.appointment_time} has been requested. It is currently pending confirmation.")
            return redirect('appointment_success')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentBookingForm()

    context = {
        'doctor': doctor,
        'form': form,
    }
# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot # Import DoctorSlot
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm, DoctorProfileEditForm, DoctorSlotForm # Import DoctorSlotForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser
from django.db.models import Q
import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

# ... (existing views) ...

@login_required
def doctor_slot_management(request):
    """
    Allows a logged-in doctor to manage their available time slots.
    """
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
            slot.doctor = doctor # Link the slot to the logged-in doctor
            try:
                slot.save()
                messages.success(request, f"New slot created: {slot.date} {slot.start_time}-{slot.end_time}.")
                return redirect('doctor_slot_management') # Redirect to refresh the list
            except Exception as e: # Catch potential unique_together errors
                messages.error(request, f"Error creating slot: {e}. (Perhaps an overlapping slot already exists?)")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorSlotForm()

    # Fetch existing slots for this doctor, ordered by date and time
    existing_slots = DoctorSlot.objects.filter(doctor=doctor).order_by('date', 'start_time')

    context = {
        'form': form,
        'existing_slots': existing_slots,
        'doctor': doctor, # Pass doctor for template context
    }
    return render(request, 'doctors/doctor_slot_management.html', context)
# healthcare_app_motihari/doctors/views.py

# ... (imports) ...

@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id, is_approved=True)

    # --- FIX STARTS HERE ---
    # Check if the logged-in user is a doctor. If so, redirect them.
    # This block needs to ensure it always returns if the condition is met.
    try:
        # Attempt to get the doctor profile for the logged-in user
        logged_in_doctor_profile = request.user.doctor_login_profile
        # If the user is a doctor, they should not use this form to book appointments for themselves
        messages.error(request, "Doctors cannot book appointments for themselves using this form.")
        return redirect('doctor_dashboard') # Always return a redirect if they are a doctor
    except Doctor.DoesNotExist:
        # This means the logged-in user does not have a doctor_login_profile,
        # so they are a patient or a general user. Proceed with booking.
        pass
    # --- FIX ENDS HERE ---


    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment_date = form.cleaned_data.get('appointment_date')
            appointment_time = form.cleaned_data.get('appointment_time')

            if doctor.working_days and doctor.start_time and doctor.end_time:
                day_of_week_full = appointment_date.strftime('%A')
                is_working_day = False
                if 'Mon-Fri' in doctor.working_days and appointment_date.weekday() < 5:
                    is_working_day = True
                elif 'Sat-Sun' in doctor.working_days and appointment_date.weekday() >= 5:
                    is_working_day = True
                elif day_of_week_full in doctor.working_days.split(','):
                    is_working_day = True
                elif appointment_date.strftime('%a') in doctor.working_days.split(','):
                    is_working_day = True


                if not is_working_day:
                    messages.error(request, f"Dr. {doctor.full_name} does not typically work on {day_of_week_full}s.")
                    return render(request, 'doctors/book_appointment.html', {'doctor': doctor, 'form': form})

                if not (doctor.start_time <= appointment_time <= doctor.end_time):
                    messages.error(request, f"Dr. {doctor.full_name} is available between {doctor.start_time.strftime('%I:%M %p')} and {doctor.end_time.strftime('%I:%M %p')}.")
                    return render(request, 'doctors/book_appointment.html', {'doctor': doctor, 'form': form})
            else:
                messages.warning(request, "Doctor's specific working hours are not set. Your request will be manually reviewed.")

            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.save()

            messages.success(request, f"Your appointment with Dr. {doctor.full_name} on {appointment.appointment_date} at {appointment.appointment_time} has been requested. It is currently pending confirmation.")
            return redirect('appointment_success')
        else:
            messages.error(request, 'Please correct the errors below.')
    else: # This block handles GET requests or invalid POST submissions
        form = AppointmentBookingForm()

    context = {
        'doctor': doctor,
        'form': form,
    }
    return render(request, 'doctors/book_appointment.html', context)
# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot # Import DoctorSlot
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm, DoctorProfileEditForm, DoctorSlotForm # Import DoctorSlotForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser
from django.db.models import Q
import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

# ... (existing views) ...

@login_required
def doctor_slot_management(request):
    """
    Allows a logged-in doctor to manage their available time slots.
    """
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
            slot.doctor = doctor # Link the slot to the logged-in doctor
            try:
                slot.save()
                messages.success(request, f"New slot created: {slot.date} {slot.start_time}-{slot.end_time}.")
                return redirect('doctor_slot_management') # Redirect to refresh the list
            except Exception as e: # Catch potential unique_together errors
                messages.error(request, f"Error creating slot: {e}. (Perhaps an overlapping slot already exists?)")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorSlotForm()

    # Fetch existing slots for this doctor, ordered by date and time
    existing_slots = DoctorSlot.objects.filter(doctor=doctor).order_by('date', 'start_time')

    context = {
        'form': form,
        'existing_slots': existing_slots,
        'doctor': doctor, # Pass doctor for template context
    }
    return render(request, 'doctors/doctor_slot_management.html', context)
# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot # Ensure DoctorSlot is imported
from .forms import ClinicRegistrationForm, PatientSignUpForm, AppointmentBookingForm, ReportUploadForm, DoctorProfileEditForm, DoctorSlotForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from users.models import CustomUser
from django.db.models import Q
import datetime
# Removed email imports as per previous instruction to skip email for now
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.conf import settings

# ... (existing views) ...

@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id, is_approved=True)

    try:
        logged_in_doctor_profile = request.user.doctor_login_profile
        messages.error(request, "Doctors cannot book appointments for themselves using this form.")
        return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        pass

    if request.method == 'POST':
        # Pass the doctor instance to the form for queryset filtering
        form = AppointmentBookingForm(request.POST, doctor=doctor)
        if form.is_valid():
            # Get the selected DoctorSlot object from the form
            selected_slot = form.cleaned_data['available_slot']

            # Check if this slot is already booked by another pending/confirmed appointment
            # This is a crucial check to prevent double booking the same DoctorSlot
            if Appointment.objects.filter(
                appointment_slot=selected_slot,
                status__in=['pending', 'confirmed']
            ).exists():
                messages.error(request, "This slot is no longer available. Please select another time.")
                # Re-render the form with updated available slots
                form = AppointmentBookingForm(doctor=doctor) # Re-initialize form with doctor to refresh slots
                context = {'doctor': doctor, 'form': form}
                return render(request, 'doctors/book_appointment.html', context)


            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.appointment_date = selected_slot.date # Set date from slot
            appointment.appointment_time = selected_slot.start_time # Set time from slot (start_time of slot)
            appointment.appointment_slot = selected_slot # <--- IMPORTANT: Link to the selected slot
            appointment.save()

            # Mark the selected slot as unavailable after successful booking
            selected_slot.is_available = False
            selected_slot.save()

            messages.success(request, f"Your appointment with Dr. {doctor.full_name} on {appointment.appointment_date} at {appointment.appointment_time} has been requested. It is currently pending confirmation.")
            return redirect('appointment_success')
        else:
            messages.error(request, 'Please correct the errors below.')
    else: # GET request
        # Pass the doctor instance to the form for queryset filtering
        form = AppointmentBookingForm(doctor=doctor)

    context = {
        'doctor': doctor,
        'form': form,
    }
    return render(request, 'doctors/book_appointment.html', context)

# ... (rest of the views, including confirm_appointment and cancel_appointment) ...

# --- Update confirm_appointment to affect DoctorSlot ---
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

            # Mark associated DoctorSlot as unavailable
            if appointment.appointment_slot: # Check if a slot is linked
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

# --- Update cancel_appointment to affect DoctorSlot ---
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

            # Mark associated DoctorSlot as available again
            if appointment.appointment_slot: # Check if a slot is linked
                appointment.appointment_slot.is_available = True
                appointment.appointment_slot.save()
            else:
                messages.warning(request, "Associated time slot not found or already available.")

            redirect_url = 'doctor_dashboard' if canceller_is_doctor else 'patient_dashboard'
            return redirect(redirect_url)
        else:
            messages.warning(request, "This appointment cannot be cancelled as it is already completed or cancelled.")
        return redirect('doctor_dashboard') # Fallback redirect if not cancelled
    else:
        raise Http404("Only POST requests are allowed for this action.")