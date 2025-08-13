# healthcare_app_motihari/doctors/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Public-facing URLs
    path('', views.doctor_list, name='doctor_list'),
    path('<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('register-clinic/', views.register_clinic, name='register_clinic'),
    path('<int:doctor_id>/book-appointment/', views.book_appointment, name='book_appointment'),
    path('appointment-success/', views.appointment_success, name='appointment_success'),

    # Doctor-facing management URLs
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('profile/edit/', views.doctor_profile_edit, name='doctor_profile_edit'),
    path('appointments/<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('slots/manage/', views.doctor_slot_management, name='doctor_slot_management'),
    path('slots/generate/', views.doctor_generate_slots, name='doctor_generate_slots'),
    path('slots/toggle-availability/<int:slot_id>/', views.toggle_slot_availability, name='toggle_slot_availability'),

    # Patient/Report Management URLs
    path('patient/<int:patient_id>/details/', views.doctor_patient_detail, name='doctor_patient_detail'),
    path('patient/add/', views.doctor_add_patient, name='doctor_add_patient'),
    path('reports/upload/patient/<int:patient_id>/', views.doctor_upload_report, name='doctor_upload_report'),
    path('reports/upload/self/', views.patient_upload_report, name='patient_upload_report'),
    path('<int:doctor_id>/book-followup/<int:patient_id>/', views.book_followup_appointment, name='book_followup_appointment'),

]