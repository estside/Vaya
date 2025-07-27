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
from django.conf import settings
from doctors.models import Appointment #

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    # ADD THIS NEW FIELD for user-specific AI chat history:
    ai_chat_for_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_conversations')

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        if self.appointment:
            return f"Appt Chat: {self.sender.username} in Appt {self.appointment.id} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        elif self.ai_chat_for_user:
            return f"AI Chat: {self.sender.username} to {self.ai_chat_for_user.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        return f"Message from {self.sender.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"