from pathlib import Path

import duckdb
import pandas as pd

from pipeline import refinamento


def test_refinar_salarios_cria_silver_limpa_e_tipa_dados(monkeypatch, tmp_path):
    banco_teste = tmp_path / "silver.duckdb"
    conexao = duckdb.connect(str(banco_teste))
    conexao.execute("CREATE SCHEMA raw")
    conexao.execute(
        """
        CREATE TABLE raw.salarios (
            work_year VARCHAR,
            experience_level VARCHAR,
            employment_type VARCHAR,
            job_title VARCHAR,
            salary VARCHAR,
            salary_currency VARCHAR,
            salary_in_usd VARCHAR,
            employee_residence VARCHAR,
            remote_ratio VARCHAR,
            company_location VARCHAR,
            company_size VARCHAR
        )
        """
    )
    conexao.execute(
        """
        INSERT INTO raw.salarios VALUES (
            '2023', ' SE ', ' FT ', ' Data Scientist ',
            '100000', ' USD ', '100000', ' US ',
            '100', ' US ', ' L '
        )
        """
    )
    raw_antes = conexao.execute("SELECT * FROM raw.salarios").df()
    conexao.close()
    monkeypatch.setattr(
        refinamento, "conectar", lambda: duckdb.connect(str(banco_teste))
    )

    quantidade = refinamento.refinar_salarios()

    conexao = duckdb.connect(str(banco_teste))
    try:
        refined = conexao.execute("SELECT * FROM refined.salarios").df()
        tipos = dict(
            (nome, tipo)
            for nome, tipo, *_ in conexao.execute(
                "DESCRIBE refined.salarios"
            ).fetchall()
        )
        raw_depois = conexao.execute("SELECT * FROM raw.salarios").df()

        assert quantidade == 1
        assert refined.columns.tolist() == raw_antes.columns.tolist()
        assert refined.iloc[0].to_dict() == {
            "work_year": 2023,
            "experience_level": "SE",
            "employment_type": "FT",
            "job_title": "Data Scientist",
            "salary": 100000,
            "salary_currency": "USD",
            "salary_in_usd": 100000,
            "employee_residence": "US",
            "remote_ratio": 100,
            "company_location": "US",
            "company_size": "L",
        }
        assert tipos == {
            "work_year": "INTEGER",
            "experience_level": "VARCHAR",
            "employment_type": "VARCHAR",
            "job_title": "VARCHAR",
            "salary": "BIGINT",
            "salary_currency": "VARCHAR",
            "salary_in_usd": "BIGINT",
            "employee_residence": "VARCHAR",
            "remote_ratio": "SMALLINT",
            "company_location": "VARCHAR",
            "company_size": "VARCHAR",
        }
        pd.testing.assert_frame_equal(raw_depois, raw_antes)
    finally:
        conexao.close()
