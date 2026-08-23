"""Command-line interface for the data-query report generator."""

from __future__ import annotations

import argparse
import logging
import sqlite3
from pathlib import Path

from .core import InputError, write_report

LOGGER = logging.getLogger("data_query")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a deterministic analytics report from SQLite sales data.")
    parser.add_argument("--input", type=Path, default=Path("/app/input.db"), help="SQLite input database")
    parser.add_argument("--output", type=Path, default=Path("/app/output.json"), help="JSON report path")
    parser.add_argument("--verbose", action="store_true", help="enable informational logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    try:
        write_report(args.input, args.output)
    except InputError as exc:
        LOGGER.error("%s", exc)
        return 2
    except sqlite3.Error as exc:
        LOGGER.error("SQLite query failed: %s", exc)
        return 3
    LOGGER.info("report written to %s", args.output)
    return 0
