# healthcare_app_motihari/chat/models.py

from django.db import models
from users.models import CustomUser # Import your CustomUser model
from doctors.models import Appointment # Import the Appointment model

class ChatRoom(models.Model):
    """
    Represents a unique chat thread linked to a specific appointment.
    A OneToOneField ensures each appointment has at most one chat room.
    """
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='chat_room',
        help_text="The appointment this chat room is associated with."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the chat room was created."
    )

    class Meta:
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"
        ordering = ['-created_at'] # Order by most recent chat room

    def __str__(self):
        return f"Chat for Appointment {self.appointment.id} ({self.appointment.patient.username} - Dr. {self.appointment.doctor.full_name})"

from django.db import models
from django.conf import settings # For AUTH_USER_MODEL
# Import Appointment model from doctors app as per your structure
from doctors.models import Appointment

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    # IMPORTANT: Set null=True and blank=True for the initial migration
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        # Added a check for self.appointment to handle null in __str__
        return f"Message from {self.sender.username} in Appointment {self.appointment.id if self.appointment else 'N/A'} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"