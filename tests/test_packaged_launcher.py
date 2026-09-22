from pathlib import Path
import importlib
import sys


def test_app_script_path_uses_pyinstaller_bundle_directory(monkeypatch, tmp_path):
    bundled = tmp_path / "bundle"
    bundled.mkdir()
    (bundled / "app.py").write_text("# test", encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled), raising=False)

    launcher = importlib.import_module("launcher")
    assert launcher.app_script_path() == bundled / "app.py"


def test_prepare_runtime_import_path_adds_bundle_root(monkeypatch, tmp_path):
    bundled = tmp_path / "bundle"
    bundled.mkdir()
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled), raising=False)
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != str(bundled)])

    launcher = importlib.reload(importlib.import_module("launcher"))
    root = launcher.prepare_runtime_import_path()

    assert root == bundled
    assert sys.path[0] == str(bundled)
