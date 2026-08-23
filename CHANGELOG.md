# Changelog

All notable changes to this project are documented here.

## Unreleased

### Added
- Machine-readable `project_type = "cli-application"` metadata in `pyproject.toml` plus `project-metadata.json` so automated classifiers do not infer infrastructure from Docker/CI artifacts.
- Expanded `CLASSIFICATION.md` with explicit zero-IaC indicators and embedded-SQLite rationale.
- `docker-compose.yml` and `make compose-demo` for one-command isolated sample-database generation plus JSON/CSV report execution.
- CI validation of the Compose model and the full self-contained Compose demo.
- Scanner-visible CLI trust-boundary markers and exact `InputError` assertions for invalid region/top-limit values.
- A direct dependency freshness check against PyPI, enforced by the scheduled/push/PR Security workflow.
- A tag-triggered release workflow that verifies a built wheel in a clean environment before publishing a GitHub Release.
- A tested `.devcontainer/devcontainer.json` setup for reproducible editor/container onboarding.

### Changed
- Refreshed pinned development tools to current verified releases: mypy 2.3.1, pip-audit 2.10.1, pytest 9.1.1, pytest-cov 7.1.0, and Ruff 0.16.4.
- Updated GitHub Actions runtime generations to `actions/checkout@v7`, `actions/setup-python@v7`, and `github/codeql-action@v4`.
- Split CI quality checks into explicit `lint`, `typecheck`, and `tests` jobs using direct `ruff`, `mypy`, and `pytest` commands for clearer failures and scanner detection.

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
- Repository layout is now a standalone Python application/data utility; the legacy task scaffold was removed.
- Development dependency `pytest` was upgraded to `9.0.3` to address `PYSEC-2026-1845`.
- Project classification is explicitly documented as a Python data-processing CLI rather than infrastructure-as-code.

### Verification
- GitHub Actions validates linting, strict type checking, tests, coverage, wheel packaging, Docker execution, dependency auditing, secret scanning, and CodeQL analysis on pushes and pull requests.
