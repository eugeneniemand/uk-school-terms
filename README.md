# UK School Terms

`uk_school_terms` is a local-data Home Assistant custom integration that exposes
recommended UK council school term dates as binary sensors, sensors, and a
calendar. The MVP makes no network requests: council dates are bundled as
validated YAML files.

Each config entry creates:

- School day and term time binary sensors.
- Current term, next event, and days-until-next-event sensors.
- A school terms calendar containing term and half-term ranges.

`term_time` and `school_day` intentionally differ. A weekday can be in term time
but not be a school day because it is an inset day, extra closure, or excluded
bank holiday.

## Installation

### HACS custom repository

1. Publish this folder as a GitHub repository.
2. In HACS, open **Integrations**, choose **Custom repositories**, enter the
   repository URL, and select the **Integration** category.
3. Install **UK School Terms** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**, search for
   **UK School Terms**, and complete the config flow.

### Manual

Copy `custom_components/uk_school_terms` into the `custom_components` directory
inside your Home Assistant configuration directory, then restart Home Assistant.

No `configuration.yaml` entry is needed.

## Configuration and multiple schools

Choose England, a council, and optionally a school name. Add inset and extra
closure dates one per line in `YYYY-MM-DD` format. Blank lines are ignored and
duplicates are removed.

Multiple entries are supported, including repeated entries for the same council.
Use the optional school name to make entities easy to distinguish. Entries
without a school name receive distinct titles such as `UK School Terms - Kent`
and `UK School Terms - Kent 2`.

To change school-specific dates later, open the integration entry in
**Settings → Devices & services**, choose **Configure**, edit the dates, and
save. The entry reloads automatically.

## Date behaviour

- `term_time`: inside an inclusive term range and outside an inclusive half-term
  range.
- `school_day`: a weekday in term time that is not an inset day, extra closure,
  or (when enabled) bank holiday.
- `school_holiday`: any day that is not a school day.

The integration recalculates at startup, after option changes, and shortly after
local midnight each day.

## Adding a council

Add a lower-case YAML file to
`custom_components/uk_school_terms/data/england/`. Use the existing files as
templates. Required top-level keys are:

```yaml
authority: example
name: Example Council
country: england
source_url: https://example.gov.uk/term-dates
last_verified: 2026-01-01
terms:
  - name: autumn
    start: 2025-09-01
    end: 2025-12-19
    half_terms:
      - start: 2025-10-27
        end: 2025-10-31
  - name: spring
    start: 2026-01-05
    end: 2026-03-27
    half_terms:
      - start: 2026-02-16
        end: 2026-02-20
```

Dates must use `YYYY-MM-DD`. Ranges are inclusive. Academic years are inferred
from term dates, so the YAML has no academic-year wrapper and can simply append
future terms. The loader validates required keys, date formats, range order,
half-terms inside their parent term, and overlapping terms.

The calendar entity exposes `current_term` and `future_terms` attributes. Each
term includes its inferred academic year, inclusive dates, and half-term ranges.

## Current MVP limitations

- England only.
- Static bundled council data only.
- No scraping or live API.
- No postcode lookup.
- No automatic school-specific inset days.
- Bank holidays use a replaceable static internal list for the sample years.
- Council dates are recommended authority dates and are not guaranteed to match
  every school.
- Included sample dates must be independently verified before real-world use.

## Development

The pure date model can be tested without a running Home Assistant:

```bash
python -m pytest
```

For Home Assistant testing, copy or link the integration directory into the
Home Assistant config's `custom_components` directory, restart Home Assistant,
and inspect logs for `uk_school_terms`.
# uk-school-terms
