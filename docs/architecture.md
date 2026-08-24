# Architecture

Data Query is a local Python command-line application. It reads an existing SQLite database, validates it, runs deterministic analytics, and writes JSON/CSV outputs. It does not provision infrastructure or run a network service.

## Data flow

1. `cli.py` parses command-line arguments and delegates filter validation to `schemas.py`.
2. `schemas.py` validates region, dates, date ordering, `top_limit`, the cohort horizon, `product_limit`, and period-comparison preconditions as a single declarative configuration boundary.
3. `path_safety.py` normalizes input/output paths and prevents collisions with the source database or between outputs.
4. `validation.py` opens SQLite in read-only mode, enables defensive connection settings, runs `PRAGMA quick_check`, validates the required schema, and checks row integrity.
5. `reporting.py` executes static parameterized SQL for summary, top-customer, monthly-revenue, and cohort-retention analytics and assembles the versioned report.
6. `products.py` uses CTEs and SQLite window functions to rank product revenue, compute per-product/cumulative revenue share, and derive Pareto concentration metrics.
7. `comparison.py` derives an equal-length previous date window and computes current/previous completed-order and revenue metrics without dynamic SQL.
8. `writers.py` writes JSON and optional CSV files through temporary files followed by atomic replacement.
9. `logging_utils.py` emits text or structured JSON operational events without changing report output.

## Advanced analytics

### Cohort retention

Cohort assignment is based on each eligible customer's first completed order month. The output contains `(cohort_month, period)` rows with cohort size, retained customer count, and retention percentage. The caller controls the horizon through `cohort_periods`, bounded to 1..24 so the query and output cannot grow without limit.

Report date filters constrain observed activity, not the historical first-completed-order month. This preserves stable cohort identity when a caller narrows the report window.

### Equal-length period comparison

`--compare-period` is opt-in and requires both `--start-date` and `--end-date`. `comparison.py` computes an immediately preceding window with exactly the same inclusive day count. Both windows use the same region scope. Percentage change is `null` when the previous baseline is zero instead of manufacturing an infinite percentage.

### Product concentration

`products.py` aggregates completed-order revenue by product, then applies SQLite window functions over the complete scoped product population. Each product receives a deterministic revenue rank, revenue share, and cumulative revenue share. The report also exposes the top product's share and the minimum number of ranked products required to reach at least 80% of scoped revenue.

`product_limit` is bounded to 1..100 and controls only how many ranked product rows are returned. `total_products`, `products_to_80_pct`, and `top_product_share_pct` are calculated from the complete scoped product set before output truncation, so reducing the display limit cannot change the concentration summary. Region and date filters apply to product activity before ranking.

## Trust boundaries

User-controlled CLI values enter through `ReportFilters` in `schemas.py`. Region labels are bounded, trimmed, and checked for control characters; dates must parse as ISO dates; `top_limit` and `product_limit` are constrained to 1..100; `cohort_periods` is constrained to 1..24; reversed date ranges are rejected; and comparison mode requires a complete date window. `input_validation.py` is a small adapter used by `argparse`, not a second validation implementation.

SQLite data is untrusted input as well. `validation.py` verifies table/column presence, date format, non-negative numeric values, and relationship integrity before analytics run. Query values are passed through SQLite parameter binding rather than interpolated into SQL strings. Advanced analytics use static SQL, including the product window-function query. See [THREAT_MODEL.md](../THREAT_MODEL.md) for the full asset/threat/mitigation model and residual risks.

## SQLite connection invariants

`connect_read_only()` uses a percent-encoded file URI with `mode=ro`, then enforces:

- `PRAGMA query_only = ON`
- `PRAGMA trusted_schema = OFF`
- `PRAGMA foreign_keys = ON`
- a 5-second busy timeout
- `PRAGMA quick_check` before the connection is returned

The connection is closed on validation/setup failures. Tests also verify filenames containing URI-reserved characters and confirm write statements fail.

## Failure model

Expected input/configuration failures use `InputError` and produce CLI exit code 2. Unexpected SQLite execution failures produce exit code 3. Successful validation/report execution returns 0. Structured logs include stable event names for validation failures, query failures, database validation, and report completion.

## Reproducibility and verification

The direct runtime dependency is declared consistently in `pyproject.toml`, `requirements.txt`, and `project-metadata.json`; the complete runtime graph is generated in `uv.lock`. A repository contract test verifies those manifests agree and that the expected Pydantic transitive packages are present. CI verifies the lock with `uv lock --check`, installs it with `uv sync --frozen`, runs Ruff, strict mypy, the Python 3.11/3.12 test matrix with coverage, wheel installation, Docker/Compose execution, dependency auditing, secret scanning, and CodeQL.

## Why container tooling exists in a non-service project

The `Dockerfile`, `docker-compose.yml`, and `.devcontainer/` files are reproducible development and verification environments for this local CLI. Compose builds the same application image and runs an isolated demo/test flow; it does not expose ports, create a long-running service, provision cloud resources, or represent infrastructure-as-code. The Dev Container gives contributors a repeatable editor/runtime environment. These artifacts must not be used as evidence that the repository is an infrastructure or backend-service project.

The project is intentionally a CLI application rather than a service, so service-only concerns such as HTTP health endpoints, distributed tracing, autoscaling, deployment stages, and remote infrastructure state are out of scope.
