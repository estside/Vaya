# healthcare_app_motihari/users/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('redirect/', views.custom_login_redirect, name='custom_login_redirect'),
    path('signup/patient/', views.patient_signup, name='patient_signup'),
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('profile/edit/', views.patient_profile_edit, name='patient_profile_edit'), # <--- ADDED HERE
]