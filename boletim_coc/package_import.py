from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import uuid
import zipfile

from boletim_coc.config import ALLOWED_EXTENSIONS, MAX_ATTACHMENT_BYTES, AppPaths
from boletim_coc.pdf_export import content_hash
from boletim_coc.repository import get_boletim


def validate_member_name(name: str) -> None:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("Caminho inválido dentro do ZIP.")
    if len(p.parts) and ":" in p.parts[0]:
        raise ValueError("Caminho absoluto do Windows não é permitido.")


def _package_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def import_package(conn: sqlite3.Connection, paths: AppPaths, zip_path: Path, windows_user: str):
    zip_path = Path(zip_path)
    package_hash = _package_sha(zip_path)

    if conn.execute("select 1 from importacoes where hash_pacote=?", (package_hash,)).fetchone():
        raise ValueError("Este pacote já foi importado.")

    temp_root = paths.received / (".import-" + str(uuid.uuid4()))
    temp_root.mkdir(parents=True, exist_ok=True)
    b = {}
    try:
        with zipfile.ZipFile(zip_path) as zf:
            members = zf.namelist()
            for info in zf.infolist():
                validate_member_name(info.filename)
            if len(members) != len(set(members)):
                raise ValueError("Pacote inválido: existem membros duplicados no ZIP.")
            names = set(members)
            if "boletim.json" not in names or "boletim.pdf" not in names:
                raise ValueError("Pacote inválido: faltam boletim.json ou boletim.pdf.")

            manifest = json.loads(zf.read("boletim.json"))
            if manifest.get("format_version") != 1:
                raise ValueError("versão de pacote não suportada.")
            b = manifest.get("boletim") or {}
            bulletin_id = str(b.get("id") or "")
            if not bulletin_id or not b.get("codigo"):
                raise ValueError("Manifesto do boletim está incompleto.")
            if get_boletim(conn, bulletin_id):
                raise ValueError("Este boletim já foi importado.")

            target_dir = paths.received / bulletin_id
            if target_dir.exists():
                raise ValueError("Diretório do boletim recebido já existe.")

            attachment_rows = []
            for item in b.get("anexos", []):
                name = Path(str(item["nome_original"]).replace("\\", "/")).name
                ext = Path(name).suffix.lower()
                if ext not in ALLOWED_EXTENSIONS:
                    raise ValueError(f"Extensão de anexo não permitida: {ext}")
                package_name = str(item.get("arquivo_pacote") or name)
                member = f"anexos/{package_name}"
                validate_member_name(member)
                if member not in names:
                    raise ValueError(f"Anexo ausente no pacote: {name}")
                if zf.getinfo(member).file_size > MAX_ATTACHMENT_BYTES:
                    raise ValueError(f"Anexo excede o tamanho máximo permitido: {name}")
                raw = zf.read(member)
                actual = hashlib.sha256(raw).hexdigest()
                if actual != item["sha256"]:
                    raise ValueError(f"Hash inválido para o anexo: {name}")
                if len(raw) != int(item["tamanho_bytes"]):
                    raise ValueError(f"Tamanho inválido para o anexo: {name}")
                stored = str(uuid.uuid4()) + ext
                (temp_root / stored).write_bytes(raw)
                attachment_rows.append((item, stored, raw))

            actual_content_hash = content_hash(
                {
                    **b,
                    "windows_user": windows_user,
                    "origem": "recebido",
                    "atualizado_em": b.get("finalizado_em") or b.get("criado_em"),
                    "hash_conteudo": b.get("hash_conteudo"),
                },
                [
                    {
                        "nome_original": item["nome_original"],
                        "mime_type": item["mime_type"],
                        "tamanho_bytes": item["tamanho_bytes"],
                        "sha256": item["sha256"],
                    }
                    for item, _, _ in attachment_rows
                ],
            )
            if actual_content_hash != b.get("hash_conteudo"):
                raise ValueError("Integridade do boletim inválida.")

            target_dir.mkdir(parents=True)
            for item, stored, raw in attachment_rows:
                shutil.move(str(temp_root / stored), target_dir / stored)

            stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
            with conn:
                conn.execute(
                    """
                    insert into boletins(
                        id,codigo,origem,windows_user,autor_original,
                        data_ocorrencia,hora_ocorrencia,local,setor,tipo_ocorrencia,
                        titulo,descricao,consequencias,pessoas_envolvidas,
                        acoes_imediatas,acoes_preventivas,status,criado_em,atualizado_em,
                        finalizado_em,hash_conteudo
                    ) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        bulletin_id, b["codigo"], "recebido", windows_user, b["autor_original"],
                        b["data_ocorrencia"], b["hora_ocorrencia"], b["local"], b["setor"],
                        b["tipo_ocorrencia"], b["titulo"], b["descricao"],
                        b.get("consequencias", ""), b.get("pessoas_envolvidas", ""),
                        b.get("acoes_imediatas", ""), b.get("acoes_preventivas", ""),
                        "finalizado", b["criado_em"], stamp, b.get("finalizado_em"),
                        b["hash_conteudo"],
                    ),
                )
                for item, stored, raw in attachment_rows:
                    att_id = str(uuid.uuid4())
                    relative = (target_dir / stored).relative_to(paths.root).as_posix()
                    conn.execute(
                        """
                        insert into anexos(
                            id,boletim_id,nome_original,nome_armazenado,caminho_relativo,
                            mime_type,tamanho_bytes,sha256,criado_em
                        ) values(?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            att_id, bulletin_id, item["nome_original"], stored, relative,
                            item["mime_type"], item["tamanho_bytes"], item["sha256"], stamp,
                        ),
                    )
                conn.execute(
                    """
                    insert into importacoes(id,boletim_id,arquivo_origem,importado_em,hash_pacote)
                    values(?,?,?,?,?)
                    """,
                    (str(uuid.uuid4()), bulletin_id, zip_path.name, stamp, package_hash),
                )
            return get_boletim(conn, bulletin_id)
    except Exception:
        bulletin_id = str(b.get("id") or "")
        if bulletin_id and not get_boletim(conn, bulletin_id):
            shutil.rmtree(paths.received / bulletin_id, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
