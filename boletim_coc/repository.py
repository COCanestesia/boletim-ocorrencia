from datetime import datetime, timezone
import sqlite3
import uuid

from boletim_coc.models import BoletimDraft


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def next_codigo(conn: sqlite3.Connection, year: int) -> str:
    prefix = f"COC-{year}-"
    row = conn.execute(
        "select codigo from boletins where origem='local' and codigo like ? order by codigo desc limit 1",
        (prefix + "%",),
    ).fetchone()
    seq = int(row["codigo"].split("-")[-1]) + 1 if row else 1
    return f"{prefix}{seq:06d}"


def get_boletim(conn: sqlite3.Connection, boletim_id: str):
    return conn.execute("select * from boletins where id=?", (boletim_id,)).fetchone()


def create_boletim(conn: sqlite3.Connection, draft: BoletimDraft, windows_user: str):
    draft.validate()
    record_id = str(uuid.uuid4())
    stamp = now_iso()
    codigo = next_codigo(conn, draft.data_ocorrencia.year)
    conn.execute(
        """
        insert into boletins(
            id,codigo,origem,windows_user,autor_original,
            data_ocorrencia,hora_ocorrencia,local,setor,tipo_ocorrencia,
            titulo,descricao,consequencias,pessoas_envolvidas,
            acoes_imediatas,acoes_preventivas,status,criado_em,atualizado_em
        ) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            record_id, codigo, "local", windows_user, windows_user,
            draft.data_ocorrencia.isoformat(),
            draft.hora_ocorrencia.strftime("%H:%M"),
            draft.local.strip(), draft.setor.strip(), draft.tipo_ocorrencia.strip(),
            draft.titulo.strip(), draft.descricao.strip(), draft.consequencias.strip(),
            draft.pessoas_envolvidas.strip(), draft.acoes_imediatas.strip(),
            draft.acoes_preventivas.strip(), "rascunho", stamp, stamp,
        ),
    )
    conn.commit()
    return get_boletim(conn, record_id)


def list_my_records(conn, windows_user: str, query="", status=None, tipo=None):
    sql = "select * from boletins where origem='local' and windows_user=?"
    args = [windows_user]
    if query:
        sql += " and (titulo like ? or descricao like ? or codigo like ? or local like ?)"
        like = f"%{query.strip()}%"
        args += [like, like, like, like]
    if status:
        sql += " and status=?"
        args.append(status)
    if tipo:
        sql += " and tipo_ocorrencia=?"
        args.append(tipo)
    sql += " order by criado_em desc"
    return list(conn.execute(sql, args).fetchall())


def _assert_editable(row) -> None:
    if row is None:
        raise KeyError("Boletim não encontrado.")
    if row["origem"] == "recebido":
        raise PermissionError("Boletim recebido é somente leitura.")
    if row["status"] == "finalizado":
        raise PermissionError("Boletim finalizado não pode ser editado.")


def update_draft(conn, boletim_id: str, changes: dict):
    row = get_boletim(conn, boletim_id)
    _assert_editable(row)
    allowed = {
        "data_ocorrencia", "hora_ocorrencia", "local", "setor", "tipo_ocorrencia",
        "titulo", "descricao", "consequencias", "pessoas_envolvidas",
        "acoes_imediatas", "acoes_preventivas",
    }
    clean = {k: v for k, v in changes.items() if k in allowed}
    if not clean:
        return row
    setters = ", ".join(f"{k}=?" for k in clean)
    values = list(clean.values()) + [now_iso(), boletim_id]
    conn.execute(
        f"update boletins set {setters}, atualizado_em=? where id=?",
        values,
    )
    conn.commit()
    return get_boletim(conn, boletim_id)


def finalize_boletim(conn, boletim_id: str, attachments=()):
    from boletim_coc.pdf_export import content_hash

    row = get_boletim(conn, boletim_id)
    _assert_editable(row)
    stamp = now_iso()
    digest = content_hash(
        {**dict(row), "status": "finalizado", "finalizado_em": stamp},
        attachments,
    )
    conn.execute(
        """
        update boletins
        set status='finalizado', finalizado_em=?, atualizado_em=?, hash_conteudo=?
        where id=?
        """,
        (stamp, stamp, digest, boletim_id),
    )
    conn.commit()
    return get_boletim(conn, boletim_id)


def list_received(conn, windows_user: str):
    return list(
        conn.execute(
            """
            select * from boletins
            where origem='recebido' and windows_user=?
            order by criado_em desc
            """,
            (windows_user,),
        ).fetchall()
    )
