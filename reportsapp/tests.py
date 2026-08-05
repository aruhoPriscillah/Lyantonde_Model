import io

from django.test import SimpleTestCase
from openpyxl import load_workbook

from .utils import export_excel


class DownloadAlignmentTests(SimpleTestCase):
    def test_excel_headers_and_values_are_left_aligned(self):
        response = export_excel("alignment", "Alignment", ["Name", "Status"], [["Pupil", "Present"]])
        workbook = load_workbook(io.BytesIO(response.content))
        sheet = workbook.active

        self.assertEqual(sheet["A3"].alignment.horizontal, "left")
        self.assertEqual(sheet["B3"].alignment.horizontal, "left")
        self.assertEqual(sheet["A4"].alignment.horizontal, "left")
        self.assertEqual(sheet["B4"].alignment.horizontal, "left")
