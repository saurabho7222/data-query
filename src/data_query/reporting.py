"""Static SQL queries and report aggregation."""

from __future__ import annotations

import sqlite3

from .models import Report, ReportFilters

SUMMARY_SQL = """
SELECT
    COUNT(DISTINCT c.id) AS total_customers,
    COUNT(DISTINCT o.id) AS total_orders,
    COUNT(DISTINCT CASE WHEN o.status = 'completed' THEN o.id END) AS completed_orders,
    COALESCE(SUM(CASE WHEN o.status = 'completed' THEN oi.quantity * oi.unit_price ELSE 0 END), 0) AS completed_revenue
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
LEFT JOIN order_items oi ON oi.order_id = o.id
WHERE (:region IS NULL OR c.region = :region)
  AND (:start_date IS NULL OR o.order_date >= :start_date)
  AND (:end_date IS NULL OR o.order_date <= :end_date)
"""

TOP_CUSTOMERS_SQL = """
SELECT
    c.id AS customer_id,
    c.name,
    c.region,
    COUNT(DISTINCT o.id) AS orders,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.id AND o.status = 'completed'
JOIN order_items oi ON oi.order_id = o.id
WHERE (:region IS NULL OR c.region = :region)
  AND (:start_date IS NULL OR o.order_date >= :start_date)
  AND (:end_date IS NULL OR o.order_date <= :end_date)
GROUP BY c.id, c.name, c.region
ORDER BY revenue DESC, c.id ASC
LIMIT :top_limit
"""

MONTHLY_REVENUE_SQL = """
SELECT
    substr(o.order_date, 1, 7) AS month,
    COUNT(DISTINCT o.id) AS orders,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
FROM orders o
JOIN customers c ON c.id = o.customer_id
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'completed'
  AND (:region IS NULL OR c.region = :region)
  AND (:start_date IS NULL OR o.order_date >= :start_date)
  AND (:end_date IS NULL OR o.order_date <= :end_date)
GROUP BY substr(o.order_date, 1, 7)
ORDER BY month ASC
"""


def _money(value: float | int | None) -> float:
    return round(float(value or 0), 2)


def _scope_params(filters: ReportFilters) -> dict[str, str | None]:
    return {
        "region": filters.region,
        "start_date": filters.start_date.isoformat() if filters.start_date else None,
        "end_date": filters.end_date.isoformat() if filters.end_date else None,
    }


def build_report(connection: sqlite3.Connection, filters: ReportFilters | None = None) -> Report:
    """Build deterministic aggregate data from a validated database."""

    filters = filters or ReportFilters()
    params = _scope_params(filters)

    summary_row = connection.execute(SUMMARY_SQL, params).fetchone()
    top_customer_rows = connection.execute(
        TOP_CUSTOMERS_SQL,
        {**params, "top_limit": filters.top_limit},
    ).fetchall()
    monthly_rows = connection.execute(MONTHLY_REVENUE_SQL, params).fetchall()

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
