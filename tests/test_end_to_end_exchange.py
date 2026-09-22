from datetime import date, time

import pytest

from boletim_coc.attachments import list_attachments, save_attachment
from boletim_coc.config import AppPaths
from boletim_coc.db import connect_db, initialize_database
from boletim_coc.models import BoletimDraft
from boletim_coc.package_export import export_zip
from boletim_coc.package_import import import_package
from boletim_coc.repository import (
    create_boletim,
    finalize_boletim,
    list_my_records,
    list_received,
    update_draft,
)


def paths(root):
    for name in ["anexos", "recebidos", "exportados", "logs"]:
        (root / name).mkdir(parents=True, exist_ok=True)
    return AppPaths(
        root, root / "boletins.db", root / "anexos",
        root / "recebidos", root / "exportados", root / "logs",
    )


def test_exchange_between_two_local_profiles(tmp_path):
    maria_paths = paths(tmp_path / "maria")
    joao_paths = paths(tmp_path / "joao")
    maria = connect_db(maria_paths); initialize_database(maria)
    joao = connect_db(joao_paths); initialize_database(joao)

    row = create_boletim(
        maria,
        BoletimDraft(
            date(2026, 9, 22), time(9, 15), "Hospital COC", "Centro cirúrgico",
            "Segurança", "Teste de troca", "Ocorrência de teste.",
        ),
        "MARIA",
    )
    save_attachment(
        maria, maria_paths, row["id"], "evidencia.jpg", b"imagem",
        "image/jpeg",
    )
    attachments = list_attachments(maria, row["id"])
    final = finalize_boletim(maria, row["id"], attachments)
    package = export_zip(maria_paths, final, attachments)

    received = import_package(joao, joao_paths, package, "JOAO")

    assert len(list_my_records(maria, "MARIA")) == 1
    assert len(list_my_records(joao, "JOAO")) == 0
    assert len(list_received(joao, "JOAO")) == 1
    assert received["autor_original"] == "MARIA"

    with pytest.raises(PermissionError):
        update_draft(joao, received["id"], {"titulo": "Não pode"})


def test_import_allows_same_human_code_from_another_computer(tmp_path):
    maria_paths = paths(tmp_path / "maria-collision")
    joao_paths = paths(tmp_path / "joao-collision")
    maria = connect_db(maria_paths); initialize_database(maria)
    joao = connect_db(joao_paths); initialize_database(joao)

    maria_row = create_boletim(
        maria,
        BoletimDraft(
            date(2026, 9, 22), time(9, 15), "Hospital A", "Centro",
            "Segurança", "Registro Maria", "Teste.",
        ),
        "MARIA",
    )
    maria_final = finalize_boletim(maria, maria_row["id"], [])
    package = export_zip(maria_paths, maria_final, [])

    joao_local = create_boletim(
        joao,
        BoletimDraft(
            date(2026, 9, 22), time(10, 0), "Hospital B", "Centro",
            "Segurança", "Registro João", "Teste.",
        ),
        "JOAO",
    )
    assert maria_final["codigo"] == joao_local["codigo"] == "COC-2026-000001"

    received = import_package(joao, joao_paths, package, "JOAO")
    assert received["id"] == maria_final["id"]
    assert len(list_received(joao, "JOAO")) == 1


def test_exchange_supports_duplicate_original_attachment_names(tmp_path):
    maria_paths = paths(tmp_path / "maria-dup")
    joao_paths = paths(tmp_path / "joao-dup")
    maria = connect_db(maria_paths); initialize_database(maria)
    joao = connect_db(joao_paths); initialize_database(joao)

    row = create_boletim(
        maria,
        BoletimDraft(
            date(2026, 9, 22), time(11, 0), "Hospital", "Centro",
            "Segurança", "Anexos duplicados", "Teste.",
        ),
        "MARIA",
    )
    save_attachment(maria, maria_paths, row["id"], "foto.jpg", b"primeira", "image/jpeg")
    save_attachment(maria, maria_paths, row["id"], "foto.jpg", b"segunda", "image/jpeg")
    attachments = list_attachments(maria, row["id"])
    final = finalize_boletim(maria, row["id"], attachments)
    package = export_zip(maria_paths, final, attachments)

    received = import_package(joao, joao_paths, package, "JOAO")
    imported = list_attachments(joao, received["id"])
    assert len(imported) == 2
    assert [item["nome_original"] for item in imported] == ["foto.jpg", "foto.jpg"]
    assert {item["sha256"] for item in imported} == {item["sha256"] for item in attachments}
