from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a role that drives dashboard access and permissions."""

    class Role(models.TextChoices):
        HEADTEACHER = "HEADTEACHER", "Headteacher"
        BURSAR = "BURSAR", "Bursar"
        TEACHER = "TEACHER", "Teacher"

    role = models.CharField(max_length=20, choices=Role.choices)
    phone_number = models.CharField(max_length=20, blank=True)

    def is_headteacher(self):
        return self.role == self.Role.HEADTEACHER

    def is_bursar(self):
        return self.role == self.Role.BURSAR

    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
