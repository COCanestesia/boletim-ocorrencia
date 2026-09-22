import json
import zipfile

import pytest

from boletim_coc.package_export import export_zip
from boletim_coc.config import AppPaths


def make_paths(root):
    for name in ["anexos", "recebidos", "exportados", "logs"]:
        (root / name).mkdir()
    return AppPaths(
        root, root / "boletins.db", root / "anexos",
        root / "recebidos", root / "exportados", root / "logs",
    )


def fake_row(code="COC-2026-000001"):
    return {
        "id": "bulletin", "codigo": code, "origem": "local",
        "windows_user": "MARIA", "autor_original": "MARIA",
        "data_ocorrencia": "2026-09-22", "hora_ocorrencia": "08:30",
        "local": "Hospital", "setor": "Centro", "tipo_ocorrencia": "Segurança",
        "titulo": "Título", "descricao": "Descrição", "consequencias": "",
        "pessoas_envolvidas": "", "acoes_imediatas": "", "acoes_preventivas": "",
        "status": "finalizado", "criado_em": "2026-09-22T08:40:00-04:00",
        "atualizado_em": "2026-09-22T08:45:00-04:00",
        "finalizado_em": "2026-09-22T08:45:00-04:00",
        "hash_conteudo": "a" * 64,
    }


def test_export_zip_contains_pdf_manifest_and_attachments(tmp_path):
    paths = make_paths(tmp_path)
    attachment_file = tmp_path / "anexos" / "bulletin" / "x.jpg"
    attachment_file.parent.mkdir(parents=True)
    attachment_file.write_bytes(b"abc")

    att = {
        "nome_original": "foto.jpg", "mime_type": "image/jpeg", "tamanho_bytes": 3,
        "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        "caminho_relativo": "anexos/bulletin/x.jpg",
    }
    target = export_zip(paths, fake_row(), [att])
    with zipfile.ZipFile(target) as zf:
        names = set(zf.namelist())
        assert {"boletim.pdf", "boletim.json", "anexos/foto.jpg"} <= names
        manifest = json.loads(zf.read("boletim.json"))
        assert manifest["format_version"] == 1
        assert manifest["boletim"]["id"] == "bulletin"
        assert manifest["boletim"]["hash_conteudo"] == "a" * 64


def test_export_zip_does_not_leave_partial_file_on_hash_failure(tmp_path):
    paths = make_paths(tmp_path)
    p = tmp_path / "anexos" / "bulletin" / "x.jpg"
    p.parent.mkdir(parents=True); p.write_bytes(b"abc")
    att = {
        "nome_original": "foto.jpg", "mime_type": "image/jpeg", "tamanho_bytes": 3,
        "sha256": "0" * 64, "caminho_relativo": "anexos/bulletin/x.jpg",
    }
    with pytest.raises(ValueError, match="Integridade"):
        export_zip(paths, fake_row("COC-2026-000002"), [att])
    assert not any(paths.exports.glob("*.part"))


def test_manifest_package_names_stay_unique_when_numbered_name_already_exists():
    from boletim_coc.package_export import build_manifest

    row = fake_row()
    attachments = [
        {"nome_original": "foto (2).jpg", "mime_type": "image/jpeg", "tamanho_bytes": 1, "sha256": "1" * 64},
        {"nome_original": "foto.jpg", "mime_type": "image/jpeg", "tamanho_bytes": 1, "sha256": "2" * 64},
        {"nome_original": "foto.jpg", "mime_type": "image/jpeg", "tamanho_bytes": 1, "sha256": "3" * 64},
    ]
    names = [item["arquivo_pacote"] for item in build_manifest(row, attachments)["boletim"]["anexos"]]
    assert len({name.casefold() for name in names}) == len(names)
