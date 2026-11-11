from __future__ import annotations

import re
import uuid
from pathlib import Path

import duckdb
import pandas as pd


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DATABASE_PATH = _PROJECT_ROOT / "salarios.duckdb"
_SCHEMAS = ("raw", "refined", "marts")


def conectar(caminho: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Abre uma conexão com o banco DuckDB do projeto."""
    return duckdb.connect(str(caminho or _DATABASE_PATH))


def criar_schema(conexao: duckdb.DuckDBPyConnection) -> None:
    """Cria os schemas usados pelas etapas do pipeline."""
    for schema in _SCHEMAS:
        conexao.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')


def gravar(
    dados: pd.DataFrame,
    tabela: str,
    schema: str = "raw",
    conexao: duckdb.DuckDBPyConnection | None = None,
) -> None:
    """Substitui a tabela indicada pelo conteúdo do DataFrame."""
    for identificador in (schema, tabela):
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identificador) is None:
            raise ValueError(f"Identificador SQL inválido: {identificador!r}")

    conexao_propria = conexao is None
    if conexao is None:
        conexao = conectar()
    nome_temporario = f"_dados_{uuid.uuid4().hex}"

    try:
        conexao.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        conexao.register(nome_temporario, dados)
        try:
            conexao.execute(
                f'CREATE OR REPLACE TABLE "{schema}"."{tabela}" '
                f"AS SELECT * FROM {nome_temporario}"
            )
        finally:
            conexao.unregister(nome_temporario)
    finally:
        if conexao_propria:
            conexao.close()
