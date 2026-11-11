import matplotlib

matplotlib.use("Agg")

import duckdb
from matplotlib.axes import Axes
from matplotlib.figure import Figure

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
            ('EX', 150000),
            ('SE', 110000),
            ('MI', 80000),
            ('EN', 50000)
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
    conexao.executemany(
        "INSERT INTO marts.salario_por_pais VALUES (?, ?)",
        [
            (codigo, indice * 10000)
            for indice, codigo in enumerate(
                [
                    "US", "GB", "CA", "AU", "DE", "FR",
                    "IN", "JP", "SE", "NZ", "BR", "ES",
                ],
                start=1,
            )
        ],
    )
    conexao.close()
    monkeypatch.setattr(
        graficos, "conectar", lambda caminho=None: duckdb.connect(str(banco_teste))
    )
    salvar_grafico = graficos._salvar_grafico
    dados_grafico_cargos = {}
    dados_grafico_experiencia = {}
    salvar_grafico_paises = graficos._salvar_grafico_paises
    dados_grafico_paises = {}
    dimensoes_figuras = []
    layouts_ajustados = []
    fontes_paises = []
    rotulos_salario = []
    criar_subplots = graficos.plt.subplots
    bar_label = Axes.bar_label
    invert_yaxis = Axes.invert_yaxis
    tight_layout = Figure.tight_layout
    tick_params = Axes.tick_params
    eixo_pais_invertido = []

    def capturar_subplots(*args, **kwargs):
        dimensoes_figuras.append(kwargs.get("figsize"))
        return criar_subplots(*args, **kwargs)

    def capturar_bar_label(self, container, labels=None, *args, **kwargs):
        rotulos_salario.append(list(labels))
        return bar_label(self, container, labels=labels, *args, **kwargs)

    def capturar_tight_layout(self, *args, **kwargs):
        if tuple(self.get_size_inches()) == (12.0, 10.0):
            layouts_ajustados.append(True)
        return tight_layout(self, *args, **kwargs)

    def capturar_invert_yaxis(self):
        if tuple(self.figure.get_size_inches()) == (12.0, 10.0):
            eixo_pais_invertido.append(True)
        return invert_yaxis(self)

    def capturar_tick_params(self, *args, **kwargs):
        if kwargs.get("axis") == "y" and kwargs.get("labelsize") == 13:
            fontes_paises.append(kwargs["labelsize"])
        return tick_params(self, *args, **kwargs)

    def capturar_grafico(
        dados, coluna_categoria, coluna_salario, titulo, rotulo_categoria, destino
    ):
        if destino.name == "salario_por_cargo.png":
            dados_grafico_cargos["dados"] = dados.copy()
        elif destino.name == "salario_por_experiencia.png":
            dados_grafico_experiencia["dados"] = dados.copy()
        salvar_grafico(
            dados,
            coluna_categoria,
            coluna_salario,
            titulo,
            rotulo_categoria,
            destino,
        )

    def capturar_grafico_paises(dados, destino):
        dados_grafico_paises["dados"] = dados.copy()
        salvar_grafico_paises(dados, destino)

    monkeypatch.setattr(graficos, "_salvar_grafico", capturar_grafico)
    monkeypatch.setattr(graficos, "_salvar_grafico_paises", capturar_grafico_paises)
    monkeypatch.setattr(graficos.plt, "subplots", capturar_subplots)
    monkeypatch.setattr(Axes, "bar_label", capturar_bar_label)
    monkeypatch.setattr(Axes, "invert_yaxis", capturar_invert_yaxis)
    monkeypatch.setattr(Figure, "tight_layout", capturar_tight_layout)
    monkeypatch.setattr(Axes, "tick_params", capturar_tick_params)

    arquivos = graficos.gerar_graficos(pasta_saida=tmp_path / "graficos")

    cargos_plotados = dados_grafico_cargos["dados"]
    assert len(cargos_plotados) == 10
    assert set(cargos_plotados["job_title"]) == {
        f"Cargo {indice:02d}" for indice in range(3, 13)
    }
    experiencia_plotada = dados_grafico_experiencia["dados"]
    assert experiencia_plotada.set_index("experience_level")[
        "salario_medio_usd"
    ].to_dict() == {
        "Executivo": 150000,
        "Sênior": 110000,
        "Pleno": 80000,
        "Iniciante": 50000,
    }
    paises_plotados = dados_grafico_paises["dados"]
    assert paises_plotados["nome_pais"].tolist() == [
        "Spain",
        "Brazil",
        "New Zealand",
        "Sweden",
        "Japan",
        "India",
        "France",
        "Germany",
        "Australia",
        "Canada",
    ]
    assert paises_plotados["salario_medio_usd"].tolist() == [
        120000,
        110000,
        100000,
        90000,
        80000,
        70000,
        60000,
        50000,
        40000,
        30000,
    ]
    assert (12, 10) in dimensoes_figuras
    assert layouts_ajustados
    assert eixo_pais_invertido == [True]
    assert fontes_paises == [13]
    assert rotulos_salario == [
        [
            f"US$ {valor:,.0f}"
            for valor in paises_plotados["salario_medio_usd"]
        ]
    ]
    assert {arquivo.name for arquivo in arquivos} == {
        "salario_por_cargo.png",
        "salario_por_experiencia.png",
        "salario_por_pais.png",
    }
    for arquivo in arquivos:
        assert arquivo.is_file()
        assert arquivo.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
