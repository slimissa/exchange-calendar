#!/usr/bin/env python3
"""
check_stale_verifications.py — Flags stale `Last verified` dates in BLOCKED.md.

BLOCKED.md documents every manually-tracked exchange (a source that has no
automated fetcher, or an automated fetcher whose live health needs periodic
re-confirmation) with a `**Last verified:** YYYY-MM-DD` line under each
`##`/`###` section heading. Sources drift — pages get redesigned, bot
detection gets added, domains die — so a verdict that hasn't been re-checked
in a long time is a liability if it's silently trusted forever.

This script parses every `Last verified` line in BLOCKED.md and fails if any
of them is older than 18 months (549 days) relative to today.

Usage:
    check_stale_verifications.py [path]

Defaults:
    path = "BLOCKED.md" (relative to the current working directory)

Exit codes:
    0 — All `Last verified` dates are within the 18-month window
    1 — At least one date is stale, missing, or malformed
    2 — The target file itself is missing or unreadable
"""

import re
import sys
from datetime import date, timedelta
from pathlib import Path

STALENESS_WINDOW_DAYS = 549  # ~18 months

# Matches a "## " or "### " heading line, capturing the heading text.
HEADING_RE = re.compile(r"^(#{2,3})\s+(.*\S)\s*$")

# Matches a "**Last verified:** YYYY-MM-DD" line (the value is captured
# loosely so malformed dates can be reported rather than silently skipped).
LAST_VERIFIED_RE = re.compile(r"^\*\*Last verified:\*\*\s*(\S+)\s*$")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Entry:
    """One exchange section's `Last verified` status."""

    def __init__(self, heading, raw_value, line_no):
        self.heading = heading
        self.raw_value = raw_value
        self.line_no = line_no
        self.parsed_date = None
        self.error = None

        if raw_value is None:
            self.error = "missing Last verified line"
            return

        if not DATE_RE.match(raw_value):
            self.error = f"malformed date {raw_value!r} (expected YYYY-MM-DD)"
            return

        try:
            year, month, day = (int(part) for part in raw_value.split("-"))
            self.parsed_date = date(year, month, day)
        except ValueError as exc:
            self.error = f"malformed date {raw_value!r} ({exc})"

    def is_stale(self, cutoff):
        if self.error is not None:
            return True
        return self.parsed_date < cutoff

    def reason(self, cutoff):
        if self.error is not None:
            return self.error
        age_days = (date.today() - self.parsed_date).days
        return f"last verified {self.parsed_date.isoformat()} ({age_days} days ago, cutoff is {cutoff.isoformat()})"


def parse_entries(text):
    """Walk BLOCKED.md line by line, pairing each ##/### heading with the
    next `Last verified` line that follows it (before the next heading, if
    any). A heading with no `Last verified` line before the next heading
    (or end of file) is recorded with raw_value=None.
    """
    lines = text.splitlines()
    entries = []

    current_heading = None
    current_heading_line = None
    awaiting_value = False

    def flush_missing():
        if current_heading is not None and awaiting_value:
            entries.append(Entry(current_heading, None, current_heading_line))

    for i, line in enumerate(lines, start=1):
        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush_missing()
            current_heading = heading_match.group(2)
            current_heading_line = i
            awaiting_value = True
            continue

        if awaiting_value:
            lv_match = LAST_VERIFIED_RE.match(line.strip())
            if lv_match:
                entries.append(Entry(current_heading, lv_match.group(1), i))
                awaiting_value = False

    flush_missing()
    return entries


def check(path):
    """Return (exit_code, report_lines)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return 2, [f"ERROR: could not read {path}: {exc}"]

    entries = parse_entries(text)
    cutoff = date.today() - timedelta(days=STALENESS_WINDOW_DAYS)

    if not entries:
        return 2, [f"ERROR: no '##'/'###' sections with a Last verified line found in {path}"]

    stale = [e for e in entries if e.is_stale(cutoff)]

    report = []
    report.append(f"Checked {len(entries)} section(s) in {path}.")
    report.append(f"Staleness cutoff: {cutoff.isoformat()} (entries older than {STALENESS_WINDOW_DAYS} days / 18 months fail).")

    if not stale:
        report.append("All entries are within the 18-month window.")
        return 0, report

    report.append("")
    report.append(f"STALE ENTRIES ({len(stale)}):")
    for e in stale:
        report.append(f"  - line {e.line_no}: {e.heading} — {e.reason(cutoff)}")

    return 1, report


def main(argv):
    path = argv[1] if len(argv) > 1 else "BLOCKED.md"
    exit_code, report = check(path)
    for line in report:
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
