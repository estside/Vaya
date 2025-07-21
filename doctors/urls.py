# healthcare_app_motihari/doctors/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('register-clinic/', views.register_clinic, name='register_clinic'),
    path('register-clinic/success/', views.clinic_registration_success, name='clinic_registration_success'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('<int:doctor_id>/book-appointment/', views.book_appointment, name='book_appointment'), # <--- NEW URL
    path('appointment-success/', views.appointment_success, name='appointment_success'), # <--- NEW URL
]