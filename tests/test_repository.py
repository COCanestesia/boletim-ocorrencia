from boletim_coc.config import AppPaths
from boletim_coc.db import connect_db, initialize_database


def make_paths(tmp_path):
    return AppPaths(
        root=tmp_path,
        database=tmp_path / "boletins.db",
        attachments=tmp_path / "anexos",
        received=tmp_path / "recebidos",
        exports=tmp_path / "exportados",
        logs=tmp_path / "logs",
    )


def test_initialize_database_creates_tables(tmp_path):
    paths = make_paths(tmp_path)
    conn = connect_db(paths)
    initialize_database(conn)
    names = {
        row[0]
        for row in conn.execute("select name from sqlite_master where type='table'")
    }
    assert {"boletins", "anexos", "importacoes"} <= names

from datetime import date, time
import pytest

from boletim_coc.models import BoletimDraft
from boletim_coc.repository import (
    create_boletim,
    finalize_boletim,
    list_my_records,
    update_draft,
)


def open_db(tmp_path):
    paths = make_paths(tmp_path)
    conn = connect_db(paths)
    initialize_database(conn)
    return conn


def sample_draft(titulo="Queda no corredor"):
    return BoletimDraft(
        data_ocorrencia=date(2026, 9, 22),
        hora_ocorrencia=time(8, 30),
        local="Hospital COC",
        setor="Centro cirúrgico",
        tipo_ocorrencia="Segurança",
        titulo=titulo,
        descricao="Descrição completa da ocorrência.",
        consequencias="Sem dano.",
        pessoas_envolvidas="Equipe do setor.",
        acoes_imediatas="Área sinalizada.",
        acoes_preventivas="Revisar rotina.",
    )


def test_list_my_records_isolates_windows_user(tmp_path):
    conn = open_db(tmp_path)
    create_boletim(conn, sample_draft("A"), "MARIA")
    create_boletim(conn, sample_draft("B"), "JOAO")
    rows = list_my_records(conn, "MARIA")
    assert [row["titulo"] for row in rows] == ["A"]


def test_create_boletim_uses_explicit_author_name(tmp_path):
    conn = open_db(tmp_path)
    row = create_boletim(
        conn,
        sample_draft(),
        "USUARIO_WINDOWS",
        author_name="Maria Aparecida da Silva",
    )
    assert row["windows_user"] == "USUARIO_WINDOWS"
    assert row["autor_original"] == "Maria Aparecida da Silva"


def test_update_draft_can_change_author_name(tmp_path):
    conn = open_db(tmp_path)
    row = create_boletim(conn, sample_draft(), "MARIA", author_name="Maria A.")
    updated = update_draft(conn, row["id"], {"autor_original": "Maria Aparecida"})
    assert updated["autor_original"] == "Maria Aparecida"


def test_finalized_record_cannot_be_edited(tmp_path):
    conn = open_db(tmp_path)
    row = create_boletim(conn, sample_draft(), "MARIA")
    finalize_boletim(conn, row["id"])
    with pytest.raises(PermissionError, match="finalizado"):
        update_draft(conn, row["id"], {"titulo": "Alterado"})


def test_received_record_cannot_be_edited(tmp_path):
    conn = open_db(tmp_path)
    row = create_boletim(conn, sample_draft(), "MARIA")
    conn.execute("update boletins set origem='recebido' where id=?", (row["id"],))
    conn.commit()
    with pytest.raises(PermissionError, match="recebido"):
        update_draft(conn, row["id"], {"titulo": "Alterado"})


def test_codes_increment_per_year(tmp_path):
    conn = open_db(tmp_path)
    first = create_boletim(conn, sample_draft("A"), "MARIA")
    second = create_boletim(conn, sample_draft("B"), "MARIA")
    assert first["codigo"] == "COC-2026-000001"
    assert second["codigo"] == "COC-2026-000002"


def test_list_my_records_searches_title_and_code(tmp_path):
    conn = open_db(tmp_path)
    create_boletim(conn, sample_draft("Falha no equipamento"), "MARIA")
    create_boletim(conn, sample_draft("Outro registro"), "MARIA")
    assert len(list_my_records(conn, "MARIA", query="equipamento")) == 1
    assert len(list_my_records(conn, "MARIA", query="COC-2026-000001")) == 1


def test_finalize_persists_content_hash(tmp_path):
    conn = open_db(tmp_path)
    row = create_boletim(conn, sample_draft(), "MARIA")
    final = finalize_boletim(conn, row["id"], attachments=[])
    assert final["hash_conteudo"]
    assert len(final["hash_conteudo"]) == 64


def test_received_codes_do_not_advance_local_sequence(tmp_path):
    conn = open_db(tmp_path)
    first = create_boletim(conn, sample_draft("Local A"), "MARIA")
    received_like = create_boletim(conn, sample_draft("Recebido"), "MARIA")
    conn.execute(
        "update boletins set origem='recebido', codigo='COC-2026-999999' where id=?",
        (received_like["id"],),
    )
    conn.commit()
    next_local = create_boletim(conn, sample_draft("Local B"), "MARIA")
    assert first["codigo"] == "COC-2026-000001"
    assert next_local["codigo"] == "COC-2026-000002"
