"""Shared data models and public configuration types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TypedDict


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


class InputError(ValueError):
    """Raised when input data or user-provided configuration is invalid."""


@dataclass(frozen=True, slots=True)
class ReportFilters:
    """Optional filters applied consistently to every report section."""

    region: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    top_limit: int = 5

    def __post_init__(self) -> None:
        if self.top_limit < 1 or self.top_limit > 100:
            raise InputError("top limit must be between 1 and 100")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise InputError("start date must not be after end date")


@dataclass(frozen=True, slots=True)
class ReportOptions:
    """Output configuration for a report run."""

    output_json: Path
    customers_csv: Path | None = None
    monthly_csv: Path | None = None
