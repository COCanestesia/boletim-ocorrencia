import sqlite3

from boletim_coc.config import AppPaths

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS boletins (
    id TEXT PRIMARY KEY,
    codigo TEXT NOT NULL,
    origem TEXT NOT NULL CHECK(origem IN ('local','recebido')),
    windows_user TEXT NOT NULL,
    autor_original TEXT NOT NULL,
    data_ocorrencia TEXT NOT NULL,
    hora_ocorrencia TEXT NOT NULL,
    local TEXT NOT NULL,
    setor TEXT NOT NULL,
    tipo_ocorrencia TEXT NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    consequencias TEXT NOT NULL DEFAULT '',
    pessoas_envolvidas TEXT NOT NULL DEFAULT '',
    acoes_imediatas TEXT NOT NULL DEFAULT '',
    acoes_preventivas TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('rascunho','finalizado')),
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    finalizado_em TEXT,
    hash_conteudo TEXT
);

CREATE INDEX IF NOT EXISTS idx_boletins_owner
ON boletins(origem, windows_user, criado_em DESC);

CREATE TABLE IF NOT EXISTS anexos (
    id TEXT PRIMARY KEY,
    boletim_id TEXT NOT NULL REFERENCES boletins(id) ON DELETE CASCADE,
    nome_original TEXT NOT NULL,
    nome_armazenado TEXT NOT NULL,
    caminho_relativo TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    tamanho_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS importacoes (
    id TEXT PRIMARY KEY,
    boletim_id TEXT NOT NULL UNIQUE REFERENCES boletins(id) ON DELETE CASCADE,
    arquivo_origem TEXT NOT NULL,
    importado_em TEXT NOT NULL,
    hash_pacote TEXT NOT NULL UNIQUE
);
"""


def connect_db(paths: AppPaths) -> sqlite3.Connection:
    paths.root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(paths.database, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
