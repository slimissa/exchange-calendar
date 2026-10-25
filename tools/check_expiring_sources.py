#!/usr/bin/env python3
"""
check_expiring_sources.py — Fails CI when a source in the "Expiring sources"
table of docs/FETCHERS.md has passed its expiry.

The table documents sources that stop being current on a known trigger. This
turns the dates in its "Expiry / trigger" column into a gate, so maintainers
learn that a URL needs replacing from a red build rather than from a wrong
calendar.

Which dates count
-----------------
Only dates that are stated as an expiry. The column also holds dates that are
NOT expiries (for example "the two latest releases 2024-11-08 and
2025-12-23"), and counting every date would fail on the day this gate is
added. A cell expires on the earliest of:

    until|expires|expiry|expiring <DATE>    e.g. "allowlisted until 2027-06-01"
    <YYYY> to <YYYY>                        coverage range; expires at the end
                                            of the second year ("2026 to 2028")

where <DATE> is YYYY-MM-DD, YYYY-MM or YYYY. A YYYY-MM-DD date is covered
through that day. A YYYY-MM date is covered through the end of that month, a
YYYY through 31 December. The source is expired when today is later than that.
A cell with none of these (for example "current year") is ignored.

Table rules
-----------
The table is the first pipe table under the "## Expiring sources" heading. Its
header must contain an "Expiry / trigger" column. A keyword followed by
something date-shaped that is not a valid date (2027-13-01, 2027/06/01,
2027-6-1) is an error, not a silent skip.

Exit codes
----------
    0  no source has expired
    1  at least one source has expired (each is printed)
    2  usage or parse problem: file missing, section or table missing,
       column missing, malformed date, or no dated row found at all

Usage
-----
    python3 tools/check_expiring_sources.py
    python3 tools/check_expiring_sources.py --today 2028-01-01
    python3 tools/check_expiring_sources.py --file path/to/FETCHERS.md
"""

from __future__ import annotations

import argparse
import calendar
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "docs" / "FETCHERS.md"
HEADING = "## Expiring sources"
COLUMN = "expiry / trigger"

# Keyword followed by a date-shaped token; validated strictly afterwards.
KEYWORD_RE = re.compile(
    r"\b(?:until|expires?|expiry|expiring)\s+(\d{4}(?:[-/.]\d+)*)", re.IGNORECASE
)
RANGE_RE = re.compile(r"\b(\d{4})\s+to\s+(\d{4})\b")
STRICT_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")


class ParseProblem(Exception):
    """Raised for anything that should exit 2."""


def last_covered_day(token: str) -> date:
    """Last day a YYYY, YYYY-MM or YYYY-MM-DD token covers."""
    m = STRICT_RE.match(token)
    if not m:
        raise ParseProblem(f"malformed date {token!r} (use YYYY-MM-DD, YYYY-MM or YYYY)")
    year, month, day = (int(g) if g else None for g in m.groups())
    try:
        if month is None:
            return date(year, 12, 31)
        if day is None:
            return date(year, month, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    except ValueError as exc:
        raise ParseProblem(f"invalid date {token!r}: {exc}") from None


def cell_expiry(cell: str) -> date | None:
    """Earliest stated expiry in a cell, or None if it states none."""
    found = [last_covered_day(t) for t in KEYWORD_RE.findall(cell)]
    found += [last_covered_day(b) for _, b in RANGE_RE.findall(cell)]
    return min(found) if found else None


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_rows(text: str) -> tuple[list[str], list[list[str]]]:
    """Header and body rows of the first table under HEADING."""
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == HEADING)
    except StopIteration:
        raise ParseProblem(f"no {HEADING!r} section") from None
    rows: list[str] = []
    for ln in lines[start + 1:]:
        if ln.startswith("## "):
            break
        if ln.lstrip().startswith("|"):
            rows.append(ln)
        elif rows:
            break
    if len(rows) < 3:
        raise ParseProblem(f"no table under {HEADING!r}")
    header = [h.lower() for h in split_row(rows[0])]
    return header, [split_row(r) for r in rows[2:]]


def check(text: str, today: date) -> tuple[list[str], int]:
    """Return (expired messages, number of rows with an expiry)."""
    header, body = table_rows(text)
    if COLUMN not in header:
        raise ParseProblem(f"table has no {COLUMN!r} column (found: {header})")
    idx = header.index(COLUMN)
    expired: list[str] = []
    dated = 0
    for n, row in enumerate(body, 1):
        if len(row) <= idx:
            raise ParseProblem(f"row {n} has {len(row)} cells, expected {len(header)}")
        try:
            expiry = cell_expiry(row[idx])
        except ParseProblem as exc:
            raise ParseProblem(f"row {n} ({row[0]}): {exc}") from None
        if expiry is None:
            continue
        dated += 1
        if today > expiry:
            expired.append(
                f"{row[0]}: expired {expiry.isoformat()} "
                f"(today {today.isoformat()}). Action: "
                f"{row[idx + 1] if len(row) > idx + 1 else 'see docs/FETCHERS.md'}"
            )
    return expired, dated


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    p.add_argument("--file", type=Path, default=DEFAULT_FILE, help="FETCHERS.md path")
    args = p.parse_args(argv)
    try:
        today = date.fromisoformat(args.today) if args.today else date.today()
    except ValueError:
        print(f"error: --today must be YYYY-MM-DD, got {args.today!r}", file=sys.stderr)
        return 2
    try:
        text = args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2
    try:
        expired, dated = check(text, today)
    except ParseProblem as exc:
        print(f"error: {args.file.name}: {exc}", file=sys.stderr)
        return 2
    if dated == 0:
        print("error: no row in the table states an expiry; the gate would check nothing",
              file=sys.stderr)
        return 2
    for msg in expired:
        print(f"EXPIRED  {msg}")
    if expired:
        print(f"\n{len(expired)} source(s) past expiry. Update the URL, then the row.")
        return 1
    print(f"OK: {dated} dated row(s), none expired as of {today.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
