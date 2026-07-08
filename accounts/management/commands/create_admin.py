"""
Creates (or updates) a Headteacher/superuser account from environment variables.
Safe to run on every deploy — if the account already exists, it just updates
the password instead of failing.

Reads: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
If any of these are missing, the command does nothing (so it's safe to run
even before you've set them, e.g. on first deploy).
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create or update the admin/headteacher account from environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                "DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD not set — skipping admin creation."
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": User.Role.HEADTEACHER,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.email = email
        user.role = User.Role.HEADTEACHER
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created admin account '{username}'."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated existing admin account '{username}'."))