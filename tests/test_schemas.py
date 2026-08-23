from __future__ import annotations

from datetime import date

import pytest

from data_query.models import InputError, ReportFilters


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"region": ""}, "region must not be empty"),
        ({"region": " north"}, "region must not have leading or trailing whitespace"),
        ({"region": "north\x00east"}, "region must not contain control characters"),
        ({"region": "x" * 65}, "region must be at most 64 characters"),
        ({"top_limit": 0}, "top limit must be between 1 and 100"),
        ({"top_limit": 101}, "top limit must be between 1 and 100"),
        ({"top_limit": "abc"}, "top limit must be an integer"),
        ({"start_date": "not-a-date"}, "expected YYYY-MM-DD"),
    ],
)
def test_report_filter_schema_rejects_invalid_values(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(InputError, match=f"^{message}$"):
        ReportFilters(**kwargs)


def test_report_filter_schema_rejects_reversed_date_range() -> None:
    with pytest.raises(InputError, match="^start date must not be after end date$"):
        ReportFilters(start_date=date(2026, 3, 1), end_date=date(2026, 2, 28))


def test_report_filter_schema_accepts_valid_values() -> None:
    filters = ReportFilters(region="north-east", start_date="2026-02-01", end_date="2026-02-28", top_limit="10")

    assert filters.region == "north-east"
    assert filters.start_date == date(2026, 2, 1)
    assert filters.end_date == date(2026, 2, 28)
    assert filters.top_limit == 10


def test_report_filter_json_schema_exposes_declarative_bounds() -> None:
    schema = ReportFilters.model_json_schema()
    properties = schema["properties"]

    assert schema["additionalProperties"] is False
    assert properties["top_limit"]["minimum"] == 1
    assert properties["top_limit"]["maximum"] == 100
    region_schema = properties["region"]["anyOf"][0]
    assert region_schema["minLength"] == 1
    assert region_schema["maxLength"] == 64
    assert "pattern" in region_schema
