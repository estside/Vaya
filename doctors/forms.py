# healthcare_app_motihari/doctors/forms.py

from django import forms
from .models import Doctor, Specialty, Appointment, Report, DoctorSlot
from users.models import CustomUser
from django.contrib.auth.forms import UserCreationForm
import datetime

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

class PatientSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Choose a username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Your email address'})

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
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Briefly describe your reason for visit', 'class': 'form-control'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        
        if doctor:
            now = datetime.datetime.now()
            future_available_slots = DoctorSlot.objects.filter(
                doctor=doctor,
                is_available=True,
                date__gte=now.date()
            ).order_by('date', 'start_time')
            
            current_time = now.time()
            final_available_slots = [
                slot for slot in future_available_slots
                if not (slot.date == now.date() and slot.end_time <= current_time)
            ]
            
            self.fields['available_slot'].queryset = DoctorSlot.objects.filter(
                id__in=[s.id for s in final_available_slots]
            )
            
            self.fields['available_slot'].label_from_instance = lambda obj: f"{obj.date.strftime('%B %d, %Y')} - {obj.start_time.strftime('%I:%M %p')} to {obj.end_time.strftime('%I:%M %p')}"

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

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
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief description or notes about the report.', 'class': 'form-control'}),
        }

class DoctorProfileEditForm(forms.ModelForm):
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
            'working_days', 'start_time', 'end_time'
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
            'clinic_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'qualifications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'working_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g., Mon-Fri or Mon,Wed,Fri'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'clinic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "End time must be after start time.")
        return cleaned_data

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
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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

class DoctorAddPatientForm(forms.ModelForm):
    """
    Form for doctors to add patients online with time slots.
    This form allows doctors to create patient accounts and book appointments for them.
    """
    # Patient creation fields
    patient_username = forms.CharField(
        max_length=150, 
        required=True, 
        label="Patient Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username for the patient'})
    )
    patient_email = forms.EmailField(
        required=True, 
        label="Patient Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'patient@example.com'})
    )
    patient_phone = forms.CharField(
        max_length=15, 
        required=True, 
        label="Patient Phone",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'})
    )
    patient_first_name = forms.CharField(
        max_length=150, 
        required=True, 
        label="Patient First Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    patient_last_name = forms.CharField(
        max_length=150, 
        required=True, 
        label="Patient Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    
    # Appointment details
    available_slot = forms.ModelChoiceField(
        queryset=DoctorSlot.objects.none(),
        empty_label="--- Select an available slot ---",
        label="Available Appointment Slot",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Appointment fields
    reason = forms.CharField(
        required=False,
        label="Reason for Appointment",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Briefly describe the reason for visit', 'class': 'form-control'})
    )
    appointment_type = forms.ChoiceField(
        choices=Appointment.APPOINTMENT_TYPE_CHOICES,
        label="Appointment Type",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Appointment
        fields = ['reason', 'appointment_type']

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        
        if doctor:
            # Filter available slots for this doctor
            now = datetime.datetime.now()
            future_available_slots = DoctorSlot.objects.filter(
                doctor=doctor,
                is_available=True,
                date__gte=now.date()
            ).order_by('date', 'start_time')
            
            # Filter out slots that are in the past for today's date
            current_time = now.time()
            final_available_slots = [
                slot for slot in future_available_slots
                if not (slot.date == now.date() and slot.end_time <= current_time)
            ]
            
            # Set the queryset for available_slot field
            self.fields['available_slot'].queryset = DoctorSlot.objects.filter(
                id__in=[s.id for s in final_available_slots]
            )
            
            # Customize the display of each slot in the dropdown
            self.fields['available_slot'].label_from_instance = lambda obj: f"{obj.date.strftime('%B %d, %Y')} - {obj.start_time.strftime('%I:%M %p')} to {obj.end_time.strftime('%I:%M %p')}"

    def clean(self):
        cleaned_data = super().clean()
        
        # Check if username already exists
        patient_username = cleaned_data.get('patient_username')
        if patient_username and CustomUser.objects.filter(username=patient_username).exists():
            self.add_error('patient_username', 'This username is already taken.')
        
        # Check if email already exists
        patient_email = cleaned_data.get('patient_email')
        if patient_email and CustomUser.objects.filter(email=patient_email).exists():
            self.add_error('patient_email', 'This email is already registered.')
        
        # Check if phone already exists (if phone field exists in CustomUser)
        patient_phone = cleaned_data.get('patient_phone')
        if hasattr(CustomUser, 'phone') and patient_phone and CustomUser.objects.filter(phone=patient_phone).exists():
            self.add_error('patient_phone', 'This phone number is already registered.')
        
        return cleaned_data

    def save(self, commit=True):
        # This form doesn't save directly - it's handled in the view
        # We just return the cleaned data for the view to process
        return self.cleaned_data

# --- NEW FORM: DoctorScheduleForm ---
class DoctorScheduleForm(forms.Form):
    """
    Form for doctors to set their working schedule and automatically generate time slots.
    """
    WORKING_DAYS_CHOICES = [
        ('Mon-Fri', 'Monday to Friday'),
        ('Mon-Sat', 'Monday to Saturday'),
        ('Mon-Sun', 'Monday to Sunday'),
        ('Mon,Wed,Fri', 'Monday, Wednesday, Friday'),
        ('Tue,Thu,Sat', 'Tuesday, Thursday, Saturday'),
        ('Mon,Tue,Wed', 'Monday, Tuesday, Wednesday'),
        ('Thu,Fri,Sat', 'Thursday, Friday, Saturday'),
        ('Mon,Tue,Wed,Thu,Fri', 'Monday to Friday'),
        ('Mon,Tue,Wed,Thu,Fri,Sat', 'Monday to Saturday'),
        ('Mon,Tue,Wed,Thu,Fri,Sat,Sun', 'Every Day'),
    ]
    
    working_days = forms.ChoiceField(
        choices=WORKING_DAYS_CHOICES,
        label="Working Days",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_time = forms.TimeField(
        label="Daily Start Time",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="What time do you start seeing patients each day?"
    )
    
    end_time = forms.TimeField(
        label="Daily End Time", 
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="What time do you stop seeing patients each day?"
    )
    
    slot_duration = forms.ChoiceField(
        choices=[
            (15, '15 minutes'),
            (30, '30 minutes'),
            (45, '45 minutes'),
            (60, '1 hour'),
        ],
        initial=30,
        label="Appointment Slot Duration",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="How long should each appointment slot be?"
    )
    
    generate_for_weeks = forms.IntegerField(
        min_value=1,
        max_value=12,
        initial=4,
        label="Generate Slots For (Weeks)",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="How many weeks ahead should we generate slots?"
    )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "End time must be after start time.")
        
        if start_time and end_time:
            # Calculate total working minutes
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute
            total_minutes = end_minutes - start_minutes
            
            if total_minutes < 30:
                self.add_error('end_time', "Working hours must be at least 30 minutes long.")
        
        return cleaned_data
# --- END NEW FORM ---
