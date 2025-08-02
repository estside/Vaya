# healthcare_app_motihari/doctors/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Specialty, Doctor, Appointment, Report, DoctorSlot

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_specialties', 'clinic_name', 'contact_phone', 'approval_status', 'created_date')
    list_filter = ('specialties', 'is_approved', 'created_at')
    search_fields = ('full_name', 'clinic_name', 'contact_phone', 'clinic_address', 'contact_email')
    readonly_fields = ('created_at',)
    actions = ['approve_doctors', 'reject_doctors', 'show_specialty_details']
    filter_horizontal = ('specialties',)  # Better widget for many-to-many fields
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('full_name', 'clinic_name', 'contact_phone', 'contact_email')
        }),
        ('Clinic Details', {
            'fields': ('clinic_address', 'qualifications')
        }),
        ('Specialties & Approval', {
            'fields': ('specialties', 'is_approved', 'created_at'),
            'description': 'Select the specialties this doctor offers and approve their registration.'
        }),
        ('Working Hours', {
            'fields': ('working_days', 'start_time', 'end_time'),
            'classes': ('collapse',)
        }),
        ('User Account', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
    )

    def approve_doctors(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} doctor(s) have been approved successfully.')
    approve_doctors.short_description = "Approve selected doctors"

    def reject_doctors(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} doctor(s) have been rejected.')
    reject_doctors.short_description = "Reject selected doctors"

    def show_specialty_details(self, request, queryset):
        details = []
        for doctor in queryset:
            specialties = list(doctor.specialties.all())
            specialty_names = [s.name for s in specialties]
            details.append(f"{doctor.full_name}: {', '.join(specialty_names) if specialty_names else 'No specialties'}")
        
        message = "\n".join(details)
        self.message_user(request, f"Specialty details:\n{message}")
    show_specialty_details.short_description = "Show specialty details for selected doctors"

    def display_specialties(self, obj):
        specialties = obj.specialties.all()
        if specialties:
            specialty_names = [s.name for s in specialties]
            return format_html('<span style="color: blue; font-weight: bold;">{}</span>', ", ".join(specialty_names))
        return format_html('<span style="color: red; font-style: italic;">No specialties selected</span>')
    display_specialties.short_description = 'Specialties'

    def approval_status(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green; font-weight: bold;">✓ Approved</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Pending Approval</span>')
    approval_status.short_description = 'Approval Status'

    def created_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_date.short_description = 'Registration Date'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('specialties')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'appointment_type', 'created_at')
    list_filter = ('status', 'appointment_type', 'doctor__specialties')
    search_fields = ('patient__username', 'doctor__full_name', 'reason')
    date_hierarchy = 'appointment_date'
    raw_id_fields = ('patient', 'doctor')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'patient', 'doctor', 'uploaded_at', 'report_date', 'report_file')
    list_filter = ('uploaded_at', 'report_date', 'doctor')
    search_fields = ('title', 'patient__username', 'doctor__full_name', 'description')
    raw_id_fields = ('patient', 'doctor')

@admin.register(DoctorSlot)
class DoctorSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'date', 'doctor')
    search_fields = ('doctor__full_name',)
    date_hierarchy = 'date'
    raw_id_fields = ('doctor',)