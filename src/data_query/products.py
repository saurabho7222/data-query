"""Product concentration and Pareto-style revenue analytics."""

from __future__ import annotations

import sqlite3

from .models import ProductConcentration, ProductPerformanceRow, ReportFilters

PRODUCT_CONCENTRATION_SQL = """
WITH product_totals AS (
    SELECT
        oi.product AS product,
        COUNT(DISTINCT o.id) AS orders,
        COALESCE(SUM(oi.quantity), 0) AS units,
        COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id AND o.status = 'completed'
    JOIN customers c ON c.id = o.customer_id
    WHERE (:region IS NULL OR c.region = :region)
      AND (:start_date IS NULL OR o.order_date >= :start_date)
      AND (:end_date IS NULL OR o.order_date <= :end_date)
    GROUP BY oi.product
),
scored AS (
    SELECT
        product,
        orders,
        units,
        revenue,
        CASE
            WHEN SUM(revenue) OVER () = 0 THEN 0.0
            ELSE 100.0 * revenue / SUM(revenue) OVER ()
        END AS revenue_share_pct,
        CASE
            WHEN SUM(revenue) OVER () = 0 THEN 0.0
            ELSE 100.0 * SUM(revenue) OVER (
                ORDER BY revenue DESC, product ASC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) / SUM(revenue) OVER ()
        END AS cumulative_revenue_share_pct,
        ROW_NUMBER() OVER (ORDER BY revenue DESC, product ASC) AS product_rank
    FROM product_totals
)
SELECT
    product,
    orders,
    units,
    revenue,
    revenue_share_pct,
    cumulative_revenue_share_pct,
    product_rank
FROM scored
ORDER BY product_rank ASC
"""


def _round_metric(value: float | int | None) -> float:
    return round(float(value or 0), 2)


def build_product_concentration(
    connection: sqlite3.Connection,
    filters: ReportFilters,
) -> ProductConcentration:
    """Build ranked product revenue distribution and Pareto concentration metrics."""

    rows = connection.execute(
        PRODUCT_CONCENTRATION_SQL,
        {
            "region": filters.region,
            "start_date": filters.start_date.isoformat() if filters.start_date else None,
            "end_date": filters.end_date.isoformat() if filters.end_date else None,
        },
    ).fetchall()

    products: list[ProductPerformanceRow] = [
        {
            "product": str(row["product"]),
            "orders": int(row["orders"]),
            "units": _round_metric(row["units"]),
            "revenue": _round_metric(row["revenue"]),
            "revenue_share_pct": _round_metric(row["revenue_share_pct"]),
            "cumulative_revenue_share_pct": _round_metric(row["cumulative_revenue_share_pct"]),
        }
        for row in rows
    ]

    total_revenue = sum(product["revenue"] for product in products)
    products_to_80_pct = 0
    if total_revenue > 0:
        products_to_80_pct = next(
            (
                index
                for index, product in enumerate(products, start=1)
                if product["cumulative_revenue_share_pct"] >= 80.0
            ),
            len(products),
        )

    return {
        "total_products": len(products),
        "products_to_80_pct": products_to_80_pct,
        "top_product_share_pct": products[0]["revenue_share_pct"] if products else 0.0,
        "products": products[: filters.product_limit],
    }
