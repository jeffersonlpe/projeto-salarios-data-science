from __future__ import annotations

from pathlib import Path

from .db import conectar, criar_schema


_SQL_PATH = (
    Path(__file__).resolve().parent
    / "sql"
    / "marts"
    / "salario_por_cargo.sql"
)
_SQL_DIRECTORY = Path(__file__).resolve().parent / "sql" / "marts"


def criar_salario_por_cargo(caminho_banco: str | Path | None = None) -> int:
    """Cria o mart agregado de salário médio e vagas por cargo."""
    conexao = (
        conectar(caminho_banco)
        if caminho_banco is not None
        else conectar()
    )
    try:
        criar_schema(conexao)
        conexao.execute(_SQL_PATH.read_text(encoding="utf-8"))
        return conexao.execute(
            "SELECT COUNT(*) FROM marts.salario_por_cargo"
        ).fetchone()[0]
    finally:
        conexao.close()


def criar_salario_por_experiencia(
    caminho_banco: str | Path | None = None,
) -> int:
    """Cria o mart de salário médio por nível de experiência."""
    conexao = (
        conectar(caminho_banco)
        if caminho_banco is not None
        else conectar()
    )
    try:
        criar_schema(conexao)
        conexao.execute(
            (_SQL_DIRECTORY / "salario_por_experiencia.sql").read_text(
                encoding="utf-8"
            )
        )
        return conexao.execute(
            "SELECT COUNT(*) FROM marts.salario_por_experiencia"
        ).fetchone()[0]
    finally:
        conexao.close()


def criar_salario_por_pais(
    caminho_banco: str | Path | None = None,
) -> int:
    """Cria o mart de salário médio por localização da empresa."""
    conexao = (
        conectar(caminho_banco)
        if caminho_banco is not None
        else conectar()
    )
    try:
        criar_schema(conexao)
        conexao.execute(
            (_SQL_DIRECTORY / "salario_por_pais.sql").read_text(
                encoding="utf-8"
            )
        )
        return conexao.execute(
            "SELECT COUNT(*) FROM marts.salario_por_pais"
        ).fetchone()[0]
    finally:
        conexao.close()


def criar_salarios_por_perfil(
    caminho_banco: str | Path | None = None,
) -> int:
    """Cria o mart detalhado por cargo, experiência e tamanho da empresa."""
    conexao = (
        conectar(caminho_banco)
        if caminho_banco is not None
        else conectar()
    )
    try:
        criar_schema(conexao)
        conexao.execute(
            (_SQL_DIRECTORY / "salarios_por_perfil.sql").read_text(
                encoding="utf-8"
            )
        )
        return conexao.execute(
            "SELECT COUNT(*) FROM marts.salarios_por_perfil"
        ).fetchone()[0]
    finally:
        conexao.close()
