import matplotlib

matplotlib.use("Agg")

import duckdb

from pipeline import graficos


def test_gerar_graficos_cria_tres_pngs(monkeypatch, tmp_path):
    banco_teste = tmp_path / "validacao.duckdb"
    conexao = duckdb.connect(str(banco_teste))
    conexao.execute("CREATE SCHEMA marts")
    conexao.execute(
        """
        CREATE TABLE marts.salario_por_cargo (
            job_title VARCHAR,
            salario_medio_usd DOUBLE,
            quantidade_vagas BIGINT
        )
        """
    )
    conexao.executemany(
        "INSERT INTO marts.salario_por_cargo VALUES (?, ?, ?)",
        [
            (f"Cargo {indice:02d}", indice * 10000, 1)
            for indice in range(1, 13)
        ],
    )
    conexao.execute(
        """
        CREATE TABLE marts.salario_por_experiencia (
            experience_level VARCHAR,
            salario_medio_usd DOUBLE
        )
        """
    )
    conexao.execute(
        """
        INSERT INTO marts.salario_por_experiencia VALUES
            ('SE', 110000),
            ('MI', 80000)
        """
    )
    conexao.execute(
        """
        CREATE TABLE marts.salario_por_pais (
            company_location VARCHAR,
            salario_medio_usd DOUBLE
        )
        """
    )
    conexao.execute(
        """
        INSERT INTO marts.salario_por_pais VALUES
            ('US', 120000),
            ('GB', 90000)
        """
    )
    conexao.close()
    monkeypatch.setattr(
        graficos, "conectar", lambda caminho=None: duckdb.connect(str(banco_teste))
    )
    salvar_grafico = graficos._salvar_grafico
    dados_grafico_cargos = {}

    def capturar_grafico(
        dados, coluna_categoria, coluna_salario, titulo, rotulo_categoria, destino
    ):
        if destino.name == "salario_por_cargo.png":
            dados_grafico_cargos["dados"] = dados.copy()
        salvar_grafico(
            dados,
            coluna_categoria,
            coluna_salario,
            titulo,
            rotulo_categoria,
            destino,
        )

    monkeypatch.setattr(graficos, "_salvar_grafico", capturar_grafico)

    arquivos = graficos.gerar_graficos(pasta_saida=tmp_path / "graficos")

    cargos_plotados = dados_grafico_cargos["dados"]
    assert len(cargos_plotados) == 10
    assert set(cargos_plotados["job_title"]) == {
        f"Cargo {indice:02d}" for indice in range(3, 13)
    }
    assert {arquivo.name for arquivo in arquivos} == {
        "salario_por_cargo.png",
        "salario_por_experiencia.png",
        "salario_por_pais.png",
    }
    for arquivo in arquivos:
        assert arquivo.is_file()
        assert arquivo.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
