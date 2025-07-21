# healthcare_app_motihari/doctors/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('register-clinic/', views.register_clinic, name='register_clinic'), # New URL for registration
    path('register-clinic/success/', views.clinic_registration_success, name='clinic_registration_success'), # Success page URL
]