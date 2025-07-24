# healthcare_app_motihari/doctors/models.py

from django.db import models
from users.models import CustomUser
import datetime # Import datetime for default values if needed

class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Specialties"

    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_login_profile')
    full_name = models.CharField(max_length=200)
    specialties = models.ManyToManyField(Specialty, blank=True, related_name='doctors')
    clinic_name = models.CharField(max_length=200)
    clinic_address = models.TextField()
    contact_phone = models.CharField(max_length=15, unique=True)
    contact_email = models.EmailField(unique=True, blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    working_days = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="E.g., Mon-Fri, Mon,Wed,Fri, or All Weekends"
    )
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        specialty_names = ", ".join([s.name for s in self.specialties.all()])
        return f"Dr. {self.full_name} ({specialty_names})"

    class Meta:
        ordering = ['full_name']

class DoctorSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='available_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"Dr. {self.doctor.full_name} - {self.date} {self.start_time}-{self.end_time} ({'Available' if self.is_available else 'Blocked'})"

    def is_slot_available_for_appointment(self, appointment_date, appointment_time):
        if not self.is_available:
            return False
        if self.date != appointment_date:
            return False
        if not (self.start_time <= appointment_time < self.end_time):
            return False
        return True

class Appointment(models.Model):
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='doctor_appointments')

    # --- IMPORTANT: Ensure this ForeignKey to DoctorSlot exists ---
    appointment_slot = models.ForeignKey(DoctorSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_appointments')
    # -------------------------------------------------------------

    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    APPOINTMENT_TYPE_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid (Coming Soon!)'),
    ]
    appointment_type = models.CharField(max_length=10, choices=APPOINTMENT_TYPE_CHOICES, default='unpaid')

    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        # Use unique_together on doctor, date, time if not using appointment_slot for uniqueness
        # If using appointment_slot, then unique_together = ('appointment_slot',) is more precise
        # For now, let's keep it simple:
        unique_together = ('doctor', 'appointment_date', 'appointment_time') # Keep this for now

    def __str__(self):
        return f"Appointment for {self.patient.username} with Dr. {self.doctor.full_name} on {self.appointment_date} at {self.appointment_time} ({self.status})"

class Report(models.Model):
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='medical_reports')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    report_file = models.FileField(upload_to='patient_reports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    report_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} for {self.patient.username} ({self.report_date if self.report_date else 'N/A'})"

    class Meta:
        ordering = ['-uploaded_at']
# healthcare_app_motihari/doctors/models.py

from django.db import models
from users.models import CustomUser
import datetime

# ... (Specialty, Doctor, DoctorSlot models remain the same) ...

class Appointment(models.Model):
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='doctor_appointments')

    # This is the crucial link to the DoctorSlot
    appointment_slot = models.ForeignKey(DoctorSlot, on_delete=models.PROTECT, # Use PROTECT or CASCADE based on desired behavior
                                         null=True, blank=True, related_name='booked_appointments')
    # Keep appointment_date and appointment_time for convenience/reporting,
    # but they will now be populated from the selected appointment_slot.
    # No longer need unique_together on these if appointment_slot is unique.
    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    APPOINTMENT_TYPE_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid (Coming Soon!)'),
    ]
    appointment_type = models.CharField(max_length=10, choices=APPOINTMENT_TYPE_CHOICES, default='unpaid')

    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        # --- FIX STARTS HERE ---
        # The uniqueness should now be based solely on the appointment_slot.
        # An appointment 'uses up' one specific slot.
        # If you want to ensure a patient can't book the same slot twice,
        # you might consider unique_together = ('patient', 'appointment_slot').
        # For a single booking per slot, just rely on the DoctorSlot's `is_available` flag.
        # Removing the old unique_together as it clashes with DoctorSlot based booking.
        # If you still want to ensure no two appointments can *ever* point to the same slot,
        # you can enforce it programmatically in the view or by making appointment_slot unique.
        # However, the `is_available` flag in DoctorSlot and the check in `book_appointment` view are sufficient.
        # So, we can remove unique_together here entirely if relying on `is_available` and view logic.
        # Or, if an appointment *always* implies a slot, you might want:
        # unique_together = ('appointment_slot',) # If a slot can only have ONE appointment.
        # But this would mean a slot can only ever be booked once. If you want to reuse slots
        # after cancellation, the `is_available` flag approach is better.

        # Given your `DoctorSlot` already has `unique_together = ('doctor', 'date', 'start_time', 'end_time')`,
        # and you are marking `is_available=False` after booking, and checking it in the form,
        # you don't strictly need a unique_together on Appointment itself for preventing double-booking *the same slot*.
        # The primary protection is the `is_available` flag and the `Appointment.objects.filter(appointment_slot=selected_slot, ...).exists()` check.
        # So, let's remove the problematic unique_together.

        # Old: unique_together = ('doctor', 'appointment_date', 'appointment_time')
        # New: Remove it as uniqueness is managed by DoctorSlot's availability and the view's checks.
        pass # No unique_together constraint here
        # --- FIX ENDS HERE ---

    def __str__(self):
        return f"Appointment for {self.patient.username} with Dr. {self.doctor.full_name} on {self.appointment_date} at {self.appointment_time} ({self.status})"

# ... (Report model remains the same) ...