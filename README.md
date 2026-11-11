# Pipeline de Dados Salariais

Pipeline de engenharia de dados para transformar registros salariais de um CSV
em tabelas organizadas para análise e gerar visualizações. O projeto usa Python,
pandas, DuckDB e Matplotlib.

## Objetivo

Preservar os dados de origem, preparar uma versão limpa e tipada para consulta e
gerar agregações que permitam analisar salários por cargo, nível de experiência
e país de localização da empresa. As médias são calculadas em dólares
americanos para evitar misturar moedas diferentes.

## Arquitetura

O fluxo segue as camadas `raw`, `refined` e `marts`:

```text
raw/ds_salaries.csv
        │
        ▼
raw.salarios ───────────────┐
        │                   ├─ JOIN (job_title) ──> marts.salario_por_cargo
        ├──> refined.salarios                     ├─> marts.salario_por_experiencia
        │                                         └─> marts.salario_por_pais
raw.cargos ─────────────────┘
```

### Raw

Camada de entrada, carregada de `raw/ds_salaries.csv`:

- `raw.salarios`: registros do CSV, preservando as colunas e os valores de
  origem. Cada registro representa uma observação salarial.
- `raw.cargos`: uma linha por cargo distinto, com `id_cargo` sequencial e
  `job_title`.

As duas tabelas podem ser relacionadas por `job_title`. `raw.salarios` mantém a
estrutura original do CSV e não recebe uma coluna de ID de cargo.

### Refined (Silver)

`refined.salarios` deriva de `raw.salarios`. Mantém as colunas do conjunto de
origem, remove espaços externos dos valores textuais e aplica tipos explícitos:

- `work_year`: `INTEGER`
- `salary` e `salary_in_usd`: `BIGINT`
- `remote_ratio`: `SMALLINT`
- demais colunas: `VARCHAR`

A transformação não modifica as tabelas da camada raw.

### Marts

As tabelas de marts agregam os salários por dimensões diferentes e usam
`salary_in_usd` como medida de salário:

- `marts.salario_por_cargo`: faz `INNER JOIN` entre `raw.salarios` e
  `raw.cargos` por `job_title`; gera uma linha por `id_cargo`, com
  `job_title`, `salario_medio_usd` e `quantidade_vagas`;
- `marts.salario_por_experiencia`: agrega `refined.salarios` por
  `experience_level`, com `salario_medio_usd`;
- `marts.salario_por_pais`: agrega `refined.salarios` por `company_location`,
  com `salario_medio_usd`.

`quantidade_vagas` representa a quantidade de registros salariais agregados por
cargo.

O gráfico `salario_por_pais.png` exibe os 10 países com maior média salarial,
em ordem decrescente, usando nomes completos em vez de códigos.
No gráfico `salario_por_experiencia.png`, os códigos de experiência são
apresentados como Executivo, Sênior, Pleno e Iniciante.

## Requisitos

- Python 3.10 ou superior
- Dependências declaradas em `pyproject.toml`

## Instalação

Na raiz do repositório, crie e ative um ambiente virtual e instale o projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

No macOS ou Linux, ative o ambiente com:

```bash
source .venv/bin/activate
```

## Executar o pipeline

Rode as etapas na ordem indicada, a partir da raiz do projeto:

```bash
# Carrega o CSV em raw.salarios e cria raw.cargos
python -m pipeline.ingestao

# Cria refined.salarios a partir de raw.salarios
python -c "from pipeline.refinamento import refinar_salarios; print(refinar_salarios())"

# Cria marts.salario_por_cargo juntando raw.salarios e raw.cargos
python -c "from pipeline.marts import criar_salario_por_cargo; print(criar_salario_por_cargo())"

# Cria as médias por experiência e localização da empresa
python -c "from pipeline.marts import criar_salario_por_experiencia; print(criar_salario_por_experiencia())"
python -c "from pipeline.marts import criar_salario_por_pais; print(criar_salario_por_pais())"

# Gera os três gráficos PNG em graficos/
python -m pipeline.graficos
```

Por padrão, o banco DuckDB é criado como `salarios.duckdb` na raiz do projeto.
As etapas usam `CREATE OR REPLACE`: ao executá-las novamente, as tabelas de
destino são substituídas pelo resultado mais recente. A ingestão substitui
`raw.salarios` e `raw.cargos`.
O comando de gráficos lê os três marts existentes e salva seus arquivos PNG na
pasta `graficos/`, criada automaticamente.

## Testes

Execute toda a suíte com:

```bash
python -m pytest -q
```

Os testes verificam a ingestão do CSV real e a relação entre salários e cargos,
a limpeza e tipagem da camada refined, e as médias e contagens agregadas por
cargo, experiência e localização em marts. Os bancos usados pelos testes são
temporários. Também verificam a geração dos três arquivos PNG.

## Estrutura do projeto

```text
.
├── pipeline/
│   ├── __init__.py
│   ├── db.py
│   ├── ingestao.py
│   ├── refinamento.py
│   ├── marts.py
│   ├── graficos.py
│   └── sql/
│       ├── refined/
│       │   └── salarios.sql
│       └── marts/
│           ├── salario_por_cargo.sql
│           ├── salario_por_experiencia.sql
│           └── salario_por_pais.sql
├── raw/
│   └── ds_salaries.csv
├── tests/
│   ├── test_ingestao.py
│   ├── test_refinamento.py
│   ├── test_marts.py
│   └── test_graficos.py
├── graficos/  # criada ao executar pipeline.graficos; contém os PNGs gerados
├── pyproject.toml
└── README.md
```

## Como eu conferi

O projeto foi desenvolvido por mim, com apoio de IA para agilizar o código. Eu
validei cada etapa: conferi as tabelas, os JOINs e os resultados dos testes. Por
exemplo, a IA indicou inicialmente apenas 1 tabela, mas ao conferir, identifiquei
2 tabelas (salarios e cargos) e corrigi o JOIN entre elas.
