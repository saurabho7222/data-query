#!/usr/bin/env python3
"""Generate a deterministic JSON analytics report from a SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

REQUIRED_SCHEMA = {
    "customers": {"id", "name", "region"},
    "orders": {"id", "customer_id", "order_date", "status"},
    "order_items": {"order_id", "product", "quantity", "unit_price"},
}


class InputError(ValueError):
    """Raised when the input database cannot be safely processed."""


def _connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise InputError(f"input database does not exist: {path}")
    if not path.is_file():
        raise InputError(f"input path is not a file: {path}")

    try:
        connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA schema_version").fetchone()
        return connection
    except sqlite3.Error as exc:
        raise InputError(f"input is not a readable SQLite database: {path}") from exc


def _validate_schema(connection: sqlite3.Connection) -> None:
    missing: list[str] = []
    for table, required_columns in REQUIRED_SCHEMA.items():
        rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
        if not rows:
            missing.append(f"table {table}")
            continue
        actual_columns = {row["name"] for row in rows}
        absent_columns = sorted(required_columns - actual_columns)
        if absent_columns:
            missing.append(f"{table} columns: {', '.join(absent_columns)}")

    if missing:
        raise InputError("invalid database schema; missing " + "; ".join(missing))


def _money(value: float | int | None) -> float:
    return round(float(value or 0), 2)


def build_report(connection: sqlite3.Connection) -> dict[str, object]:
    summary_row = connection.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM customers) AS total_customers,
            (SELECT COUNT(*) FROM orders) AS total_orders,
            (SELECT COUNT(*) FROM orders WHERE status = 'completed') AS completed_orders,
            (
                SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                WHERE o.status = 'completed'
            ) AS completed_revenue
        """
    ).fetchone()

    top_customer_rows = connection.execute(
        """
        SELECT
            c.id AS customer_id,
            c.name,
            c.region,
            COUNT(DISTINCT o.id) AS orders,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
        FROM customers c
        JOIN orders o ON o.customer_id = c.id AND o.status = 'completed'
        JOIN order_items oi ON oi.order_id = o.id
        GROUP BY c.id, c.name, c.region
        ORDER BY revenue DESC, c.id ASC
        LIMIT 5
        """
    ).fetchall()

    monthly_rows = connection.execute(
        """
        SELECT
            substr(o.order_date, 1, 7) AS month,
            COUNT(DISTINCT o.id) AS orders,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.status = 'completed'
        GROUP BY substr(o.order_date, 1, 7)
        ORDER BY month ASC
        """
    ).fetchall()

    return {
        "schema_version": 1,
        "summary": {
            "total_customers": int(summary_row["total_customers"]),
            "total_orders": int(summary_row["total_orders"]),
            "completed_orders": int(summary_row["completed_orders"]),
            "completed_revenue": _money(summary_row["completed_revenue"]),
        },
        "top_customers": [
            {
                "customer_id": int(row["customer_id"]),
                "name": row["name"],
                "region": row["region"],
                "orders": int(row["orders"]),
                "revenue": _money(row["revenue"]),
            }
            for row in top_customer_rows
        ],
        "monthly_revenue": [
            {
                "month": row["month"],
                "orders": int(row["orders"]),
                "revenue": _money(row["revenue"]),
            }
            for row in monthly_rows
        ],
    }


def write_report(input_db: Path, output_json: Path) -> None:
    connection = _connect_read_only(input_db)
    try:
        _validate_schema(connection)
        report = build_report(connection)
    finally:
        connection.close()

    output_json.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output_json.with_suffix(output_json.suffix + ".tmp")
    temporary_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_output.replace(output_json)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("/app/input.db"), help="SQLite input database")
    parser.add_argument("--output", type=Path, default=Path("/app/output.json"), help="JSON report path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        write_report(args.input, args.output)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except sqlite3.Error as exc:
        print(f"error: SQLite query failed: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
