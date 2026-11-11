import duckdb

from pipeline import marts


def test_criar_salario_por_cargo_calcula_media_e_quantidade(
    monkeypatch, tmp_path
):
    banco_teste = tmp_path / "validacao.duckdb"
    conexao = duckdb.connect(str(banco_teste))
    conexao.execute("CREATE SCHEMA refined")
    conexao.execute(
        """
        CREATE TABLE refined.salarios (
            job_title VARCHAR,
            salary_in_usd BIGINT
        )
        """
    )
    conexao.execute(
        """
        INSERT INTO refined.salarios VALUES
            ('Data Scientist', 90000),
            ('Data Scientist', 110000),
            ('Data Analyst', 70000),
            ('ML Engineer', 50000),
            ('ML Engineer', 70000),
            ('ML Engineer', 90000)
        """
    )
    conexao.close()
    monkeypatch.setattr(
        marts, "conectar", lambda: duckdb.connect(str(banco_teste))
    )

    quantidade_cargos = marts.criar_salario_por_cargo()

    conexao = duckdb.connect(str(banco_teste))
    try:
        resultados = conexao.execute(
            """
            SELECT job_title, salario_medio_usd, quantidade_vagas
            FROM marts.salario_por_cargo
            ORDER BY job_title
            """
        ).fetchall()
        assert quantidade_cargos == 3
        assert resultados == [
            ("Data Analyst", 70000.0, 1),
            ("Data Scientist", 100000.0, 2),
            ("ML Engineer", 70000.0, 3),
        ]
    finally:
        conexao.close()
