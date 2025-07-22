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