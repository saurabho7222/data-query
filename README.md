# Data Query

[![CI](https://github.com/saurabho7222/data-query/actions/workflows/ci.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/ci.yml)
[![Security](https://github.com/saurabho7222/data-query/actions/workflows/security.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/security.yml)

A typed Python data-utility CLI that validates a SQLite sales database and produces deterministic analytics in JSON, with optional CSV exports.

> **Classification:** application / data-processing utility / CLI. This is **not infrastructure-as-code**; Docker and GitHub Actions are only used to package and verify the application. See `CLASSIFICATION.md`.

## Features

- read-only SQLite access with schema and data-integrity validation;
- overall customer/order/revenue metrics;
- top customers by completed-order revenue;
- monthly completed revenue;
- optional customer-region and inclusive date-range filters;
- configurable top-customer limit;
- deterministic JSON plus optional customer/monthly CSV exports;
- atomic output writes so failed runs do not leave partial reports;
- conventional `src/` package and root `tests/` suite;
- coverage, lint, type-check, dependency-audit, secret-scan, Docker, and CI gates.

## Requirements

- Python 3.11+
- `pip`
- Docker (optional)

The application runtime uses only the Python standard library. `uv.lock` records the dependency-free runtime package graph in a standard lockfile. Development and verification tools are pinned in `requirements-dev.txt` and kept current by Dependabot.

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

`make quality` runs linting, static type checking, and the coverage-gated test suite. The same checks run in GitHub Actions on every push and pull request.

## Run the CLI

Create a sample database:

```bash
python task/examples/create_sample_db.py .local/input.db
```

Generate the default JSON report:

```bash
data-query --input .local/input.db --output .local/report.json
```

Filter to the north region and February 2026:

```bash
data-query \
  --input .local/input.db \
  --output .local/north-feb.json \
  --region north \
  --start-date 2026-02-01 \
  --end-date 2026-02-28 \
  --top-limit 3
```

Export CSV views alongside JSON:

```bash
data-query \
  --input .local/input.db \
  --output .local/report.json \
  --customers-csv .local/customers.csv \
  --monthly-csv .local/monthly.csv
```

The compatibility wrapper remains available:

```bash
INPUT_DB=.local/input.db OUTPUT_JSON=.local/report.json sh task/solution/solve.sh
```

## Input contract

The SQLite database must contain:

```text
customers(id, name, region)
orders(id, customer_id, order_date, status)
order_items(order_id, product, quantity, unit_price)
```

Validation rejects missing tables/columns, invalid `YYYY-MM-DD` order dates, negative/non-numeric quantity or price values, orders without customers, and order items without orders. Only `orders.status = 'completed'` contributes to revenue.

## Tests and quality gates

```bash
make test       # behavioral/unit suite
make coverage   # >= 90% required
make lint       # Ruff
make typecheck  # mypy strict mode
make quality    # lint + typecheck + coverage
make security   # dependency audit
```

The test suite is intentionally under the conventional root `tests/` directory so standard Python tooling and repository analyzers can discover it without custom knowledge of the compatibility `task/` layout.

## Docker

Build and test the same environment CI uses:

```bash
docker build -t data-query .
docker run --rm data-query sh task/tests/test.sh
```

Run the CLI with mounted SQLite data:

```bash
mkdir -p .local
python task/examples/create_sample_db.py .local/input.db
docker run --rm \
  -v "$PWD/.local:/data" \
  data-query \
  python3 -m data_query --input /data/input.db --output /data/output.json
```

SQLite is embedded, so no database server or sibling service is required; a Compose stack would add complexity without improving reproducibility.

## Project structure

```text
src/data_query/                 application package and CLI
tests/                          discoverable behavioral/unit tests
task/solution/                  compatibility entry points
task/examples/                  sample database generator
task/tests/test.sh              compatibility test command
.github/workflows/ci.yml        lint, type, coverage, Docker gates
.github/workflows/security.yml  dependency and secret scanning
.github/dependabot.yml          dependency update automation
pyproject.toml                  package + Ruff/mypy/pytest/coverage config
uv.lock                         runtime dependency lock
requirements-dev.txt            pinned development/security tools
```

## Development

See `CONTRIBUTING.md`. Keep each feature or fix in a focused commit with the tests that demonstrate the new behavior. `CHANGELOG.md` records user-visible changes.
