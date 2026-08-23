# Data Query

[![CI](https://github.com/saurabho7222/data-query/actions/workflows/ci.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/ci.yml)
[![Security](https://github.com/saurabho7222/data-query/actions/workflows/security.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/security.yml)
[![CodeQL](https://github.com/saurabho7222/data-query/actions/workflows/codeql.yml/badge.svg)](https://github.com/saurabho7222/data-query/actions/workflows/codeql.yml)

A typed Python data-processing CLI application that validates a SQLite sales database and produces deterministic analytics in JSON, with optional CSV exports.

> **Project type:** `cli-application`. This is **not infrastructure-as-code**. The canonical machine-readable marker lives in `[tool.data-query]` in `pyproject.toml` and is mirrored in `project-metadata.json`; `infrastructure_as_code = false`. See [CLASSIFICATION.md](CLASSIFICATION.md#why-this-is-not-infrastructure) for the explicit rationale and zero-IaC indicators.

## Features

- read-only SQLite access with schema and data-integrity validation;
- overall customer/order/revenue metrics;
- top customers by completed-order revenue;
- monthly completed revenue;
- optional customer-region and inclusive date-range filters;
- configurable top-customer limit with explicit trust-boundary validation;
- deterministic JSON plus optional customer/monthly CSV exports;
- atomic output writes and path-collision protection;
- validate-only database health checks that write no artifacts;
- human-readable or structured JSON logging;
- conventional `src/` package and root `tests/` suite;
- one-command self-contained Docker Compose demo;
- wheel build/install verification in a clean virtual environment;
- coverage, lint, strict type-check, dependency-audit, dependency-freshness, secret-scan, CodeQL, Docker, and CI gates.

## Requirements

- Python 3.11+
- `pip`
- Docker with the Compose plugin (optional; used for isolated verification)

The application runtime uses only the Python standard library. `uv.lock` records the dependency-free runtime package graph in a standard lockfile. Development and verification tools are exactly pinned in `requirements-dev.txt`, checked against PyPI by `scripts/check_dependency_freshness.py`, and kept current by Dependabot.

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

`make quality` runs linting, strict static type checking, and the coverage-gated test suite. The same checks run in GitHub Actions on every push and pull request.

## One-command isolated run

To build the image, generate a sample SQLite database, run the CLI, and produce JSON plus both CSV exports without installing Python locally:

```bash
make compose-demo
```

The command writes `.local/input.db`, `.local/report.json`, `.local/customers.csv`, and `.local/monthly.csv`. The Compose model has only two short-lived application jobs: `sample-db` creates the embedded SQLite fixture and `report` runs after it completes successfully. No database server, cloud account, network service, or sibling repository is required.

## Run the CLI

Create a sample database:

```bash
python examples/create_sample_db.py .local/input.db
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

Validate the database without writing report files:

```bash
data-query --input .local/input.db --validate-only --log-level INFO
```

Emit machine-readable logs for automation:

```bash
data-query \
  --input .local/input.db \
  --output .local/report.json \
  --log-level INFO \
  --log-format json
```

## Input contract

The SQLite database must contain:

```text
customers(id, name, region)
orders(id, customer_id, order_date, status)
order_items(order_id, product, quantity, unit_price)
```

Validation rejects missing tables/columns, invalid `YYYY-MM-DD` order dates, negative/non-numeric quantity or price values, orders without customers, and order items without orders. CLI filter values are explicitly validated before query execution. Only `orders.status = 'completed'` contributes to revenue.

Output paths are normalized before execution. A report or CSV export cannot overwrite the input database, and two output options cannot target the same file.

## Tests and quality gates

```bash
make test                         # behavioral/unit suite
make coverage                     # >= 90% required
make lint                         # Ruff
make typecheck                    # mypy strict mode
make quality                      # lint + typecheck + coverage
make security                     # dependency vulnerability audit
python scripts/check_dependency_freshness.py  # exact direct-pin freshness
make package-check                # wheel build + clean-venv install + CLI smoke test
make compose-config               # validate Compose model
make compose-demo                 # build + isolated end-to-end run
```

The test suite lives under the conventional root `tests/` directory so standard Python tooling and repository analyzers can discover it without project-specific knowledge.

## Docker

Build and test the same environment CI uses:

```bash
docker build -t data-query .
docker run --rm data-query python3 -m pytest tests -v
```

Or use the self-contained Compose workflow:

```bash
make compose-demo
```

SQLite is embedded, so Compose does not provision external infrastructure. It exists only to make the complete application exercise reproducible with one command in an isolated container environment.

## Project structure

```text
src/data_query/                   application package and CLI
src/data_query/models.py          typed public configuration/report models
src/data_query/validation.py      SQLite schema and row-integrity checks
src/data_query/reporting.py       SQL aggregation logic
src/data_query/writers.py         atomic JSON/CSV output writers
src/data_query/path_safety.py     output collision protection
src/data_query/logging_utils.py   structured logging support
src/data_query/input_validation.py explicit CLI trust-boundary validation
examples/                         runnable sample database generator
scripts/                          maintenance/freshness checks
tests/                            discoverable behavioral/unit tests
compose.yaml                      one-command isolated end-to-end execution
project-metadata.json             machine-readable application classification
.github/workflows/ci.yml          lint, type, coverage, package, Docker/Compose gates
.github/workflows/security.yml    dependency audit/freshness and secret scanning
.github/workflows/codeql.yml      CodeQL static analysis
.github/dependabot.yml            pip + GitHub Actions update automation
pyproject.toml                    package metadata, project type, quality config
uv.lock                           runtime dependency lock
requirements-dev.txt              exact development/security tool pins
```

## Development

See `CONTRIBUTING.md`. Keep each feature or fix in a focused commit with the tests that demonstrate the new behavior. `CHANGELOG.md` records user-visible changes. Genuine maintenance history should grow through real development sessions; contributor identity and timestamps must not be fabricated.
