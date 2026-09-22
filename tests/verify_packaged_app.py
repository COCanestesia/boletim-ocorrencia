from __future__ import annotations

from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("uso: verify_packaged_app.py <appsrc>")

    appsrc = Path(sys.argv[1]).resolve()
    app_file = appsrc / "app.py"
    package_dir = appsrc / "boletim_coc"
    required = [
        app_file,
        package_dir / "__init__.py",
        package_dir / "config.py",
        package_dir / "db.py",
        package_dir / "identity.py",
        package_dir / "theme.py",
        package_dir / "views" / "new_record.py",
        package_dir / "views" / "my_records.py",
        package_dir / "views" / "received.py",
        package_dir / "views" / "detail.py",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise AssertionError("Arquivos físicos ausentes no pacote:\n" + "\n".join(missing))

    appsrc_text = str(appsrc)
    if appsrc_text in sys.path:
        sys.path.remove(appsrc_text)
    sys.path.insert(0, appsrc_text)

    for name in list(sys.modules):
        if name == "boletim_coc" or name.startswith("boletim_coc."):
            del sys.modules[name]

    import boletim_coc.config as config

    config_path = Path(config.__file__).resolve()
    expected_config = (package_dir / "config.py").resolve()
    if config_path != expected_config:
        raise AssertionError(
            f"boletim_coc.config veio de {config_path}, esperado {expected_config}"
        )

    app_test = AppTest.from_file(str(app_file), default_timeout=30)
    app_test.run()
    if app_test.exception:
        details = "\n".join(str(item) for item in app_test.exception)
        raise AssertionError(f"Streamlit executou app.py com exceção:\n{details}")

    print(f"OK: app físico executado pelo Streamlit em {app_file}")
    print(f"OK: boletim_coc.config carregado de {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
