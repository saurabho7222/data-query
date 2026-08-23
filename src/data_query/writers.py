"""Atomic JSON and CSV output writers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Report, ReportOptions


def _atomic_text_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def write_outputs(report: Report, options: ReportOptions) -> None:
    """Write all requested report artifacts atomically per destination."""

    _atomic_text_write(options.output_json, json.dumps(report, indent=2, sort_keys=True) + "\n")
    if options.customers_csv is not None:
        _write_csv(
            options.customers_csv,
            ["customer_id", "name", "region", "orders", "revenue"],
            [dict(row) for row in report["top_customers"]],
        )
    if options.monthly_csv is not None:
        _write_csv(
            options.monthly_csv,
            ["month", "orders", "revenue"],
            [dict(row) for row in report["monthly_revenue"]],
        )
