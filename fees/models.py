from django.conf import settings
from django.db import models
from students.models import Student, SchoolClass


TERM_CHOICES = [
    ("TERM1", "Term 1"),
    ("TERM2", "Term 2"),
    ("TERM3", "Term 3"),
]


class FeeStructure(models.Model):
    """Expected fee amount for a class in a given term/year."""

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="fee_structures")
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    year = models.PositiveIntegerField()
    boarding_status = models.CharField(
        max_length=10, choices=Student.BoardingStatus.choices, default=Student.BoardingStatus.DAY
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ("school_class", "term", "year", "boarding_status")
        ordering = ["-year", "term"]

    def __str__(self):
        return f"{self.school_class} - {self.get_term_display()} {self.year}: {self.amount}"


class Payment(models.Model):
    METHOD_CHOICES = [
        ("CASH", "Cash"),
        ("MOBILE_MONEY", "Mobile Money"),
        ("BANK", "Bank Deposit"),
        ("CHEQUE", "Cheque"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="CASH")
    date_paid = models.DateField(auto_now_add=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-date_paid"]

    def __str__(self):
        return f"{self.student.admission_number} paid {self.amount} ({self.get_term_display()} {self.year})"


def fee_status_for_student(student, term, year):
    """Return dict with expected, paid, balance, is_defaulter for one student/term/year."""
    try:
        structure = FeeStructure.objects.get(
            school_class=student.school_class,
            term=term,
            year=year,
            boarding_status=student.boarding_status,
        )
        expected = structure.amount
    except FeeStructure.DoesNotExist:
        expected = 0

    paid = student.payments.filter(term=term, year=year).aggregate(
        total=models.Sum("amount")
    )["total"] or 0

    balance = expected - paid
    return {
        "student": student,
        "expected": expected,
        "paid": paid,
        "balance": balance,
        "is_defaulter": balance > 0,
    }


def fee_report_for_class(school_class, term, year):
    """Fee status for every active student in a class."""
    return [
        fee_status_for_student(s, term, year)
        for s in school_class.students.filter(is_active=True)
    ]


def all_defaulters(term, year):
    """Fee status rows (defaulters only) across the whole school."""
    rows = [
        fee_status_for_student(s, term, year)
        for s in Student.objects.filter(is_active=True)
    ]
    return [r for r in rows if r["is_defaulter"]]
