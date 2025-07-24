# healthcare_app_motihari/doctors/forms.py

from django import forms
from .models import Doctor, Specialty, Appointment, Report 
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
    # --- NEW REPORT UPLOAD FORM STARTS HERE ---
class ReportUploadForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'description', 'report_file', 'report_date']
        labels = {
            'title': 'Report Title',
            'description': 'Description (Optional)',
            'report_file': 'Upload File (PDF, Image, etc.)',
            'report_date': 'Date of Report (e.g., Lab Test Date)'
        }
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief description or notes about the report.'}),
        }
# --- NEW REPORT UPLOAD FORM ENDS HERE ---
# healthcare_app_motihari/doctors/forms.py

from django import forms
from .models import Doctor, Specialty, Appointment, Report
from users.models import CustomUser
from django.contrib.auth.forms import UserCreationForm
import datetime

# ... (PatientSignUpForm, ClinicRegistrationForm, AppointmentBookingForm, ReportUploadForm definitions) ...

# --- NEW: DoctorProfileEditForm ---
class DoctorProfileEditForm(forms.ModelForm):
    # This form will allow doctors to edit their profile, including specialties and availability
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Main Specialties Offered"
    )

    class Meta:
        model = Doctor
        fields = [
            'full_name', 'clinic_name', 'clinic_address', 'contact_phone',
            'contact_email', 'qualifications', 'specialties',
            'working_days', 'start_time', 'end_time' # Include new availability fields
        ]
        labels = {
            'full_name': 'Full Name',
            'clinic_name': 'Clinic Name',
            'clinic_address': 'Clinic Address',
            'contact_phone': 'Contact Phone Number',
            'contact_email': 'Contact Email',
            'qualifications': 'Qualifications',
            'working_days': 'Working Days',
            'start_time': 'Daily Start Time',
            'end_time': 'Daily End Time',
        }
        widgets = {
            'clinic_address': forms.Textarea(attrs={'rows': 3}),
            'qualifications': forms.Textarea(attrs={'rows': 3}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}), # HTML5 time input
            'end_time': forms.TimeInput(attrs={'type': 'time'}),   # HTML5 time input
        }

    # You might want to add custom clean methods here for time validation (e.g., end_time after start_time)
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "End time must be after start time.")
        return cleaned_data
# healthcare_app_motihari/doctors/forms.py

from django import forms
# ... (existing imports) ...
# Ensure DoctorSlot is imported
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot

# ... (PatientSignUpForm, ClinicRegistrationForm, AppointmentBookingForm, PatientProfileEditForm, ReportUploadForm definitions) ...

