# Threat Model

This document describes security boundaries for Data Query, a read-only SQLite analytics application with a primary CLI and an optional HTTP API. The application does not provision infrastructure.

## Assets

- source SQLite databases, which analytics must never modify;
- generated JSON/CSV reports;
- API responses derived from validated analytics;
- caller-selected filesystem paths and configured API data roots;
- operational logs and aggregate service metrics;
- the Python dependency/build graph.

## Attacker capabilities considered

An untrusted caller may control CLI arguments, HTTP query parameters, requested database names, input/output paths, and all database rows/schema contents. A malicious database may contain malformed values, confusing schema objects, URI-reserved filename characters, or values intended to alter SQL semantics.

The model does not assume protection against a fully compromised host, malicious interpreter/kernel, or hostile deployment platform.

## Threats and mitigations

### Source database mutation

**Threat:** analytics changes a source database.

**Mitigations:** `connect_read_only()` uses SQLite URI `mode=ro`, enables `PRAGMA query_only = ON`, and tests verify writes fail. The API reuses this same connection path. CLI output collision checks prevent report destinations from resolving to the input database.

### HTTP filesystem traversal

**Threat:** an API caller uses `database=../...` or another crafted path to read a file outside the allowed database directory.

**Mitigations:** `api.py` resolves both `DATA_QUERY_DATA_ROOT` and the requested candidate path, then requires the candidate to remain relative to the resolved root. Traversal/outside-root requests raise `InputError` and return HTTP 422. Compose mounts the API's `/data` directory read-only.

### SQL injection through filters

**Threat:** region/date/numeric values change SQL structure.

**Mitigations:** analytics use static SQL with SQLite bound parameters. `ReportFilters` validates semantic constraints and FastAPI validates HTTP query bounds before the report pipeline runs.

### Malicious or confusing SQLite schema/data

**Threat:** malformed schema, relationships, dates, or negative/non-numeric monetary values produce unsafe or misleading output.

**Mitigations:** `validate_schema()` and `validate_data()` run before report construction for both CLI and API interfaces. The connection disables trusted-schema behavior and enforces integrity checks.

### Corrupted database input

**Threat:** corrupted SQLite data causes undefined behavior.

**Mitigations:** opened databases must pass `PRAGMA quick_check`; unreadable/invalid input is converted to stable `InputError` behavior.

### API error disclosure

**Threat:** raw SQLite exceptions reveal internal database or filesystem details.

**Mitigations:** expected input errors use a stable HTTP 422 envelope. Unexpected `sqlite3.Error` failures map to a sanitized HTTP 500 message rather than returning the raw exception text.

### Resource exhaustion

**Threat:** expensive analytics or excessive HTTP requests consume CPU/memory/I/O.

**Mitigations:** `top_limit` and `product_limit` are bounded to 1..100, `cohort_periods` to 1..24, SQLite has a finite busy timeout, and API database selection cannot recursively access arbitrary filesystem trees. Very large valid databases or high request concurrency remain documented residual risks; deployment-level rate limiting/process limits are outside this repository.

### Output overwrite/path collision

**Threat:** CLI output destinations alias the source database or one another.

**Mitigations:** `path_safety.py` normalizes destinations and rejects collisions before report execution; writers use temporary files and atomic replacement.

### Sensitive data leakage through logs/metrics

**Threat:** diagnostics expose report rows or database contents.

**Mitigations:** structured logs contain event metadata, selected paths, severity, and error class—not report row payloads. `JSON_LOG_SCHEMA` defines the stable field contract. `/metrics` exports aggregate integer counters only, not query values, filenames, report contents, or customer/product data.

### Network exposure

**Threat:** the optional API is exposed beyond the intended host boundary.

**Mitigations:** bind host/port are explicit environment settings. The repository's Compose verification binds only `127.0.0.1:8000`. Operators choosing a broader bind are responsible for network controls/authentication appropriate to their environment. This repository does not provision firewalls, TLS termination, or cloud networking.

### Dependency and repository supply chain

**Threat:** vulnerable or unexpectedly changed dependencies alter behavior.

**Mitigations:** FastAPI, Pydantic, and Uvicorn are exactly pinned; `uv.lock` captures the transitive runtime graph; CI verifies frozen lock consistency and runs dependency audit, freshness checks, CodeQL, and Gitleaks. Development/security tools are also pinned.

## Analytics invariants

Cohort identity uses each eligible customer's first completed order. Date filters restrict observed cohort activity without rewriting history. Period comparison uses an immediately preceding equal-length window and returns `null` for zero baselines. Product concentration computes full-population shares before applying the bounded output limit.

## Residual risks

- Very large valid SQLite files can consume substantial CPU, memory, and disk I/O.
- A public-facing deployment requires authentication, rate limiting, TLS, and network policy appropriate to its environment; those deployment controls are not provisioned here.
- Read-only application behavior cannot prevent another process from modifying the database concurrently.
- Security ultimately depends on the host Python/SQLite/runtime and filesystem permission model.
- In-process metrics reset on process restart and are not a durable monitoring system.

## Security regression evidence

Tests cover read-only SQLite behavior, URI-reserved filenames, SQL metacharacters as literal values, CLI path collisions, malformed relational data, bounded schemas, cohort/product limits, period-comparison requirements, API traversal rejection, HTTP input mapping, health/metrics behavior, and Python 3.11/3.12 response-model compatibility. CI additionally runs strict typing, coverage, containerized API health/report/metrics smoke tests, dependency audits, Gitleaks, and CodeQL.
