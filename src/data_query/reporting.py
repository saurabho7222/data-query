"""SQL query construction and report aggregation."""

from __future__ import annotations

import sqlite3
from typing import Any

from .models import Report, ReportFilters


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
