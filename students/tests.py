from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import SchoolClass


class ClassManagementTests(TestCase):
    def setUp(self):
        self.headteacher = User.objects.create_user(
            username="headteacher", password="test-password", role=User.Role.HEADTEACHER
        )
        self.client.force_login(self.headteacher)

    def test_add_class(self):
        response = self.client.post(
            reverse("students:manage_classes"), {"name": "Middle Class", "class_teacher": ""}
        )

        self.assertRedirects(response, reverse("students:manage_classes"))
        self.assertTrue(SchoolClass.objects.filter(name="Middle Class").exists())

    def test_duplicate_class_name_displays_validation_error(self):
        SchoolClass.objects.create(name="Top Class")

        response = self.client.post(
            reverse("students:manage_classes"), {"name": "Top Class", "class_teacher": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "School class with this Name already exists")

    def test_edit_class_page_loads_and_saves(self):
        school_class = SchoolClass.objects.create(name="Nursery")
        url = reverse("students:edit_class", args=[school_class.pk])

        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {"name": "Baby Class", "class_teacher": ""})

        self.assertRedirects(response, reverse("students:manage_classes"))
        school_class.refresh_from_db()
        self.assertEqual(school_class.name, "Baby Class")
