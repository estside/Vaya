# healthcare_app_motihari/doctors/forms.py

from django import forms
from .models import Doctor, Specialty
from users.models import CustomUser # Import CustomUser for potential user creation

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