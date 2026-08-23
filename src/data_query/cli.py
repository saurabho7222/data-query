"""Command-line interface for the data-query report generator."""

from __future__ import annotations

import argparse
import logging
import sqlite3
from datetime import date
from pathlib import Path

from .core import InputError, ReportFilters, ReportOptions, write_report
from .logging_utils import configure_logger

LOGGER = logging.getLogger("data_query")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
LOG_FORMATS = ("text", "json")


def _iso_date(value: str) -> date:
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
    parser.add_argument("--verbose", action="store_true", help="enable informational logging (compatibility alias)")
    parser.add_argument("--log-level", choices=LOG_LEVELS, help="explicit log threshold")
    parser.add_argument("--log-format", choices=LOG_FORMATS, default="text", help="log output format")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    log_level = args.log_level or ("INFO" if args.verbose else "WARNING")
    configure_logger(LOGGER, level=log_level, log_format=args.log_format)

    try:
        filters = ReportFilters(
            region=args.region,
            start_date=args.start_date,
            end_date=args.end_date,
            top_limit=args.top_limit,
        )
        options = ReportOptions(
            output_json=args.output,
            customers_csv=args.customers_csv,
            monthly_csv=args.monthly_csv,
        )
        write_report(args.input, options, filters)
    except InputError as exc:
        LOGGER.error(
            "%s",
            exc,
            extra={
                "event": "validation_failed",
                "error_type": "input",
                "input_path": str(args.input),
            },
        )
        return 2
    except sqlite3.Error as exc:
        LOGGER.error(
            "SQLite query failed: %s",
            exc,
            extra={
                "event": "query_failed",
                "error_type": "sqlite",
                "input_path": str(args.input),
            },
        )
        return 3

    LOGGER.info(
        "report written to %s",
        args.output,
        extra={"event": "report_written", "output_path": str(args.output)},
    )
    return 0
