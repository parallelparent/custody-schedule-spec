# Usage

## Install

```bash
pip install git+https://github.com/parallelparent/custody-schedule-spec
```

The core has no dependencies. `jsonschema` is installed alongside it for the `validate` command; if it's missing, `validate` stops with an error instead of reporting a false pass.

## Command line

```bash
custody-schedule presets                       # list built-in rotations
custody-schedule validate my-schedule.json     # exit code 0 = OK, 1 = errors
custody-schedule summary my-schedule.json --from 2027-01-01 --to 2027-12-31
custody-schedule ics my-schedule.json --from 2027-01-01 --to 2027-12-31 -o parenting-time.ics
```

`summary` prints days and percentage per parent for the range, with holidays and overrides applied.

## Python

```python
import json
from datetime import date
from custody_schedule import resolve, summarize, to_ics, validate

schedule = json.load(open("my-schedule.json"))
problems = validate(schedule)
blocks = resolve(schedule, date(2027, 1, 1), date(2027, 12, 31))
for b in blocks:
    print(b.parent, b.start, b.end, b.source)
open("parenting-time.ics", "w", newline="").write(to_ics(schedule, blocks))
```

## Load the calendar into a calendar app

- **Google Calendar:** Settings, then Import & export, then Import. Choose the `.ics` file and the calendar to add it to.
- **Apple Calendar (Mac):** File, then Import, then choose the `.ics` file.
- **Outlook:** File, then Open & Export, then Import/Export, then "Import an iCalendar (.ics) file".

Events are all-day and marked "free", so they don't block your availability for meetings. Event IDs are deterministic, so importing an updated file replaces events instead of duplicating them in apps that honor UIDs.
