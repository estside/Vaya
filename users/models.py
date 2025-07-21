# healthcare_app_motihari/users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Add any extra fields here for all users (e.g., phone_number, address)
    # For now, we'll keep it simple, but this is where you'd extend.
    # For example:
    # phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    # Add related_name to avoid clashes with default User model's relationships
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        related_name="customuser_set", # Add this
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="customuser_set", # Add this
        related_query_name="customuser",
    )

    def __str__(self):
        return self.username # Or self.get_full_name() if you use it