"""Helpers for `regular_hours`, which is one object or a dated list.

An exchange whose hours never changed stores one object:

    "regular_hours": {"open": "09:30", "close": "16:00"}

An exchange whose hours changed stores a list, one entry per regime, each
with the first date it applies:

    "regular_hours": [
      {"effective_from": "1997-01-01", "open": "09:00", "close": "15:00"},
      {"effective_from": "2024-11-05", "open": "09:00", "close": "15:30"}
    ]

The entry in force on a date is the latest one whose effective_from is on or
before it; a date before the first entry gets the first entry. The "current"
hours are the latest entry.
"""
from __future__ import annotations

import datetime as dt


def history(regular_hours) -> list[dict]:
    """Every entry, oldest first (a single object is one undated entry)."""
    if isinstance(regular_hours, list):
        return sorted(regular_hours, key=lambda e: e["effective_from"])
    return [regular_hours]


def current(regular_hours) -> dict:
    """The hours in force now: the single object, or the latest dated entry."""
    return history(regular_hours)[-1]


def on(regular_hours, day: dt.date | str) -> dict:
    """The entry in force on `day`."""
    iso = day if isinstance(day, str) else day.isoformat()
    in_force = history(regular_hours)[0]
    for entry in history(regular_hours):
        if entry.get("effective_from", "") <= iso:
            in_force = entry
    return in_force


def problems(regular_hours, generation_start: str | None = None) -> list[str]:
    """Reasons a regular_hours value is inconsistent; empty when sound.

    Format (HH:MM, YYYY-MM-DD) is the schema's job. This checks what a schema
    pattern cannot: open before close in every entry, and for a list, strictly
    increasing unique effective_from dates with the first no later than the
    start of the exchange's generation_range, so no generated date falls
    before the first entry.
    """
    out: list[str] = []
    if isinstance(regular_hours, list):
        dates = [e.get("effective_from") for e in regular_hours]
        if not regular_hours:
            return ["regular_hours list is empty"]
        if any(not isinstance(d, str) for d in dates):
            return ["every regular_hours entry in a list needs effective_from"]
        if dates != sorted(set(dates)):
            out.append("regular_hours effective_from dates must be unique and in ascending order")
        if generation_start and min(dates) > generation_start:
            out.append(f"first regular_hours effective_from ({min(dates)}) is after "
                       f"generation_range start ({generation_start})")
    for e in history(regular_hours):
        if e.get("open", "") >= e.get("close", ""):
            label = e.get("effective_from", "")
            out.append(f"regular_hours open ({e.get('open')}) must be before close "
                       f"({e.get('close')})" + (f" for entry {label}" if label else ""))
    return out
