from io import BytesIO
from html import escape
import hashlib
import json

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


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


def content_hash(row, attachments) -> str:
    raw = json.dumps(
        canonical_payload(row, attachments),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def render_pdf(row, attachments) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "CocTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=17,
        leading=21,
        spaceAfter=5,
    )
    subtitle = ParagraphStyle(
        "CocSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        spaceAfter=12,
    )
    body = styles["BodyText"]
    body.leading = 14

    story = [
        Paragraph("COC — Boletim de Ocorrência", title),
        Paragraph(f'{row["codigo"]} · Status: {row["status"].upper()}', subtitle),
    ]

    meta = [
        ["Data", row["data_ocorrencia"], "Hora", row["hora_ocorrencia"]],
        ["Local", row["local"], "Setor", row["setor"]],
        ["Tipo", row["tipo_ocorrencia"], "Autor", row["autor_original"]],
    ]
    table = Table(meta, colWidths=[24 * mm, 55 * mm, 24 * mm, 55 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, "#CCCCCC"),
        ("BACKGROUND", (0, 0), (0, -1), "#F1F5F9"),
        ("BACKGROUND", (2, 0), (2, -1), "#F1F5F9"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [table, Spacer(1, 8)]

    sections = [
        ("Título", row["titulo"]),
        ("Descrição da ocorrência", row["descricao"]),
        ("Consequências / impacto", row["consequencias"]),
        ("Pessoas envolvidas", row["pessoas_envolvidas"]),
        ("Ações imediatas", row["acoes_imediatas"]),
        ("Ações preventivas / recomendações", row["acoes_preventivas"]),
    ]
    for label, value in sections:
        story.append(Paragraph(f"<b>{label}</b>", body))
        story.append(Paragraph(paragraph_text(value), body))
        story.append(Spacer(1, 6))

    names = ", ".join(a["nome_original"] for a in attachments) or "Nenhum anexo"
    story.append(Paragraph("<b>Anexos</b>", body))
    story.append(Paragraph(paragraph_text(names), body))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f'Criado em: {row["criado_em"]}', body))
    if row["finalizado_em"]:
        story.append(Paragraph(f'Finalizado em: {row["finalizado_em"]}', body))

    doc.build(story)
    return buf.getvalue()
