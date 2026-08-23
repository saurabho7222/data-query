# Security Policy

## Supported version

Security fixes are applied to the current `main` branch.

## Reporting a vulnerability

Please do not publish sensitive vulnerability details in a public issue. Prefer GitHub's private vulnerability reporting or Security Advisory flow from the repository's **Security** tab when available.

For non-sensitive hardening ideas, a normal issue or pull request is appropriate.

## Automated checks

Every push and pull request runs:

- `pip-audit` against pinned development dependencies;
- Gitleaks against full repository history to detect accidental secrets;
- CodeQL static analysis for Python security and quality findings;
- Ruff, mypy, tests, and coverage in the main CI workflow;
- a clean wheel build/install smoke test and Docker verification.

Dependabot checks Python dependencies weekly and GitHub Actions monthly.
