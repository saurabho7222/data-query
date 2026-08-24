"""Static SQL queries and report aggregation."""

from __future__ import annotations

import sqlite3

from .comparison import build_period_comparison
from .models import Report, ReportFilters
from .products import build_product_concentration

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

COHORT_RETENTION_SQL = """
WITH eligible_customers AS (
    SELECT c.id AS customer_id
    FROM customers c
    WHERE (:region IS NULL OR c.region = :region)
),
first_completed AS (
    SELECT
        o.customer_id,
        MIN(substr(o.order_date, 1, 7)) AS cohort_month
    FROM orders o
    JOIN eligible_customers ec ON ec.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY o.customer_id
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM first_completed
    GROUP BY cohort_month
),
activity AS (
    SELECT
        fc.cohort_month,
        (
            (CAST(substr(o.order_date, 1, 4) AS INTEGER) - CAST(substr(fc.cohort_month, 1, 4) AS INTEGER)) * 12
            + CAST(substr(o.order_date, 6, 2) AS INTEGER)
            - CAST(substr(fc.cohort_month, 6, 2) AS INTEGER)
        ) AS period,
        o.customer_id
    FROM first_completed fc
    JOIN orders o ON o.customer_id = fc.customer_id
    WHERE o.status = 'completed'
      AND (:start_date IS NULL OR o.order_date >= :start_date)
      AND (:end_date IS NULL OR o.order_date <= :end_date)
    GROUP BY fc.cohort_month, period, o.customer_id
)
SELECT
    a.cohort_month,
    a.period,
    cs.cohort_size,
    COUNT(*) AS retained_customers,
    ROUND(100.0 * COUNT(*) / cs.cohort_size, 2) AS retention_rate
FROM activity a
JOIN cohort_sizes cs ON cs.cohort_month = a.cohort_month
WHERE a.period >= 0
  AND a.period < :cohort_periods
GROUP BY a.cohort_month, a.period, cs.cohort_size
ORDER BY a.cohort_month ASC, a.period ASC
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
    """Build deterministic aggregate, cohort, product, and comparison analytics."""

    filters = filters or ReportFilters()
    params = _scope_params(filters)

    summary_row = connection.execute(SUMMARY_SQL, params).fetchone()
    top_customer_rows = connection.execute(
        TOP_CUSTOMERS_SQL,
        {**params, "top_limit": filters.top_limit},
    ).fetchall()
    monthly_rows = connection.execute(MONTHLY_REVENUE_SQL, params).fetchall()
    cohort_rows = connection.execute(
        COHORT_RETENTION_SQL,
        {**params, "cohort_periods": filters.cohort_periods},
    ).fetchall()

    return {
        "schema_version": 4,
        "filters": {
            "region": filters.region,
            "start_date": filters.start_date.isoformat() if filters.start_date else None,
            "end_date": filters.end_date.isoformat() if filters.end_date else None,
            "top_limit": filters.top_limit,
            "cohort_periods": filters.cohort_periods,
            "product_limit": filters.product_limit,
            "compare_period": filters.compare_period,
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
        "cohort_retention": [
            {
                "cohort_month": row["cohort_month"],
                "period": int(row["period"]),
                "cohort_size": int(row["cohort_size"]),
                "retained_customers": int(row["retained_customers"]),
                "retention_rate": _money(row["retention_rate"]),
            }
            for row in cohort_rows
        ],
        "product_concentration": build_product_concentration(connection, filters),
        "period_comparison": build_period_comparison(connection, filters),
    }
