from __future__ import annotations

from pathlib import Path

import pandas as pd

from .db import conectar, criar_schema, gravar


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CSV_PATH = _PROJECT_ROOT / "raw" / "ds_salaries.csv"


def ingerir(
    arquivo: str | Path = _CSV_PATH,
    caminho_banco: str | Path | None = None,
) -> int:
    """Lê o CSV e substitui raw.salarios e raw.cargos."""
    dados = pd.read_csv(arquivo)
    cargos = (
        dados[["job_title"]]
        .drop_duplicates()
        .sort_values("job_title")
        .reset_index(drop=True)
    )
    cargos.insert(0, "id_cargo", range(1, len(cargos) + 1))

    conexao = (
        conectar(caminho_banco)
        if caminho_banco is not None
        else conectar()
    )
    try:
        criar_schema(conexao)
        gravar(dados, "salarios", schema="raw", conexao=conexao)
        gravar(cargos, "cargos", schema="raw", conexao=conexao)
    finally:
        conexao.close()
    return len(dados)


if __name__ == "__main__":
    ingerir()
