from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

from boletim_coc.attachments import resolve_attachment_path, sanitize_filename
from boletim_coc.pdf_export import canonical_payload, render_pdf


def _package_names(attachments):
    taken = set()
    result = []
    for att in attachments:
        safe = sanitize_filename(att["nome_original"])
        path = Path(safe)
        candidate = safe
        counter = 2
        while candidate.casefold() in taken:
            candidate = f"{path.stem} ({counter}){path.suffix}"
            counter += 1
        taken.add(candidate.casefold())
        result.append(candidate)
    return result


def build_manifest(row, attachments):
    payload = canonical_payload(row, attachments)
    for item, package_name in zip(payload["anexos"], _package_names(attachments)):
        item["arquivo_pacote"] = package_name
    return {
        "format_version": 1,
        "exported_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "boletim": {
            **payload,
            "hash_conteudo": row["hash_conteudo"],
        },
    }


def export_pdf_file(paths, row, attachments) -> Path:
    if row["status"] != "finalizado":
        raise ValueError("Finalize o boletim antes de exportar.")
    paths.exports.mkdir(parents=True, exist_ok=True)
    target = paths.exports / f'{row["codigo"]}.pdf'
    target.write_bytes(render_pdf(row, attachments))
    return target


def export_zip(paths, row, attachments) -> Path:
    if row["status"] != "finalizado":
        raise ValueError("Finalize o boletim antes de exportar.")
    paths.exports.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(row, attachments)
    target = paths.exports / f'{row["codigo"]}.zip'
    temp = target.with_suffix(".zip.part")
    try:
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("boletim.pdf", render_pdf(row, attachments))
            zf.writestr(
                "boletim.json",
                json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            )
            for att, manifest_att in zip(attachments, manifest["boletim"]["anexos"]):
                source = resolve_attachment_path(paths, att)
                raw = source.read_bytes()
                if hashlib.sha256(raw).hexdigest() != att["sha256"]:
                    raise ValueError(f'Integridade inválida no anexo {att["nome_original"]}.')
                zf.writestr(f'anexos/{manifest_att["arquivo_pacote"]}', raw)
        temp.replace(target)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    return target
