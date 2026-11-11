# Pipeline de Dados Salariais

Pipeline de engenharia de dados que carrega dados de salários de um CSV,
organiza-os em camadas analíticas e publica tabelas agregadas para análise.
O projeto usa Python, pandas e DuckDB.

## Arquitetura

O fluxo segue as camadas `raw`, `refined` e `marts`:

```text
raw/ds_salaries.csv
        │
        ▼
raw.salarios ── raw.cargos
        │
        ▼
refined.salarios
        │
        ▼
┌───────────────────────────────┐
│ marts.salario_por_cargo       │
│ marts.salario_por_experiencia │
│ marts.salario_por_pais        │
└───────────────────────────────┘
```

### Raw

Camada de entrada, carregada de `raw/ds_salaries.csv`:

- `raw.salarios`: dados do CSV, preservando as colunas originais.
- `raw.cargos`: cargos distintos, com `id_cargo` e `job_title`.

As tabelas podem ser relacionadas por `job_title`.

### Refined (Silver)

`refined.salarios` deriva de `raw.salarios`. Mantém as colunas do conjunto de
origem, remove espaços externos dos valores textuais e aplica tipos explícitos:

- `work_year`: `INTEGER`
- `salary` e `salary_in_usd`: `BIGINT`
- `remote_ratio`: `SMALLINT`
- demais colunas: `VARCHAR`

A transformação não modifica as tabelas da camada raw.

### Marts

As tabelas de marts agregam `refined.salarios` por dimensões diferentes:

- `marts.salario_por_cargo`: média de salário e quantidade de registros por
  `job_title`;
- `marts.salario_por_experiencia`: média de salário por `experience_level`;
- `marts.salario_por_pais`: média de salário por `company_location`.

As médias são calculadas com `salary_in_usd` e expostas como
`salario_medio_usd`, permitindo comparar salários sem misturar moedas de origem
diferentes. A tabela por cargo também inclui `quantidade_vagas`.

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

# Cria marts.salario_por_cargo a partir de refined.salarios
python -c "from pipeline.marts import criar_salario_por_cargo; print(criar_salario_por_cargo())"

# Cria as médias por experiência e localização da empresa
python -c "from pipeline.marts import criar_salario_por_experiencia; print(criar_salario_por_experiencia())"
python -c "from pipeline.marts import criar_salario_por_pais; print(criar_salario_por_pais())"
```

Por padrão, o banco DuckDB é criado como `salarios.duckdb` na raiz do projeto.
As etapas usam `CREATE OR REPLACE`: ao executá-las novamente, as tabelas de
destino são substituídas pelo resultado mais recente. A ingestão substitui
`raw.salarios` e `raw.cargos`.

## Testes

Execute toda a suíte com:

```bash
python -m pytest -q
```

Os testes verificam a ingestão do CSV real e a relação entre salários e cargos,
a limpeza e tipagem da camada refined, e as médias e contagens agregadas por
cargo, experiência e localização em marts. Os bancos usados pelos testes são
temporários.

## Estrutura do projeto

```text
.
├── pipeline/
│   ├── db.py
│   ├── ingestao.py
│   ├── refinamento.py
│   ├── marts.py
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
│   └── test_marts.py
└── pyproject.toml
```
