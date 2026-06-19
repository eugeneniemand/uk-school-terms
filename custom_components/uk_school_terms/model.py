"""Pure data model and date calculations for UK School Terms."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Iterable


class CouncilDataError(ValueError):
    """Raised when council data is invalid."""


class DateListError(ValueError):
    """Raised when an override date list is invalid."""


@dataclass(frozen=True)
class DateRange:
    """An inclusive date range."""

    start: date
    end: date

    def contains(self, value: date) -> bool:
        """Return whether value is in this inclusive range."""
        return self.start <= value <= self.end


@dataclass(frozen=True)
class Term:
    """A school term."""

    key: str
    name: str
    academic_year: str
    dates: DateRange
    half_terms: tuple[DateRange, ...]


@dataclass(frozen=True)
class CouncilData:
    """Validated council term data."""

    authority: str
    name: str
    country: str
    source_url: str
    last_verified: date
    terms: tuple[Term, ...]


@dataclass(frozen=True)
class SchoolDayStatus:
    """Calculated state for a date."""

    school_day: bool
    term_time: bool
    reason: str
    academic_year: str | None
    current_term: str | None


@dataclass(frozen=True)
class SchoolEvent:
    """A future school calendar boundary."""

    name: str
    event_type: str
    event_date: date
    academic_year: str


TERM_NAMES = {
    "autumn": "Autumn",
    "spring": "Spring",
    "summer": "Summer",
}


def infer_academic_year(value: date) -> str:
    """Infer the UK academic year containing a date."""
    start_year = value.year if value.month >= 8 else value.year - 1
    return f"{start_year}-{start_year + 1}"


def parse_iso_date(value: Any, field: str = "date") -> date:
    """Parse a strict YYYY-MM-DD date."""
    if not isinstance(value, str):
        raise CouncilDataError(f"{field} must be a YYYY-MM-DD string")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as err:
        raise CouncilDataError(f"Invalid {field}: {value}") from err
    if parsed.isoformat() != value:
        raise CouncilDataError(f"Invalid {field}: {value}")
    return parsed


def parse_override_dates(value: str | Iterable[str] | None) -> list[str]:
    """Parse, validate, sort, and deduplicate override dates."""
    if value is None:
        return []
    values = value.splitlines() if isinstance(value, str) else value
    parsed: set[date] = set()
    for raw_value in values:
        text = str(raw_value).strip()
        if not text:
            continue
        try:
            parsed_date = date.fromisoformat(text)
        except ValueError as err:
            raise DateListError(f"Invalid date: {text}") from err
        if parsed_date.isoformat() != text:
            raise DateListError(f"Invalid date: {text}")
        parsed.add(parsed_date)
    return [value.isoformat() for value in sorted(parsed)]


def validate_council_data(raw: Any) -> CouncilData:
    """Validate raw council YAML data and return a typed model."""
    if not isinstance(raw, dict):
        raise CouncilDataError("Council data must be a mapping")

    required = {
        "authority",
        "name",
        "country",
        "source_url",
        "last_verified",
        "terms",
    }
    missing = sorted(required - raw.keys())
    if missing:
        raise CouncilDataError(f"Missing required keys: {', '.join(missing)}")
    if not isinstance(raw["terms"], list) or not raw["terms"]:
        raise CouncilDataError("terms must be a non-empty list")

    terms: list[Term] = []
    for index, term_value in enumerate(raw["terms"]):
        field = f"terms[{index}]"
        if not isinstance(term_value, dict):
            raise CouncilDataError(f"{field} must be a mapping")
        if not {"name", "start", "end"} <= term_value.keys():
            raise CouncilDataError(f"{field} needs name, start, and end")

        term_key = str(term_value["name"]).strip().lower()
        if not term_key:
            raise CouncilDataError(f"{field}.name cannot be empty")
        start = parse_iso_date(term_value["start"], f"{field}.start")
        end = parse_iso_date(term_value["end"], f"{field}.end")
        if start > end:
            raise CouncilDataError(f"{field} starts after it ends")

        academic_year = infer_academic_year(start)
        if infer_academic_year(end) != academic_year:
            raise CouncilDataError(f"{field} crosses academic-year boundaries")

        half_terms: list[DateRange] = []
        for half_index, half_term in enumerate(term_value.get("half_terms", [])):
            half_field = f"{field}.half_terms[{half_index}]"
            if not isinstance(half_term, dict):
                raise CouncilDataError(f"{half_field} must be a mapping")
            half_start = parse_iso_date(half_term.get("start"), f"{half_field}.start")
            half_end = parse_iso_date(half_term.get("end"), f"{half_field}.end")
            if half_start > half_end:
                raise CouncilDataError(f"{half_field} starts after it ends")
            if half_start < start or half_end > end:
                raise CouncilDataError(f"{half_field} must be inside its parent term")
            half_terms.append(DateRange(half_start, half_end))

        _validate_non_overlapping_ranges(half_terms, f"{field} half-terms")
        terms.append(
            Term(
                key=term_key,
                name=TERM_NAMES.get(term_key, term_key.title()),
                academic_year=academic_year,
                dates=DateRange(start, end),
                half_terms=tuple(sorted(half_terms, key=lambda item: item.start)),
            )
        )

    sorted_terms = sorted(terms, key=lambda item: item.dates.start)
    _validate_non_overlapping_ranges([term.dates for term in sorted_terms], "terms")

    return CouncilData(
        authority=str(raw["authority"]),
        name=str(raw["name"]),
        country=str(raw["country"]),
        source_url=str(raw["source_url"]),
        last_verified=parse_iso_date(raw["last_verified"], "last_verified"),
        terms=tuple(sorted_terms),
    )


def _validate_non_overlapping_ranges(
    ranges: Iterable[DateRange], description: str
) -> None:
    """Validate ranges do not overlap."""
    previous: DateRange | None = None
    for current in sorted(ranges, key=lambda item: item.start):
        if previous is not None and current.start <= previous.end:
            raise CouncilDataError(f"Overlapping {description}")
        previous = current


def current_term(council: CouncilData, today: date) -> Term | None:
    """Return the term whose inclusive range contains today."""
    return next((term for term in council.terms if term.dates.contains(today)), None)


def future_terms(council: CouncilData, today: date) -> tuple[Term, ...]:
    """Return terms beginning after today."""
    return tuple(term for term in council.terms if term.dates.start > today)


def calculate_status(
    council: CouncilData,
    today: date,
    inset_days: Iterable[str] = (),
    closure_days: Iterable[str] = (),
    exclude_bank_holidays: bool = True,
    bank_holidays: Iterable[date] = (),
) -> SchoolDayStatus:
    """Calculate school-day and term-time state for a date."""
    term = current_term(council, today)
    in_half_term = term is not None and any(
        item.contains(today) for item in term.half_terms
    )
    term_time = term is not None and not in_half_term
    defined_years = {item.academic_year for item in council.terms}
    academic_year = infer_academic_year(today)
    has_year_data = academic_year in defined_years

    if today.weekday() >= 5:
        reason = "weekend"
    elif in_half_term:
        reason = "half_term"
    elif term is None:
        reason = "school_holiday" if has_year_data else "unknown_no_data"
    elif today.isoformat() in set(inset_days):
        reason = "inset_day"
    elif today.isoformat() in set(closure_days):
        reason = "extra_closure"
    elif exclude_bank_holidays and today in set(bank_holidays):
        reason = "bank_holiday"
    else:
        reason = "school_day"

    return SchoolDayStatus(
        school_day=reason == "school_day",
        term_time=term_time,
        reason=reason,
        academic_year=academic_year if has_year_data else None,
        current_term=term.name if term else None,
    )


def build_events(council: CouncilData) -> tuple[SchoolEvent, ...]:
    """Build deterministic boundary events from council data."""
    events: list[SchoolEvent] = []
    for term in council.terms:
        events.append(
            SchoolEvent(
                name=f"{term.name} term starts",
                event_type="term_start",
                event_date=term.dates.start,
                academic_year=term.academic_year,
            )
        )
        for half_term in term.half_terms:
            events.append(
                SchoolEvent(
                    name=f"{term.name} half-term starts",
                    event_type="half_term_start",
                    event_date=half_term.start,
                    academic_year=term.academic_year,
                )
            )
            if half_term.end < term.dates.end:
                events.append(
                    SchoolEvent(
                        name=f"{term.name} term resumes",
                        event_type="term_resume",
                        event_date=half_term.end + timedelta(days=1),
                        academic_year=term.academic_year,
                    )
                )
        holiday_name = (
            "Summer holiday starts"
            if term.key == "summer"
            else f"{term.name} term ends"
        )
        events.append(
            SchoolEvent(
                name=holiday_name,
                event_type="holiday_start",
                event_date=term.dates.end + timedelta(days=1),
                academic_year=term.academic_year,
            )
        )
    return tuple(sorted(events, key=lambda item: item.event_date))


def next_event(council: CouncilData, today: date) -> SchoolEvent | None:
    """Return the next event on or after today."""
    return next(
        (event for event in build_events(council) if event.event_date >= today), None
    )
