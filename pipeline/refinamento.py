from __future__ import annotations

from pathlib import Path

from .db import conectar, criar_schema


_SQL_PATH = Path(__file__).resolve().parent / "sql" / "refined" / "salarios.sql"


def refinar_salarios(caminho_banco: str | Path | None = None) -> int:
    """Cria a tabela silver refined.salarios a partir de raw.salarios."""
    conexao = (
        conectar(caminho_banco)
        if caminho_banco is not None
        else conectar()
    )
    try:
        criar_schema(conexao)
        conexao.execute(_SQL_PATH.read_text(encoding="utf-8"))
        return conexao.execute(
            "SELECT COUNT(*) FROM refined.salarios"
        ).fetchone()[0]
    finally:
        conexao.close()
