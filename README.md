# Data Query

[![CI](https://github.com/saurabho7222/data-query/actions/workflows/ci.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/ci.yml)
[![Security](https://github.com/saurabho7222/data-query/actions/workflows/security.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/security.yml)
[![CodeQL](https://github.com/saurabho7222/data-query/actions/workflows/codeql.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/codeql.yml)

A typed Python **SQLite analytics application** with a primary CLI and an optional HTTP API. Both interfaces reuse the same validated, read-only analytics engine for summary, cohort-retention, period-comparison, and product-concentration reporting.

> **Project type:** `application`, not infrastructure-as-code. The primary interface is `command-line`; an optional `http-api` is also supported. Canonical machine metadata lives in `[tool.data-query]` in `pyproject.toml` and `project-metadata.json`. See [CLASSIFICATION.md](CLASSIFICATION.md).

## Features

- primary `data-query` CLI plus optional `data-query-api` HTTP service;
- `/healthz`, `/metrics`, and `/v1/report` service endpoints;
- sandboxed API database selection under `DATA_QUERY_DATA_ROOT`;
- declarative Pydantic validation for region, dates, bounded limits, and comparison preconditions;
- hardened read-only SQLite access with integrity checks and defensive PRAGMAs;
- static parameterized SQL and row-integrity validation;
- summary, top-customer, monthly-revenue, cohort-retention, equal-length period comparison, and Pareto-style product analytics;
- optional CSV exports for CLI runs;
- atomic writes and output-path collision protection;
- versioned structured JSON logging schema for CLI diagnostics;
- formal threat model covering CLI, HTTP, filesystem, SQLite, observability, and dependency boundaries;
- reproducible Docker/Compose and Dev Container environments;
- CI gates for frozen locks, Ruff, strict mypy, Python 3.11/3.12 tests with >=90% coverage, packaging, Docker/Compose API smoke tests, dependency audits, Gitleaks, and CodeQL.

## Requirements

- Python 3.11+
- `pip`
- Docker with Compose for isolated container verification (optional)

### Runtime dependencies

Direct runtime dependencies are exactly pinned and intentionally scanner-visible in both `pyproject.toml` and `requirements.txt`:

```text
fastapi==0.141.1
pydantic==2.13.4
uvicorn==0.52.3
```

`uv.lock` contains the generated transitive graph. CI verifies reproducibility with:

```bash
uv lock --check
uv sync --frozen
```

Development/security tools are exactly pinned in `requirements-dev.txt`; dependency freshness and vulnerability checks run in GitHub Actions.

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

For isolated verification:

```bash
make compose-demo
make compose-api-smoke
```

`compose-demo` creates `.local/input.db` and JSON/CSV reports. `compose-api-smoke` builds the same image, starts the healthchecked API on localhost, verifies `/v1/report`, and checks metrics.

## Run the CLI

Create sample data:

```bash
mkdir -p .local
python examples/create_sample_db.py .local/input.db
```

Generate a report:

```bash
data-query --input .local/input.db --output .local/report.json
```

Use filters and bounded advanced analytics:

```bash
data-query \
  --input .local/input.db \
  --output .local/north.json \
  --region north \
  --cohort-periods 12 \
  --product-limit 20
```

Compare an inclusive period with the immediately preceding equal-length period:

```bash
data-query \
  --input .local/input.db \
  --output .local/feb-comparison.json \
  --start-date 2026-02-01 \
  --end-date 2026-02-28 \
  --compare-period
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

## Run the optional HTTP API

The API reads only databases located beneath `DATA_QUERY_DATA_ROOT`. For local use:

```bash
DATA_QUERY_DATA_ROOT="$PWD/.local" \
DATA_QUERY_HOST=127.0.0.1 \
DATA_QUERY_PORT=8000 \
data-query-api
```

Health:

```bash
curl http://127.0.0.1:8000/healthz
```

Analytics:

```bash
curl 'http://127.0.0.1:8000/v1/report?database=input.db&region=north&product_limit=2'
```

Metrics:

```bash
curl http://127.0.0.1:8000/metrics
```

The `database` query value is resolved relative to the configured data root. Absolute/traversal access outside that sandbox is rejected. Input/schema failures return HTTP 422; unexpected SQLite execution failures return a sanitized HTTP 500 envelope.

## Advanced analytics

### Cohort retention

Cohort identity is the month of each eligible customer's first completed order. `cohort_periods` is bounded to `1..24`; report date filters constrain observed activity without rewriting historical cohort identity.

### Equal-length period comparison

`compare_period` requires both start and end dates. Percentage changes are `null` when the previous baseline is zero.

### Product concentration

Product analytics rank completed-order revenue and report units, completed-order count, revenue share, cumulative share, top-product share, and the minimum number of products needed to reach at least 80% of scoped revenue. `product_limit` is bounded to `1..100` and truncates returned product rows only after full-population metrics are calculated.

## Input contract

Required SQLite columns:

```text
customers(id, name, region)
orders(id, customer_id, order_date, status)
order_items(order_id, product, quantity, unit_price)
```

Validation rejects missing schema, malformed dates, negative/non-numeric quantity or price values, orphan relationships, corrupted databases, and unsafe paths. SQL values are bound parameters rather than interpolated strings.

## Report contract

JSON reports use an independent `schema_version`. Version 4 contains `summary`, `top_customers`, `monthly_revenue`, `cohort_retention`, `product_concentration`, `period_comparison`, and validated filter metadata. CLI and API return the same report model.

## Structured logging

`--log-format json` emits a versioned one-line JSON contract. `JSON_LOG_SCHEMA` version 1 defines common fields (`schema_version`, `level`, `logger`, `message`, `event`) and event-specific path/error requirements. Tests exercise actual success, validate-only, input-failure, and query-failure CLI paths.

## Quality and security checks

```bash
make test
make coverage
make lint
make typecheck
make quality
uv lock --check
uv sync --frozen
python scripts/check_dependency_freshness.py
make security
make package-check
make compose-config
make compose-demo
make compose-api-smoke
```

CI executes Python 3.11 and 3.12 tests, strict typing, lint, frozen runtime sync, wheel installation, CLI/API import checks, Docker tests, real containerized health/report/metrics smoke tests, dependency auditing, Gitleaks, and CodeQL.

## Project structure

```text
src/data_query/api.py              optional FastAPI service, sandbox and metrics
src/data_query/cli.py              primary command-line interface
src/data_query/errors.py           application exception hierarchy
src/data_query/schemas.py          declarative configuration validation
src/data_query/models.py           typed report/configuration models
src/data_query/validation.py       hardened SQLite/schema/data validation
src/data_query/reporting.py        report orchestration
src/data_query/products.py         Pareto/product concentration analytics
src/data_query/comparison.py       equal-length period comparison
src/data_query/writers.py          atomic JSON/CSV output
src/data_query/path_safety.py      CLI output collision checks
src/data_query/logging_utils.py    versioned structured logging
THREAT_MODEL.md                    security boundaries and residual risks
docs/architecture.md              architecture and interface design
docker-compose.yml                 CLI and localhost API verification
project-metadata.json              machine-readable application metadata
pyproject.toml                     package/runtime/quality configuration
requirements.txt                   direct runtime pins
uv.lock                            generated transitive runtime lock
requirements-dev.txt               development/security pins
```

## Classification

The optional HTTP service changes the application from CLI-only to a multi-interface application; it does **not** turn the repository into infrastructure-as-code. No Terraform, Kubernetes, Helm, Pulumi, Ansible, CloudFormation, or remote infrastructure state is present. See [CLASSIFICATION.md](CLASSIFICATION.md).

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep each behavior/fix focused and pair it with tests. Authorship and timestamps must reflect real contributors and real development sessions.
