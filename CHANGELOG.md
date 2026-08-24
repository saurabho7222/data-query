# Changelog

All notable changes to this project are documented here.

## Unreleased

No unreleased user-visible changes.

## [0.4.0] - 2026-08-24

### Added
- Optional `data-query-api` FastAPI/Uvicorn service over the existing validated SQLite analytics engine.
- `/healthz` service identity/version endpoint and `/metrics` Prometheus-style aggregate counters.
- `/v1/report` HTTP analytics endpoint using the same report schema and validation pipeline as the CLI.
- API database-path sandboxing through `DATA_QUERY_DATA_ROOT`, rejecting traversal outside the configured root.
- Exact runtime pins for FastAPI, Pydantic, and Uvicorn with a regenerated transitive `uv.lock`.
- Scanner-visible multi-interface application metadata: primary CLI plus optional HTTP API, `service=true`, `infrastructure_as_code=false`.
- `JSON_LOG_SCHEMA` version 1 plus end-to-end CLI tests for success, validation, validate-only, and SQLite-failure events.
- Docker/Compose API service with localhost binding, read-only data mount, healthcheck, and a real health/report/metrics smoke target.

### Changed
- Project metadata now describes Data Query as an application rather than a CLI-only application while keeping the CLI as the primary interface.
- Docker exposes application port 8000 for the optional API; the default container command remains the CLI help command.
- CI verifies locked, installed, packaged, and containerized API behavior in addition to existing CLI checks.
- Shared report `TypedDict` models now use `typing_extensions.TypedDict` for Pydantic/FastAPI compatibility on Python 3.11 and 3.12.
- Documentation, classification guidance, architecture, and threat model now describe both interfaces without implying infrastructure provisioning.

### Security
- API database selection is restricted to a resolved configured data root.
- SQLite errors returned over HTTP are sanitized; expected input errors use a stable HTTP 422 envelope.
- Compose mounts API database data read-only and binds the verification service to `127.0.0.1`.
- Metrics expose aggregate counters only and do not contain report rows or query/database contents.

### Verification
- API behavior was introduced contract-first in `tests/test_api.py` before implementation.
- Python 3.11 CI identified a real Pydantic `TypedDict` compatibility issue; the focused compatibility fix preserves response-model validation rather than disabling it.
- CI now smoke-tests `/healthz`, `/v1/report`, and `/metrics` through the running container service.
- Frozen lock verification, Python 3.11/3.12 coverage tests, strict mypy, Ruff, packaging, dependency audits, Gitleaks, and CodeQL remain gating checks.

## [0.3.0] - 2026-08-24

### Added
- Monthly customer cohort-retention analytics based on each eligible customer's first completed order.
- A bounded `--cohort-periods` option (1..24) with declarative schema validation and deterministic retention rows.
- Opt-in `--compare-period` analytics that compare a complete date window with the immediately preceding equal-length window.
- Zero-baseline-safe percentage changes: comparison percentages are `null` when a previous metric is zero.
- Ranked product concentration analytics using SQLite CTEs/window functions for units, completed-order count, revenue share, cumulative revenue share, and Pareto-style 80% concentration.
- A bounded `--product-limit` option (1..100) that truncates ranked product rows without changing full-population concentration metrics.
- Dedicated `comparison.py` and `products.py` analytics engines so advanced calculations remain separate from aggregate report assembly.
- A formal `THREAT_MODEL.md` covering assets, attacker capabilities, SQLite/path/SQL/resource-exhaustion threats, mitigations, supply-chain controls, and residual risks.

### Changed
- JSON report schema advanced to version 4 with cohort, period-comparison, product-concentration, and bounded-filter fields.
- Root `requirements.txt` mirrors the canonical runtime dependency metadata for conventional scanners.

### Verification
- Cohort retention and product concentration were introduced with contract-first `test:` commits followed by separate `feat:` implementation commits.
- Python 3.11/3.12 tests, strict mypy, Ruff, package verification, lock verification, Docker/Compose execution, dependency audits, Gitleaks, and CodeQL remain gating checks.

## [0.2.1] - 2026-08-23

### Added
- Machine-readable application metadata and `project-metadata.json` with explicit `infrastructure_as_code = false`.
- `docker-compose.yml`, Dev Container configuration, declarative Pydantic filters, hardened SQLite connection settings, architecture docs, dependency freshness checks, and release automation.

### Changed
- Runtime validation uses exactly pinned Pydantic and a generated `uv.lock` graph.
- Analytics SQL uses static queries with bound values.
- CI exposes explicit lint, typecheck, matrixed tests, package, lock, and Docker/Compose jobs.

### Security
- Added SQL-metacharacter, read-only SQLite, defensive PRAGMA, and URI-reserved filename tests.

## [0.2.0] - 2026-08-23

### Added
- Conventional `src/data_query` installable package and `data-query` console entry point.
- Root pytest suite with coverage enforcement, filters, CSV exports, validation, collision protection, validate-only mode, structured logging, typed modules, `uv.lock`, pinned development dependencies, CI, dependency auditing, Gitleaks, and CodeQL.
