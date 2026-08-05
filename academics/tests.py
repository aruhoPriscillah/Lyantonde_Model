from django.test import SimpleTestCase, TestCase

from accounts.models import User
from students.models import SchoolClass

from .forms import BulkResultFilterForm, ResultForm
from .models import Subject
from .views import is_lower_primary_class, is_nursery_class, is_upper_primary_class, nursery_report_rows


class NurseryClassDetectionTests(SimpleTestCase):
    def test_supported_nursery_class_names(self):
        for name in ("Baby Class", "Nursery", "Nursery Class", "Middle", "Middle Class", "Top Class"):
            with self.subTest(name=name):
                self.assertTrue(is_nursery_class(SchoolClass(name=name)))

    def test_primary_class_is_not_nursery(self):
        self.assertFalse(is_nursery_class(SchoolClass(name="Primary Four")))


class ResultFormTests(SimpleTestCase):
    def test_remarks_is_a_dropdown_with_all_remark_choices(self):
        form = ResultForm()

        self.assertEqual(form.fields["remarks"].widget.__class__.__name__, "Select")
        self.assertEqual(
            list(form.fields["remarks"].choices),
            [
                ("", "---------"),
                ("POOR", "Poor"),
                ("FAIR", "Fair"),
                ("GOOD", "Good"),
                ("VERY_GOOD", "Very Good"),
                ("EXCELLENT", "Excellent"),
            ],
        )


class LowerPrimaryClassDetectionTests(SimpleTestCase):
    def test_supported_lower_primary_names(self):
        for name in ("P1", "P 2", "P3 Class", "Primary 1", "Primary Two", "Primary Three"):
            with self.subTest(name=name):
                self.assertTrue(is_lower_primary_class(SchoolClass(name=name)))

    def test_other_classes_are_not_lower_primary(self):
        for name in ("Baby Class", "P4", "Primary Four"):
            with self.subTest(name=name):
                self.assertFalse(is_lower_primary_class(SchoolClass(name=name)))


class UpperPrimaryClassDetectionTests(SimpleTestCase):
    def test_supported_upper_primary_names(self):
        for name in ("P4", "P 5", "P6 Class", "P7", "Primary 4", "Primary Five", "Primary Seven"):
            with self.subTest(name=name):
                self.assertTrue(is_upper_primary_class(SchoolClass(name=name)))

    def test_other_classes_are_not_upper_primary(self):
        for name in ("Top Class", "P3", "Primary Three"):
            with self.subTest(name=name):
                self.assertFalse(is_upper_primary_class(SchoolClass(name=name)))


class ClassSubjectDropdownTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name in (
            "Numbers", "English", "Reading", "Health Habits", "Social Development", "Drawing", "Writing",
            "Mathematics", "Literacy I", "Literacy II (Reading)", "Religious Education", "Luganda", "SST", "Science",
        ):
            Subject.objects.get_or_create(name=name)

    def subject_names(self, form):
        return set(form.fields["subject"].queryset.values_list("name", flat=True))

    def test_nursery_dropdown_only_has_nursery_subjects(self):
        form = ResultForm(teacher_class=SchoolClass.objects.create(name="Baby Class"))
        self.assertEqual(self.subject_names(form), {
            "Numbers", "English", "Reading", "Health Habits", "Social Development", "Drawing", "Writing",
        })

    def test_lower_primary_dropdown_only_has_lower_primary_subjects(self):
        form = ResultForm(teacher_class=SchoolClass.objects.create(name="P2"))
        self.assertEqual(self.subject_names(form), {
            "Mathematics", "English", "Literacy I", "Literacy II (Reading)", "Religious Education", "Luganda",
        })

    def test_upper_primary_single_and_bulk_dropdowns_match(self):
        school_class = SchoolClass.objects.create(name="Primary 6")
        expected = {"Mathematics", "English", "SST", "Science"}
        self.assertEqual(self.subject_names(ResultForm(teacher_class=school_class)), expected)
        self.assertEqual(self.subject_names(BulkResultFilterForm(teacher_class=school_class)), expected)

    def test_nursery_report_includes_all_subjects_without_results(self):
        school_class = SchoolClass.objects.create(name="Top Class")
        student = school_class.students.create(
            first_name="Test",
            last_name="Pupil",
            gender="F",
            date_of_birth="2021-01-01",
            guardian_name="Parent",
            guardian_phone="0700000000",
        )

        rows = nursery_report_rows(student, "TERM1", 2026)

        self.assertEqual([row["subject"] for row in rows], [
            "Numbers", "English", "Reading", "Health Habits", "Social Development", "Drawing", "Writing",
        ])
        self.assertTrue(all(row["score"] is None for row in rows))
