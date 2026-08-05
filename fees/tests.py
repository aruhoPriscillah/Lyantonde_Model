from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase

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
