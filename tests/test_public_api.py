from __future__ import annotations

import data_query
from data_query import core, models, reporting, validation


def test_core_facade_preserves_public_symbols() -> None:
    assert core.InputError is models.InputError
    assert core.ReportFilters is models.ReportFilters
    assert core.ReportOptions is models.ReportOptions
    assert core.build_report is reporting.build_report
    assert core.connect_read_only is validation.connect_read_only
    assert core.validate_schema is validation.validate_schema
    assert core.validate_data is validation.validate_data


def test_package_level_api_remains_backward_compatible() -> None:
    assert data_query.InputError is core.InputError
    assert data_query.ReportFilters is core.ReportFilters
    assert data_query.ReportOptions is core.ReportOptions
    assert data_query.build_report is core.build_report
    assert data_query.write_report is core.write_report
