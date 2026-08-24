from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from data_query.core import InputError, ReportFilters, ReportOptions, write_report


def test_report_includes_ranked_product_concentration(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(sales_db, ReportOptions(tmp_path / "report.json"))
    concentration = report["product_concentration"]

    assert concentration["total_products"] == 5
    assert concentration["products_to_80_pct"] == 3
    assert concentration["top_product_share_pct"] == 37.38
    assert concentration["products"][:3] == [
        {
            "product": "dock",
            "orders": 1,
            "units": 1,
            "revenue": 120.0,
            "revenue_share_pct": 37.38,
            "cumulative_revenue_share_pct": 37.38,
        },
        {
            "product": "keyboard",
            "orders": 1,
            "units": 2,
            "revenue": 91.0,
            "revenue_share_pct": 28.35,
            "cumulative_revenue_share_pct": 65.73,
        },
        {
            "product": "adapter",
            "orders": 1,
            "units": 2,
            "revenue": 50.0,
            "revenue_share_pct": 15.58,
            "cumulative_revenue_share_pct": 81.31,
        },
    ]


def test_product_limit_truncates_rows_not_concentration_summary(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "top-products.json"),
        ReportFilters(product_limit=2),
    )

    concentration = report["product_concentration"]
    assert len(concentration["products"]) == 2
    assert concentration["total_products"] == 5
    assert concentration["products_to_80_pct"] == 3
    assert report["filters"]["product_limit"] == 2


def test_product_concentration_respects_region_and_date_scope(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "north-feb.json"),
        ReportFilters(
            region="north",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        ),
    )

    assert report["product_concentration"] == {
        "total_products": 1,
        "products_to_80_pct": 1,
        "top_product_share_pct": 100.0,
        "products": [
            {
                "product": "dock",
                "orders": 1,
                "units": 1,
                "revenue": 120.0,
                "revenue_share_pct": 100.0,
                "cumulative_revenue_share_pct": 100.0,
            }
        ],
    }


def test_product_limit_is_bounded() -> None:
    with pytest.raises(InputError, match="product limit"):
        ReportFilters(product_limit=0)
    with pytest.raises(InputError, match="product limit"):
        ReportFilters(product_limit=101)