# --- NEW DOCTOR SLOT FORM STARTS HERE ---
class DoctorSlotForm(forms.ModelForm):
    class Meta:
        model = DoctorSlot
        fields = ['date', 'start_time', 'end_time', 'is_available']
        labels = {
            'date': 'Date',
            'start_time': 'Start Time',
            'end_time': 'End Time',
            'is_available': 'Mark as Available',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if date and date < datetime.date.today():
            self.add_error('date', "Cannot create slots for a past date.")

        if start_time and end_time:
            if start_time >= end_time:
                self.add_error('end_time', "End time must be after start time.")
            # Optional: Add validation for minimum slot duration (e.g., 15 minutes)
            # if (datetime.datetime.combine(date, end_time) - datetime.datetime.combine(date, start_time)).total_seconds() < 900: # 15 mins
            #     self.add_error('end_time', "Slot must be at least 15 minutes long.")

        return cleaned_data
# --- NEW DOCTOR SLOT FORM ENDS HERE ---
# healthcare_app_motihari/doctors/forms.py

from django import forms
# ... (existing imports) ...
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot # Ensure DoctorSlot is imported
import datetime

# ... (PatientSignUpForm, ClinicRegistrationForm, PatientProfileEditForm, ReportUploadForm definitions) ...

# --- MODIFIED APPOINTMENT BOOKING FORM STARTS HERE ---
class AppointmentBookingForm(forms.ModelForm):
    # This field will be dynamically populated in the view
    # It will represent the DoctorSlot chosen by the patient
    available_slot = forms.ModelChoiceField(
        queryset=DoctorSlot.objects.none(), # Initial queryset is empty, will be set in view
        empty_label="--- Select an available slot ---",
        label="Available Appointment Slot",
        widget=forms.Select(attrs={'class': 'form-control'}) # Apply a class for styling
    )

    class Meta:
        model = Appointment
        # Remove appointment_date and appointment_time as they come from available_slot
        fields = ['reason', 'appointment_type']
        labels = {
            'reason': 'Reason for Appointment (Optional)',
            'appointment_type': 'Appointment Type'
        }
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Briefly describe your reason for visit'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'})
        }

    # Custom constructor to filter available_slot queryset based on the doctor
    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None) # Pop the doctor instance from kwargs
        super().__init__(*args, **kwargs)

        if doctor:
            # Filter available slots for this specific doctor
            # Only show slots that are available and in the future
            now = datetime.datetime.now()
            # Combine date and time for comparison
            # Filter out slots that are entirely in the past
            future_available_slots = DoctorSlot.objects.filter(
                doctor=doctor,
                is_available=True,
                date__gte=now.date() # Slots on or after today
            ).order_by('date', 'start_time')

            # Further filter out slots that are in the past today
            current_time = now.time()
            # Filter out slots where date is today AND end_time is in the past
            future_available_slots = [
                slot for slot in future_available_slots
                if not (slot.date == now.date() and slot.end_time <= current_time)
            ]

            # Convert the filtered list back to a queryset for ModelChoiceField
            self.fields['available_slot'].queryset = DoctorSlot.objects.filter(id__in=[s.id for s in future_available_slots])

            # Optional: Customize the display of each slot in the dropdown
            self.fields['available_slot'].label_from_instance = lambda obj: f"{obj.date.strftime('%B %d, %Y')} - {obj.start_time.strftime('%I:%M %p')} to {obj.end_time.strftime('%I:%M %p')}"

    def clean(self):
        cleaned_data = super().clean()
        # No need for date/time validation here, as it's handled by selecting an existing slot.
        # The selected slot itself implicitly means it's a future, valid time.
        return cleaned_data
# --- MODIFIED APPOINTMENT BOOKING FORM ENDS HERE ---
# healthcare_app_motihari/doctors/forms.py

from django import forms
# ... (existing imports) ...
import datetime

# ... (other forms) ...

