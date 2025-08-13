# healthcare_app_motihari/doctors/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Specialty, Doctor, DoctorSlot, Appointment, Report


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.action(description='Approve selected doctors')
def approve_doctors(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description='Reject selected doctors')
def reject_doctors(modeladmin, request, queryset):
    queryset.update(is_approved=False)


@admin.action(description='Show specialty details for selected doctors')
def show_specialty_details(modeladmin, request, queryset):
    for doctor in queryset:
        specialties_list = ", ".join([s.name for s in doctor.specialties.all()])
        modeladmin.message_user(request, f"Dr. {doctor.full_name}: {specialties_list}")


class DoctorSlotInline(admin.TabularInline):
    model = DoctorSlot
    extra = 1  # Number of extra forms to display
    fields = ('date', 'start_time', 'end_time', 'is_available')
    readonly_fields = ('is_available',)
    
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_add_permission(self, request, obj=None):
        return True

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'clinic_name', 'specialties_list', 'is_approved_status', 'created_at')
    list_filter = ('is_approved', 'specialties__name', 'created_at')
    search_fields = ('full_name', 'clinic_name', 'contact_phone', 'user__username')
    actions = [approve_doctors, reject_doctors, show_specialty_details]
    
    date_hierarchy = 'created_at' # Add a date hierarchy for navigation
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'full_name', 'qualifications'),
        }),
        ('Clinic Details', {
            'fields': ('clinic_name', 'clinic_address', 'contact_phone', 'contact_email'),
        }),
        ('Specialties & Approval', {
            'fields': ('specialties', 'is_approved'),
            'description': 'Check the "Is approved" box to make the doctor visible to patients.',
        }),
        ('Working Hours', {
            'fields': ('working_days', 'start_time', 'end_time'),
            'classes': ('collapse',), # Makes this section collapsible
        }),
    )

    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(appointment_count=Count('appointments'))
        return queryset

    def is_approved_status(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green; font-weight: bold;">✓ Approved</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Pending Approval</span>')
    is_approved_status.short_description = 'Approval Status'

    def specialties_list(self, obj):
        specialties = [s.name for s in obj.specialties.all()]
        if specialties:
            return format_html(
                '<span style="color: blue; font-weight: bold;">{}</span>',
                ", ".join(specialties)
            )
        return format_html('<span style="color: red; font-style: italic;">No specialties selected</span>')
    specialties_list.short_description = 'Specialties'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'appointment_type')
    list_filter = ('status', 'appointment_type', 'doctor__full_name', 'appointment_date')
    search_fields = ('patient__username', 'doctor__full_name')
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        (None, {
            'fields': ('patient', 'doctor', 'appointment_slot', 'status', 'appointment_type', 'reason'),
        }),
        ('Additional Details', {
            'fields': ('comments', 'payment_status'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('patient', 'doctor', 'appointment_slot', 'appointment_date', 'appointment_time')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'patient', 'doctor', 'uploaded_at', 'report_date')
    list_filter = ('uploaded_at', 'report_date', 'doctor__full_name')
    search_fields = ('title', 'patient__username', 'doctor__full_name')
    readonly_fields = ('uploaded_at',)

@admin.register(DoctorSlot)
class DoctorSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'doctor__full_name')
    search_fields = ('doctor__full_name',)
    date_hierarchy = 'date'
    readonly_fields = ('doctor', 'date', 'start_time', 'end_time')