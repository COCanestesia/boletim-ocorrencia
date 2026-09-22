from pathlib import Path
import importlib
import sys


def test_launcher_uses_bundled_app_and_local_only_streamlit_args(monkeypatch, tmp_path):
    bundled = tmp_path / "bundle"
    bundled.mkdir()
    (bundled / "app.py").write_text("# app", encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled), raising=False)

    launcher = importlib.import_module("launcher")
    app_path = launcher.app_script_path()
    args = launcher.streamlit_args(app_path)

    assert app_path == bundled / "app.py"
    assert args[:2] == ["streamlit", "run"]
    assert str(app_path) in args
    assert "--server.address=127.0.0.1" in args
    assert "--server.port=8765" in args
    assert "--server.headless=true" in args
    assert "--server.showEmailPrompt=false" in args
    assert "--server.fileWatcherType=none" in args
    assert "--browser.gatherUsageStats=false" in args


def test_pyinstaller_spec_collects_streamlit_and_local_app():
    source = Path("COCBoletim.spec").read_text(encoding="utf-8")
    assert 'collect_all("streamlit")' in source
    assert 'collect_submodules("boletim_coc")' in source
    assert '("app.py", ".")' in source
    assert 'name="COCBoletim"' in source
    assert "console=False" in source


def test_inno_installer_is_per_user_and_preserves_local_data():
    source = Path("installer/boletim_coc.iss").read_text(encoding="utf-8")
    assert "PrivilegesRequired=lowest" in source
    assert r"DefaultDirName={localappdata}\Programs\COC\BoletimOcorrencia" in source
    assert 'Filename: "{app}\\{#MyAppExeName}"' in source
    assert "{autodesktop}" in source
    assert r"COC\\BoletimOcorrencia\\boletins.db" not in source
    assert "UninstallDelete" not in source


def test_windows_build_workflow_builds_and_releases_installer():
    source = Path(".github/workflows/build-windows.yml").read_text(encoding="utf-8")
    assert "windows-latest" in source
    assert "python -m pytest -q" in source
    assert "pyinstaller --noconfirm --clean COCBoletim.spec" in source
    assert "Smoke test packaged application" in source
    assert "127.0.0.1:8765/_stcore/health" in source
    assert "ISCC.exe" in source
    assert "actions/upload-artifact@v4" in source
    assert "softprops/action-gh-release@v2" in source
    assert "VERSION" in source


def test_version_file_is_semver():
    version = Path("VERSION").read_text(encoding="utf-8").strip()
    parts = version.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_readme_has_simple_nursing_installation_flow():
    source = Path("README.md").read_text(encoding="utf-8")
    assert "Instalar_Boletim_COC" in source
    assert "não precisa instalar Python" in source
    assert "%LOCALAPPDATA%\\COC\\BoletimOcorrencia" in source
    assert "assinatura digital" in source
