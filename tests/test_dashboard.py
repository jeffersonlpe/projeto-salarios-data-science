import matplotlib

matplotlib.use("Agg")

import duckdb
import pandas as pd
import pytest

import dashboard


def test_banco_do_dashboard_e_criado_do_csv_em_caminho_independente(tmp_path):
    caminho_banco = dashboard._caminho_banco_temporario(tmp_path)
    assert not caminho_banco.exists()

    dashboard._construir_banco_dashboard(caminho_banco)

    conexao = duckdb.connect(str(caminho_banco), read_only=True)
    try:
        quantidade = conexao.execute(
            "SELECT COUNT(*) FROM marts.salarios_por_perfil"
        ).fetchone()[0]
        assert quantidade > 0
        assert conexao.execute(
            "SELECT COUNT(*) FROM raw.salarios"
        ).fetchone()[0] == 3755
    finally:
        conexao.close()


def test_graficos_do_dashboard_mantem_proporcao_e_espaco_para_rotulos(monkeypatch):
    figuras = []
    monkeypatch.setattr(
        dashboard.st,
        "pyplot",
        lambda figura, **kwargs: figuras.append(figura),
    )

    dashboard._desenhar_barras(
        pd.DataFrame(
            {
                "cargo": [f"Cargo {indice}" for indice in range(10)],
                "salario": [100_000 + indice * 10_000 for indice in range(10)],
            }
        ),
        "cargo",
        "salario",
        "Top 10 cargos por salário médio",
        "#8b7bff",
    )
    dashboard._desenhar_barras(
        pd.DataFrame(
            {
                "nivel": ["Iniciante", "Pleno", "Sênior", "Executivo"],
                "salario": [50_000, 80_000, 110_000, 150_000],
            }
        ),
        "nivel",
        "salario",
        "Salário médio por nível",
        "#8b7bff",
    )

    assert len(figuras) == 2
    alturas = [
        [barra.get_height() for barra in figura.axes[0].patches]
        for figura in figuras
    ]
    assert alturas[0] == pytest.approx([0.68] * 10)
    assert alturas[1] == pytest.approx([0.272] * 4)
    assert [
        tuple(figura.get_size_inches()) for figura in figuras
    ] == [(8.0, 5.0), (8.0, 5.0)]
    assert figuras[1].axes[0].get_xlim()[1] == pytest.approx(150_000 * 1.4)
