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