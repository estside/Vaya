from django.shortcuts import render

# Create your views here.
# healthcare_app_motihari/users/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from doctors.models import Doctor # Import the Doctor model

# ... (any other views in users/views.py, if any) ...


   
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages # Import messages
from doctors.models import Doctor # Import Doctor model
from .forms import PatientSignUpForm # Import the new form

# ... (existing custom_login_redirect view) ...

def patient_signup(request):
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # By default, UserCreationForm creates an active user.
            # You might want to set is_active=False here and require email verification later.
            # For now, let's assume they are active.
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login') # Redirect to login page after successful signup
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PatientSignUpForm()
    return render(request, 'users/patient_signup.html', {'form': form})
# healthcare_app_motihari/users/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from doctors.models import Doctor, Appointment # Import Doctor and Appointment models
from .forms import PatientSignUpForm

# ... (existing custom_login_redirect and patient_signup views) ...

@login_required
def patient_dashboard(request):
    """
    Displays the dashboard for a logged-in patient.
    Shows their profile and a list of their appointments.
    """
    user = request.user

    # Check if the logged-in user is actually a doctor.
    # If they are, redirect them to the doctor dashboard.
    try:
        doctor_profile = Doctor.objects.get(user=user)
        if doctor_profile.is_approved:
            return redirect('doctor_dashboard')
        else:
            # Doctor profile exists but is not approved
            messages.warning(request, "Your doctor profile is pending approval. Please wait for an administrator to approve it.")
            return redirect('landing_page')
    except Doctor.DoesNotExist:
        # This user is not a doctor, so they are a patient or general user. Proceed.
        pass

    # Fetch appointments for this patient
    # Order by appointment date and time
    upcoming_appointments = Appointment.objects.filter(
        patient=user,
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')

    past_appointments = Appointment.objects.filter(
        patient=user,
        status__in=['completed', 'cancelled']
    ).order_by('-appointment_date', '-appointment_time') # Order by most recent first

    context = {
        'user': user, # The CustomUser object for the patient
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'users/patient_dashboard.html', context)
# healthcare_app_motihari/users/views.py

# ... (imports) ...

@login_required
def custom_login_redirect(request):
    """
    Redirects logged-in users based on their profile type (e.g., Doctor or Patient).
    """
    user = request.user
    try:
        doctor_profile = Doctor.objects.get(user=user)
        if doctor_profile.is_approved:
            return redirect('doctor_dashboard')
        else:
            messages.warning(request, "Your doctor profile is pending approval. Please wait for an administrator to approve it.")
            return redirect('landing_page') # Or a specific 'pending_approval' page
    except Doctor.DoesNotExist:
        # If the user does NOT have a Doctor profile, assume they are a patient
        # and redirect them to the patient dashboard.
        return redirect('patient_dashboard') # <--- CHANGE THIS LINE
# healthcare_app_motihari/users/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from doctors.models import Doctor, Appointment # Import Doctor and Appointment models
from .forms import PatientSignUpForm

# ... (existing custom_login_redirect and patient_signup views) ...

@login_required
def patient_dashboard(request):
    """
    Displays the dashboard for a logged-in patient.
    Shows their profile and a list of their appointments.
    """
    user = request.user

    # Check if the logged-in user is actually a doctor.
    # If they are, redirect them to the doctor dashboard.
    try:
        doctor_profile = Doctor.objects.get(user=user)
        if doctor_profile.is_approved:
            return redirect('doctor_dashboard')
        else:
            # Doctor profile exists but is not approved
            messages.warning(request, "Your doctor profile is pending approval. Please wait for an administrator to approve it.")
            return redirect('landing_page')
    except Doctor.DoesNotExist:
        # This user is not a doctor, so they are a patient or general user. Proceed.
        pass

    # Fetch appointments for this patient
    # Order by appointment date and time
    upcoming_appointments = Appointment.objects.filter(
        patient=user,
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')

    past_appointments = Appointment.objects.filter(
        patient=user,
        status__in=['completed', 'cancelled']
    ).order_by('-appointment_date', '-appointment_time') # Order by most recent first

    context = {
        'user': user, # The CustomUser object for the patient
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'users/patient_dashboard.html', context)
# healthcare_app_motihari/users/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from doctors.models import Doctor, Appointment
from .forms import PatientSignUpForm, PatientProfileEditForm # Import new form

# ... (existing custom_login_redirect, patient_signup, patient_dashboard views) ...

@login_required
def patient_profile_edit(request):
    """
    Allows a logged-in patient to edit their profile information.
    """
    # Ensure this user is not a doctor trying to edit a patient profile
    try:
        if request.user.doctor_login_profile:
            messages.error(request, "Doctors manage their profiles via the Doctor Dashboard.")
            return redirect('doctor_dashboard')
    except Doctor.DoesNotExist:
        pass # This user is not a doctor, proceed as patient

    if request.method == 'POST':
        form = PatientProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('patient_dashboard') # Redirect back to patient dashboard
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PatientProfileEditForm(instance=request.user) # Pre-populate form with current user data

    context = {
        'form': form,
    }
    return render(request, 'users/patient_profile_edit.html', context)