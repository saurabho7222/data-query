from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from data_query.core import InputError, ReportFilters, ReportOptions, write_report


def test_equal_length_previous_period_comparison(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "comparison.json"),
        ReportFilters(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            compare_period=True,
        ),
    )

    assert report["period_comparison"] == {
        "current_start": "2026-02-01",
        "current_end": "2026-02-28",
        "previous_start": "2026-01-04",
        "previous_end": "2026-01-31",
        "current": {"completed_orders": 2, "completed_revenue": 240.99},
        "previous": {"completed_orders": 1, "completed_revenue": 80.0},
        "order_change_pct": 100.0,
        "revenue_change_pct": 201.24,
    }


def test_period_comparison_respects_region_scope(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "west.json"),
        ReportFilters(
            region="west",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            compare_period=True,
        ),
    )

    comparison = report["period_comparison"]
    assert comparison is not None
    assert comparison["current"] == {"completed_orders": 1, "completed_revenue": 120.99}
    assert comparison["previous"] == {"completed_orders": 0, "completed_revenue": 0.0}
    assert comparison["order_change_pct"] is None
    assert comparison["revenue_change_pct"] is None


def test_period_comparison_is_opt_in(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "plain.json"),
        ReportFilters(start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)),
    )

    assert report["period_comparison"] is None


def test_period_comparison_requires_complete_date_window() -> None:
    with pytest.raises(InputError, match="requires both start date and end date"):
        ReportFilters(start_date=date(2026, 2, 1), compare_period=True)
    with pytest.raises(InputError, match="requires both start date and end date"):
        ReportFilters(end_date=date(2026, 2, 28), compare_period=True)
