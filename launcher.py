from __future__ import annotations

import os
from pathlib import Path
import sys


def app_script_path() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "app.py"


def streamlit_args(app_path: Path) -> list[str]:
    return [
        "streamlit",
        "run",
        str(app_path),
        "--server.address=127.0.0.1",
        "--server.headless=false",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]


def main() -> int:
    app_path = app_script_path()
    if not app_path.is_file():
        raise FileNotFoundError(f"Arquivo principal não encontrado: {app_path}")

    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.argv = streamlit_args(app_path)

    from streamlit.web import cli as stcli

    return int(stcli.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
