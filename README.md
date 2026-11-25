# custody-schedule-spec

An open, machine-readable format for parenting-time schedules, plus a dependency-light Python tool that validates a schedule and exports it as a standard `.ics` calendar.

- Rotations: `2-2-3`, `2-2-5-5`, `3-4-4-3`, `5-2-2-5`, `alternating-weeks`, `every-other-weekend`, or any custom cycle
- Holidays: fixed dates or "Nth weekday of the month" rules, with even/odd-year alternation
- 18 consistency checks that catch contradictory schedules
- `.ics` export for Google Calendar, Apple Calendar and Outlook

```bash
pip install git+https://github.com/parallelparent/custody-schedule-spec
custody-schedule validate examples/2-2-3-with-holidays.json
custody-schedule ics examples/2-2-3-with-holidays.json --from 2027-01-01 --to 2027-12-31 -o parenting-time.ics
```

**Docs:** https://custody-schedule-spec.readthedocs.io

## Layout

```
schema/custody-schedule.schema.json   the format (JSON Schema 2020-12)
src/custody_schedule/                 resolver, validator, .ics writer, CLI
examples/                             3 valid schedules + 1 deliberately broken one
tests/test_core.py                    python tests/test_core.py  (no pytest needed)
docs/                                 the Read the Docs site
```

## Maintainer

Maintained by [Parallel Parent](https://parallelparent.io). MIT-licensed and free for anyone to use, including competing products. This project describes schedules; it is not legal advice, and a court order always controls over a schedule file.
