from __future__ import annotations

import tempfile
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import streamlit as st
from matplotlib.ticker import FuncFormatter

from pipeline.ingestao import ingerir
from pipeline.marts import criar_salarios_por_perfil
from pipeline.refinamento import refinar_salarios

_PROJECT_ROOT = Path(__file__).resolve().parent
_CSV_PATH = _PROJECT_ROOT / "raw" / "ds_salaries.csv"
_EXPERIENCE_LABELS = {
    "EN": "Iniciante",
    "MI": "Pleno",
    "SE": "Sênior",
    "EX": "Executivo",
}
_COMPANY_SIZE_LABELS = {
    "S": "Pequena (S)",
    "M": "Média (M)",
    "L": "Grande (L)",
}


def _construir_banco_dashboard(
    caminho_banco: str | Path,
    arquivo_csv: str | Path = _CSV_PATH,
) -> None:
    ingerir(arquivo_csv, caminho_banco=caminho_banco)
    refinar_salarios(caminho_banco=caminho_banco)
    criar_salarios_por_perfil(caminho_banco=caminho_banco)


def _caminho_banco_temporario(
    diretorio: str | Path | None = None,
) -> Path:
    with tempfile.NamedTemporaryFile(
        prefix="salarios-dashboard-",
        suffix=".duckdb",
        dir=diretorio,
        delete=False,
    ) as arquivo_temporario:
        caminho_banco = Path(arquivo_temporario.name)
    caminho_banco.unlink()
    return caminho_banco


@st.cache_resource
def _preparar_banco_dashboard() -> str:
    caminho_banco = _caminho_banco_temporario()
    _construir_banco_dashboard(caminho_banco)
    return str(caminho_banco)


def _where_clause(
    experience_level: str | None,
    company_size: str | None,
    cargo_search: str | None = None,
) -> tuple[str, list[str]]:
    conditions = []
    parameters = []
    if experience_level is not None:
        conditions.append("experience_level = ?")
        parameters.append(experience_level)
    if company_size is not None:
        conditions.append("company_size = ?")
        parameters.append(company_size)
    if cargo_search and cargo_search.strip():
        conditions.append("job_title ILIKE ?")
        parameters.append(f"%{cargo_search.strip()}%")
    return " AND ".join(conditions) if conditions else "TRUE", parameters


def _formatar_usd(valor: int | float | None) -> str:
    if valor is None:
        return "—"
    return f"US$ {valor:,.0f}"


def _desenhar_barras(
    dados,
    coluna_categoria: str,
    coluna_valor: str,
    titulo: str,
    cor: str,
) -> None:
    figura, eixo = plt.subplots(figsize=(8, 5))
    try:
        barras = eixo.barh(
            dados[coluna_categoria],
            dados[coluna_valor],
            color=cor,
            height=min(0.68, 0.068 * len(dados)),
        )
        eixo.invert_yaxis()
        eixo.bar_label(
            barras,
            labels=[_formatar_usd(valor) for valor in dados[coluna_valor]],
            padding=5,
            fontsize=9,
        )
        eixo.set_title(titulo, loc="left", fontsize=14, fontweight="bold", pad=14)
        eixo.set_xlabel("Salário médio (US$)")
        eixo.xaxis.set_major_formatter(
            FuncFormatter(lambda valor, _: f"US$ {valor:,.0f}")
        )
        eixo.set_xlim(0, dados[coluna_valor].max() * 1.4)
        eixo.grid(axis="x", linestyle="--", alpha=0.25)
        eixo.set_axisbelow(True)
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)
        figura.tight_layout()
        st.pyplot(figura, use_container_width=True)
    finally:
        plt.close(figura)