class AppointmentBookingForm(forms.ModelForm):
    available_slot = forms.ModelChoiceField(
        queryset=DoctorSlot.objects.none(),
        empty_label="--- Select an available slot ---",
        label="Available Appointment Slot",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Appointment
        fields = ['reason', 'appointment_type']
        labels = {
            'reason': 'Reason for Appointment (Optional)',
            'appointment_type': 'Appointment Type'
        }
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Briefly describe your reason for visit'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None) # Pop the doctor instance from kwargs
        super().__init__(*args, **kwargs)

        print(f"DEBUG FORM: Doctor passed to form: {doctor}") # DEBUG PRINT

        if doctor:
            now = datetime.datetime.now()
            
            # Filter for future available slots
            future_available_slots_query = DoctorSlot.objects.filter(
                doctor=doctor,
                is_available=True,
                date__gte=now.date()
            ).order_by('date', 'start_time')

            # Filter out slots that are in the past for today's date
            current_time = now.time()
            final_available_slots = []
            for slot in future_available_slots_query:
                if not (slot.date == now.date() and slot.end_time <= current_time):
                    final_available_slots.append(slot)
            
            # Convert the filtered list back to a queryset for ModelChoiceField
            self.fields['available_slot'].queryset = DoctorSlot.objects.filter(id__in=[s.id for s in final_available_slots])

            print(f"DEBUG FORM: Queryset for available_slot: {self.fields['available_slot'].queryset}") # DEBUG PRINT
            print(f"DEBUG FORM: Number of slots found: {self.fields['available_slot'].queryset.count()}") # DEBUG PRINT

            self.fields['available_slot'].label_from_instance = lambda obj: f"{obj.date.strftime('%B %d, %Y')} - {obj.start_time.strftime('%I:%M %p')} to {obj.end_time.strftime('%I:%M %p')}"
        else:
            print("DEBUG FORM: No doctor passed to AppointmentBookingForm.") # DEBUG PRINT

    def clean(self):
        cleaned_data = super().clean()
        # ... (existing clean method) ...
        return cleaned_data
# healthcare_app_motihari/doctors/forms.py

from django import forms
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot # Ensure DoctorSlot is imported
from users.models import CustomUser
from django.contrib.auth.forms import UserCreationForm
import datetime

# ... (PatientSignUpForm, ClinicRegistrationForm, PatientProfileEditForm, ReportUploadForm definitions) ...

class DoctorSlotForm(forms.ModelForm):
    class Meta:
        model = DoctorSlot
        fields = ['date', 'start_time', 'end_time', 'is_available']
        labels = {
            'date': 'Date',
            'start_time': 'Start Time',
            'end_time': 'End Time',
            'is_available': 'Mark as Available',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if date and date < datetime.date.today():
            self.add_error('date', "Cannot create slots for a past date.")

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "End time must be after start time.")
        return cleaned_data

# --- CORRECTED APPOINTMENT BOOKING FORM STARTS HERE ---
class AppointmentBookingForm(forms.ModelForm):
    # This field will be dynamically populated in the view
    # It will represent the DoctorSlot chosen by the patient
    available_slot = forms.ModelChoiceField(
        queryset=DoctorSlot.objects.none(), # Initial queryset is empty, will be set in view
        empty_label="--- Select an available slot ---",
        label="Available Appointment Slot",
        widget=forms.Select(attrs={'class': 'form-control'}) # Apply a class for styling
    )

    class Meta:
        model = Appointment
        # Remove appointment_date and appointment_time as they come from available_slot
        fields = ['reason', 'appointment_type'] # Only reason and appointment_type are direct inputs
        labels = {
            'reason': 'Reason for Appointment (Optional)',
            'appointment_type': 'Appointment Type'
        }
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Briefly describe your reason for visit'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'})
        }

    # Custom constructor to filter available_slot queryset based on the doctor
    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None) # Pop the doctor instance from kwargs
        super().__init__(*args, **kwargs)

        # print(f"DEBUG FORM: Doctor passed to form: {doctor}") # DEBUG PRINT

        if doctor:
            now = datetime.datetime.now()
            
            # Filter for future available slots that are marked as available
            # We filter by date__gte=now.date() first for efficiency
            future_available_slots_query = DoctorSlot.objects.filter(
                doctor=doctor,
                is_available=True, # Only show slots marked as available
                date__gte=now.date() # Slots on or after today
            ).order_by('date', 'start_time')

            # Further filter out slots that are in the past for today's date
            current_time = now.time()
            final_available_slots = []
            for slot in future_available_slots_query:
                # If the slot date is today, check if its end time is in the future
                if not (slot.date == now.date() and slot.end_time <= current_time):
                    final_available_slots.append(slot)
            
            # Set the queryset for the available_slot field
            # Use filter(id__in=...) to create a queryset from the list of filtered slots
            self.fields['available_slot'].queryset = DoctorSlot.objects.filter(id__in=[s.id for s in final_available_slots])

            # print(f"DEBUG FORM: Queryset for available_slot: {self.fields['available_slot'].queryset}") # DEBUG PRINT
            # print(f"DEBUG FORM: Number of slots found: {self.fields['available_slot'].queryset.count()}") # DEBUG PRINT

            # Customize the display of each slot in the dropdown
            self.fields['available_slot'].label_from_instance = lambda obj: f"{obj.date.strftime('%B %d, %Y')} - {obj.start_time.strftime('%I:%M %p')} to {obj.end_time.strftime('%I:%M %p')}"
        # else:
            # print("DEBUG FORM: No doctor passed to AppointmentBookingForm.") # DEBUG PRINT

    def clean(self):
        cleaned_data = super().clean()
        # No need for date/time validation here, as it's handled by selecting an existing slot.
        # The selected slot itself implicitly means it's a future, valid time.
        return cleaned_data
# --- CORRECTED APPOINTMENT BOOKING FORM ENDS HERE ---
