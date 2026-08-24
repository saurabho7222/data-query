# Security Policy

## Supported version

Security fixes are applied to the current `main` branch.

## Reporting a vulnerability

Please do not publish sensitive vulnerability details in a public issue. Prefer GitHub's private vulnerability reporting or Security Advisory flow from the repository's **Security** tab when available.

For non-sensitive hardening ideas, a normal issue or pull request is appropriate.

## Threat model

[THREAT_MODEL.md](THREAT_MODEL.md) covers untrusted CLI values, HTTP query parameters, API database-path sandboxing, malicious SQLite content, read-only invariants, parameterized SQL, bounded analytics, structured logging, metrics exposure, sanitized HTTP failures, network-binding assumptions, and dependency supply-chain risks.

The optional API is an application interface, not infrastructure provisioning. Repository Compose verification binds it to localhost; operators choosing broader exposure must provide deployment-level authentication, TLS, rate limiting, and network policy appropriate to their environment.

## Automated checks

Every push and pull request runs:

- frozen `uv.lock` verification and runtime sync;
- `pip-audit` against the frozen runtime dependency graph;
- `pip-audit` against pinned development dependencies;
- direct dependency freshness verification;
- Gitleaks against repository history;
- CodeQL static analysis;
- Ruff, strict mypy, and Python 3.11/3.12 coverage-gated tests;
- clean wheel installation with CLI and API import smoke tests;
- Docker/Compose tests including a running API `/healthz`, `/v1/report`, and `/metrics` smoke test.

Dependabot checks Python dependencies weekly and GitHub Actions monthly. Runtime dependency freshness evidence is retained by the Security workflow.
