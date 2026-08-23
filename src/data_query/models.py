"""Shared data models and public configuration types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .errors import InputError
from .schemas import ReportFilters


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


@dataclass(frozen=True, slots=True)
class ReportOptions:
    """Output configuration for a report run."""

    output_json: Path
    customers_csv: Path | None = None
    monthly_csv: Path | None = None
