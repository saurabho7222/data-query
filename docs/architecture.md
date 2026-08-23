# Architecture

Data Query is a local Python command-line application. It reads an existing SQLite database, validates it, runs deterministic analytics, and writes JSON/CSV outputs. It does not provision infrastructure or run a network service.

## Data flow

1. `cli.py` parses command-line arguments and delegates filter validation to `schemas.py`.
2. `schemas.py` validates region, dates, date ordering, and `top_limit` as a single declarative configuration boundary.
3. `path_safety.py` normalizes input/output paths and prevents collisions with the source database or between outputs.
4. `validation.py` opens SQLite in read-only mode, enables defensive connection settings, runs `PRAGMA quick_check`, validates the required schema, and checks row integrity.
5. `reporting.py` executes static SQL statements with bound parameters and builds typed report dictionaries.
6. `writers.py` writes JSON and optional CSV files through temporary files followed by atomic replacement.
7. `logging_utils.py` emits text or structured JSON operational events without changing report output.

## Trust boundaries

User-controlled CLI values enter through `ReportFilters` in `schemas.py`. Region labels are bounded, trimmed, and checked for control characters; dates must parse as ISO dates; `top_limit` is constrained to 1..100; and reversed date ranges are rejected. `input_validation.py` is a small adapter used by `argparse`, not a second validation implementation.

SQLite data is untrusted input as well. `validation.py` verifies table/column presence, date format, non-negative numeric values, and relationship integrity before analytics run. Query values are passed through SQLite parameter binding rather than interpolated into SQL strings.

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

The runtime dependency is pinned in `pyproject.toml` and its full graph is generated in `uv.lock`. CI verifies the lock with `uv lock --check`, installs it with `uv sync --frozen`, runs Ruff, strict mypy, the Python 3.11/3.12 test matrix with coverage, wheel installation, Docker/Compose execution, dependency auditing, secret scanning, and CodeQL.

The project is intentionally a CLI application rather than a service, so service-only concerns such as HTTP health endpoints, distributed tracing, autoscaling, and remote state are out of scope.
