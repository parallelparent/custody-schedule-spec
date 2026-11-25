# Validation rules

`custody-schedule validate` runs two layers. First, the JSON Schema checks structure (code `S000`). If the structure is valid, the consistency rules below run. **Errors** stop calendar generation. **Warnings** mean the file probably doesn't say what its author meant.

| Code | Severity | Catches |
|---|---|---|
| S001 | error | Fewer than two parents defined. |
| S002 | error | `rotation.start_date` is missing or not a real date. |
| S003 | error | Unknown preset, or neither `preset` nor `cycle` given. |
| S004 | error | The rotation names a parent who isn't defined. |
| S005 | error | A rotation block has fewer than 1 day. |
| S006 | warning | The rotation only ever assigns one parent. |
| S007 | warning | Two consecutive rotation blocks go to the same parent; they could be one block. |
| S008 | error | `exchange_time` is not 24-hour `HH:MM` (for example `6pm`). |
| S010 | error | A one-time override has an invalid date. |
| S011 | error | A one-time override ends before it starts. |
| S012 | error | A one-time override assigns an undefined parent. |
| S013 | error | Two one-time overrides overlap, so the outcome would depend on file order. |
| S020 | error | A recurring override has no anchor, or has both a fixed day and a weekday rule. |
| S021 | error | `weekday` is not a weekday name. |
| S022 | error | A recurring override assigns an undefined parent. |
| S023 | error | Year alternation is missing either the even-year or the odd-year parent. |
| S024 | error | A recurring override lasts less than 1 day. |
| S025 | error | A fixed date that doesn't exist on any calendar, such as February 30. |

## Why S013 is an error and not a warning

If two one-time overrides cover the same day, one of them has to lose. Picking the later one in the file would make the result depend on how the file happened to be written. A schedule should mean the same thing no matter who edits it, so overlaps are rejected and the author has to resolve them.
