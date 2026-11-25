# Format reference

A schedule is one JSON object. The authoritative definition is [`schema/custody-schedule.schema.json`](https://github.com/parallelparent/custody-schedule-spec/blob/main/schema/custody-schedule.schema.json) (JSON Schema draft 2020-12).

## Top level

| Field | Required | Type | Meaning |
|---|---|---|---|
| `spec_version` | yes | `"1.0"` | Format version. |
| `parents` | yes | object | Two or more parent ids, each with an optional `label`. Use neutral ids such as `A` and `B`. |
| `rotation` | yes | object | The repeating pattern. See below. |
| `name` | no | string | Calendar name shown in calendar apps. |
| `timezone` | no | string | IANA time zone, such as `America/Chicago`. |
| `exchange_time` | no | `HH:MM` | Usual handoff time, 24-hour. Carried into calendar descriptions only. |
| `recurring_overrides` | no | array | Holidays and other yearly dates. |
| `overrides` | no | array | One-time date ranges. |

## Rotation

Use **either** a preset **or** a custom cycle.

```json
{"preset": "2-2-5-5", "start_date": "2027-01-04", "first_parent": "B"}
```

```json
{"start_date": "2027-01-04", "cycle": [{"parent": "A", "days": 4}, {"parent": "B", "days": 3}]}
```

- `start_date` is the first day of the first cycle. Dates before it are computed backwards, so the pattern is defined for every date.
- Presets: `alternating-weeks`, `2-2-3`, `2-2-5-5`, `3-4-4-3`, `5-2-2-5`, `every-other-weekend`.
- `first_parent` (presets only) picks who has the first block. It defaults to the first parent listed.

## Recurring overrides

| Field | Meaning |
|---|---|
| `name` | Shown on the calendar event. Required. |
| `month` | 1 to 12. Required. |
| `day` | Fixed day of the month. Use this **or** `weekday` + `nth`. |
| `weekday`, `nth` | For example `"thursday"`, `4`. `nth` may be `-1` for the last one. |
| `offset_days` | Moves the start relative to the anchor date. Default `0`. |
| `days` | Length. Default `1`. |
| `parent` | The same parent every year. **Or** both of: |
| `parent_even_years`, `parent_odd_years` | Alternate by calendar year. |

## One-time overrides

| Field | Meaning |
|---|---|
| `start`, `end` | ISO dates, both inclusive. |
| `parent` | Who has those days. |
| `name` | Optional label. |

One-time overrides must not overlap each other (rule S013). They may overlap holidays; the one-time override wins.

## What a "day" means

Each calendar date belongs to exactly one parent: the parent responsible for that night. In calendar output each block becomes an all-day event, and the end date is exclusive, as RFC 5545 requires.
