"""Equal-length period comparison analytics."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from .models import PeriodComparison, PeriodMetrics, ReportFilters

PERIOD_METRICS_SQL = """
SELECT
    COUNT(DISTINCT o.id) AS completed_orders,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS completed_revenue
FROM orders o
JOIN customers c ON c.id = o.customer_id
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'completed'
  AND (:region IS NULL OR c.region = :region)
  AND o.order_date >= :start_date
  AND o.order_date <= :end_date
"""


def _metrics(
    connection: sqlite3.Connection,
    *,
    region: str | None,
    start_date: date,
    end_date: date,
) -> PeriodMetrics:
    row = connection.execute(
        PERIOD_METRICS_SQL,
        {
            "region": region,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    ).fetchone()
    return {
        "completed_orders": int(row["completed_orders"]),
        "completed_revenue": round(float(row["completed_revenue"] or 0), 2),
    }


def _percent_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100.0, 2)


def build_period_comparison(
    connection: sqlite3.Connection,
    filters: ReportFilters,
) -> PeriodComparison | None:
    """Compare a requested date window with the immediately preceding equal-length window."""

    if not filters.compare_period:
        return None

    if filters.start_date is None or filters.end_date is None:
        raise AssertionError("validated comparison window unexpectedly incomplete")

    window_days = (filters.end_date - filters.start_date).days + 1
    previous_end = filters.start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=window_days - 1)

    current = _metrics(
        connection,
        region=filters.region,
        start_date=filters.start_date,
        end_date=filters.end_date,
    )
    previous = _metrics(
        connection,
        region=filters.region,
        start_date=previous_start,
        end_date=previous_end,
    )

    return {
        "current_start": filters.start_date.isoformat(),
        "current_end": filters.end_date.isoformat(),
        "previous_start": previous_start.isoformat(),
        "previous_end": previous_end.isoformat(),
        "current": current,
        "previous": previous,
        "order_change_pct": _percent_change(
            float(current["completed_orders"]),
            float(previous["completed_orders"]),
        ),
        "revenue_change_pct": _percent_change(
            current["completed_revenue"],
            previous["completed_revenue"],
        ),
    }
