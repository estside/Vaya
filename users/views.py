from django.shortcuts import render

# Create your views here.
# healthcare_app_motihari/users/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from doctors.models import Doctor # Import the Doctor model

# ... (any other views in users/views.py, if any) ...

@login_required # This view itself requires login
def custom_login_redirect(request):
    """
    Redirects logged-in users based on their profile type (e.g., Doctor or Patient).
    """
    user = request.user
    try:
        # Check if the user has an associated Doctor profile
        doctor_profile = Doctor.objects.get(user=user)
        if doctor_profile.is_approved:
            # If they are an approved doctor, redirect to their dashboard
            return redirect('doctor_dashboard')
        else:
            # Doctor profile exists but is not approved
            messages.warning(request, "Your doctor profile is pending approval. Please wait for an administrator to approve it.")
            return redirect('landing_page') # Or a specific 'pending_approval' page
    except Doctor.DoesNotExist:
        # If the user does NOT have a Doctor profile, assume they are a patient
        # or a general user, and redirect them to a patient dashboard or homepage.
        # You'll build a patient dashboard later. For now, redirect to homepage.
        # messages.info(request, "Welcome, Patient!") # Optional message
        return redirect('landing_page') # Redirect to patient dashboard or general user page
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