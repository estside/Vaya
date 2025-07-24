from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from doctors.models import Appointment, Doctor #
from chat.models import Message # <--- ADD THIS IMPORT!

@login_required
def chat_room(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id) #

    # Security check: Ensure the logged-in user is either the patient or the doctor for this appointment
    if not (request.user == appointment.patient or (appointment.doctor and request.user == appointment.doctor.user)):
        return render(request, 'unauthorized.html', {'message': 'You are not authorized to view this chat.'})

    # Retrieve all messages for this appointment, ordered by timestamp
    # .select_related('sender') pre-fetches the sender user to avoid N+1 queries
    # .filter(appointment=appointment) ensures only messages for this specific chat are loaded
    messages = Message.objects.filter(appointment=appointment).order_by('timestamp').select_related('sender')

    # Determine the "other user" for the chat header
    other_user = None
    if request.user == appointment.patient:
        other_user = appointment.doctor.full_name if appointment.doctor else "Unknown Doctor"
    elif appointment.doctor and request.user == appointment.doctor.user:
        other_user = appointment.patient.username

    context = {
        'appointment': appointment,
        'other_user': other_user,
        'messages': messages, # Pass the message history to the template
    }
    return render(request, 'chat/chat_room.html', context)