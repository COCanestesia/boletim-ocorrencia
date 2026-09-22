from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class BoletimDraft:
    data_ocorrencia: date
    hora_ocorrencia: time
    local: str
    setor: str
    tipo_ocorrencia: str
    titulo: str
    descricao: str
    consequencias: str = ""
    pessoas_envolvidas: str = ""
    acoes_imediatas: str = ""
    acoes_preventivas: str = ""

    def validate(self) -> None:
        required = {
            "local": self.local,
            "setor": self.setor,
            "tipo_ocorrencia": self.tipo_ocorrencia,
            "titulo": self.titulo,
            "descricao": self.descricao,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError("Campos obrigatórios: " + ", ".join(missing))
