"""Command line interface: custody-schedule {validate,ics,summary,presets}."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from importlib import resources
from pathlib import Path

from . import core


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _schema() -> dict:
    here = Path(__file__).resolve()
    for candidate in (here.parent / "custody-schedule.schema.json",
                      here.parents[2] / "schema" / "custody-schedule.schema.json"):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    raise SystemExit("schema file not found")


def _range(args, schedule) -> tuple[date, date]:
    start = date.fromisoformat(args.start) if args.start else \
        date.fromisoformat(schedule["rotation"]["start_date"])
    end = date.fromisoformat(args.end) if args.end else date(start.year, 12, 31)
    return start, end


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="custody-schedule",
                                description="Validate and render parenting-time schedules.")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="check a schedule file")
    v.add_argument("file")
    for name, help_ in (("ics", "write an iCalendar file"),
                        ("summary", "days per parent in a date range")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("file")
        s.add_argument("--from", dest="start", help="YYYY-MM-DD (default: rotation start)")
        s.add_argument("--to", dest="end", help="YYYY-MM-DD (default: Dec 31 of start year)")
        if name == "ics":
            s.add_argument("-o", "--output", help="output path (default: stdout)")
    sub.add_parser("presets", help="list built-in rotation presets")
    args = p.parse_args(argv)

    try:
        if args.cmd == "presets":
            for k, blocks in core.PRESETS.items():
                pattern = " ".join(f"{'AB'[s]}{n}" for s, n in blocks)
                print(f"{k:<22} {pattern}   ({sum(n for _, n in blocks)}-day cycle)")
            return 0

        schedule = _load(args.file)

        if args.cmd == "validate":
            issues = core.validate_schema(schedule, _schema())
            if not issues:
                issues = core.validate(schedule)
            for i in issues:
                print(i)
            errors = [i for i in issues if i.severity == "error"]
            print(f"{'FAIL' if errors else 'OK'}: {len(errors)} error(s), "
                  f"{len(issues) - len(errors)} warning(s)")
            return 1 if errors else 0

        start, end = _range(args, schedule)
        if args.cmd == "summary":
            for parent, row in core.summarize(schedule, start, end).items():
                label = schedule["parents"][parent].get("label", parent)
                print(f"{label:<20} {row['days']:>4} days  {row['share']:.1%}")
            return 0

        text = core.to_ics(schedule, core.resolve(schedule, start, end))
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8", newline="")
            print(f"wrote {args.output}")
        else:
            sys.stdout.write(text)
        return 0
    except core.ScheduleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:  # e.g. piping to head
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
