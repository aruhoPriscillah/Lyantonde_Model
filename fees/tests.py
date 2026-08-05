from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase, TestCase

from students.models import SchoolClass, Student

from .forms import PaymentForm
from .models import FeeStructure, Payment, fee_status_for_student
from .utils import format_ugx


class UgxFormattingTests(SimpleTestCase):
    def test_formats_amount_with_currency_and_grouping(self):
        self.assertEqual(format_ugx(Decimal("1250000.00")), "UGX 1,250,000")

    def test_template_filter_uses_ugx_format(self):
        rendered = Template("{% load fees_format %}{{ amount|ugx }}").render(
            Context({"amount": Decimal("1250000.00")})
        )
        self.assertEqual(rendered, "UGX 1,250,000")

# Create your tests here.

class PreviousBalanceTests(TestCase):
    def setUp(self):
        self.school_class = SchoolClass.objects.create(name="Balance Test Class")
        self.student = Student.objects.create(
            first_name="Balance",
            last_name="Pupil",
            gender="M",
            date_of_birth="2015-01-01",
            school_class=self.school_class,
            boarding_status="DAY",
            guardian_name="Guardian",
            guardian_phone="0700000000",
        )
        FeeStructure.objects.create(
            school_class=self.school_class, term="TERM1", year=2025,
            boarding_status="DAY", amount=Decimal("100000"),
        )
        FeeStructure.objects.create(
            school_class=self.school_class, term="TERM2", year=2025,
            boarding_status="DAY", amount=Decimal("120000"),
        )
        FeeStructure.objects.create(
            school_class=self.school_class, term="TERM1", year=2026,
            boarding_status="DAY", amount=Decimal("150000"),
        )

    def payment(self, term, year, amount):
        return Payment.objects.create(student=self.student, term=term, year=year, amount=amount)

    def test_carries_previous_term_balance_into_total_due(self):
        self.payment("TERM1", 2025, Decimal("60000"))
        self.payment("TERM2", 2025, Decimal("20000"))
        self.payment("TERM3", 2025, Decimal("999999"))

        status = fee_status_for_student(self.student, "TERM2", 2025)

        self.assertEqual(status["previous_balance"], Decimal("40000"))
        self.assertEqual(status["expected"], Decimal("120000"))
        self.assertEqual(status["total_due"], Decimal("160000"))
        self.assertEqual(status["paid"], Decimal("20000"))
        self.assertEqual(status["balance"], Decimal("140000"))

    def test_carries_balance_across_years(self):
        self.payment("TERM1", 2025, Decimal("60000"))
        self.payment("TERM2", 2025, Decimal("100000"))

        status = fee_status_for_student(self.student, "TERM1", 2026)

        self.assertEqual(status["previous_balance"], Decimal("60000"))
        self.assertEqual(status["total_due"], Decimal("210000"))

    def test_prior_credit_reduces_current_total_due(self):
        self.payment("TERM1", 2025, Decimal("110000"))

        status = fee_status_for_student(self.student, "TERM2", 2025)

        self.assertEqual(status["previous_balance"], Decimal("-10000"))
        self.assertEqual(status["total_due"], Decimal("110000"))


class PaymentAmountValidationTests(TestCase):
    def setUp(self):
        school_class = SchoolClass.objects.create(name="Payment Validation Class")
        self.student = Student.objects.create(
            first_name="Payment",
            last_name="Pupil",
            gender="F",
            date_of_birth="2015-01-01",
            school_class=school_class,
            guardian_name="Guardian",
            guardian_phone="0700000000",
        )

    def form_for_amount(self, amount):
        return PaymentForm(data={
            "student": self.student.pk,
            "term": "TERM1",
            "year": 2026,
            "amount": amount,
            "method": "CASH",
            "reference": "",
        })

    def test_rejects_zero_payment(self):
        form = self.form_for_amount("0")
        self.assertFalse(form.is_valid())
        self.assertIn("Payment amount must be greater than zero.", form.errors["amount"])

    def test_rejects_negative_payment(self):
        form = self.form_for_amount("-5000")
        self.assertFalse(form.is_valid())
        self.assertIn("Payment amount must be greater than zero.", form.errors["amount"])

    def test_accepts_positive_payment(self):
        self.assertTrue(self.form_for_amount("0.01").is_valid())