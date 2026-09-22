from boletim_coc.config import resolve_paths
from boletim_coc.identity import current_windows_user


def test_resolve_paths_uses_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    paths = resolve_paths()
    assert paths.root == tmp_path / "COC" / "BoletimOcorrencia"
    assert paths.database == paths.root / "boletins.db"
    assert paths.attachments == paths.root / "anexos"
    assert paths.received == paths.root / "recebidos"
    assert paths.exports == paths.root / "exportados"
    assert paths.logs == paths.root / "logs"


def test_resolve_paths_creates_directories(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    paths = resolve_paths()
    for folder in [paths.root, paths.attachments, paths.received, paths.exports, paths.logs]:
        assert folder.is_dir()


def test_current_windows_user_returns_nonempty(monkeypatch):
    monkeypatch.setattr("getpass.getuser", lambda: "MARIA.COC")
    assert current_windows_user() == "MARIA.COC"