def main() -> None:
    st.set_page_config(
        page_title="Quanto ganha quem trabalha com Dados?",
        page_icon="📊",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(ellipse at 85% 0%, #232052 0, transparent 36%),
                #0b1020;
        }
        [data-testid="stHeader"] { background: transparent; }
        .block-container {
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            padding: 2rem 2.2rem;
            margin-bottom: 1.4rem;
            border: 1px solid #29334b;
            border-radius: 22px;
            background: linear-gradient(115deg, #151d31 0%, #17152e 60%, #21163b 100%);
            box-shadow: 0 18px 50px #03061180;
        }
        .hero-kicker {
            color: #62e6c6;
            font-size: .76rem;
            font-weight: 700;
            letter-spacing: .16em;
            text-transform: uppercase;
        }
        .hero h1 {
            margin: .55rem 0 .45rem;
            color: #f5f7ff;
            font-size: clamp(2rem, 4vw, 3.1rem);
            line-height: 1.12;
        }
        .hero p {
            margin: 0;
            color: #aab4ca;
            font-size: 1.02rem;
        }
        div[data-testid="stMetric"] {
            min-height: 122px;
            padding: 1.05rem 1.1rem;
            border: 1px solid #28334b;
            border-radius: 16px;
            background: linear-gradient(145deg, #151e31, #111827);
        }
        div[data-testid="stMetricLabel"] p {
            color: #aab4ca;
            font-size: .88rem;
        }
        div[data-testid="stMetricValue"] {
            color: #f3f6ff;
            font-weight: 700;
        }
        div[data-testid="stSelectbox"] label,
        div[data-testid="stTextInput"] label {
            color: #cbd4e5;
            font-weight: 600;
        }
        h2, h3 { color: #f3f6ff; }
        </style>
        <section class="hero">
            <div class="hero-kicker">Panorama salarial · mercado de dados</div>
            <h1>Quanto ganha quem trabalha com Dados?</h1>
            <p>Explore os salários com filtros por experiência e porte da empresa.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if not _CSV_PATH.is_file():
        st.error(
            f"O CSV de dados não foi encontrado: {_CSV_PATH}"
        )
        return

    caminho_banco = _preparar_banco_dashboard()
    conexao = duckdb.connect(caminho_banco, read_only=True)
    try:
        try:
            conexao.execute(
                "SELECT 1 FROM marts.salarios_por_perfil LIMIT 0"
            )
        except duckdb.CatalogException:
            st.error(
                "A tabela marts.salarios_por_perfil não existe. Execute "
                "criar_salarios_por_perfil() antes de abrir o dashboard."
            )
            return

        niveis = [
            row[0]
            for row in conexao.execute(
                """
                SELECT DISTINCT experience_level
                FROM marts.salarios_por_perfil
                ORDER BY CASE experience_level
                    WHEN 'EN' THEN 1
                    WHEN 'MI' THEN 2
                    WHEN 'SE' THEN 3
                    WHEN 'EX' THEN 4
                    ELSE 5
                END
                """
            ).fetchall()
        ]
        portes = [
            row[0]
            for row in conexao.execute(
                """
                SELECT DISTINCT company_size
                FROM marts.salarios_por_perfil
                ORDER BY company_size
                """
            ).fetchall()
        ]

        filtros = st.columns(2, gap="large")
        with filtros[0]:
            experience_level = st.selectbox(
                "Nível de experiência",
                [None, *niveis],
                format_func=lambda value: (
                    "Todos os níveis"
                    if value is None
                    else _EXPERIENCE_LABELS.get(value, value)
                ),
            )
        with filtros[1]:
            company_size = st.selectbox(
                "Porte da empresa",
                [None, *portes],
                format_func=lambda value: (
                    "Todos os portes"
                    if value is None
                    else _COMPANY_SIZE_LABELS.get(value, value)
                ),
            )

        where, parameters = _where_clause(experience_level, company_size)
        indicadores = conexao.execute(
            f"""
            SELECT
                COALESCE(SUM(quantidade_vagas), 0)::BIGINT AS total_vagas,
                SUM(salario_medio_usd * quantidade_vagas)
                    / NULLIF(SUM(quantidade_vagas), 0) AS media_salario_usd,
                MAX(maior_salario_usd) AS maior_salario_usd,
                COUNT(DISTINCT id_cargo)::BIGINT AS total_cargos
            FROM marts.salarios_por_perfil
            WHERE {where}
            """,
            parameters,
        ).fetchone()
        total_vagas, media_usd, maior_salario, total_cargos = indicadores

        st.markdown("#### Visão geral")
        kpis = st.columns(4, gap="medium")
        kpis[0].metric("Total de Vagas", f"{total_vagas:,}")
        kpis[1].metric(
            "Média Salarial USD",
            _formatar_usd(media_usd) if total_vagas else "—",
        )
        kpis[2].metric(
            "Maior Salário",
            _formatar_usd(maior_salario) if total_vagas else "—",
        )
        kpis[3].metric("Total de Cargos", f"{total_cargos:,}")

        if not total_vagas:
            st.info("Não há registros para a combinação de filtros selecionada.")
            return

        top_cargos = conexao.execute(
            f"""
            SELECT
                job_title AS cargo,
                SUM(salario_medio_usd * quantidade_vagas)
                    / NULLIF(SUM(quantidade_vagas), 0) AS salario_medio_usd
            FROM marts.salarios_por_perfil
            WHERE {where}
            GROUP BY id_cargo, job_title
            ORDER BY salario_medio_usd DESC, job_title
            LIMIT 10
            """,
            parameters,
        ).fetchdf()
        salarios_experiencia = conexao.execute(
            f"""
            SELECT
                CASE experience_level
                    WHEN 'EN' THEN 'Iniciante'
                    WHEN 'MI' THEN 'Pleno'
                    WHEN 'SE' THEN 'Sênior'
                    WHEN 'EX' THEN 'Executivo'
                    ELSE experience_level
                END AS nivel,
                SUM(salario_medio_usd * quantidade_vagas)
                    / NULLIF(SUM(quantidade_vagas), 0) AS salario_medio_usd
            FROM marts.salarios_por_perfil
            WHERE {where}
            GROUP BY experience_level
            ORDER BY CASE experience_level
                WHEN 'EN' THEN 1
                WHEN 'MI' THEN 2
                WHEN 'SE' THEN 3
                WHEN 'EX' THEN 4
                ELSE 5
            END
            """,
            parameters,
        ).fetchdf()

        st.markdown("#### Onde estão as melhores médias?")
        col_cargos, col_experiencia = st.columns(2, gap="large")
        with col_cargos:
            _desenhar_barras(
                top_cargos,
                "cargo",
                "salario_medio_usd",
                "Top 10 cargos por salário médio",
                "#8b7bff",
            )
        with col_experiencia:
            _desenhar_barras(
                salarios_experiencia,
                "nivel",
                "salario_medio_usd",
                "Salário médio por nível",
                "#8b7bff",
            )

        st.markdown("#### Cargos em destaque")
        busca = st.text_input(
            "Pesquisar cargo",
            placeholder="Digite parte do nome do cargo",
        )
        where_tabela, parametros_tabela = _where_clause(
            experience_level, company_size, busca
        )
        tabela_cargos = conexao.execute(
            f"""
            SELECT
                job_title AS "Cargo",
                SUM(salario_medio_usd * quantidade_vagas)
                    / NULLIF(SUM(quantidade_vagas), 0) AS "Média salarial USD",
                SUM(quantidade_vagas)::BIGINT AS "Vagas"
            FROM marts.salarios_por_perfil
            WHERE {where_tabela}
            GROUP BY id_cargo, job_title
            ORDER BY "Média salarial USD" DESC, "Cargo"
            LIMIT 10
            """,
            parametros_tabela,
        ).fetchdf()
        if tabela_cargos.empty:
            st.info("Nenhum cargo corresponde à pesquisa.")
        else:
            st.dataframe(
                tabela_cargos,
                column_config={
                    "Média salarial USD": st.column_config.NumberColumn(
                        format="US$ %.0f"
                    ),
                    "Vagas": st.column_config.NumberColumn(format="%d"),
                },
                hide_index=True,
                use_container_width=True,
                height=390,
            )
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
