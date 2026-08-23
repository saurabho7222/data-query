"""Command-line interface for the data-query report generator."""

from __future__ import annotations

import argparse
import logging
import re
import sqlite3
from datetime import date
from pathlib import Path

from .core import InputError, ReportFilters, ReportOptions, validate_database, write_report

LOGGER = logging.getLogger("data_query")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _iso_date(value: str) -> date:
    if ISO_DATE_PATTERN.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a deterministic analytics report from SQLite sales data.")
    parser.add_argument("--input", type=Path, default=Path("/app/input.db"), help="SQLite input database")
    parser.add_argument("--output", type=Path, default=Path("/app/output.json"), help="JSON report path")
    parser.add_argument("--region", help="restrict report data to one customer region")
    parser.add_argument("--start-date", type=_iso_date, help="include orders on/after YYYY-MM-DD")
    parser.add_argument("--end-date", type=_iso_date, help="include orders on/before YYYY-MM-DD")
    parser.add_argument("--top-limit", type=int, default=5, help="number of top customers to include (1-100)")
    parser.add_argument("--customers-csv", type=Path, help="optional CSV export of top customers")
    parser.add_argument("--monthly-csv", type=Path, help="optional CSV export of monthly revenue")
    parser.add_argument("--validate-only", action="store_true", help="validate input and exit without writing reports")
    parser.add_argument("--verbose", action="store_true", help="enable informational logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    try:
        filters = ReportFilters(
            region=args.region,
            start_date=args.start_date,
            end_date=args.end_date,
            top_limit=args.top_limit,
        )
        if args.validate_only:
            validate_database(args.input)
        else:
            options = ReportOptions(
                output_json=args.output,
                customers_csv=args.customers_csv,
                monthly_csv=args.monthly_csv,
            )
            write_report(args.input, options, filters)
    except InputError as exc:
        LOGGER.error("%s", exc)
        return 2
    except sqlite3.Error as exc:
        LOGGER.error("SQLite query failed: %s", exc)
        return 3

    if args.validate_only:
        LOGGER.info("input database is valid: %s", args.input)
    else:
        LOGGER.info("report written to %s", args.output)
    return 0
