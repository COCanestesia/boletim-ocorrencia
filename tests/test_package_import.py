import json
from pathlib import Path
import zipfile

import pytest

from boletim_coc.config import AppPaths
from boletim_coc.db import connect_db, initialize_database
from boletim_coc.package_import import import_package, validate_member_name
from boletim_coc.pdf_export import content_hash


def paths(tmp_path):
    for name in ["anexos", "recebidos", "exportados", "logs"]:
        (tmp_path / name).mkdir()
    return AppPaths(
        tmp_path, tmp_path / "boletins.db", tmp_path / "anexos",
        tmp_path / "recebidos", tmp_path / "exportados", tmp_path / "logs",
    )


def manifest():
    b = {
        "id": "11111111-1111-1111-1111-111111111111",
        "codigo": "COC-2026-000001",
        "autor_original": "MARIA",
        "data_ocorrencia": "2026-09-22",
        "hora_ocorrencia": "08:30",
        "local": "Hospital",
        "setor": "Centro",
        "tipo_ocorrencia": "Segurança",
        "titulo": "Título",
        "descricao": "Descrição",
        "consequencias": "",
        "pessoas_envolvidas": "",
        "acoes_imediatas": "",
        "acoes_preventivas": "",
        "status": "finalizado",
        "criado_em": "2026-09-22T08:40:00-04:00",
        "finalizado_em": "2026-09-22T08:45:00-04:00",
        "anexos": [],
    }
    b["hash_conteudo"] = content_hash(b, [])
    return {
        "format_version": 1,
        "exported_at": "2026-09-22T09:00:00-04:00",
        "boletim": b,
    }


def make_zip(path, data=None):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("boletim.json", json.dumps(data or manifest()))
        zf.writestr("boletim.pdf", b"%PDF-1.4 fake")
    return path


def test_validate_member_name_rejects_path_traversal():
    for bad in ["../evil.txt", "/absolute.txt", "C:/evil.txt", "anexos/../../evil.txt"]:
        with pytest.raises(ValueError, match="Caminho"):
            validate_member_name(bad)


def test_import_package_creates_received_readonly_record(tmp_path):
    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    row = import_package(conn, p, make_zip(tmp_path / "one.zip"), "JOAO")
    assert row["origem"] == "recebido"
    assert row["windows_user"] == "JOAO"
    assert row["autor_original"] == "MARIA"
    assert row["status"] == "finalizado"


def test_import_package_rejects_duplicate_bulletin(tmp_path):
    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    source = make_zip(tmp_path / "one.zip")
    import_package(conn, p, source, "JOAO")
    with pytest.raises(ValueError, match="já foi importado"):
        import_package(conn, p, source, "JOAO")


def test_import_package_rejects_wrong_format_version(tmp_path):
    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    data = manifest(); data["format_version"] = 99
    with pytest.raises(ValueError, match="versão"):
        import_package(conn, p, make_zip(tmp_path / "bad.zip", data), "JOAO")


def test_import_same_bytes_under_new_filename_is_duplicate(tmp_path):
    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    first = make_zip(tmp_path / "first.zip")
    second = tmp_path / "renamed.zip"
    second.write_bytes(first.read_bytes())
    import_package(conn, p, first, "JOAO")
    with pytest.raises(ValueError, match="já foi importado"):
        import_package(conn, p, second, "JOAO")


def manifest_with_attachment(raw=b"abc", name="foto.jpg"):
    import hashlib

    data = manifest()
    b = data["boletim"]
    item = {
        "nome_original": name,
        "arquivo_pacote": name,
        "mime_type": "image/jpeg",
        "tamanho_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    b["anexos"] = [item]
    b["hash_conteudo"] = content_hash(b, [item])
    return data


def test_import_package_rejects_oversized_attachment(tmp_path, monkeypatch):
    import boletim_coc.package_import as package_import

    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    raw = b"abc"
    data = manifest_with_attachment(raw)
    source = tmp_path / "oversize.zip"
    with zipfile.ZipFile(source, "w") as zf:
        zf.writestr("boletim.json", json.dumps(data))
        zf.writestr("boletim.pdf", b"%PDF-1.4 fake")
        zf.writestr("anexos/foto.jpg", raw)
    monkeypatch.setattr(package_import, "MAX_ATTACHMENT_BYTES", 2, raising=False)
    with pytest.raises(ValueError, match="tamanho máximo"):
        import_package(conn, p, source, "JOAO")


def test_import_package_rejects_duplicate_zip_members(tmp_path):
    p = paths(tmp_path)
    conn = connect_db(p); initialize_database(conn)
    source = tmp_path / "duplicate-member.zip"
    payload = json.dumps(manifest())
    with pytest.warns(UserWarning, match="Duplicate name"):
        with zipfile.ZipFile(source, "w") as zf:
            zf.writestr("boletim.json", payload)
            zf.writestr("boletim.json", payload)
            zf.writestr("boletim.pdf", b"%PDF-1.4 fake")
    with pytest.raises(ValueError, match="duplicad"):
        import_package(conn, p, source, "JOAO")
