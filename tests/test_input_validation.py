from __future__ import annotations

import pytest

from data_query import cli
from data_query.input_validation import (
    validate_cohort_periods,
    validate_product_limit,
    validate_region_name,
    validate_top_limit,
)
from data_query.models import InputError


def test_region_validator_accepts_normal_labels() -> None:
    assert validate_region_name("north-east") == "north-east"
    assert validate_region_name("APAC 2") == "APAC 2"


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("", "region must not be empty"),
        (" north", "region must not have leading or trailing whitespace"),
        ("north ", "region must not have leading or trailing whitespace"),
        ("north\n", "region must not have leading or trailing whitespace"),
        ("x" * 65, "region must be at most 64 characters"),
    ],
)
def test_region_validator_rejects_invalid_input_with_exact_error(value: str, message: str) -> None:
    with pytest.raises(InputError, match=f"^{message}$"):
        validate_region_name(value)


def test_region_validator_rejects_embedded_control_character() -> None:
    with pytest.raises(InputError, match="^region must not contain control characters$"):
        validate_region_name("north\x00east")


@pytest.mark.parametrize(("value", "expected"), [("1", 1), ("5", 5), ("100", 100)])
def test_top_limit_validator_accepts_bounds(value: str, expected: int) -> None:
    assert validate_top_limit(value) == expected


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("0", "top limit must be between 1 and 100"),
        ("101", "top limit must be between 1 and 100"),
        ("abc", "top limit must be an integer"),
        ("1.5", "top limit must be an integer"),
    ],
)
def test_top_limit_validator_rejects_invalid_values_with_exact_error(value: str, message: str) -> None:
    with pytest.raises(InputError, match=f"^{message}$"):
        validate_top_limit(value)


@pytest.mark.parametrize(("value", "expected"), [("1", 1), ("6", 6), ("24", 24)])
def test_cohort_period_validator_accepts_bounds(value: str, expected: int) -> None:
    assert validate_cohort_periods(value) == expected


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("0", "cohort periods must be between 1 and 24"),
        ("25", "cohort periods must be between 1 and 24"),
        ("abc", "cohort periods must be an integer"),
    ],
)
def test_cohort_period_validator_rejects_invalid_values(value: str, message: str) -> None:
    with pytest.raises(InputError, match=f"^{message}$"):
        validate_cohort_periods(value)


@pytest.mark.parametrize(("value", "expected"), [("1", 1), ("10", 10), ("100", 100)])
def test_product_limit_validator_accepts_bounds(value: str, expected: int) -> None:
    assert validate_product_limit(value) == expected


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("0", "product limit must be between 1 and 100"),
        ("101", "product limit must be between 1 and 100"),
        ("abc", "product limit must be an integer"),
    ],
)
def test_product_limit_validator_rejects_invalid_values(value: str, message: str) -> None:
    with pytest.raises(InputError, match=f"^{message}$"):
        validate_product_limit(value)


def test_cli_parser_uses_explicit_input_validators() -> None:
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--region", " north"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--top-limit", "0"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--cohort-periods", "25"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--product-limit", "101"])

    args = parser.parse_args(
        ["--region", "north-east", "--top-limit", "10", "--cohort-periods", "12", "--product-limit", "20"]
    )
    assert args.region == "north-east"
    assert args.top_limit == 10
    assert args.cohort_periods == 12
    assert args.product_limit == 20
