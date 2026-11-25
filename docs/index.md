# custody-schedule-spec

**An open, machine-readable format for parenting-time schedules, plus a small tool that turns one into a calendar.**

Parenting plans describe schedules in prose: "Parent A has the children Monday and Tuesday, Parent B Wednesday and Thursday, alternating weekends." Every calendar app, family-law office and co-parenting tool then re-types that sentence by hand. This project gives the schedule one structured shape so it can be checked, shared and loaded into any calendar without re-typing.

## What it does

- **Describes** a repeating rotation (2-2-3, 2-2-5-5, week on / week off, or any custom cycle) anchored to a start date.
- **Layers holidays on top**: fixed dates (December 24) or rules like "the fourth Thursday of November", with optional even-year / odd-year alternation.
- **Checks itself.** 18 consistency rules catch schedules that are well formed but contradictory, such as two trips that overlap or a holiday assigned to a parent who isn't defined.
- **Exports a standard `.ics` calendar** that Google Calendar, Apple Calendar and Outlook import directly.
- **Counts days** per parent across any date range.

## Quick start

```bash
pip install git+https://github.com/parallelparent/custody-schedule-spec
custody-schedule presets
custody-schedule validate examples/2-2-3-with-holidays.json
custody-schedule ics examples/2-2-3-with-holidays.json --from 2027-01-01 --to 2027-12-31 -o parenting-time.ics
```

A minimal schedule file:

```json
{
  "spec_version": "1.0",
  "parents": {"A": {"label": "Parent A"}, "B": {"label": "Parent B"}},
  "rotation": {"preset": "2-2-3", "start_date": "2027-01-04", "first_parent": "A"}
}
```

## Where to go next

- [Common schedules explained](schedules.md): how each rotation actually lays out across two weeks
- [Format reference](format.md): every field
- [Validation rules](rules.md): what each check catches and why
- [Usage](usage.md): command line, Python, and importing into calendar apps

## Who maintains this

custody-schedule-spec is maintained by [Parallel Parent](https://parallelparent.io), which builds tools for parents managing a parallel parenting arrangement. Parallel Parent uses this format to turn uploaded parenting plans into calendars. The format, the code and these docs are MIT-licensed and free for anyone to use, including competing products. No part of the format depends on Parallel Parent or favors any product.

This project describes schedules. It does not give legal advice, and it is not a substitute for the wording of a court order. When a court order and a schedule file disagree, the court order controls.
