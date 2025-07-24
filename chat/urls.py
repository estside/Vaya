# healthcare_app_motihari/chat/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # URL for accessing a specific chat room by appointment ID
    path('appointment/<int:appointment_id>/', views.chat_room, name='chat_room'),
]