from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from students.models import Student
from fees.models import TERM_CHOICES




class AcademicTerm(models.Model):
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    year = models.PositiveIntegerField()
    opens_on = models.DateField()
    closes_on = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("term", "year")
        ordering = ["-year", "term"]

    def clean(self):
        if self.opens_on and self.closes_on and self.closes_on < self.opens_on:
            raise ValidationError({"closes_on": "Closing date cannot be before opening date."})

    @property
    def effectively_closed(self):
        return self.is_closed or timezone.localdate() > self.closes_on

    @property
    def status(self):
        today = timezone.localdate()
        if self.effectively_closed:
            return "Closed"
        if today < self.opens_on:
            return "Scheduled"
        return "Open"

    def __str__(self):
        return f"{self.get_term_display()} {self.year}"


def term_is_closed(term, year):
    configured_term = AcademicTerm.objects.filter(term=term, year=year).first()
    return configured_term.effectively_closed if configured_term else False


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class GradingScale(models.Model):
    """
    Headteacher-configurable grade bands, e.g. D1 from 90, D2 from 80, etc.
    A score maps to the highest band whose min_score it meets or exceeds.
    """
    grade = models.CharField(max_length=5, unique=True)
    min_score = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        ordering = ["-min_score"]

    def __str__(self):
        return f"{self.grade} (from {self.min_score})"


_DEFAULT_SCALE = [
    ("D1", 90), ("D2", 80), ("C3", 70), ("C4", 60),
    ("C5", 55), ("C6", 50), ("P7", 45), ("P8", 40), ("F9", 0),
]


def compute_grade(score):
    s = float(score)
    bands = list(GradingScale.objects.order_by("-min_score"))
    if bands:
        for band in bands:
            if s >= float(band.min_score):
                return band.grade
        return bands[-1].grade
    for grade, min_score in _DEFAULT_SCALE:
        if s >= min_score:
            return grade
    return _DEFAULT_SCALE[-1][0]

class Remark(models.TextChoices):
    POOR = "POOR", "Poor"
    FAIR = "FAIR", "Fair"
    GOOD = "GOOD", "Good"
    VERY_GOOD = "VERY_GOOD", "Very Good"
    EXCELLENT = "EXCELLENT", "Excellent"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="results")
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    year = models.PositiveIntegerField()
    score = models.DecimalField(max_digits=5, decimal_places=2)
    remarks = models.CharField(max_length=20, choices=Remark.choices, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date_recorded = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "subject", "term", "year")
        ordering = ["student", "subject"]

    def grade(self):
        return compute_grade(self.score)

    def __str__(self):
        return f"{self.student.admission_number} - {self.subject} ({self.term} {self.year}): {self.score}"
