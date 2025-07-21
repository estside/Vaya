# healthcare_app_motihari/doctors/admin.py

from django.contrib import admin
from .models import Specialty, Doctor, Appointment # Import Appointment

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_specialties', 'clinic_name', 'contact_phone', 'is_approved')
    list_filter = ('specialties', 'is_approved')
    search_fields = ('full_name', 'clinic_name', 'contact_phone', 'clinic_address')
    actions = ['approve_doctors']

    def approve_doctors(self, request, queryset):
        queryset.update(is_approved=True)
    approve_doctors.short_description = "Approve selected doctors"

    def display_specialties(self, obj):
        return ", ".join([s.name for s in obj.specialties.all()])
    display_specialties.short_description = 'Specialties'

# --- NEW APPOINTMENT ADMIN STARTS HERE ---
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'appointment_type', 'created_at')
    list_filter = ('status', 'appointment_type', 'doctor__specialties') # Filter by doctor's specialty
    search_fields = ('patient__username', 'doctor__full_name', 'reason')
    date_hierarchy = 'appointment_date' # Adds date navigation
    raw_id_fields = ('patient', 'doctor') # Use raw ID input for ForeignKey fields for better performance with many users/doctors
# --- NEW APPOINTMENT ADMIN ENDS HERE ---