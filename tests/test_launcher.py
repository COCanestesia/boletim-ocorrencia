from pathlib import Path


def test_windows_launcher_accepts_any_supported_python3_and_opens_browser():
    source = Path("run_coc.bat").read_text(encoding="utf-8")
    assert "py -3 -m venv .venv" in source
    assert "py -3.12 -m venv .venv" not in source
    assert "--server.headless true" not in source
    assert "python -m streamlit run app.py" in source
