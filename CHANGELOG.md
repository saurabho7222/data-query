# Changelog

All notable changes to this project are documented here.

## Unreleased

No unreleased user-visible changes.

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
- Architecture documentation for cohort semantics, period-comparison invariants, product concentration, and the non-service purpose of Docker/Compose/Dev Container tooling.

### Changed
- JSON report schema advanced to version 4 with `cohort_retention`, `period_comparison`, `product_concentration`, `cohort_periods`, `product_limit`, and `compare_period` fields.
- Root `requirements.txt` now mirrors the canonical pinned runtime dependency from `pyproject.toml`; repository contract tests also verify key transitive packages are present in `uv.lock`.
- CLI description and README now document advanced analytics behavior and report contracts.
- Repository classification guidance explicitly tells automated classifiers not to infer infrastructure/service status from local verification containers.

### Verification
- Cohort retention was introduced with a contract-first `test:` commit followed by a separate `feat:` implementation commit.
- Product concentration was introduced with a contract-first `test:` commit followed by a separate `feat:` implementation commit.
- Runtime-manifest consistency is protected by a focused repository contract test.
- Python 3.11/3.12 tests, strict mypy, Ruff, package verification, lock verification, Docker/Compose execution, dependency audits, Gitleaks, and CodeQL remain gating checks.

## [0.2.1] - 2026-08-23

### Added
- Machine-readable `project_type = "cli-application"` metadata in `pyproject.toml` plus `project-metadata.json` with explicit `infrastructure_as_code = false`.
- `docker-compose.yml` and `make compose-demo` for one-command isolated sample-database generation plus JSON/CSV report execution.
- A tested `.devcontainer/devcontainer.json` setup for reproducible editor/container onboarding.
- A canonical Pydantic `ReportFilters` schema in `src/data_query/schemas.py` covering region bounds, ISO dates, date ordering, and `top_limit` bounds.
- An application error hierarchy in `src/data_query/errors.py` while preserving the public `InputError` API.
- SQLite connection hardening with URI-safe filenames, read-only/query-only mode, `trusted_schema=OFF`, foreign keys, busy timeout, and `PRAGMA quick_check`.
- Architecture documentation covering data flow, trust boundaries, failure handling, and reproducibility.
- Runtime dependency freshness checks alongside development dependency checks, with CI artifact upload for the audit result.
- Locked-runtime CI verification using `uv lock --check` and `uv sync --frozen`.
- A tag/release workflow that verifies a built wheel in a clean environment before publishing a GitHub Release.

### Changed
- Runtime validation now uses the exactly pinned `pydantic==2.13.4` dependency; the full transitive graph is generated into `uv.lock`.
- Analytics SQL is now static query text with bound values instead of dynamically assembled filter SQL.
- SQLite schema inspection now uses a parameterized `pragma_table_info(?)` table-valued query.
- Dependency auditing now covers the locked runtime project and exactly pinned development tools.
- Refreshed pinned development tools to current verified releases: mypy 2.3.1, pip-audit 2.10.1, pytest 9.1.1, pytest-cov 7.1.0, and Ruff 0.16.4.
- Updated GitHub Actions generations to `actions/checkout@v7`, `actions/setup-python@v7`, `actions/upload-artifact@v7`, and `github/codeql-action@v4`.
- CI quality checks are exposed as explicit `lint`, `typecheck`, and matrixed `tests` jobs, plus package, dependency-lock, and Docker/Compose jobs.

### Security
- Added explicit tests proving SQL metacharacters in region values remain literal bound data.
- Added tests for read-only SQLite enforcement, defensive PRAGMAs, and URI-reserved database filenames.
- Dependency freshness evidence is retained as a workflow artifact on every Security run.

## [0.2.0] - 2026-08-23

### Added
- Conventional `src/data_query` installable Python package and `data-query` console entry point.
- Root-level discoverable test suite with coverage enforcement across Python 3.11 and 3.12.
- Region, inclusive date-range, and bounded top-customer filters.
- Optional CSV exports for customer and monthly aggregates.
- Explicit CLI value validators for region labels and numeric limits.
- Data-integrity validation for dates, monetary values, and relational references.
- Output-path collision protection so reports cannot overwrite the source database or each other.
- `--validate-only` database health-check mode that writes no artifacts.
- Human-readable and structured JSON logging with configurable log levels.
- Responsibility-based modules for models, validation, reporting, output writers, path safety, and logging.
- `uv.lock`, pinned development dependencies, and Dependabot configuration.
- Ruff linting, strict mypy checks, and a 90% minimum coverage gate.
- Clean wheel build/install verification and Docker build/test verification in CI.
- Dependency auditing, full-history Gitleaks scanning, and CodeQL static analysis.
- `CLASSIFICATION.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.env.example`, and reproducible Make targets.

### Changed
- Repository layout is a standalone Python application/data utility.
- Development dependency `pytest` was upgraded to a patched release.
- Project classification is explicitly documented as a Python data-processing CLI rather than infrastructure-as-code.

### Verification
- GitHub Actions validates linting, strict type checking, tests, coverage, wheel packaging, Docker execution, dependency auditing, secret scanning, and CodeQL analysis on pushes and pull requests.
