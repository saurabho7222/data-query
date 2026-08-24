# Threat Model

This document describes the security boundaries for Data Query, a local read-only SQLite analytics CLI. The application does not expose a network service and does not provision infrastructure.

## Assets

- the source SQLite database, which must never be modified by analytics execution;
- generated JSON and CSV reports;
- filesystem paths selected by the caller;
- operational logs, which may reveal paths and error classes but should not contain row payloads;
- the Python dependency and build graph used to execute the CLI.

## Attacker capabilities considered

The model assumes an untrusted caller may control CLI arguments, input/output paths, SQLite filenames, and all database rows/schema content inside the supplied file. A malicious database may contain malformed values, unexpected schema objects, URI-reserved filename characters, or data intended to alter SQL semantics.

The model does not assume the process can defend a host that is already fully compromised. OS-level sandboxing, hostile kernel behavior, and malicious Python interpreters are outside application scope.

## Threats and mitigations

### Source database mutation

**Threat:** analytics accidentally or maliciously changes the input database.

**Mitigations:** `connect_read_only()` uses SQLite URI `mode=ro`, enables `PRAGMA query_only = ON`, and tests verify write statements fail. Output collision checks prevent report destinations from resolving to the input database path.

### SQL injection through filters

**Threat:** region names, date values, or numeric limits alter query structure.

**Mitigations:** analytics statements are static SQL; user-controlled values use SQLite parameter binding. `ReportFilters` validates region length/control characters, ISO dates, `top_limit`, and the bounded cohort horizon before execution.

### Malicious or confusing SQLite schema

**Threat:** unexpected schema objects, invalid relationships, malformed dates, or negative monetary values produce unsafe or misleading reports.

**Mitigations:** the connection disables trusted schema behavior, `validate_schema()` checks required tables/columns, and `validate_data()` checks row types, date format, non-negative monetary inputs, and relational integrity before analytics execute.

### Corrupted database input

**Threat:** a corrupted SQLite file causes undefined report behavior.

**Mitigations:** every opened database must pass `PRAGMA quick_check`; unreadable or invalid databases are converted to a stable `InputError` path.

### Resource exhaustion

**Threat:** caller-controlled analytics parameters cause excessive work or output growth.

**Mitigations:** `top_limit` is bounded to 1..100, `cohort_periods` is bounded to 1..24, SQLite uses a finite busy timeout, and the application performs no recursive network fetches. Very large valid databases can still consume significant CPU and are a documented residual risk.

### Output overwrite and path collision

**Threat:** multiple output destinations alias one another or overwrite the input database.

**Mitigations:** `path_safety.py` normalizes destinations and rejects collisions before the database is opened for reporting. Writers use temporary files followed by atomic replacement.

### Sensitive data leakage through logs

**Threat:** operational errors expose database row contents.

**Mitigations:** structured logs contain event names, severity, error class, and selected paths; report row payloads are not logged. Callers remain responsible for treating filesystem paths as potentially sensitive metadata.

### Dependency and repository supply chain

**Threat:** vulnerable or unexpectedly changed dependencies alter runtime behavior.

**Mitigations:** direct runtime dependencies are exactly pinned, `uv.lock` captures the transitive graph, CI runs frozen lock verification and `pip-audit`, Dependabot checks updates, CodeQL scans Python code, and Gitleaks scans repository history for accidental secrets.

## Advanced analytics invariants

Cohort membership is based on each eligible customer's first completed order. Date filters restrict observed activity but do not rewrite the historical cohort assignment. Period comparison is opt-in and requires a complete start/end window; the previous window has exactly the same number of calendar days and immediately precedes the current window. Percent changes return `null` when the previous baseline is zero rather than reporting an infinite or misleading percentage.

## Residual risks

- Very large but valid SQLite files can consume substantial CPU, memory, and disk I/O.
- Security ultimately depends on the SQLite and Python runtimes supplied by the host environment.
- Atomic replacement reduces partial-output risk but is not a substitute for a host filesystem permission model.
- Read-only application behavior does not prevent another process from modifying the database concurrently; callers should provide stable inputs when deterministic results matter.

## Security regression evidence

Security-sensitive behavior is covered by tests for read-only SQLite invariants, URI-reserved filenames, SQL metacharacters as literal data, path collisions, malformed relational data, bounded schemas, cohort horizon validation, and period-comparison date-window requirements. CI additionally gates dependency audit, secret scanning, static analysis, linting, strict typing, package installation, and containerized execution.
