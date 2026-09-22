from datetime import datetime, timezone
import hashlib
from pathlib import Path, PurePath
import re
import sqlite3
import uuid

from boletim_coc.config import ALLOWED_EXTENSIONS, MAX_ATTACHMENT_BYTES, AppPaths
from boletim_coc.repository import get_boletim


INVALID_WIN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str) -> str:
    base = PurePath(str(name).replace("\\", "/")).name.strip()
    base = INVALID_WIN_CHARS.sub("_", base).rstrip(". ")
    if not base:
        base = "arquivo"
    return base[:180]


def list_attachments(conn: sqlite3.Connection, boletim_id: str):
    return list(
        conn.execute(
            "select * from anexos where boletim_id=? order by criado_em, nome_original",
            (boletim_id,),
        ).fetchall()
    )


def save_attachment(conn, paths: AppPaths, boletim_id: str, original_name: str, content: bytes, mime_type: str):
    boletim = get_boletim(conn, boletim_id)
    if boletim is None:
        raise KeyError("Boletim não encontrado.")
    if boletim["origem"] == "recebido" or boletim["status"] == "finalizado":
        raise PermissionError("Não é permitido alterar anexos deste boletim.")

    safe = sanitize_filename(original_name)
    suffix = Path(safe).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Extensão de arquivo não permitida.")
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise ValueError("Arquivo excede o tamanho máximo permitido.")

    attachment_id = str(uuid.uuid4())
    stored_name = attachment_id + suffix
    folder = paths.attachments / boletim_id
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / stored_name
    target.write_bytes(content)
    sha = hashlib.sha256(content).hexdigest()
    stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    relative = target.relative_to(paths.root).as_posix()

    conn.execute(
        """
        insert into anexos(
            id,boletim_id,nome_original,nome_armazenado,caminho_relativo,
            mime_type,tamanho_bytes,sha256,criado_em
        ) values(?,?,?,?,?,?,?,?,?)
        """,
        (
            attachment_id, boletim_id, original_name, stored_name, relative,
            mime_type or "application/octet-stream", len(content), sha, stamp,
        ),
    )
    conn.commit()
    return conn.execute("select * from anexos where id=?", (attachment_id,)).fetchone()


def resolve_attachment_path(paths: AppPaths, row) -> Path:
    candidate = (paths.root / row["caminho_relativo"]).resolve()
    root = paths.root.resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError("Caminho de anexo inválido.")
    return candidate
