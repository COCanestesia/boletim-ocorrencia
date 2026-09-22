from boletim_coc.pdf_export import (
    canonical_payload,
    content_hash,
    format_date_br,
    format_datetime_br,
    paragraph_text,
    render_pdf,
)


def fake_row():
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "codigo": "COC-2026-000001",
        "origem": "local",
        "windows_user": "MARIA",
        "autor_original": "Maria Aparecida da Silva",
        "data_ocorrencia": "2026-09-22",
        "hora_ocorrencia": "08:30",
        "local": "Hospital",
        "setor": "Centro cirúrgico",
        "tipo_ocorrencia": "Segurança",
        "titulo": "Queda",
        "descricao": "Descrição",
        "consequencias": "Sem dano",
        "pessoas_envolvidas": "Equipe",
        "acoes_imediatas": "Sinalizado",
        "acoes_preventivas": "Revisão",
        "status": "finalizado",
        "criado_em": "2026-09-22T08:40:00-04:00",
        "atualizado_em": "2026-09-22T08:45:00-04:00",
        "finalizado_em": "2026-09-22T08:45:00-04:00",
        "hash_conteudo": None,
    }


def test_content_hash_is_stable():
    row = fake_row()
    assert content_hash(row, []) == content_hash(dict(row), [])


def test_render_pdf_returns_pdf_bytes():
    data = render_pdf(fake_row(), [])
    assert data.startswith(b"%PDF")
    assert len(data) > 1500


def test_canonical_payload_excludes_machine_specific_fields():
    payload = canonical_payload(fake_row(), [])
    assert "windows_user" not in payload
    assert payload["autor_original"] == "Maria Aparecida da Silva"


def test_paragraph_text_preserves_literal_markup_characters():
    assert paragraph_text("<script>A&B</script>\nC") == "&lt;script&gt;A&amp;B&lt;/script&gt;<br/>C"


def test_format_date_br_uses_brazilian_order():
    assert format_date_br("2026-09-22") == "22/09/2026"


def test_format_datetime_br_removes_iso_technical_format():
    assert format_datetime_br("2026-09-22T08:45:00-04:00") == "22/09/2026 às 08:45"
    assert format_datetime_br(None) == "—"
