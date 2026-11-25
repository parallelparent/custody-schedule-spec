"""Tests. Run with:  python -m pytest   or   python tests/test_core.py"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from custody_schedule import core  # noqa: E402
from custody_schedule.cli import main  # noqa: E402

EX = ROOT / "examples"
SCHEMA = json.loads((ROOT / "schema" / "custody-schedule.schema.json").read_text())


def load(name):
    return json.loads((EX / name).read_text())


def codes(schedule):
    return {i.code for i in core.validate(schedule)}


def test_presets_are_balanced_two_week_cycles():
    for name, blocks in core.PRESETS.items():
        if name == "every-other-weekend":
            continue
        a = sum(n for s, n in blocks if s == 0)
        b = sum(n for s, n in blocks if s == 1)
        assert a == b == 7, name


def test_2_2_3_pattern_over_two_weeks():
    s = load("2-2-3-with-holidays.json")
    days = core.resolve_days(s, date(2027, 1, 4), date(2027, 1, 17))
    got = "".join(p for _, p, _ in days)
    assert got == "AABBAAABBAABBB", got


def test_rotation_works_before_start_date():
    s = load("alternating-weeks.json")
    # one cycle (14 days) before the start, the pattern repeats exactly
    assert core.rotation_parent(s, date(2026, 12, 20)) == core.rotation_parent(s, date(2027, 1, 3))


def test_first_parent_is_respected():
    s = load("alternating-weeks.json")
    assert core.rotation_parent(s, date(2027, 1, 3)) == "B"
    assert core.rotation_parent(s, date(2027, 1, 10)) == "A"


def test_nth_weekday_holidays():
    assert core.nth_weekday(2027, 11, "thursday", 4) == date(2027, 11, 25)
    assert core.nth_weekday(2028, 11, "thursday", 4) == date(2028, 11, 23)
    assert core.nth_weekday(2027, 5, "monday", -1) == date(2027, 5, 31)   # Memorial Day
    assert core.nth_weekday(2027, 6, "sunday", 3) == date(2027, 6, 20)


def test_thanksgiving_alternates_by_year_parity():
    s = load("2-2-3-with-holidays.json")
    d27 = dict((d, p) for d, p, _ in core.resolve_days(s, date(2027, 11, 24), date(2027, 11, 28)))
    d28 = dict((d, p) for d, p, _ in core.resolve_days(s, date(2028, 11, 22), date(2028, 11, 26)))
    assert set(d27.values()) == {"B"}   # odd year
    assert set(d28.values()) == {"A"}   # even year


def test_one_time_beats_recurring_beats_rotation():
    s = load("2-2-3-with-holidays.json")
    s["overrides"].append({"name": "Swap", "start": "2027-12-25", "end": "2027-12-25", "parent": "B"})
    got = dict((d, (p, src)) for d, p, src in core.resolve_days(s, date(2027, 12, 24), date(2027, 12, 25)))
    assert got[date(2027, 12, 24)] == ("A", "Christmas Eve")   # recurring, odd year
    assert got[date(2027, 12, 25)] == ("B", "Swap")            # one-time wins


def test_override_crossing_year_boundary():
    s = load("custom-cycle.json")
    s["recurring_overrides"] = [{"name": "New Year", "month": 12, "day": 31, "days": 2, "parent": "B"}]
    got = dict((d, p) for d, p, _ in core.resolve_days(s, date(2028, 1, 1), date(2028, 1, 1)))
    assert got[date(2028, 1, 1)] == "B"   # started Dec 31 2027, outside the range


def test_blocks_merge_and_split_on_source():
    s = load("2-2-3-with-holidays.json")
    blocks = core.resolve(s, date(2027, 7, 8), date(2027, 7, 19))
    sources = [b.source for b in blocks]
    assert "Summer trip" in sources
    trip = next(b for b in blocks if b.source == "Summer trip")
    assert (trip.start, trip.end, trip.days) == (date(2027, 7, 10), date(2027, 7, 17), 8)


def test_summary_shares_sum_to_one():
    s = load("alternating-weeks.json")
    sm = core.summarize(s, date(2027, 1, 3), date(2027, 1, 30))
    assert sm["A"]["days"] == sm["B"]["days"] == 14
    assert abs(sum(r["share"] for r in sm.values()) - 1) < 1e-9


def test_broken_example_reports_each_defect():
    c = codes(load("broken-overlap.json"))
    assert {"S011", "S012", "S013"} <= c, c


def test_rule_catalog_edge_cases():
    base = load("custom-cycle.json")
    one = dict(base, parents={"A": {}})
    assert "S001" in codes(one)
    assert "S003" in codes(dict(base, rotation={"start_date": "2027-01-01", "preset": "9-9-9"}))
    assert "S004" in codes(dict(base, rotation={"start_date": "2027-01-01",
                                                "cycle": [{"parent": "Z", "days": 3}, {"parent": "A", "days": 3}]}))
    assert "S007" in codes(dict(base, rotation={"start_date": "2027-01-01",
                                                "cycle": [{"parent": "A", "days": 3}, {"parent": "A", "days": 3},
                                                          {"parent": "B", "days": 1}]}))
    assert "S008" in codes(dict(base, exchange_time="6pm"))
    assert "S020" in codes(dict(base, recurring_overrides=[{"name": "x", "month": 1, "parent": "A"}]))
    assert "S023" in codes(dict(base, recurring_overrides=[{"name": "x", "month": 1, "day": 1,
                                                             "parent_even_years": "A"}]))
    assert "S025" in codes(dict(base, recurring_overrides=[{"name": "x", "month": 2, "day": 30, "parent": "A"}]))
    assert not [i for i in core.validate(base) if i.severity == "error"]


def test_resolve_refuses_invalid_schedule():
    try:
        core.resolve(load("broken-overlap.json"), date(2027, 1, 1), date(2027, 1, 2))
    except core.ScheduleError:
        return
    raise AssertionError("expected ScheduleError")


def test_ics_is_well_formed():
    s = load("2-2-3-with-holidays.json")
    text = core.to_ics(s, core.resolve(s, date(2027, 1, 4), date(2027, 12, 31)))
    lines = text.split("\r\n")
    assert lines[0] == "BEGIN:VCALENDAR" and lines[-2] == "END:VCALENDAR"
    assert text.count("BEGIN:VEVENT") == text.count("END:VEVENT") > 50
    assert all(len(l.encode()) <= 75 for l in lines)
    assert "DTSTART;VALUE=DATE:20270104" in text and "DTEND;VALUE=DATE:20270106" in text
    uids = [l for l in lines if l.startswith("UID:")]
    assert len(uids) == len(set(uids))
    # reproducible
    assert text == core.to_ics(s, core.resolve(s, date(2027, 1, 4), date(2027, 12, 31)))


def test_examples_match_schema():
    for f in EX.glob("*.json"):
        issues = core.validate_schema(json.loads(f.read_text()), SCHEMA)
        if f.name.startswith("broken"):
            continue
        assert not issues, (f.name, issues)


def test_cli_exit_codes(capsys=None):
    assert main(["validate", str(EX / "2-2-3-with-holidays.json")]) == 0
    assert main(["validate", str(EX / "broken-overlap.json")]) == 1
    assert main(["presets"]) == 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok  ", fn.__name__)
    print(f"{len(fns)} passed")
