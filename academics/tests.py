from django.test import SimpleTestCase

from students.models import SchoolClass

from .views import is_nursery_class


class NurseryClassDetectionTests(SimpleTestCase):
    def test_supported_nursery_class_names(self):
        for name in ("Baby Class", "Nursery", "Nursery Class", "Middle", "Middle Class", "Top Class"):
            with self.subTest(name=name):
                self.assertTrue(is_nursery_class(SchoolClass(name=name)))

    def test_primary_class_is_not_nursery(self):
        self.assertFalse(is_nursery_class(SchoolClass(name="Primary Four")))
