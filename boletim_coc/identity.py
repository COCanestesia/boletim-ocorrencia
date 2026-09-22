import getpass


def current_windows_user() -> str:
    value = str(getpass.getuser() or "").strip()
    if not value:
        raise RuntimeError("Não foi possível identificar o usuário do Windows.")
    return value
