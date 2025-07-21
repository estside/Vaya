# healthcare_app_motihari/users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class PatientSignUpForm(UserCreationForm):
    # You can add extra fields here if patients need them later, e.g., phone_number, address
    # For now, we'll keep it simple, just extending the default UserCreationForm fields.

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email',) # Include email field
        # If you added phone_number to CustomUser, you'd add it here too:
        # fields = UserCreationForm.Meta.fields + ('email', 'phone_number',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Add placeholders or customize widgets
        self.fields['username'].widget.attrs.update({'placeholder': 'Choose a username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Your email address'})
# healthcare_app_motihari/users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from doctors.models import Doctor, Specialty, Appointment # Ensure these are imported if other forms use them

# ... (PatientSignUpForm and ClinicRegistrationForm definitions) ...

class PatientProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name'] # Add more fields if CustomUser has them
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
        }
        widgets = {
            'username': forms.TextInput(attrs={'readonly': 'readonly'}), # Make username read-only
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is already taken by another user (excluding current user)
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email