from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from django.contrib.auth import get_user_model
import datetime # Required for timestamps

# Adjust these imports based on your actual app structure.
from doctors.models import Appointment, Doctor #
from chat.models import Message # Import the Message model for chat history

User = get_user_model() # Get the currently active User model (which is CustomUser)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appointment_id = self.scope['url_route']['kwargs']['appointment_id']
        self.room_group_name = f'chat_{self.appointment_id}'

        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        try:
            self.appointment = await database_sync_to_async(Appointment.objects.get)(id=self.appointment_id)

            is_patient = False
            is_doctor = False

            # Retrieve the patient (which is a CustomUser directly)
            user_from_appointment_patient = await database_sync_to_async(lambda: self.appointment.patient)()
            if user_from_appointment_patient:
                is_patient = (user == user_from_appointment_patient)

            # Retrieve the doctor's user
            doctor_obj = await database_sync_to_async(lambda: self.appointment.doctor)()
            if doctor_obj:
                user_from_appointment_doctor = await database_sync_to_async(lambda: doctor_obj.user)()
                is_doctor = (user == user_from_appointment_doctor)

            if is_patient or is_doctor:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
            else:
                await self.close()

        except Appointment.DoesNotExist:
            await self.close()
        except Exception as e:
            # You might want to log this critical error to a file/monitoring system
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message'] # Renamed for clarity

        # Save the message to the database
        # The timestamp will be automatically set by auto_now_add=True on the Message model
        message_obj = await database_sync_to_async(Message.objects.create)(
            appointment=self.appointment,
            sender=self.scope["user"],
            content=message_content,
        )

        # Get the timestamp from the saved object to ensure consistency for sending
        timestamp_to_send = message_obj.timestamp.isoformat()

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender': self.scope["user"].username,
                'timestamp': timestamp_to_send # Use the timestamp from the saved object
            }
        )

    # Receive message from room group (This is called by the channel layer)
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']

        # Send message back to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp
        }))