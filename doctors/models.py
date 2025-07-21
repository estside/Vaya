# healthcare_app_motihari/doctors/models.py

from django.db import models
from users.models import CustomUser

class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Specialties"

    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_login_profile')
    # If you want to link a manager:
    # managed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_doctors')

    full_name = models.CharField(max_length=200)
    # --- CHANGE THIS LINE ---
    # From: specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    # To:
    specialties = models.ManyToManyField(Specialty, blank=True, related_name='doctors') # Changed name to plural
    # -----------------------

    clinic_name = models.CharField(max_length=200)
    clinic_address = models.TextField()
    contact_phone = models.CharField(max_length=15, unique=True)
    contact_email = models.EmailField(unique=True, blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        # Adjust __str__ to reflect multiple specialties
        specialty_names = ", ".join([s.name for s in self.specialties.all()])
        return f"Dr. {self.full_name} ({specialty_names})"

    class Meta:
        ordering = ['full_name']