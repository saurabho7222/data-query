#!/usr/bin/env python3
"""Fail when an exactly pinned direct development dependency is not current on PyPI."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REQUIREMENTS = Path(__file__).resolve().parents[1] / "requirements-dev.txt"
PYPI_URL = "https://pypi.org/pypi/{name}/json"


def _pinned_requirements(path: Path) -> list[tuple[str, str]]:
    pins: list[tuple[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(f"development dependency must use an exact == pin: {line}")
        name, version = line.split("==", 1)
        pins.append((name.strip(), version.strip()))
    return pins


def _latest_version(name: str) -> str:
    request = urllib.request.Request(
        PYPI_URL.format(name=name),
        headers={"User-Agent": "data-query-dependency-freshness/1"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.load(response)
    return str(payload["info"]["version"])


def main() -> int:
    stale: list[str] = []
    try:
        pins = _pinned_requirements(REQUIREMENTS)
        for name, pinned in pins:
            latest = _latest_version(name)
            print(f"{name}: pinned={pinned} latest={latest}")
            if pinned != latest:
                stale.append(f"{name} {pinned} -> {latest}")
    except (OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        print(f"dependency freshness check failed: {exc}", file=sys.stderr)
        return 2

    if stale:
        print("outdated direct development dependencies:", file=sys.stderr)
        for item in stale:
            print(f"- {item}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
