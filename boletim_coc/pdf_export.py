from datetime import date, datetime
from html import escape
from io import BytesIO
import hashlib
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


BLUE = colors.HexColor("#0B5EA8")
DARK_BLUE = colors.HexColor("#083B66")
LIGHT_BLUE = colors.HexColor("#EAF3FB")
BORDER = colors.HexColor("#D6E1EB")
TEXT = colors.HexColor("#243447")
MUTED = colors.HexColor("#64748B")
GREEN = colors.HexColor("#1E7A46")


def canonical_payload(row, attachments):
    fields = [
        "id", "codigo", "autor_original", "data_ocorrencia", "hora_ocorrencia", "local",
        "setor", "tipo_ocorrencia", "titulo", "descricao", "consequencias",
        "pessoas_envolvidas", "acoes_imediatas", "acoes_preventivas", "status",
        "criado_em", "finalizado_em",
    ]
    payload = {field: row[field] for field in fields}
    payload["anexos"] = [
        {
            "nome_original": a["nome_original"],
            "mime_type": a["mime_type"],
            "tamanho_bytes": a["tamanho_bytes"],
            "sha256": a["sha256"],
        }
        for a in attachments
    ]
    return payload


def paragraph_text(value) -> str:
    return escape(str(value or "—")).replace("\n", "<br/>")


def format_date_br(value) -> str:
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    try:
        return date.fromisoformat(str(value)[:10]).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return str(value)


def format_datetime_br(value) -> str:
    if not value:
        return "—"
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        return parsed.strftime("%d/%m/%Y às %H:%M")
    except (TypeError, ValueError):
        return str(value)


def content_hash(row, attachments) -> str:
    raw = json.dumps(
        canonical_payload(row, attachments),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _footer(canvas, doc, codigo: str):
    canvas.saveState()
    width, _ = A4
    y = 10 * mm
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, y + 5 * mm, width - doc.rightMargin, y + 5 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, y, f"COC Anestesia · {codigo}")
    canvas.drawRightString(width - doc.rightMargin, y, f"Página {doc.page}")
    canvas.restoreState()


def _info_cell(label: str, value, label_style, value_style):
    return [
        Paragraph(paragraph_text(label).upper(), label_style),
        Paragraph(paragraph_text(value), value_style),
    ]


def _section(label: str, value, section_style, body_style):
    block = Table(
        [[Paragraph(label, section_style)], [Paragraph(paragraph_text(value), body_style)]],
        colWidths=[174 * mm],
    )
    block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return block


def render_pdf(row, attachments) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=22 * mm,
        title=f'Boletim de Ocorrência {row["codigo"]}',
        author="COC Anestesia",
    )
    styles = getSampleStyleSheet()
    brand = ParagraphStyle(
        "Brand",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
        spaceAfter=2,
    )
    title = ParagraphStyle(
        "CocTitle",
        parent=styles["Title"],
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=colors.white,
        spaceAfter=2,
    )
    header_meta = ParagraphStyle(
        "HeaderMeta",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#DCEEFF"),
    )
    info_label = ParagraphStyle(
        "InfoLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=MUTED,
    )
    info_value = ParagraphStyle(
        "InfoValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=TEXT,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=DARK_BLUE,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        textColor=TEXT,
    )
    headline = ParagraphStyle(
        "Headline",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=DARK_BLUE,
        spaceAfter=4,
    )
    caption = ParagraphStyle(
        "Caption",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=MUTED,
    )

    status_text = str(row["status"] or "").upper()
    status_bg = GREEN if status_text == "FINALIZADO" else colors.HexColor("#B7791F")
    status = Table(
        [[Paragraph(f"<b>{paragraph_text(status_text)}</b>", ParagraphStyle(
            "Status", parent=styles["Normal"], fontSize=8, textColor=colors.white, alignment=TA_CENTER
        ))]],
        colWidths=[31 * mm],
    )
    status.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), status_bg),
        ("BOX", (0, 0), (-1, -1), 0, status_bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    header_left = [
        Paragraph("COC ANESTESIA", brand),
        Paragraph("Boletim de Ocorrência", title),
        Paragraph(f'Documento {paragraph_text(row["codigo"])}', header_meta),
    ]
    header_table = Table([[header_left, status]], colWidths=[139 * mm, 35 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE),
        ("LEFTPADDING", (0, 0), (0, 0), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    info_rows = [
        [
            _info_cell("Data", format_date_br(row["data_ocorrencia"]), info_label, info_value),
            _info_cell("Hora", row["hora_ocorrencia"], info_label, info_value),
            _info_cell("Tipo", row["tipo_ocorrencia"], info_label, info_value),
        ],
        [
            _info_cell("Local", row["local"], info_label, info_value),
            _info_cell("Setor", row["setor"], info_label, info_value),
            _info_cell("Autor", row["autor_original"], info_label, info_value),
        ],
    ]
    info_table = Table(info_rows, colWidths=[58 * mm, 58 * mm, 58 * mm])
    info_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story = [
        header_table,
        Spacer(1, 7 * mm),
        info_table,
        Spacer(1, 7 * mm),
        Paragraph("Ocorrência", caption),
        Paragraph(paragraph_text(row["titulo"]), headline),
        Spacer(1, 2 * mm),
    ]

    sections = [
        ("Descrição da ocorrência", row["descricao"]),
        ("Consequências / impacto", row["consequencias"]),
        ("Pessoas envolvidas", row["pessoas_envolvidas"]),
        ("Ações imediatas tomadas", row["acoes_imediatas"]),
        ("Ações corretivas / preventivas", row["acoes_preventivas"]),
    ]
    for label, value in sections:
        story.append(_section(label, value, section_style, body))
        story.append(Spacer(1, 3 * mm))

    names = ", ".join(a["nome_original"] for a in attachments) or "Nenhum anexo"
    story.append(_section("Anexos", names, section_style, body))
    story.append(Spacer(1, 5 * mm))

    audit = Table(
        [[
            Paragraph(f'<b>Criado em:</b> {paragraph_text(format_datetime_br(row["criado_em"]))}', caption),
            Paragraph(f'<b>Finalizado em:</b> {paragraph_text(format_datetime_br(row["finalizado_em"]))}', caption),
        ]],
        colWidths=[87 * mm, 87 * mm],
    )
    audit.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(audit)

    footer = lambda canvas, document: _footer(canvas, document, row["codigo"])
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
