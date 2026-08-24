# Security Policy

## Supported version

Security fixes are applied to the current `main` branch.

## Reporting a vulnerability

Please do not publish sensitive vulnerability details in a public issue. Prefer GitHub's private vulnerability reporting or Security Advisory flow from the repository's **Security** tab when available.

For non-sensitive hardening ideas, a normal issue or pull request is appropriate.

## Threat model

The repository's security boundaries, attacker capabilities, mitigations, and residual risks are documented in [THREAT_MODEL.md](THREAT_MODEL.md). The model covers untrusted CLI values, malicious SQLite content, path collisions, read-only database invariants, SQL parameterization, bounded analytics work, logging exposure, and dependency supply-chain risks.

## Automated checks

Every push and pull request runs:

- `pip-audit` against the frozen runtime dependency graph exported from `uv.lock`;
- `pip-audit` against pinned development dependencies;
- Gitleaks against full repository history to detect accidental secrets;
- CodeQL static analysis for Python security and quality findings;
- Ruff, strict mypy, tests, and coverage in the main CI workflow;
- a clean wheel build/install smoke test and Docker/Compose verification.

Dependabot checks Python dependencies weekly and GitHub Actions monthly. Runtime dependency freshness is also checked by `scripts/check_dependency_freshness.py`, with evidence uploaded from the Security workflow.
