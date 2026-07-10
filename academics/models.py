from django.conf import settings
from django.db import models
from students.models import Student
from fees.models import TERM_CHOICES


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="results")
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    year = models.PositiveIntegerField()
    score = models.DecimalField(max_digits=5, decimal_places=2)  # out of 100
    remarks = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date_recorded = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "subject", "term", "year")
        ordering = ["student", "subject"]

    def grade(self):
        s = float(self.score)
        if s >= 90:
            return "D1"
        if s >= 80:
            return "D2"
        if s >= 70:
            return "C3"
        if s >= 60:
            return "C4"
        if s >= 55:
            return "C5"
        if s >= 50:
            return "C6"
        if s >= 45:
            return "P7"
        if s >= 40:
            return "P8"
        return "F9"

    def __str__(self):
        return f"{self.student.admission_number} - {self.subject} ({self.term} {self.year}): {self.score}"
