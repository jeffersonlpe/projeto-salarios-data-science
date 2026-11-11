from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pycountry
from matplotlib.ticker import FuncFormatter

from .db import conectar


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_OUTPUT_DIRECTORY = _PROJECT_ROOT / "graficos"
_ROTULOS_EXPERIENCIA = {
    "EX": "Executivo",
    "SE": "Sênior",
    "MI": "Pleno",
    "EN": "Iniciante",
}


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


def _preparar_top_10_paises(dados: pd.DataFrame) -> pd.DataFrame:
    top_10 = dados.nlargest(10, "salario_medio_usd").copy()
    nomes = []
    for codigo in top_10["company_location"]:
        pais = pycountry.countries.get(alpha_2=str(codigo).upper())
        if pais is None:
            raise ValueError(
                f"Código de país ISO 3166-1 alpha-2 inválido: {codigo}"
            )
        nomes.append(pais.name)
    top_10["nome_pais"] = nomes
    return top_10


def _salvar_grafico_paises(dados: pd.DataFrame, destino: Path) -> None:
    figura, eixo = plt.subplots(figsize=(12, 10))
    mapa_cores = plt.get_cmap("viridis")
    cores = [
        mapa_cores(0.2 + 0.65 * indice / max(len(dados) - 1, 1))
        for indice in range(len(dados))
    ]

    try:
        barras = eixo.barh(
            dados["nome_pais"],
            dados["salario_medio_usd"],
            color=cores,
            height=0.72,
        )
        eixo.invert_yaxis()
        eixo.bar_label(
            barras,
            labels=[
                f"US$ {valor:,.0f}" for valor in dados["salario_medio_usd"]
            ],
            padding=6,
            fontsize=11,
        )
        eixo.set_title(
            "Top 10 países por salário médio",
            loc="left",
            fontsize=16,
            fontweight="bold",
            pad=16,
        )
        eixo.set_xlabel("Salário médio (US$)")
        eixo.set_ylabel("País da empresa")
        eixo.xaxis.set_major_formatter(
            FuncFormatter(lambda valor, _: f"US$ {valor:,.0f}")
        )
        eixo.set_xlim(0, dados["salario_medio_usd"].max() * 1.22)
        eixo.grid(axis="x", linestyle="--", alpha=0.3)
        eixo.set_axisbelow(True)
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)
        eixo.tick_params(axis="y", labelsize=13)
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
            "País da empresa",
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
        if nome == "salario_por_pais":
            _salvar_grafico_paises(_preparar_top_10_paises(dados), destino)
        else:
            dados_grafico = dados
            if nome == "salario_por_cargo":
                dados_grafico = dados.nlargest(10, "salario_medio_usd")
            elif nome == "salario_por_experiencia":
                dados_grafico = dados.copy()
                dados_grafico[coluna_categoria] = dados_grafico[
                    coluna_categoria
                ].replace(_ROTULOS_EXPERIENCIA)
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
