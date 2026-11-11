from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from .db import conectar


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_OUTPUT_DIRECTORY = _PROJECT_ROOT / "graficos"


def _salvar_grafico(
    dados: pd.DataFrame,
    coluna_categoria: str,
    coluna_salario: str,
    titulo: str,
    rotulo_categoria: str,
    destino: Path,
) -> None:
    dados = dados.sort_values(coluna_salario).reset_index(drop=True)
    altura = max(5.5, len(dados) * 0.27)
    figura, eixo = plt.subplots(figsize=(12, altura))
    mapa_cores = plt.get_cmap("viridis")
    cores = [
        mapa_cores(0.2 + 0.65 * indice / max(len(dados) - 1, 1))
        for indice in range(len(dados))
    ]

    try:
        eixo.barh(
            dados[coluna_categoria].astype(str),
            dados[coluna_salario],
            color=cores,
            height=0.75,
        )
        eixo.set_title(titulo, loc="left", fontsize=16, fontweight="bold", pad=16)
        eixo.set_xlabel("Salário médio (US$)")
        eixo.set_ylabel(rotulo_categoria)
        eixo.xaxis.set_major_formatter(
            FuncFormatter(lambda valor, _: f"US$ {valor:,.0f}")
        )
        eixo.grid(axis="x", linestyle="--", alpha=0.3)
        eixo.set_axisbelow(True)
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)
        eixo.tick_params(axis="y", labelsize=8 if len(dados) > 25 else 10)
        figura.tight_layout()
        figura.savefig(destino, dpi=160, bbox_inches="tight", facecolor="white")
    finally:
        plt.close(figura)


def gerar_graficos(
    caminho_banco: str | Path | None = None,
    pasta_saida: str | Path | None = None,
) -> list[Path]:
    """Gera gráficos PNG de salário médio para as três tabelas de marts."""
    definicoes = (
        (
            "salario_por_cargo",
            "SELECT job_title, salario_medio_usd FROM marts.salario_por_cargo",
            "job_title",
            "Cargo",
            "Salário médio por cargo",
        ),
        (
            "salario_por_experiencia",
            """
            SELECT experience_level, salario_medio_usd
            FROM marts.salario_por_experiencia
            """,
            "experience_level",
            "Nível de experiência",
            "Salário médio por nível de experiência",
        ),
        (
            "salario_por_pais",
            """
            SELECT company_location, salario_medio_usd
            FROM marts.salario_por_pais
            """,
            "company_location",
            "País da empresa (código)",
            "Salário médio por país da empresa",
        ),
    )

    conexao = conectar(caminho_banco)
    try:
        resultados = [
            (
                nome,
                conexao.execute(consulta).fetchdf(),
                coluna_categoria,
                rotulo_categoria,
                titulo,
            )
            for nome, consulta, coluna_categoria, rotulo_categoria, titulo in definicoes
        ]
    finally:
        conexao.close()

    for nome, dados, *_ in resultados:
        if dados.empty:
            raise ValueError(f"A tabela marts.{nome} está vazia.")

    pasta = Path(pasta_saida) if pasta_saida is not None else _OUTPUT_DIRECTORY
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for nome, dados, coluna_categoria, rotulo_categoria, titulo in resultados:
        destino = pasta / f"{nome}.png"
        dados_grafico = (
            dados.nlargest(10, "salario_medio_usd")
            if nome == "salario_por_cargo"
            else dados
        )
        _salvar_grafico(
            dados_grafico,
            coluna_categoria,
            "salario_medio_usd",
            titulo,
            rotulo_categoria,
            destino,
        )
        caminhos.append(destino)

    return caminhos


if __name__ == "__main__":
    for arquivo in gerar_graficos():
        print(f"Gráfico salvo em: {arquivo}")
