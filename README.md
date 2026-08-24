# Data Query

[![CI](https://github.com/saurabho7222/data-query/actions/workflows/ci.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/ci.yml)
[![Security](https://github.com/saurabho7222/data-query/actions/workflows/security.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/security.yml)
[![CodeQL](https://github.com/saurabho7222/data-query/actions/workflows/codeql.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/codeql.yml)

A typed Python **CLI application** for validating a SQLite sales database and producing deterministic JSON analytics with optional CSV exports, cohort retention, equal-length period comparisons, and Pareto-style product concentration analysis.

> **Project type:** `cli-application`. This project does not provision infrastructure. The canonical metadata is in `[tool.data-query]` in `pyproject.toml` and `project-metadata.json`; see [CLASSIFICATION.md](CLASSIFICATION.md).

## Features

- declarative Pydantic schema for region, date, date-range, top-limit, cohort-horizon, product-limit, and comparison-window validation;
- hardened read-only SQLite access with integrity checks and defensive PRAGMAs;
- static parameterized SQL for analytics queries;
- database schema and row-integrity validation;
- customer/order/revenue summary, top-customer, and monthly-revenue analytics;
- monthly customer-cohort retention with a bounded 1..24 period horizon;
- equal-length previous-period comparison for completed orders and revenue;
- ranked product revenue concentration with units, order counts, revenue share, cumulative share, and an 80% Pareto threshold;
- optional region/date filters and CSV exports;
- atomic output writes and output-path collision protection;
- validate-only mode and structured JSON logging;
- formal threat model covering untrusted CLI/database/path inputs and dependency supply-chain risks;
- reproducible Docker Compose and Dev Container workflows used only for local execution and verification;
- CI gates for dependency lock consistency, linting, strict typing, tests/coverage, packaging, Docker/Compose, dependency audits, secret scanning, and CodeQL.

## Requirements

- Python 3.11+
- `pip`
- Docker with the Compose plugin for isolated container verification (optional)
- a Dev Container compatible editor (optional)

### Runtime dependencies

`pydantic==2.13.4` is the direct runtime dependency. It provides the canonical declarative `ReportFilters` schema and CLI boundary validation. `requirements.txt` mirrors this direct dependency for conventional package scanners, while the complete transitive runtime graph is generated in `uv.lock`.

CI verifies dependency reproducibility with:

```bash
uv lock --check
uv sync --frozen
```

Development/security tools are exactly pinned in `requirements-dev.txt`. `scripts/check_dependency_freshness.py` checks both runtime and development direct pins against PyPI, and the Security workflow retains the result as an artifact.

## Fresh-clone setup

```bash
git clone https://github.com/saurabho7222/data-query.git
cd data-query
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
make quality
```

See [docs/architecture.md](docs/architecture.md) for component boundaries, advanced analytics semantics, trust boundaries, SQLite safety invariants, failure handling, the container-tooling rationale, and verification strategy. See [THREAT_MODEL.md](THREAT_MODEL.md) for the explicit security model.

## Dev Container

`.devcontainer/devcontainer.json` provides a reproducible editor/container environment. Its `postCreateCommand` installs the package and pinned development tools and runs the coverage-gated test suite. `tests/test_repository_contract.py` verifies the Dev Container configuration alongside the repository classification and dependency-manifest contracts.

## One-command isolated run

```bash
make compose-demo
```

This builds the image, creates a sample SQLite database, and writes:

```text
.local/input.db
.local/report.json
.local/customers.csv
.local/monthly.csv
```

The Compose model contains only short-lived application jobs; SQLite is embedded, so no database server, cloud account, exposed port, or external service is required. Docker/Compose/Dev Container artifacts are reproducible application test environments, not infrastructure-as-code.

## Run the CLI

Create a sample database:

```bash
python examples/create_sample_db.py .local/input.db
```

Generate a JSON report:

```bash
data-query --input .local/input.db --output .local/report.json
```

Filter by region and inclusive date range:

```bash
data-query \
  --input .local/input.db \
  --output .local/north-feb.json \
  --region north \
  --start-date 2026-02-01 \
  --end-date 2026-02-28 \
  --top-limit 3
```

### Cohort retention

Every JSON report includes monthly customer-cohort retention. Cohort identity is the month of a customer's first completed order. Limit the returned month offsets with `--cohort-periods`:

```bash
data-query \
  --input .local/input.db \
  --output .local/cohorts.json \
  --cohort-periods 12
```

A retention row contains:

```json
{
  "cohort_month": "2026-01",
  "period": 1,
  "cohort_size": 42,
  "retained_customers": 17,
  "retention_rate": 40.48
}
```

Date filters restrict observed cohort activity but do not rewrite the customer's original cohort month.

### Equal-length period comparison

Use `--compare-period` with a complete date window to compare the requested range with the immediately preceding range containing the same number of inclusive calendar days:

```bash
data-query \
  --input .local/input.db \
  --output .local/feb-comparison.json \
  --start-date 2026-02-01 \
  --end-date 2026-02-28 \
  --compare-period
```

The report includes current and previous completed-order/revenue metrics plus percentage changes. When a previous baseline is zero, the corresponding percentage change is `null` rather than an infinite value.

### Product concentration and Pareto share

Every report also analyzes completed-order revenue by product. The engine ranks products deterministically and calculates units, completed-order count, revenue, each product's revenue share, and cumulative revenue share. `products_to_80_pct` reports how many ranked products are required to reach at least 80% of scoped revenue.

Use `--product-limit` to control how many ranked product rows are emitted without changing the full-population concentration summary:

```bash
data-query \
  --input .local/input.db \
  --output .local/products.json \
  --product-limit 20
```

The limit is bounded to `1..100`. Region and date filters apply to product activity exactly as they do to the other scoped aggregates.

A product row looks like:

```json
{
  "product": "dock",
  "orders": 8,
  "units": 11.0,
  "revenue": 1320.0,
  "revenue_share_pct": 37.38,
  "cumulative_revenue_share_pct": 65.73
}
```

Write CSV views too:

```bash
data-query \
  --input .local/input.db \
  --output .local/report.json \
  --customers-csv .local/customers.csv \
  --monthly-csv .local/monthly.csv
```

Validate without writing outputs:

```bash
data-query --input .local/input.db --validate-only --log-level INFO
```

Emit structured logs:

```bash
data-query \
  --input .local/input.db \
  --output .local/report.json \
  --log-level INFO \
  --log-format json
```

## Input contract

Required SQLite tables/columns:

```text
customers(id, name, region)
orders(id, customer_id, order_date, status)
order_items(order_id, product, quantity, unit_price)
```

`src/data_query/schemas.py` is the canonical configuration schema. Database validation rejects missing tables/columns, malformed `YYYY-MM-DD` dates, negative or non-numeric quantity/price values, orders without customers, and order items without orders. Query values use SQLite parameter binding rather than SQL string interpolation.

Output paths are normalized before execution. Outputs cannot overwrite the input database, and two output options cannot target the same destination.

## Report contract

The JSON report schema is versioned independently inside each document with `schema_version`. Version 4 includes `cohort_retention`, `period_comparison`, `product_concentration`, and the associated bounded filter metadata while retaining summary, top-customer, and monthly-revenue sections.

## Quality and security checks

```bash
make test
make coverage                     # >= 90%
make lint                         # Ruff
make typecheck                    # mypy strict
make quality
uv lock --check
uv sync --frozen
python scripts/check_dependency_freshness.py
make security
make package-check
make compose-config
make compose-demo
```

The GitHub Actions test matrix covers Python 3.11 and 3.12. The Security workflow audits the locked runtime graph and pinned development dependencies, uploads dependency-freshness evidence, scans repository history with Gitleaks, and CodeQL runs separately.

## Project structure

```text
src/data_query/errors.py           application error hierarchy
src/data_query/schemas.py          declarative input/config validation
src/data_query/models.py           typed report models and output options
src/data_query/validation.py       hardened SQLite/schema/data checks
src/data_query/reporting.py        aggregate/cohort report orchestration
src/data_query/comparison.py       equal-length period comparison engine
src/data_query/products.py         product concentration and Pareto analytics
src/data_query/writers.py          atomic JSON/CSV writers
src/data_query/path_safety.py      output collision protection
src/data_query/logging_utils.py    structured logging
src/data_query/input_validation.py CLI validation adapters
docs/architecture.md               architecture and trust-boundary design
THREAT_MODEL.md                    assets, threats, mitigations, residual risks
examples/                          sample database generator
scripts/                           maintenance checks
tests/                             behavioral/unit/contract tests
.devcontainer/devcontainer.json    reproducible development container
docker-compose.yml                 isolated end-to-end execution
project-metadata.json              machine-readable application metadata
.github/workflows/                 CI, security, CodeQL, and release automation
pyproject.toml                     package/runtime/quality configuration
requirements.txt                   conventional direct runtime manifest
uv.lock                            generated runtime dependency lock
requirements-dev.txt               exact development/security pins
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep features and fixes focused and include the tests that demonstrate their behavior. Use conventional commit prefixes for new work. `CHANGELOG.md` records user-visible changes.
