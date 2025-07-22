# healthcare_app_motihari/users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

# healthcare_app_motihari/users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser # Ensure CustomUser is imported
# ... (other imports) ...

class PatientSignUpForm(UserCreationForm):
    # Add new fields for patient signup
    first_name = forms.CharField(max_length=150, required=False, label="First Name")
    last_name = forms.CharField(max_length=150, required=False, label="Last Name")
    phone_number = forms.CharField(max_length=15, required=False, label="Phone Number")
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date of Birth"
    )
    gender = forms.ChoiceField(
        choices=CustomUser.GENDER_CHOICES,
        required=False,
        label="Gender",
        widget=forms.Select
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + (
            'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'gender'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Choose a username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Your email address'})
        self.fields['phone_number'].widget.attrs.update({'placeholder': 'E.g., +91 9876543210'})

    def save(self, commit=True):
        user = super().save(commit=False)
        # Ensure new fields are saved
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.phone_number = self.cleaned_data.get('phone_number')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        user.gender = self.cleaned_data.get('gender')
        if commit:
            user.save()
        return user

# ... (other forms) ...

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from doctors.models import Doctor, Specialty, Appointment # Ensure these are imported if other forms use them

# ... (PatientSignUpForm and ClinicRegistrationForm definitions) ...

# healthcare_app_motihari/users/forms.py

# ... (existing imports) ...

class PatientProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'gender' # Add new fields here
        ]
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'phone_number': 'Phone Number',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
        }
        widgets = {
            'username': forms.TextInput(attrs={'readonly': 'readonly'}), # Make username read-only
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}), # HTML5 date input
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email

# ... (other forms) ...