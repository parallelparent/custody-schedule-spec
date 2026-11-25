"""Core logic for custody-schedule-spec.

Zero third-party dependencies. Everything here runs on the Python
standard library so the format can be implemented anywhere.

Model
-----
A schedule is a repeating *rotation* (a cycle of blocks, each block
assigning N consecutive days to one parent) anchored to a start date,
plus *overrides* that replace the rotation on specific days:

* recurring overrides: holidays that come back every year
  (a fixed date, or "the Nth weekday of a month"), optionally
  alternating parent by even/odd year
* one-time overrides: a specific date range for a specific parent

Precedence, lowest to highest: rotation < recurring < one-time.

A "day" is a calendar date. The parent assigned to a date is the
parent responsible for that date's overnight. ``exchange_time`` is
carried through to calendar output as information only.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, timedelta

SPEC_VERSION = "1.0"

# Each preset is a list of (parent_slot, days). Slot 0 is the
# rotation's first_parent, slot 1 is the other parent.
PRESETS: dict[str, list[tuple[int, int]]] = {
    "alternating-weeks": [(0, 7), (1, 7)],
    "2-2-3": [(0, 2), (1, 2), (0, 3), (1, 2), (0, 2), (1, 3)],
    "2-2-5-5": [(0, 2), (1, 2), (0, 5), (1, 5)],
    "3-4-4-3": [(0, 3), (1, 4), (0, 4), (1, 3)],
    "5-2-2-5": [(0, 5), (1, 2), (0, 2), (1, 5)],
    # Start the rotation on a Monday: parent 0 Mon-Fri, parent 1 Sat-Sun,
    # then parent 0 the full following week.
    "every-other-weekend": [(0, 5), (1, 2), (0, 7)],
}

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday"]

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class ScheduleError(ValueError):
    """Raised when a schedule cannot be resolved."""


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str  # "error" | "warning"
    message: str

    def __str__(self) -> str:
        return f"{self.code} [{self.severity}] {self.message}"


@dataclass(frozen=True)
class Block:
    parent: str
    start: date      # inclusive
    end: date        # inclusive
    source: str      # "rotation" | override name

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


# --------------------------------------------------------------------------
# parsing helpers
# --------------------------------------------------------------------------

def _d(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ScheduleError(f"{field}: '{value}' is not an ISO date (YYYY-MM-DD)")


def _other(parents: list[str], first: str) -> str:
    return next(p for p in parents if p != first)


def expand_cycle(schedule: dict) -> list[tuple[str, int]]:
    """Return the rotation as a list of (parent_id, days)."""
    rot = schedule.get("rotation") or {}
    parents = list((schedule.get("parents") or {}).keys())
    if "preset" in rot:
        preset = PRESETS.get(rot["preset"])
        if preset is None:
            raise ScheduleError(f"unknown preset '{rot['preset']}'")
        if len(parents) < 2:
            raise ScheduleError("presets need two parents")
        first = rot.get("first_parent", parents[0])
        second = _other(parents, first)
        slots = [first, second]
        return [(slots[s], n) for s, n in preset]
    cycle = rot.get("cycle")
    if not cycle:
        raise ScheduleError("rotation needs either 'preset' or 'cycle'")
    return [(b["parent"], int(b["days"])) for b in cycle]


def nth_weekday(year: int, month: int, weekday: str, nth: int) -> date:
    """nth >= 1 counts from the start of the month; nth == -1 is the last."""
    wd = WEEKDAYS.index(weekday.lower())
    if nth == -1:
        nxt = date(year + (month == 12), month % 12 + 1, 1)
        d = nxt - timedelta(days=1)
        while d.weekday() != wd:
            d -= timedelta(days=1)
        return d
    d = date(year, month, 1)
    while d.weekday() != wd:
        d += timedelta(days=1)
    d += timedelta(weeks=nth - 1)
    if d.month != month:
        raise ScheduleError(f"there is no {nth}th {weekday} in {year}-{month:02d}")
    return d


def recurring_dates(rule: dict, year: int) -> tuple[date, date]:
    """Resolve a recurring override to (start, end) for a given year."""
    if "day" in rule:
        anchor = date(year, rule["month"], rule["day"])
    else:
        anchor = nth_weekday(year, rule["month"], rule["weekday"], rule["nth"])
    start = anchor + timedelta(days=rule.get("offset_days", 0))
    end = start + timedelta(days=rule.get("days", 1) - 1)
    return start, end


def recurring_parent(rule: dict, year: int) -> str | None:
    if "parent" in rule:
        return rule["parent"]
    key = "parent_even_years" if year % 2 == 0 else "parent_odd_years"
    return rule.get(key)


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

def validate(schedule: dict) -> list[Issue]:
    """Check a schedule for internal contradictions.

    Schema validation (types, required fields) is handled separately by
    ``validate_schema``; these rules catch schedules that are well formed
    but cannot mean what they say.
    """
    issues: list[Issue] = []
    E = lambda c, m: issues.append(Issue(c, "error", m))      # noqa: E731
    W = lambda c, m: issues.append(Issue(c, "warning", m))    # noqa: E731

    parents = schedule.get("parents") or {}
    ids = set(parents)
    if len(ids) < 2:
        E("S001", "a schedule needs at least two parents")

    rot = schedule.get("rotation") or {}
    try:
        _d(rot.get("start_date"), "rotation.start_date")
    except ScheduleError as exc:
        E("S002", str(exc))

    try:
        cycle = expand_cycle(schedule)
    except ScheduleError as exc:
        E("S003", str(exc))
        cycle = []

    if "first_parent" in rot and rot["first_parent"] not in ids:
        E("S004", f"rotation.first_parent '{rot['first_parent']}' is not a defined parent")
    for p, n in cycle:
        if p not in ids:
            E("S004", f"rotation uses parent '{p}', which is not defined")
        if n < 1:
            E("S005", f"rotation block for '{p}' has {n} days; every block needs at least 1")
    if cycle and len({p for p, _ in cycle}) < 2:
        W("S006", "the rotation only ever assigns one parent")
    for i in range(1, len(cycle)):
        if cycle[i][0] == cycle[i - 1][0]:
            W("S007", f"rotation blocks {i} and {i + 1} both go to '{cycle[i][0]}'; "
                      "they could be one block")

    et = schedule.get("exchange_time")
    if et is not None and not _TIME_RE.match(str(et)):
        E("S008", f"exchange_time '{et}' must be 24-hour HH:MM")

    # one-time overrides
    spans: list[tuple[date, date, str]] = []
    for i, ov in enumerate(schedule.get("overrides") or []):
        label = ov.get("name", f"overrides[{i}]")
        try:
            s, e = _d(ov.get("start"), f"{label}.start"), _d(ov.get("end"), f"{label}.end")
        except ScheduleError as exc:
            E("S010", str(exc))
            continue
        if e < s:
            E("S011", f"'{label}' ends ({e}) before it starts ({s})")
        if ov.get("parent") not in ids:
            E("S012", f"'{label}' assigns parent '{ov.get('parent')}', which is not defined")
        for os_, oe, ol in spans:
            if s <= oe and os_ <= e:
                E("S013", f"'{label}' overlaps '{ol}'; one-time overrides must not overlap")
        spans.append((s, e, label))

    # recurring overrides
    for i, rule in enumerate(schedule.get("recurring_overrides") or []):
        label = rule.get("name", f"recurring_overrides[{i}]")
        has_fixed = "day" in rule
        has_nth = "weekday" in rule and "nth" in rule
        if has_fixed == has_nth:
            E("S020", f"'{label}' needs exactly one anchor: 'day' or 'weekday'+'nth'")
        if "weekday" in rule and str(rule["weekday"]).lower() not in WEEKDAYS:
            E("S021", f"'{label}' weekday '{rule['weekday']}' is not a weekday name")
        if "parent" in rule:
            if rule["parent"] not in ids:
                E("S022", f"'{label}' assigns parent '{rule['parent']}', which is not defined")
        else:
            for key in ("parent_even_years", "parent_odd_years"):
                if key not in rule:
                    E("S023", f"'{label}' alternates by year but has no '{key}'")
                elif rule[key] not in ids:
                    E("S022", f"'{label}' {key} '{rule[key]}' is not a defined parent")
        if rule.get("days", 1) < 1:
            E("S024", f"'{label}' must last at least 1 day")
        if has_fixed and not has_nth:
            try:
                date(2024, rule["month"], rule["day"])  # leap year accepts Feb 29
            except (ValueError, TypeError, KeyError):
                E("S025", f"'{label}' month/day is not a real calendar date")
    return issues


def validate_schema(schedule: dict, schema: dict) -> list[Issue]:
    """Validate against the JSON Schema. Hard-stops if jsonschema is
    missing rather than silently reporting a clean result."""
    try:
        import jsonschema  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "jsonschema is not installed, so schema validation cannot run. "
            "Install it with: pip install jsonschema") from exc
    v = jsonschema.Draft202012Validator(schema)
    return [Issue("S000", "error", f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}")
            for e in sorted(v.iter_errors(schedule), key=lambda e: list(e.path))]


# --------------------------------------------------------------------------
# resolution
# --------------------------------------------------------------------------

def rotation_parent(schedule: dict, day: date) -> str:
    cycle = expand_cycle(schedule)
    length = sum(n for _, n in cycle)
    start = _d(schedule["rotation"]["start_date"], "rotation.start_date")
    offset = (day - start).days % length
    for parent, n in cycle:
        if offset < n:
            return parent
        offset -= n
    raise AssertionError("unreachable")


def resolve_days(schedule: dict, start: date, end: date) -> list[tuple[date, str, str]]:
    """Return [(date, parent, source)] for every date in [start, end]."""
    if end < start:
        raise ScheduleError("end is before start")
    errors = [i for i in validate(schedule) if i.severity == "error"]
    if errors:
        raise ScheduleError("schedule has errors:\n" + "\n".join(map(str, errors)))

    n = (end - start).days + 1
    days = [start + timedelta(days=i) for i in range(n)]
    out = {d: (rotation_parent(schedule, d), "rotation") for d in days}

    for rule in schedule.get("recurring_overrides") or []:
        for year in range(start.year - 1, end.year + 1):
            try:
                s, e = recurring_dates(rule, year)
            except ScheduleError:
                continue
            parent = recurring_parent(rule, year)
            d = s
            while d <= e:
                if d in out:
                    out[d] = (parent, rule.get("name", "recurring override"))
                d += timedelta(days=1)

    for ov in schedule.get("overrides") or []:
        s, e = _d(ov["start"], "start"), _d(ov["end"], "end")
        d = s
        while d <= e:
            if d in out:
                out[d] = (ov["parent"], ov.get("name", "override"))
            d += timedelta(days=1)

    return [(d, *out[d]) for d in days]


def resolve(schedule: dict, start: date, end: date) -> list[Block]:
    """Resolve to contiguous blocks (same parent and same source merge)."""
    blocks: list[Block] = []
    for d, parent, source in resolve_days(schedule, start, end):
        if blocks and blocks[-1].parent == parent and blocks[-1].source == source \
                and blocks[-1].end + timedelta(days=1) == d:
            b = blocks[-1]
            blocks[-1] = Block(b.parent, b.start, d, b.source)
        else:
            blocks.append(Block(parent, d, d, source))
    return blocks


def summarize(schedule: dict, start: date, end: date) -> dict[str, dict]:
    """Days and share of days per parent across the range."""
    counts: dict[str, int] = {p: 0 for p in schedule["parents"]}
    for _, parent, _ in resolve_days(schedule, start, end):
        counts[parent] += 1
    total = sum(counts.values())
    return {p: {"days": c, "share": round(c / total, 4)} for p, c in counts.items()}


# --------------------------------------------------------------------------
# iCalendar output (RFC 5545)
# --------------------------------------------------------------------------

def _esc(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
                .replace(",", "\\,").replace("\n", "\\n"))


def _fold(line: str) -> str:
    """Fold lines longer than 75 octets, per RFC 5545 section 3.1."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        limit = 75 if not parts else 74
        if len(cur) + len(b) > limit:
            parts.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    parts.append(cur.decode("utf-8"))
    return "\r\n ".join(parts)


