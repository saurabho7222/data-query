"""SQLite analytics engine used by the command-line interface."""

from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, TypedDict

REQUIRED_SCHEMA: dict[str, set[str]] = {
    "customers": {"id", "name", "region"},
    "orders": {"id", "customer_id", "order_date", "status"},
    "order_items": {"order_id", "product", "quantity", "unit_price"},
}




class Summary(TypedDict):
    total_customers: int
    total_orders: int
    completed_orders: int
    completed_revenue: float


class CustomerRow(TypedDict):
    customer_id: int
    name: str
    region: str
    orders: int
    revenue: float


class MonthlyRow(TypedDict):
    month: str
    orders: int
    revenue: float


class AppliedFilters(TypedDict):
    region: str | None
    start_date: str | None
    end_date: str | None
    top_limit: int


class Report(TypedDict):
    schema_version: int
    filters: AppliedFilters
    summary: Summary
    top_customers: list[CustomerRow]
    monthly_revenue: list[MonthlyRow]


class InputError(ValueError):
    """Raised when input data or user-provided filters are invalid."""


@dataclass(frozen=True, slots=True)
class ReportFilters:
    """Optional filters applied consistently to every report section."""

    region: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    top_limit: int = 5

    def __post_init__(self) -> None:
        if self.top_limit < 1 or self.top_limit > 100:
            raise InputError("top limit must be between 1 and 100")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise InputError("start date must not be after end date")


@dataclass(frozen=True, slots=True)
class ReportOptions:
    """Output configuration for a report run."""

    output_json: Path
    customers_csv: Path | None = None
    monthly_csv: Path | None = None


def connect_read_only(path: Path) -> sqlite3.Connection:
    """Open a SQLite database in read-only/query-only mode."""
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


def validate_schema(connection: sqlite3.Connection) -> None:
    """Verify that all tables and columns required by the report are present."""
    missing: list[str] = []
    for table, required_columns in REQUIRED_SCHEMA.items():
        rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
        if not rows:
            missing.append(f"table {table}")
            continue
        actual_columns = {str(row["name"]) for row in rows}
        absent_columns = sorted(required_columns - actual_columns)
        if absent_columns:
            missing.append(f"{table} columns: {', '.join(absent_columns)}")

    if missing:
        raise InputError("invalid database schema; missing " + "; ".join(missing))


def validate_data(connection: sqlite3.Connection) -> None:
    """Reject malformed rows that would make monetary/date aggregates unreliable."""
    invalid_item = connection.execute(
        """
        SELECT rowid, quantity, unit_price
        FROM order_items
        WHERE typeof(quantity) NOT IN ('integer', 'real')
           OR typeof(unit_price) NOT IN ('integer', 'real')
           OR quantity < 0
           OR unit_price < 0
        LIMIT 1
        """
    ).fetchone()
    if invalid_item is not None:
        raise InputError("invalid order_items data; quantity and unit_price must be non-negative numbers")

    invalid_date = connection.execute(
        """
        SELECT id, order_date
        FROM orders
        WHERE order_date IS NULL
           OR length(order_date) != 10
           OR date(order_date) IS NULL
           OR strftime('%Y-%m-%d', order_date) != order_date
        LIMIT 1
        """
    ).fetchone()
    if invalid_date is not None:
        raise InputError("invalid orders data; order_date must use YYYY-MM-DD")

    orphan_order = connection.execute(
        """
        SELECT o.id
        FROM orders o
        LEFT JOIN customers c ON c.id = o.customer_id
        WHERE c.id IS NULL
        LIMIT 1
        """
    ).fetchone()
    if orphan_order is not None:
        raise InputError("invalid relational data; every order must reference an existing customer")

    orphan_item = connection.execute(
        """
        SELECT oi.rowid
        FROM order_items oi
        LEFT JOIN orders o ON o.id = oi.order_id
        WHERE o.id IS NULL
        LIMIT 1
        """
    ).fetchone()
    if orphan_item is not None:
        raise InputError("invalid relational data; every order item must reference an existing order")



def validate_database(input_db: Path) -> None:
    """Validate an input database without generating report artifacts."""
    connection = connect_read_only(input_db)
    try:
        validate_schema(connection)
        validate_data(connection)
    finally:
        connection.close()

def _money(value: float | int | None) -> float:
    return round(float(value or 0), 2)


def _scope(filters: ReportFilters, *, customer_alias: str, order_alias: str) -> tuple[str, dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if filters.region is not None:
        clauses.append(f"{customer_alias}.region = :region")
        params["region"] = filters.region
    if filters.start_date is not None:
        clauses.append(f"{order_alias}.order_date >= :start_date")
        params["start_date"] = filters.start_date.isoformat()
    if filters.end_date is not None:
        clauses.append(f"{order_alias}.order_date <= :end_date")
        params["end_date"] = filters.end_date.isoformat()
    return (" AND ".join(clauses) if clauses else "1 = 1", params)


def build_report(connection: sqlite3.Connection, filters: ReportFilters | None = None) -> Report:
    """Build deterministic aggregate data from a validated database."""
    filters = filters or ReportFilters()
    scope, params = _scope(filters, customer_alias="c", order_alias="o")

    summary_row = connection.execute(
        f"""
        SELECT
            COUNT(DISTINCT c.id) AS total_customers,
            COUNT(DISTINCT o.id) AS total_orders,
            COUNT(DISTINCT CASE WHEN o.status = 'completed' THEN o.id END) AS completed_orders,
            COALESCE(SUM(CASE WHEN o.status = 'completed' THEN oi.quantity * oi.unit_price ELSE 0 END), 0) AS completed_revenue
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        WHERE {scope}
        """,
        params,
    ).fetchone()

    top_customer_rows = connection.execute(
        f"""
        SELECT
            c.id AS customer_id,
            c.name,
            c.region,
            COUNT(DISTINCT o.id) AS orders,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
        FROM customers c
        JOIN orders o ON o.customer_id = c.id AND o.status = 'completed'
        JOIN order_items oi ON oi.order_id = o.id
        WHERE {scope}
        GROUP BY c.id, c.name, c.region
        ORDER BY revenue DESC, c.id ASC
        LIMIT :top_limit
        """,
        {**params, "top_limit": filters.top_limit},
    ).fetchall()

    monthly_rows = connection.execute(
        f"""
        SELECT
            substr(o.order_date, 1, 7) AS month,
            COUNT(DISTINCT o.id) AS orders,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.status = 'completed' AND {scope}
        GROUP BY substr(o.order_date, 1, 7)
        ORDER BY month ASC
        """,
        params,
    ).fetchall()

    return {
        "schema_version": 2,
        "filters": {
            "region": filters.region,
            "start_date": filters.start_date.isoformat() if filters.start_date else None,
            "end_date": filters.end_date.isoformat() if filters.end_date else None,
            "top_limit": filters.top_limit,
        },
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
            {"month": row["month"], "orders": int(row["orders"]), "revenue": _money(row["revenue"])}
            for row in monthly_rows
        ],
    }


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


def write_report(
    input_db: Path,
    options: ReportOptions,
    filters: ReportFilters | None = None,
) -> Report:
    """Validate input, build a report, and atomically write requested outputs."""
    connection = connect_read_only(input_db)
    try:
        validate_schema(connection)
        validate_data(connection)
        report = build_report(connection, filters)
    finally:
        connection.close()

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
    return report
