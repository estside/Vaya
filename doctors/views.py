# healthcare_app_motihari/doctors/views.py

from django.shortcuts import render
from .models import Doctor, Specialty
from django.shortcuts import render, redirect

def doctor_list(request):
    doctors = Doctor.objects.filter(is_approved=True).prefetch_related('specialties')
    specialties = Specialty.objects.all() # For filter options

    # Basic search functionality
    query = request.GET.get('q')
    if query:
        doctors = doctors.filter(full_name__icontains=query)

    # Basic filter by specialty
    specialty_filter = request.GET.get('specialties')
    if specialty_filter:
        doctors = doctors.filter(specialty__name=specialty_filter)

    context = {
        'doctors': doctors,
        'specialties': specialties,
        'current_query': query,
        'current_specialty': specialty_filter,
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

@login_required # Ensures only logged-in users can access this view
def doctor_dashboard(request):
    """
    Displays the dashboard for a logged-in doctor.
    Shows their profile and a list of their appointments.
    """
    try:
        # Attempt to get the Doctor profile linked to the logged-in user
        # The 'doctor_login_profile' is the related_name from CustomUser to Doctor
        doctor = request.user.doctor_login_profile
        # Check if the doctor profile is approved
        if not doctor.is_approved:
            messages.warning(request, "Your doctor profile is pending approval. Please wait for an administrator to approve it.")
            # Redirect to a generic page or back to homepage if not approved
            return redirect('landing_page') # Or a specific 'pending_approval' page

    except Doctor.DoesNotExist:
        # If the logged-in user is not linked to a Doctor profile
        messages.error(request, "You are not registered as a doctor, or your profile is incomplete. Please register your clinic.")
        return redirect('register_clinic') # Redirect to clinic registration

    # Fetch appointments for this doctor
    # Order by appointment date and time
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        status__in=['pending', 'confirmed'] # Only show pending/confirmed appointments
    ).order_by('appointment_date', 'appointment_time')

    past_appointments = Appointment.objects.filter(
        doctor=doctor,
        status__in=['completed', 'cancelled'] # Show completed/cancelled appointments
    ).order_by('-appointment_date', '-appointment_time') # Order by most recent first

    context = {
        'doctor': doctor,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'doctors/doctor_dashboard.html', context)
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