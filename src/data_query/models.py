"""Shared data models and public configuration types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .errors import InputError as InputError
from .schemas import ReportFilters as ReportFilters

__all__ = [
    "AppliedFilters",
    "CohortRetentionRow",
    "CustomerRow",
    "InputError",
    "MonthlyRow",
    "PeriodComparison",
    "PeriodMetrics",
    "ProductConcentration",
    "ProductPerformanceRow",
    "Report",
    "ReportFilters",
    "ReportOptions",
    "Summary",
]


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


class CohortRetentionRow(TypedDict):
    cohort_month: str
    period: int
    cohort_size: int
    retained_customers: int
    retention_rate: float


class PeriodMetrics(TypedDict):
    completed_orders: int
    completed_revenue: float


class PeriodComparison(TypedDict):
    current_start: str
    current_end: str
    previous_start: str
    previous_end: str
    current: PeriodMetrics
    previous: PeriodMetrics
    order_change_pct: float | None
    revenue_change_pct: float | None


class ProductPerformanceRow(TypedDict):
    product: str
    orders: int
    units: float
    revenue: float
    revenue_share_pct: float
    cumulative_revenue_share_pct: float


class ProductConcentration(TypedDict):
    total_products: int
    products_to_80_pct: int
    top_product_share_pct: float
    products: list[ProductPerformanceRow]


class AppliedFilters(TypedDict):
    region: str | None
    start_date: str | None
    end_date: str | None
    top_limit: int
    cohort_periods: int
    product_limit: int
    compare_period: bool


class Report(TypedDict):
    schema_version: int
    filters: AppliedFilters
    summary: Summary
    top_customers: list[CustomerRow]
    monthly_revenue: list[MonthlyRow]
    cohort_retention: list[CohortRetentionRow]
    product_concentration: ProductConcentration
    period_comparison: PeriodComparison | None


@dataclass(frozen=True, slots=True)
class ReportOptions:
    """Output configuration for a report run."""

    output_json: Path
    customers_csv: Path | None = None
    monthly_csv: Path | None = None
