import pytest

from boletim_coc.attachments import sanitize_filename, save_attachment
from boletim_coc.config import AppPaths
from boletim_coc.db import connect_db, initialize_database
from boletim_coc.models import BoletimDraft
from boletim_coc.repository import create_boletim
from datetime import date, time


def paths(tmp_path):
    for name in ["anexos", "recebidos", "exportados", "logs"]:
        (tmp_path / name).mkdir()
    return AppPaths(
        tmp_path, tmp_path / "boletins.db", tmp_path / "anexos",
        tmp_path / "recebidos", tmp_path / "exportados", tmp_path / "logs",
    )


def draft():
    return BoletimDraft(
        date(2026, 9, 22), time(8, 30), "Hospital", "Centro",
        "Segurança", "Título", "Descrição"
    )


def test_sanitize_filename_removes_path_components():
    assert sanitize_filename(r"..\..\laudo.pdf") == "laudo.pdf"
    assert sanitize_filename("../../foto.jpg") == "foto.jpg"


def test_save_attachment_writes_under_bulletin_directory(tmp_path):
    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    row = create_boletim(conn, draft(), "MARIA")
    att = save_attachment(conn, p, row["id"], "foto.jpg", b"abc", "image/jpeg")
    stored = p.root / att["caminho_relativo"]
    assert stored.is_file()
    assert stored.read_bytes() == b"abc"
    assert row["id"] in stored.parts


def test_save_attachment_rejects_disallowed_extension(tmp_path):
    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    row = create_boletim(conn, draft(), "MARIA")
    with pytest.raises(ValueError, match="Extensão"):
        save_attachment(conn, p, row["id"], "script.exe", b"MZ", "application/octet-stream")


def test_save_attachment_rejects_oversize(tmp_path, monkeypatch):
    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    row = create_boletim(conn, draft(), "MARIA")
    monkeypatch.setattr("boletim_coc.attachments.MAX_ATTACHMENT_BYTES", 2)
    with pytest.raises(ValueError, match="tamanho"):
        save_attachment(conn, p, row["id"], "foto.jpg", b"abc", "image/jpeg")
