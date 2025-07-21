# healthcare_app_motihari/doctors/admin.py

from django.contrib import admin
from .models import Specialty, Doctor

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    # --- CHANGES START HERE ---
    # 1. Update list_display to use a method for ManyToManyField
    #    This method will display all specialties for a doctor, joined by commas.
    list_display = ('full_name', 'display_specialties', 'clinic_name', 'contact_phone', 'is_approved')
    # 2. Update list_filter to refer to the correct ManyToManyField name
    list_filter = ('specialties', 'is_approved') # Changed from 'specialty' to 'specialties'
    # --- CHANGES END HERE ---

    search_fields = ('full_name', 'clinic_name', 'contact_phone', 'clinic_address')
    actions = ['approve_doctors']

    def approve_doctors(self, request, queryset):
        queryset.update(is_approved=True)
    approve_doctors.short_description = "Approve selected doctors"

    # Define a method to display multiple specialties in list_display
    def display_specialties(self, obj):
        # obj is the current Doctor instance
        # Access the ManyToManyField and join the names
        return ", ".join([s.name for s in obj.specialties.all()])

    display_specialties.short_description = 'Specialties' # Column header in admin