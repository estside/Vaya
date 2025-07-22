# healthcare_app_motihari/doctors/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('register-clinic/', views.register_clinic, name='register_clinic'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('<int:doctor_id>/book-appointment/', views.book_appointment, name='book_appointment'),
    path('appointment-success/', views.appointment_success, name='appointment_success'),
    path('appointment/<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('reports/upload/patient/', views.patient_upload_report, name='patient_upload_report'),
    path('reports/upload/doctor/<int:patient_id>/', views.doctor_upload_report, name='doctor_upload_report'),
    # --- NEW URL for Doctor Profile Edit ---
    path('profile/edit/', views.doctor_profile_edit, name='doctor_profile_edit'),
    # ---------------------------------------
]