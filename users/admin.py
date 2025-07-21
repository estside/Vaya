# healthcare_app_motihari/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your CustomUser model with the admin site
admin.site.register(CustomUser, UserAdmin) # UserAdmin provides default admin functionality