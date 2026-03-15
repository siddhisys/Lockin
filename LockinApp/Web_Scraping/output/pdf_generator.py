import os
from reportlab.lib.pagesizes import A4 # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # type: ignore
from reportlab.lib.units import mm # type: ignore
from reportlab.lib import colors # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer # type: ignore
from reportlab.pdfbase import pdfmetrics # type: ignore
from reportlab.pdfbase.ttfonts import TTFont # type: ignore

def generate_pdf(formatted_data, filename="scraped_content.pdf"):
    # --- Register DejaVu font if available, otherwise fall back to Helvetica ---
    current_dir = os.path.dirname(__file__)
    font_path = os.path.join(current_dir, "DejaVuSans.ttf")

    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("DejaVu", font_path))
        base_font = "DejaVu"
    else:
        base_font = "Helvetica"

    # --- Set up document ---
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        fontName=base_font,
        fontSize=16,
        leading=20,
        alignment=1,  # center
        spaceAfter=12,
        textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "ItemHeading",
        fontName=base_font,
        fontSize=13,
        leading=17,
        spaceAfter=4,
        textColor=colors.HexColor("#16213e"),
    )
    meta_style = ParagraphStyle(
        "Meta",
        fontName=base_font,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#555555"),
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName=base_font,
        fontSize=10,
        leading=14,
        spaceAfter=2,
        leftIndent=10,
    )

    story = []

    # --- Page title ---
    story.append(Paragraph("Scraped Content", title_style))
    story.append(Spacer(1, 8 * mm))

    for item in formatted_data:
        # Escape any HTML-like characters that confuse ReportLab's parser
        def safe(text):
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        story.append(Paragraph(safe(item["title"]), heading_style))
        story.append(Paragraph(f"Source: {safe(item['source'])}", meta_style))
        story.append(Paragraph(f"URL: {safe(item['url'])}", meta_style))
        story.append(Spacer(1, 3 * mm))

        for chunk in item["content"]:
            story.append(Paragraph(f"• {safe(chunk)}", body_style))
            story.append(Spacer(1, 1 * mm))

        story.append(Spacer(1, 5 * mm))

    doc.build(story)
    return filename