"""Tests for pure school-term calculations."""

from datetime import date
from pathlib import Path
import sys

import pytest
import yaml

INTEGRATION_PATH = (
    Path(__file__).parents[1] / "custom_components" / "uk_school_terms"
)
sys.path.insert(0, str(INTEGRATION_PATH))

from bank_holidays import get_bank_holidays  # noqa: E402
from model import (  # noqa: E402
    DateListError,
    calculate_status,
    current_term,
    future_terms,
    infer_academic_year,
    parse_override_dates,
    validate_council_data,
)


@pytest.fixture
def kent():
    """Load validated Kent sample data without importing Home Assistant."""
    with (INTEGRATION_PATH / "data" / "england" / "kent.yaml").open() as file:
        raw = yaml.load(file, Loader=yaml.BaseLoader)
    return validate_council_data(raw)


def status(kent, value: str, **kwargs):
    """Calculate a status using the static bank holiday provider."""
    day = date.fromisoformat(value)
    return calculate_status(
        kent,
        day,
        bank_holidays=get_bank_holidays("england", day.year),
        **kwargs,
    )


def test_weekday_during_term_is_school_day(kent):
    assert status(kent, "2025-09-09").school_day is True


def test_weekend_during_term_is_not_school_day(kent):
    result = status(kent, "2025-09-13")
    assert result.school_day is False
    assert result.reason == "weekend"
    assert result.term_time is True


def test_half_term_is_not_school_day(kent):
    result = status(kent, "2025-10-29")
    assert result.school_day is False
    assert result.term_time is False
    assert result.reason == "half_term"


def test_outside_all_terms_is_not_school_day(kent):
    result = status(kent, "2025-12-22")
    assert result.school_day is False
    assert result.reason == "school_holiday"


def test_inset_day_during_term(kent):
    result = status(kent, "2025-09-09", inset_days=["2025-09-09"])
    assert result.school_day is False
    assert result.reason == "inset_day"
    assert result.term_time is True


def test_extra_closure_during_term(kent):
    result = status(kent, "2025-09-10", closure_days=["2025-09-10"])
    assert result.school_day is False
    assert result.reason == "extra_closure"


def test_bank_holiday_during_term_when_enabled(kent):
    # The sample summer term includes the Early May bank holiday.
    result = status(kent, "2026-05-04", exclude_bank_holidays=True)
    assert result.school_day is False
    assert result.reason == "bank_holiday"


def test_bank_holiday_can_be_included(kent):
    result = status(kent, "2026-05-04", exclude_bank_holidays=False)
    assert result.school_day is True


def test_duplicate_override_dates_are_deduplicated():
    assert parse_override_dates(
        "2025-11-21\n\n2025-09-01\n2025-11-21"
    ) == ["2025-09-01", "2025-11-21"]


@pytest.mark.parametrize("value", ["01-09-2025", "2025-02-30", "2025-9-1"])
def test_invalid_date_strings_are_rejected(value):
    with pytest.raises(DateListError):
        parse_override_dates(value)


def test_multiple_instances_can_use_different_overrides(kent):
    school_one = status(kent, "2025-09-09", inset_days=["2025-09-09"])
    school_two = status(kent, "2025-09-09", inset_days=["2025-09-10"])
    assert school_one.school_day is False
    assert school_two.school_day is True


def test_all_bundled_data_is_valid():
    for path in (INTEGRATION_PATH / "data" / "england").glob("*.yaml"):
        with path.open() as file:
            raw = yaml.load(file, Loader=yaml.BaseLoader)
        validate_council_data(raw)



def test_academic_year_is_inferred_from_dates(kent):
    assert infer_academic_year(date(2025, 9, 1)) == "2025-2026"
    assert infer_academic_year(date(2026, 4, 13)) == "2025-2026"
    assert {term.academic_year for term in kent.terms} == {"2025-2026"}


def test_current_and_future_terms(kent):
    active = current_term(kent, date(2026, 1, 12))
    upcoming = future_terms(kent, date(2026, 1, 12))
    assert active is not None
    assert active.name == "Spring"
    assert [term.name for term in upcoming] == ["Summer"]