def to_ics(schedule: dict, blocks: list[Block], stamp: str = "20260101T000000Z") -> str:
    """Render blocks as all-day events. ``stamp`` is fixed by default so
    output is reproducible; pass the current UTC time if you prefer."""
    labels = {pid: (p or {}).get("label", pid) for pid, p in schedule["parents"].items()}
    name = schedule.get("name", "Parenting time")
    tz = schedule.get("timezone")
    et = schedule.get("exchange_time")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//custody-schedule-spec//EN", "CALSCALE:GREGORIAN",
             f"X-WR-CALNAME:{_esc(name)}"]
    if tz:
        lines.append(f"X-WR-TIMEZONE:{tz}")
    for b in blocks:
        uid_src = f"{name}|{b.parent}|{b.start}|{b.end}|{b.source}"
        uid = hashlib.sha1(uid_src.encode()).hexdigest()[:20] + "@custody-schedule-spec"
        summary = labels[b.parent] + ("" if b.source == "rotation" else f" ({b.source})")
        desc = f"{b.days} day(s) with {labels[b.parent]}."
        if et:
            desc += f" Exchange time {et}" + (f" {tz}" if tz else "") + "."
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{b.start:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{b.end + timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{_esc(summary)}", f"DESCRIPTION:{_esc(desc)}",
                  "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(l) for l in lines) + "\r\n"
