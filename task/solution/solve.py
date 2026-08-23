#!/usr/bin/env python3
"""Compatibility wrapper for the packaged data-query CLI."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


if __name__ == "__main__":
    runpy.run_module("data_query", run_name="__main__")
