"""Create demo users, a class, and a couple of students so the system can be explored immediately.
Run with: python manage.py seed_demo_data
"""
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from students.models import SchoolClass, Student
from fees.models import FeeStructure

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo users and sample data"

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "Admin@12345", role=User.Role.HEADTEACHER)
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin' / password 'Admin@12345' (Headteacher)"))

        bursar, created = User.objects.get_or_create(
            username="bursar", defaults={"role": User.Role.BURSAR, "first_name": "Betty", "last_name": "Bursar"}
        )
        if created:
            bursar.set_password("Bursar@12345")
            bursar.save()
            self.stdout.write(self.style.SUCCESS("Created user 'bursar' / password 'Bursar@12345'"))

        teacher, created = User.objects.get_or_create(
            username="teacher1", defaults={"role": User.Role.TEACHER, "first_name": "Tom", "last_name": "Teacher"}
        )
        if created:
            teacher.set_password("Teacher@12345")
            teacher.save()
            self.stdout.write(self.style.SUCCESS("Created user 'teacher1' / password 'Teacher@12345'"))

        p4, _ = SchoolClass.objects.get_or_create(name="Primary 4", defaults={"class_teacher": teacher})
        if p4.class_teacher_id is None:
            p4.class_teacher = teacher
            p4.save()

        year = datetime.date.today().year
        FeeStructure.objects.get_or_create(
            school_class=p4, term="TERM1", year=year, defaults={"amount": 350000}
        )

        if not Student.objects.filter(school_class=p4).exists():
            Student.objects.create(
                first_name="John", last_name="Mukasa", gender="M",
                date_of_birth=datetime.date(2016, 3, 12), school_class=p4,
                guardian_name="Peter Mukasa", guardian_phone="0700111222",
            )
            Student.objects.create(
                first_name="Grace", last_name="Nabirye", gender="F",
                date_of_birth=datetime.date(2016, 7, 5), school_class=p4,
                guardian_name="Sarah Nabirye", guardian_phone="0700333444",
            )
            self.stdout.write(self.style.SUCCESS("Created 2 demo students in Primary 4"))

        self.stdout.write(self.style.SUCCESS("Demo data seeding complete."))
