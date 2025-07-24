from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from django.contrib.auth import get_user_model
import datetime # Add this import at the top of your consumers.py

# Adjust these imports based on your actual app structure.
from doctors.models import Appointment, Doctor #

User = get_user_model() # Get the currently active User model (which is CustomUser)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appointment_id = self.scope['url_route']['kwargs']['appointment_id']
        self.room_group_name = f'chat_{self.appointment_id}'

        user = self.scope["user"]
        print(f"DEBUG: Attempting to connect. User: {user.username if user.is_authenticated else 'Anonymous'}")
        print(f"DEBUG: Appointment ID: {self.appointment_id}")

        if not user.is_authenticated:
            print("DEBUG: User is not authenticated. Closing connection.")
            await self.close()
            return

        try:
            # Fetch the appointment object asynchronously
            self.appointment = await database_sync_to_async(Appointment.objects.get)(id=self.appointment_id)

            # Fetch patient and doctor IDs asynchronously for logging
            patient_id_for_log = await database_sync_to_async(lambda: self.appointment.patient.id if self.appointment.patient else 'N/A')()
            doctor_id_for_log = await database_sync_to_async(lambda: self.appointment.doctor.id if self.appointment.doctor else 'N/A')()
            print(f"DEBUG: Fetched Appointment: ID={self.appointment.id}, Patient ID={patient_id_for_log}, Doctor ID={doctor_id_for_log}")

            is_patient = False
            is_doctor = False

            # Retrieve the patient (which is a CustomUser directly)
            user_from_appointment_patient = await database_sync_to_async(lambda: self.appointment.patient)()
            if user_from_appointment_patient:
                is_patient = (user == user_from_appointment_patient)
                print(f"DEBUG: Appointment Patient User: {user_from_appointment_patient.username if user_from_appointment_patient else 'None'}. Current User matches Patient: {is_patient}")
            else:
                print("DEBUG: No patient linked to this appointment.")

            # Retrieve the doctor's user
            doctor_obj = await database_sync_to_async(lambda: self.appointment.doctor)()
            if doctor_obj:
                user_from_appointment_doctor = await database_sync_to_async(lambda: doctor_obj.user)()
                is_doctor = (user == user_from_appointment_doctor)
                print(f"DEBUG: Appointment Doctor User: {user_from_appointment_doctor.username if user_from_appointment_doctor else 'None'}. Current User matches Doctor: {is_doctor}")
            else:
                print("DEBUG: No doctor linked to this appointment.")

            print(f"DEBUG: Is current user authorized? is_patient={is_patient}, is_doctor={is_doctor}")

            if is_patient or is_doctor:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                print(f"DEBUG: WebSocket connection accepted for appointment {self.appointment_id}.")
            else:
                print(f"DEBUG: User {user.username} is not authorized for appointment {self.appointment_id}. Closing connection.")
                await self.close()

        except Appointment.DoesNotExist:
            print(f"ERROR: Appointment with ID {self.appointment_id} does not exist. Closing connection.")
            await self.close()
        except Exception as e:
            print(f"CRITICAL ERROR during connect for appointment {self.appointment_id}: {e}")
            await self.close()

    async def disconnect(self, close_code):
        print(f"DEBUG: Disconnecting from room group: {self.room_group_name} with code: {close_code}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Add logic here to save the message to your database (e.g., a Message model)
        # from chat.models import Message # Example import if Message is in chat/models.py
        # await database_sync_to_async(Message.objects.create)(
        #     appointment=self.appointment,
        #     sender=self.scope["user"],
        #     content=message
        # )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.scope["user"].username
            }
        )
        print(f"DEBUG: Received message '{message}' from {self.scope['user'].username}. Sending to group {self.room_group_name}.")

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))
        print(f"DEBUG: Sent message '{message}' by {sender} to WebSocket.")
    # ... (other imports and ChatConsumer class definition) ...

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Get current time for timestamp
        timestamp = datetime.datetime.now().isoformat() # ISO format is good for JS parsing

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.scope["user"].username, #
                'timestamp': timestamp # Add timestamp here
            }
        )
        print(f"DEBUG: Received message '{message}' from {self.scope['user'].username}. Sending to group {self.room_group_name}.")

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp'] # Retrieve timestamp from the event

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp # Send timestamp to front-end
        }))
        print(f"DEBUG: Sent message '{message}' by {sender} to WebSocket.")

    import datetime # Add this import at the top of your consumers.py

# ... (other imports and ChatConsumer class definition) ...

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Get current time for timestamp
        timestamp = datetime.datetime.now().isoformat() # ISO format is good for JS parsing

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.scope["user"].username, #
                'timestamp': timestamp # Add timestamp here
            }
        )
        print(f"DEBUG: Received message '{message}' from {self.scope['user'].username}. Sending to group {self.room_group_name}.")

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp'] # Retrieve timestamp from the event

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp # Send timestamp to front-end
        }))
        print(f"DEBUG: Sent message '{message}' by {sender} to WebSocket.")