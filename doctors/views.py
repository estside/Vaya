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
    specialty_filter = request.GET.get('specialty')
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