from pathlib import Path

import duckdb
import pandas as pd

from pipeline import ingestao


def test_ingerir_cria_cargos_e_mantem_join_com_csv_real(monkeypatch, tmp_path):
    arquivo = Path(__file__).resolve().parents[1] / "raw" / "ds_salaries.csv"
    banco_teste = tmp_path / "validacao.duckdb"
    conexao = duckdb.connect(str(banco_teste))
    monkeypatch.setattr(ingestao, "conectar", lambda: conexao)

    try:
        dados_origem = pd.read_csv(arquivo)
        quantidade = ingestao.ingerir(arquivo)
        conexao = duckdb.connect(str(banco_teste))

        assert quantidade == len(dados_origem)

        salarios = conexao.execute("SELECT * FROM raw.salarios").df()
        cargos = conexao.execute("SELECT * FROM raw.cargos").df()
        assert salarios.columns.tolist() == dados_origem.columns.tolist()
        colunas_salarios = dados_origem.columns.tolist()
        pd.testing.assert_frame_equal(
            salarios.sort_values(colunas_salarios).reset_index(drop=True),
            dados_origem.sort_values(colunas_salarios).reset_index(drop=True),
            check_dtype=False,
        )
        assert cargos.columns.tolist() == ["id_cargo", "job_title"]
        assert cargos["id_cargo"].is_unique
        assert cargos["job_title"].is_unique
        assert set(cargos["job_title"]) == set(dados_origem["job_title"])

        quantidade_join = conexao.execute(
            """
            SELECT COUNT(*)
            FROM raw.salarios AS s
            JOIN raw.cargos AS c USING (job_title)
            """
        ).fetchone()[0]
        assert quantidade_join == len(dados_origem)
    finally:
        conexao.close()
        banco_teste.unlink(missing_ok=True)

    assert not banco_teste.exists()
