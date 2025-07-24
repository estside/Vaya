# healthcare_app_motihari/chat/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from doctors.models import Appointment # Import Appointment model
from .models import ChatRoom, Message # Import ChatRoom and Message models

@login_required
def chat_room(request, appointment_id):
    """
    Renders the chat room for a specific appointment.
    Ensures only authorized users (patient or doctor of the appointment) can access.
    """
    # Retrieve the appointment object
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Authorization check: Only the patient or doctor involved in the appointment can access the chat
    if not (request.user == appointment.patient or (appointment.doctor and request.user == appointment.doctor.user)):
        messages.error(request, "You are not authorized to view this chat.")
        return redirect('landing_page') # Redirect to a safe page if unauthorized

    # Optional: Check appointment status to allow chat (e.g., only for confirmed/pending/completed, not cancelled)
    if appointment.status == 'cancelled':
        messages.warning(request, "Chat is not available for cancelled appointments.")
        # Redirect to the appropriate dashboard
        return redirect('patient_dashboard' if request.user == appointment.patient else 'doctor_dashboard')

    # Get the ChatRoom instance for this appointment, create if it doesn't exist
    # This ensures we have a chat_room.id to use in the WebSocket URL
    chat_room_obj, created = ChatRoom.objects.get_or_create(appointment=appointment)

    # Load previous messages for this chat room
    messages_history = Message.objects.filter(chat_room=chat_room_obj).order_by('timestamp')

    # Determine the "other user" for display in the chat header
    other_user = None
    if request.user == appointment.patient:
        other_user = appointment.doctor.full_name if appointment.doctor else "N/A"
    elif appointment.doctor and request.user == appointment.doctor.user:
        other_user = appointment.patient.username

    context = {
        'appointment': appointment,
        'chat_room_id': chat_room_obj.id, # Pass chat room ID to the template for WebSocket URL
        'messages': messages_history,
        'other_user': other_user,
    }
    return render(request, 'chat/chat_room.html', context)