# healthcare_app_motihari/doctors/forms.py

from django import forms
from .models import Doctor, Specialty
from users.models import CustomUser # Import CustomUser for potential user creation
import datetime

class ClinicRegistrationForm(forms.ModelForm):
    # This field will handle the multiple specialties from the HTML form's <select multiple>
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=forms.CheckboxSelectMultiple, # Or forms.SelectMultiple if you want the multi-select box
        required=False, # Make it required at the form level if needed
        label="Main Specialties Offered"
    )

    # Add fields for creating a new user for the doctor if they'll log in
    # If you are keeping the OneToOneField on Doctor for 'user' login:
    username = forms.CharField(max_length=150, required=True, label="Login Username")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Login Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")


    class Meta:
        model = Doctor
        fields = [
            'full_name',
            'clinic_name',
            'clinic_address',
            'contact_phone',
            'contact_email',
            'qualifications',
            # 'specialties' is handled as a separate field above
        ]
        labels = {
            'full_name': 'Primary Doctor / Contact Person Name',
            'clinic_name': 'Clinic Name',
            'clinic_address': 'Clinic Address',
            'contact_phone': 'Contact Phone Number',
            'contact_email': 'Contact Email',
            'qualifications': 'Primary Doctor\'s Qualifications (Optional)',
        }
        widgets = {
            'clinic_address': forms.Textarea(attrs={'placeholder': 'Full address, including city and pin code'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': 'E.g., +91 9876543210'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'E.g., info@sharmaclinic.com'}),
            'qualifications': forms.Textarea(attrs={'placeholder': 'E.g., MBBS, MD (General Medicine)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        # You might also want to check if username or contact_email/phone already exist
        return cleaned_data

    def save(self, commit=True):
        # Override save method to create CustomUser first, then Doctor
        user_data = {
            'username': self.cleaned_data['username'],
            'password': self.cleaned_data['password'],
            'email': self.cleaned_data['contact_email'], # Use contact email as user's email
            'first_name': self.cleaned_data['full_name'].split(' ')[0] if self.cleaned_data['full_name'] else '',
            'last_name': ' '.join(self.cleaned_data['full_name'].split(' ')[1:]) if self.cleaned_data['full_name'] else '',
            'is_active': False # User is inactive until you manually approve or they verify email
        }
        user = CustomUser.objects.create_user(**user_data)

        # Save the Doctor instance
        doctor = super().save(commit=False) # Get the Doctor instance without saving to DB yet
        doctor.user = user # Link the Doctor to the newly created CustomUser
        if commit:
            doctor.save() # Save the Doctor instance
            # Handle ManyToManyField saving after the doctor instance is saved
            self.save_m2m() # This will save the specialties for the ManyToManyField

        return doctor
# healthcare_app_motihari/doctors/forms.py

from django import forms
from .models import Doctor, Specialty, Appointment
from users.models import CustomUser # Import CustomUser for potential user creation
from django.contrib.auth.forms import UserCreationForm # For PatientSignUpForm

# ... (ClinicRegistrationForm and PatientSignUpForm definitions) ...

# PatientSignUpForm (copy from above if not already there)
class PatientSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Choose a username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Your email address'})


# ClinicRegistrationForm (copy from previous answer if not already there)
class ClinicRegistrationForm(forms.ModelForm):
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Main Specialties Offered"
    )
    username = forms.CharField(max_length=150, required=True, label="Login Username")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Login Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")

    class Meta:
        model = Doctor
        fields = [
            'full_name', 'clinic_name', 'clinic_address', 'contact_phone',
            'contact_email', 'qualifications',
        ]
        labels = {
            'full_name': 'Primary Doctor / Contact Person Name',
            'clinic_name': 'Clinic Name',
            'clinic_address': 'Clinic Address',
            'contact_phone': 'Contact Phone Number',
            'contact_email': 'Contact Email',
            'qualifications': 'Primary Doctor\'s Qualifications (Optional)',
        }
        widgets = {
            'clinic_address': forms.Textarea(attrs={'placeholder': 'Full address, including city and pin code'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': 'E.g., +91 9876543210'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'E.g., info@sharmaclinic.com'}),
            'qualifications': forms.Textarea(attrs={'placeholder': 'E.g., MBBS, MD (General Medicine)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user_data = {
            'username': self.cleaned_data['username'],
            'password': self.cleaned_data['password'],
            'email': self.cleaned_data['contact_email'],
            'first_name': self.cleaned_data['full_name'].split(' ')[0] if self.cleaned_data['full_name'] else '',
            'last_name': ' '.join(self.cleaned_data['full_name'].split(' ')[1:]) if self.cleaned_data['full_name'] else '',
            'is_active': False
        }
        user = CustomUser.objects.create_user(**user_data)
        doctor = super().save(commit=False)
        doctor.user = user
        if commit:
            doctor.save()
            self.save_m2m()
        return doctor


# --- NEW APPOINTMENT BOOKING FORM STARTS HERE ---
class AppointmentBookingForm(forms.ModelForm):
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Preferred Date"
    )
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Preferred Time"
    )

    class Meta:
        model = Appointment
        fields = ['appointment_date', 'appointment_time', 'reason', 'appointment_type']
        labels = {
            'reason': 'Reason for Appointment (Optional)',
            'appointment_type': 'Appointment Type'
        }
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Briefly describe your reason for visit'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')

        # --- FIX STARTS HERE ---
        # Get today's date
        today = datetime.date.today()

        if appointment_date: # Only perform check if date is provided
            if appointment_date < today:
                self.add_error('appointment_date', "Appointment date cannot be in the past.")
            elif appointment_date == today:
                # If the date is today, check if the time is in the past
                now = datetime.datetime.now().time()
                if appointment_time and appointment_time < now:
                    self.add_error('appointment_time', "Appointment time cannot be in the past for today's date.")
        # --- FIX ENDS HERE ---

        # You'd typically check against doctor's available slots here, but for MVP, we'll keep it simple.

        return cleaned_data

