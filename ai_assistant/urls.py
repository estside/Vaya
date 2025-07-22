# healthcare_app_motihari/ai_assistant/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('symptom-checker/', views.symptom_checker, name='symptom_checker'),
]