from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from data_query.core import InputError, ReportFilters, ReportOptions, write_report


def test_report_includes_monthly_cohort_retention(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(sales_db, ReportOptions(tmp_path / "report.json"))

    assert report["cohort_retention"] == [
        {
            "cohort_month": "2026-01",
            "period": 0,
            "cohort_size": 1,
            "retained_customers": 1,
            "retention_rate": 100.0,
        },
        {
            "cohort_month": "2026-01",
            "period": 1,
            "cohort_size": 1,
            "retained_customers": 1,
            "retention_rate": 100.0,
        },
        {
            "cohort_month": "2026-02",
            "period": 0,
            "cohort_size": 1,
            "retained_customers": 1,
            "retention_rate": 100.0,
        },
    ]


def test_cohort_horizon_limits_month_offsets(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "report.json"),
        ReportFilters(cohort_periods=1),
    )

    assert [row["period"] for row in report["cohort_retention"]] == [0, 0]
    assert report["filters"]["cohort_periods"] == 1


def test_cohort_activity_respects_report_scope_but_keeps_original_cohort(sales_db: Path, tmp_path: Path) -> None:
    report = write_report(
        sales_db,
        ReportOptions(tmp_path / "north-feb.json"),
        ReportFilters(
            region="north",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            cohort_periods=6,
        ),
    )

    assert report["cohort_retention"] == [
        {
            "cohort_month": "2026-01",
            "period": 1,
            "cohort_size": 1,
            "retained_customers": 1,
            "retention_rate": 100.0,
        }
    ]


def test_cohort_horizon_is_bounded() -> None:
    with pytest.raises(InputError, match="cohort periods"):
        ReportFilters(cohort_periods=0)
    with pytest.raises(InputError, match="cohort periods"):
        ReportFilters(cohort_periods=25)
