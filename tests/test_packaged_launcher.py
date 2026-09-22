from pathlib import Path

from launcher import LOCAL_URL, streamlit_args


def test_packaged_launcher_disables_first_run_prompt_and_fixes_local_port():
    args = streamlit_args(Path("app.py"))

    assert "--server.address=127.0.0.1" in args
    assert "--server.port=8765" in args
    assert "--server.showEmailPrompt=false" in args
    assert "--server.headless=true" in args
    assert "--browser.gatherUsageStats=false" in args
    assert LOCAL_URL == "http://127.0.0.1:8765"
