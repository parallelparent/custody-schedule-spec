"""custody-schedule-spec: an open format for parenting-time rotations."""
from .core import (PRESETS, SPEC_VERSION, Block, Issue, ScheduleError,
                   expand_cycle, resolve, resolve_days, summarize, to_ics,
                   validate, validate_schema)

__version__ = "1.0.0"
__all__ = ["PRESETS", "SPEC_VERSION", "Block", "Issue", "ScheduleError",
           "expand_cycle", "resolve", "resolve_days", "summarize", "to_ics",
           "validate", "validate_schema", "__version__"]
