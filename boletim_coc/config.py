from dataclasses import dataclass
import os
from pathlib import Path

MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".xlsx"}


@dataclass(frozen=True)
class AppPaths:
    root: Path
    database: Path
    attachments: Path
    received: Path
    exports: Path
    logs: Path


def resolve_paths() -> AppPaths:
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    root = base / "COC" / "BoletimOcorrencia"
    paths = AppPaths(
        root=root,
        database=root / "boletins.db",
        attachments=root / "anexos",
        received=root / "recebidos",
        exports=root / "exportados",
        logs=root / "logs",
    )
    for folder in [paths.root, paths.attachments, paths.received, paths.exports, paths.logs]:
        folder.mkdir(parents=True, exist_ok=True)
    return paths
