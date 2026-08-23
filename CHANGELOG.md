# Changelog

All notable changes to this project are documented here.

## [0.2.0] - 2026-08-23

### Added
- Conventional `src/data_query` Python package and CLI entry point.
- Region, date-range, and top-customer filters.
- Optional CSV exports for customer and monthly aggregates.
- Data-integrity validation for dates, monetary values, and relational references.
- Root-level test suite with coverage enforcement.
- Ruff, mypy, dependency-audit, secret-scan, and dependency-update configuration.

### Changed
- `task/solution/solve.py` is now a compatibility wrapper around the packaged CLI.
- Project classification is explicitly documented as a Python data utility rather than IaC.
