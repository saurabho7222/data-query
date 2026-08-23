from __future__ import annotations

import pytest

from data_query import cli
from data_query.input_validation import validate_region_name, validate_top_limit


def test_region_validator_accepts_normal_labels() -> None:
    assert validate_region_name("north-east") == "north-east"
    assert validate_region_name("APAC 2") == "APAC 2"


@pytest.mark.parametrize("value", ["", " north", "north ", "north\n", "x" * 65])
def test_region_validator_rejects_ambiguous_or_control_input(value: str) -> None:
    with pytest.raises(ValueError):
        validate_region_name(value)


@pytest.mark.parametrize(("value", "expected"), [("1", 1), ("5", 5), ("100", 100)])
def test_top_limit_validator_accepts_bounds(value: str, expected: int) -> None:
    assert validate_top_limit(value) == expected


@pytest.mark.parametrize("value", ["0", "101", "abc", "1.5"])
def test_top_limit_validator_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        validate_top_limit(value)


def test_cli_parser_uses_explicit_input_validators() -> None:
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--region", " north"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--top-limit", "0"])

    args = parser.parse_args(["--region", "north-east", "--top-limit", "10"])
    assert args.region == "north-east"
    assert args.top_limit == 10
