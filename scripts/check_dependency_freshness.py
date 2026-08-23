#!/usr/bin/env python3
"""Fail when exactly pinned direct runtime or development dependencies are stale."""

from __future__ import annotations

import json
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
DEV_REQUIREMENTS = ROOT / "requirements-dev.txt"
PYPI_URL = "https://pypi.org/pypi/{name}/json"


def _exact_pin(spec: str, *, group: str) -> tuple[str, str]:
    if "==" not in spec:
        raise ValueError(f"{group} dependency must use an exact == pin: {spec}")
    name, version = spec.split("==", 1)
    name = name.strip()
    version = version.strip()
    if not name or not version or any(token in version for token in (";", " ", "[", "]")):
        raise ValueError(f"unsupported {group} dependency pin: {spec}")
    return name, version


def _runtime_pins(path: Path) -> list[tuple[str, str, str]]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    dependencies = payload.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError("project.dependencies must be a list")
    return [("runtime", *_exact_pin(str(spec), group="runtime")) for spec in dependencies]


def _development_pins(path: Path) -> list[tuple[str, str, str]]:
    pins: list[tuple[str, str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, version = _exact_pin(line, group="development")
        pins.append(("development", name, version))
    return pins


def _latest_version(name: str) -> str:
    request = urllib.request.Request(
        PYPI_URL.format(name=name),
        headers={"User-Agent": "data-query-dependency-freshness/2"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.load(response)
    return str(payload["info"]["version"])


def main() -> int:
    stale: list[str] = []
    try:
        pins = [*_runtime_pins(PYPROJECT), *_development_pins(DEV_REQUIREMENTS)]
        if not pins:
            raise ValueError("no direct dependency pins found")
        for group, name, pinned in pins:
            latest = _latest_version(name)
            print(f"{group}:{name}: pinned={pinned} latest={latest}")
            if pinned != latest:
                stale.append(f"{group}:{name} {pinned} -> {latest}")
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError) as exc:
        print(f"dependency freshness check failed: {exc}", file=sys.stderr)
        return 2

    if stale:
        print("outdated direct dependencies:", file=sys.stderr)
        for item in stale:
            print(f"- {item}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
