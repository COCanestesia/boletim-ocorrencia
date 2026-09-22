from __future__ import annotations

import os
from pathlib import Path
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser


LOCAL_PORT = 8765
LOCAL_URL = f"http://127.0.0.1:{LOCAL_PORT}"


def app_script_path() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "app.py"


def streamlit_args(app_path: Path) -> list[str]:
    return [
        "streamlit",
        "run",
        str(app_path),
        "--server.address=127.0.0.1",
        f"--server.port={LOCAL_PORT}",
        "--server.headless=true",
        "--server.showEmailPrompt=false",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]


def open_browser_when_ready(timeout_seconds: float = 45.0) -> None:
    health_url = f"{LOCAL_URL}/_stcore/health"
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=1.0) as response:
                if response.status == 200:
                    webbrowser.open(LOCAL_URL, new=1)
                    return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.25)


def main() -> int:
    app_path = app_script_path()
    if not app_path.is_file():
        raise FileNotFoundError(f"Arquivo principal não encontrado: {app_path}")

    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_SHOW_EMAIL_PROMPT", "false")
    os.environ.setdefault("PYTHONUTF8", "1")

    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    sys.argv = streamlit_args(app_path)

    from streamlit.web import cli as stcli

    return int(stcli.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
