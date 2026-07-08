"""Shared helpers for generating PDF and Excel reports across dashboards."""
import io
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from functools import lru_cache
from django.conf import settings
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from PIL import Image as PILImage
from reportlab.lib.utils import ImageReader

SCHOOL_BADGE_PATH = settings.BASE_DIR / "static" / "img" / "school_badge.jpeg"


@lru_cache(maxsize=1)
def _watermark_image_reader():
    if not SCHOOL_BADGE_PATH.exists():
        return None
    badge = PILImage.open(SCHOOL_BADGE_PATH).convert("RGBA")
    faded = PILImage.new("RGBA", badge.size, (255, 255, 255, 0))
    faded = PILImage.blend(faded, badge, alpha=0.08)
    buffer = io.BytesIO()
    faded.save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)


def _draw_watermark(canvas_obj, doc):
    watermark = _watermark_image_reader()
    if watermark is None:
        return
    page_width, page_height = doc.pagesize
    size = min(page_width, page_height) * 0.6
    canvas_obj.saveState()
    canvas_obj.drawImage(
        watermark,
        (page_width - size) / 2,
        (page_height - size) / 2,
        width=size,
        height=size,
        mask="auto",
        preserveAspectRatio=True,
    )
    canvas_obj.restoreState()


@lru_cache(maxsize=1)
def _excel_logo_path():
    if not SCHOOL_BADGE_PATH.exists():
        return None
    resized_path = SCHOOL_BADGE_PATH.with_name("school_badge_logo_small.png")
    if not resized_path.exists():
        badge = PILImage.open(SCHOOL_BADGE_PATH).convert("RGBA")
        badge.thumbnail((90, 135))
        badge.save(resized_path, format="PNG")
    return str(resized_path)


def export_excel(filename, title, headers, rows):
    """
    headers: list[str]
    rows: list[list] (values only, in same order as headers)
    Returns an HttpResponse with an .xlsx attachment.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31] or "Report"

    header_row_idx = 3
    logo_path = _excel_logo_path()
    if logo_path:
        img = XLImage(logo_path)
        ws.add_image(img, "A1")
        ws.row_dimensions[1].height = 80
        title_col_start = 3
    else:
        title_col_start = 1

    ws.merge_cells(
        start_row=1, start_column=title_col_start, end_row=1, end_column=max(len(headers), title_col_start)
    )
    title_cell = ws.cell(row=1, column=title_col_start, value=title)
    title_cell.font = Font(size=14, bold=True)
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=header_row_idx, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for row_offset, row in enumerate(rows, start=header_row_idx + 1):
        for col_idx, value in enumerate(row, start=1):
            ws.cell(row=row_offset, column=col_idx, value=value)

    for col_idx, header in enumerate(headers, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = max([len(str(header))] + [len(str(r[col_idx - 1])) for r in rows] or [10])
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return response


def export_pdf(filename, title, headers, rows, subtitle=None, landscape_mode=False):
    """
    headers: list[str]
    rows: list[list] (values only, in same order as headers)
    Returns an HttpResponse with a .pdf attachment.
    """
    buffer = io.BytesIO()
    pagesize = landscape(A4) if landscape_mode else A4
    doc = SimpleDocTemplate(
        buffer, pagesize=pagesize,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"])]
    if subtitle:
        elements.append(Paragraph(subtitle, styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [headers] + [[str(v) for v in row] for row in rows]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(table)
    doc.build(elements, onFirstPage=_draw_watermark, onLaterPages=_draw_watermark)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return response
