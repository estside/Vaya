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

class Message(models.Model):
    """
    Represents an individual message within a chat room.
    """
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="The chat room this message belongs to."
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        help_text="The user who sent this message."
    )
    content = models.TextField(
        help_text="The content of the message."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the message was sent."
    )

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['timestamp'] # Order messages chronologically

    def __str__(self):
        return f"'{self.content[:50]}' from {self.sender.username} in {self.chat_room.appointment.id}"
