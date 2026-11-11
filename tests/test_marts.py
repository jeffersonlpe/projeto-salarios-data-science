import duckdb
import pytest

from pipeline import marts


def test_criar_salario_por_cargo_calcula_media_e_quantidade(
    monkeypatch, tmp_path
):
    banco_teste = tmp_path / "validacao.duckdb"
    conexao = duckdb.connect(str(banco_teste))
    conexao.execute("CREATE SCHEMA raw")
    conexao.execute(
        """
        CREATE TABLE raw.salarios (
            job_title VARCHAR,
            salary_in_usd BIGINT
        )
        """
    )
    conexao.execute(
        """
        INSERT INTO raw.salarios VALUES
            ('Data Scientist', 90000),
            ('Data Scientist', 110000),
            ('Data Analyst', 70000),
            ('ML Engineer', 50000),
            ('ML Engineer', 70000),
            ('ML Engineer', 90000)
        """
    )
    conexao.execute(
        """
        CREATE TABLE raw.cargos (
            id_cargo INTEGER,
            job_title VARCHAR
        )
        """
    )
    conexao.execute(
        """
        INSERT INTO raw.cargos VALUES
            (30, 'Data Scientist'),
            (10, 'Data Analyst'),
            (20, 'ML Engineer')
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
            SELECT id_cargo, job_title, salario_medio_usd, quantidade_vagas
            FROM marts.salario_por_cargo
            ORDER BY id_cargo
            """
        ).fetchall()
        assert quantidade_cargos == 3
        assert resultados == [
            (10, "Data Analyst", 70000.0, 1),
            (20, "ML Engineer", 70000.0, 3),
            (30, "Data Scientist", 100000.0, 2),
        ]
    finally:
        conexao.close()


def test_criar_salarios_por_perfil_agrega_dimensoes_para_dashboard(
    monkeypatch, tmp_path
):
    banco_teste = tmp_path / "perfis.duckdb"
    conexao = duckdb.connect(str(banco_teste))
    conexao.execute("CREATE SCHEMA raw")
    conexao.execute("CREATE SCHEMA refined")
    conexao.execute(
        "CREATE TABLE raw.cargos (id_cargo INTEGER, job_title VARCHAR)"
    )
    conexao.execute(
        """
        INSERT INTO raw.cargos VALUES
            (1, 'Data Scientist'),
            (2, 'Data Analyst')
        """
    )
    conexao.execute(
        """
        CREATE TABLE refined.salarios (
            job_title VARCHAR,
            experience_level VARCHAR,
            company_size VARCHAR,
            salary_in_usd BIGINT
        )
        """
    )
    conexao.execute(
        """
        INSERT INTO refined.salarios VALUES
            ('Data Scientist', 'SE', 'L', 100000),
            ('Data Scientist', 'SE', 'L', 120000),
            ('Data Scientist', 'SE', 'M', 90000),
            ('Data Analyst', 'MI', 'S', 70000)
        """
    )
    conexao.close()
    monkeypatch.setattr(
        marts, "conectar", lambda: duckdb.connect(str(banco_teste))
    )

    quantidade_perfis = marts.criar_salarios_por_perfil()

    conexao = duckdb.connect(str(banco_teste))
    try:
        perfis = conexao.execute(
            """
            SELECT
                id_cargo, job_title, experience_level, company_size,
                salario_medio_usd, maior_salario_usd, quantidade_vagas
            FROM marts.salarios_por_perfil
            ORDER BY id_cargo, company_size
            """
        ).fetchall()
        assert quantidade_perfis == 3
        assert perfis == [
            (1, "Data Scientist", "SE", "L", 110000.0, 120000, 2),
            (1, "Data Scientist", "SE", "M", 90000.0, 90000, 1),
            (2, "Data Analyst", "MI", "S", 70000.0, 70000, 1),
        ]
    finally:
        conexao.close()


@pytest.mark.parametrize(
    ("criar_mart", "tabela", "coluna", "esperado"),
    [
        (
            marts.criar_salario_por_experiencia,
            "salario_por_experiencia",
            "experience_level",
            [("EN", 60000.0), ("MI", 90000.0), ("SE", 110000.0)],
        ),
        (
            marts.criar_salario_por_pais,
            "salario_por_pais",
            "company_location",
            [("CA", 60000.0), ("GB", 90000.0), ("US", 110000.0)],
        ),
    ],
)
def test_criar_marts_de_experiencia_e_pais(
    criar_mart, tabela, coluna, esperado, monkeypatch, tmp_path
):
    banco_teste = tmp_path / f"validacao_{tabela}.duckdb"
    conexao = duckdb.connect(str(banco_teste))
    conexao.execute("CREATE SCHEMA refined")
    conexao.execute(
        """
        CREATE TABLE refined.salarios (
            experience_level VARCHAR,
            company_location VARCHAR,
            salary_in_usd BIGINT
        )
        """
    )
    conexao.execute(
        """
        INSERT INTO refined.salarios VALUES
            ('SE', 'US', 100000),
            ('SE', 'US', 120000),
            ('MI', 'GB', 80000),
            ('MI', 'GB', 100000),
            ('EN', 'CA', 60000)
        """
    )
    conexao.close()
    monkeypatch.setattr(
        marts, "conectar", lambda: duckdb.connect(str(banco_teste))
    )

    quantidade_grupos = criar_mart()

    conexao = duckdb.connect(str(banco_teste))
    try:
        resultados = conexao.execute(
            f"""
            SELECT {coluna}, salario_medio_usd
            FROM marts.{tabela}
            ORDER BY {coluna}
            """
        ).fetchall()
        assert quantidade_grupos == 3
        assert resultados == esperado
    finally:
        conexao.close()
