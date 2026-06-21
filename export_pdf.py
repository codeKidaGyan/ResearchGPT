from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def export_text_to_pdf(title: str, body: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        leading=16,
        spaceAfter=10,
    )
    story = [Paragraph(title, title_style), Spacer(1, 12)]
    for paragraph in body.split("\n"):
        cleaned = paragraph.strip()
        if cleaned:
            story.append(Paragraph(cleaned.replace("&", "&amp;"), body_style))
            story.append(Spacer(1, 6))
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value