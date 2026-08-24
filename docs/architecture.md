# Architecture

Data Query is a typed Python analytics application with two interfaces over one SQLite analytics engine: a primary command-line interface and an optional HTTP API. Neither interface provisions infrastructure. Both validate caller-controlled inputs before running read-only analytics.

## Component boundaries

1. `cli.py` parses command-line arguments and delegates filter validation to `schemas.py`.
2. `api.py` exposes `/healthz`, `/metrics`, and `/v1/report`, validates HTTP query bounds, sandboxes database paths to a configured data root, and delegates analytics to the same core pipeline as the CLI.
3. `schemas.py` is the canonical Pydantic configuration boundary for region, dates, date ordering, `top_limit`, `cohort_periods`, `product_limit`, and comparison preconditions.
4. `path_safety.py` normalizes CLI output paths and prevents collisions with the input database or between outputs.
5. `validation.py` opens SQLite read-only, enables defensive settings, runs `PRAGMA quick_check`, validates schema, and checks row integrity.
6. `reporting.py` orchestrates deterministic summary, customer, monthly, cohort, product, and period analytics.
7. `products.py` uses CTEs and SQLite window functions for product revenue distribution and Pareto concentration.
8. `comparison.py` derives equal-length comparison windows without dynamic SQL.
9. `writers.py` atomically writes JSON and optional CSV outputs for CLI runs.
10. `logging_utils.py` emits human-readable logs or versioned structured JSON logs.

## Shared analytics pipeline

The HTTP API does not maintain a second query engine. `/v1/report` resolves a database below `DATA_QUERY_DATA_ROOT` and executes the same sequence used by the library/CLI core:

```text
connect_read_only
  -> validate_schema
  -> validate_data
  -> build_report
```

This keeps report schema version 4, filters, ordering, security checks, and analytical semantics identical across interfaces.

## HTTP service

The optional `data-query-api` entry point runs FastAPI/Uvicorn. Configuration is explicit:

- `DATA_QUERY_DATA_ROOT` selects the filesystem sandbox containing readable SQLite inputs;
- `DATA_QUERY_HOST` controls the bind address;
- `DATA_QUERY_PORT` is validated to `1..65535`;
- `/healthz` reports service identity/version;
- `/metrics` exposes in-process Prometheus-style counters;
- `/v1/report` returns the versioned analytics report.

Compose binds the development/smoke-test service to `127.0.0.1:8000` and mounts `/data` read-only. Production deployment topology is deliberately outside this repository; the application does not create load balancers, cloud networks, orchestration resources, or remote infrastructure state.

## Observability

`ServiceMetrics` maintains lock-protected counters for HTTP requests, report attempts, successful reports, input failures, and SQLite failures. Metrics contain aggregate counts only; report rows and database contents are not exported.

CLI JSON logs follow `JSON_LOG_SCHEMA` version 1. Every structured event includes `schema_version`, `level`, `logger`, `message`, and `event`; event-specific fields cover input/output paths and error classes. Tests call real `cli.main()` paths to protect that contract.

## Advanced analytics

### Cohort retention

Cohort identity is each eligible customer's first completed-order month. Date filters constrain observed activity without rewriting historical cohort assignment. `cohort_periods` is bounded to `1..24`.

### Equal-length period comparison

`compare_period` requires both dates and compares the selected inclusive window with the immediately preceding equal-length window. A zero previous baseline yields `null` percentage change rather than infinity.

### Product concentration

`products.py` ranks completed-order product revenue with SQLite window functions, computes per-product and cumulative revenue share, and reports the minimum product count required to reach at least 80% of scoped revenue. `product_limit` is bounded to `1..100` and truncates returned rows only after full-population concentration metrics are calculated.

## Trust boundaries

CLI and API values converge on `ReportFilters`. Region names are bounded and reject control characters; numeric limits are bounded; dates must parse correctly; reversed ranges and incomplete comparison windows are rejected.

The HTTP `database` parameter is a relative selection beneath a configured data root. `api.py` resolves both root and candidate paths and rejects candidates that escape the root, including `..` traversal. The API never accepts an arbitrary host filesystem path.

SQLite contents are untrusted. `validation.py` checks required schema, date shape, non-negative numeric values, and relationship integrity before analytics. Query values use SQLite parameter binding, not string interpolation.

## SQLite connection invariants

`connect_read_only()` uses a percent-encoded file URI with `mode=ro` and enforces:

- `PRAGMA query_only = ON`
- `PRAGMA trusted_schema = OFF`
- `PRAGMA foreign_keys = ON`
- a finite busy timeout
- `PRAGMA quick_check`

Connections close on success and failure paths, and tests verify URI-reserved filenames and failed write attempts.

## Failure model

CLI expected input/configuration failures use `InputError` and exit code 2; unexpected SQLite execution failures use exit code 3. The API maps `InputError` to HTTP 422 with a stable error envelope and maps SQLite execution errors to a sanitized HTTP 500 response that does not return raw database details. FastAPI itself returns 422 for query-schema violations.

## Dependencies and reproducibility

Direct runtime dependencies are exactly pinned and mirrored across `pyproject.toml`, `requirements.txt`, and `project-metadata.json`: FastAPI, Pydantic, and Uvicorn. `uv.lock` contains the generated transitive runtime graph, including Starlette and supporting packages. CI enforces `uv lock --check` and `uv sync --frozen`.

The CI matrix runs Python 3.11 and 3.12 coverage-gated tests, Ruff, strict mypy, package installation, locked-runtime CLI/API imports, Docker tests, Compose CLI execution, containerized API health/report/metrics smoke tests, dependency audits, secret scanning, and CodeQL.

## Why container tooling is not IaC

Docker, Compose, and the Dev Container provide reproducible execution environments for the application. The optional API service means Compose now has a localhost application port and healthcheck, but those artifacts still do not provision infrastructure. There is no Terraform/Kubernetes/Helm/Pulumi/Ansible/CloudFormation or remote infrastructure state in the repository.
