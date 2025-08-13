# healthcare_app_motihari/doctors/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from users.models import CustomUser

class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name_plural = "Specialties"
        ordering = ['name']

    def __str__(self):
        return self.name

class Doctor(models.Model):
    # This field is temporarily set to nullable to fix the migration error
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_login_profile', null=True, blank=True)

    clinic_name = models.CharField(max_length=200)
    clinic_address = models.TextField()
    
    full_name = models.CharField(max_length=255)
    contact_email = models.EmailField(unique=True, default='')
    contact_phone = models.CharField(max_length=15, unique=True)
    qualifications = models.TextField(blank=True, null=True)
    
    specialties = models.ManyToManyField(Specialty, related_name='doctors')
    
    is_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    DAYS_OF_WEEK_CHOICES = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    )
    working_days = models.CharField(max_length=100, blank=True, null=True, help_text="Comma-separated list of working days (e.g., Monday,Tuesday,Friday)")
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        return f"Dr. {self.full_name} - {self.clinic_name}"
        
    @property
    def get_specialty_names(self):
        return ", ".join([specialty.name for specialty in self.specialties.all()])

class DoctorSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.doctor.full_name} - {self.date} {self.start_time.strftime('%I:%M %p')}"

class Appointment(models.Model):
    APPOINTMENT_TYPE_CHOICES = [
        ('in-person', 'In-person'),
        ('online', 'Online'),
        ('phone', 'Phone Call')
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_slot = models.ForeignKey(DoctorSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointment_slot')

    reason = models.TextField(blank=True, default='')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='in-person')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True, default='', help_text="Doctor's private notes on the appointment.")
    payment_status = models.CharField(max_length=20, choices=[('unpaid', 'Unpaid'), ('paid', 'Paid')], default='unpaid')

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f"Appointment for {self.patient.username} with Dr. {self.doctor.full_name} on {self.appointment_date}"

class Report(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, blank=True, related_name='uploaded_reports')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    report_file = models.FileField(upload_to='patient_reports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    report_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Report: {self.title} for {self.patient.username}"