from pathlib import Path
import importlib
import sys


def test_app_script_path_uses_physical_appsrc_directory(monkeypatch, tmp_path):
    bundled = tmp_path / "bundle"
    appsrc = bundled / "appsrc"
    appsrc.mkdir(parents=True)
    (appsrc / "app.py").write_text("# test", encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled), raising=False)

    launcher = importlib.reload(importlib.import_module("launcher"))
    assert launcher.app_script_path() == appsrc / "app.py"


def test_prepare_runtime_import_path_adds_physical_appsrc_first(monkeypatch, tmp_path):
    bundled = tmp_path / "bundle"
    appsrc = bundled / "appsrc"
    appsrc.mkdir(parents=True)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled), raising=False)
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != str(appsrc)])

    launcher = importlib.reload(importlib.import_module("launcher"))
    root = launcher.prepare_runtime_import_path()

    assert root == appsrc
    assert sys.path[0] == str(appsrc)


def test_verify_runtime_modules_requires_physical_package_when_frozen(monkeypatch, tmp_path):
    bundled = tmp_path / "bundle"
    appsrc = bundled / "appsrc"
    package = appsrc / "boletim_coc"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "config.py").write_text("VALUE = 1\n", encoding="utf-8")

    monkeypatch.setattr(sys, "_MEIPASS", str(bundled), raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != str(appsrc)])
    for name in ["boletim_coc", "boletim_coc.config"]:
        sys.modules.pop(name, None)

    launcher = importlib.reload(importlib.import_module("launcher"))
    launcher.verify_runtime_modules()

    imported = sys.modules["boletim_coc.config"]
    assert Path(imported.__file__).resolve() == (package / "config.py").resolve()
