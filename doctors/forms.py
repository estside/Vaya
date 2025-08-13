# healthcare_app_motihari/doctors/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.forms import formset_factory
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot

# Use the CustomUser model for the project
CustomUser = get_user_model()


class DoctorProfileEditForm(forms.ModelForm):
    """
    Form for doctors to edit their own profile.
    This form is used in a specific view where the doctor is already authenticated.
    """
    class Meta:
        model = Doctor
        fields = [
            'full_name',
            'clinic_name',
            'clinic_address',
            'contact_phone',
            'contact_email',
            'qualifications',
            'specialties',
            'working_days',
            'start_time',
            'end_time',
        ]
        widgets = {
            'specialties': forms.CheckboxSelectMultiple,
            'working_days': forms.CheckboxSelectMultiple(choices=Doctor.DAYS_OF_WEEK_CHOICES),
        }

class ClinicRegistrationForm(forms.ModelForm):
    """
    Form for new doctors/clinics to register with the platform.
    This form creates both a Doctor profile and a CustomUser account.
    """
    username = forms.CharField(max_length=150, help_text="Required. 150 characters or fewer.")
    password = forms.CharField(widget=forms.PasswordInput, help_text="Make sure it is a strong password.")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = Doctor
        fields = [
            'clinic_name',
            'clinic_address',
            'full_name',
            'contact_email',
            'contact_phone',
            'specialties',
            'qualifications',
        ]
        widgets = {
            'specialties': forms.CheckboxSelectMultiple,
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        # Check for unique username
        username = cleaned_data.get("username")
        if username and CustomUser.objects.filter(username=username).exists():
            self.add_error('username', "This username is already taken. Please choose another.")
        
        return cleaned_data
        
    def save(self, commit=True):
        # Create a new CustomUser instance first
        user = CustomUser.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['contact_email'],
            password=self.cleaned_data['password'],
            is_active=True # Set to False for admin approval workflow
        )
        # Now, save the Doctor model instance
        doctor = super().save(commit=False)
        doctor.user = user
        doctor.is_approved = False # Require admin approval
        if commit:
            doctor.save()
            self.save_m2m()  # Save the many-to-many relationship for specialties
        return doctor


class AppointmentBookingForm(forms.ModelForm):
    """
    Form for patients to book an appointment with a specific doctor.
    """
    class Meta:
        model = Appointment
        fields = ['appointment_slot', 'reason', 'appointment_type']
        labels = {
            'appointment_slot': 'Select an available slot',
            'reason': 'Reason for appointment',
            'appointment_type': 'Type of appointment',
        }
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if doctor:
            # Filter the appointment slots to only show available slots for the given doctor
            self.fields['appointment_slot'].queryset = DoctorSlot.objects.filter(
                doctor=doctor,
                is_available=True,
                date__gte=timezone.now().date()
            ).order_by('date', 'start_time')
            self.fields['appointment_slot'].label_from_instance = lambda obj: f"{obj.date.strftime('%Y-%m-%d')} - {obj.start_time.strftime('%I:%M %p')}"
            
class FollowupAppointmentForm(forms.Form):
    """
    A form for a doctor to book a follow-up appointment for a patient.
    """
    # This field will dynamically show only the doctor's available slots
    available_slot = forms.ModelChoiceField(
        queryset=DoctorSlot.objects.none(),
        label="Select an Available Slot",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    PAYMENT_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid (Coming Soon)'),
    )
    
    payment_status = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}),
        label="Payment Status"
    )

    comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        label="Add Appointment Comments (Optional)",
        required=False
    )
    
    # Optional field for reason, from the original Appointment model
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        label="Reason for Follow-up (Optional)",
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if doctor:
            self.fields['available_slot'].queryset = DoctorSlot.objects.filter(
                doctor=doctor,
                is_available=True,
                date__gte=timezone.now().date()
            ).order_by('date', 'start_time')
            self.fields['available_slot'].label_from_instance = lambda obj: f"{obj.date.strftime('%Y-%m-%d')} - {obj.start_time.strftime('%I:%M %p')}"

class ReportUploadForm(forms.ModelForm):
    """
    Form for uploading a medical report.
    """
    class Meta:
        model = Report
        fields = ['title', 'description', 'report_file', 'report_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'report_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['report_file'].required = True


class DoctorSlotForm(forms.ModelForm):
    class Meta:
        model = DoctorSlot
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class DoctorScheduleForm(forms.Form):
    # Now referencing the choices from the Doctor model
    working_days = forms.MultipleChoiceField(
        choices=Doctor.DAYS_OF_WEEK_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Working Days"
    )

    start_time = forms.TimeField(
        label="Start Time",
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    end_time = forms.TimeField(
        label="End Time",
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    slot_duration = forms.ChoiceField(
        label="Slot Duration (in minutes)",
        choices=[(15, '15'), (30, '30'), (45, '45'), (60, '60')],
        initial=30
    )

    generate_for_weeks = forms.IntegerField(
        label="Generate for how many weeks ahead?",
        min_value=1,
        max_value=52,
        initial=4
    )
    
class DoctorAddPatientForm(forms.Form):
    """
    A form to combine patient registration and appointment booking into a single workflow for doctors.
    """
    # Patient info fields (will create a new CustomUser)
    patient_username = forms.CharField(max_length=150)
    patient_email = forms.EmailField(required=False)
    patient_first_name = forms.CharField(max_length=150, required=False)
    patient_last_name = forms.CharField(max_length=150, required=False)
    patient_phone = forms.CharField(max_length=15, help_text="Required. Use format +91XXXXXXXXXX.")

    # Appointment info fields (will create a new Appointment and link to a DoctorSlot)
    available_slot = forms.ModelChoiceField(
        queryset=DoctorSlot.objects.none(),
        label="Select an Available Slot",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    appointment_type = forms.ChoiceField(
        choices=Appointment.APPOINTMENT_TYPE_CHOICES,
        label="Appointment Type",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        label="Reason for Appointment (Optional)",
        required=False
    )

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if doctor:
            self.fields['available_slot'].queryset = DoctorSlot.objects.filter(
                doctor=doctor,
                is_available=True,
                date__gte=timezone.now().date()
            ).order_by('date', 'start_time')
            self.fields['available_slot'].label_from_instance = lambda obj: f"{obj.date.strftime('%Y-%m-%d')} - {obj.start_time.strftime('%I:%M %p')}"

    def clean_patient_username(self):
        username = self.cleaned_data['patient_username']
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get("patient_phone")
        if not phone_number or not phone_number.startswith('+91') or not phone_number[3:].isdigit() or len(phone_number) != 13:
             self.add_error('patient_phone', "Enter a valid 10-digit Indian phone number (e.g., +91XXXXXXXXXX).")
        return cleaned_data