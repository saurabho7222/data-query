"""Data-query analytics package."""

from .core import InputError, ReportFilters, ReportOptions, build_report, write_report

__all__ = ["InputError", "ReportFilters", "ReportOptions", "build_report", "write_report"]
__version__ = "0.2.1"
