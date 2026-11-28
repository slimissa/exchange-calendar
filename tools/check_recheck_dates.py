#!/usr/bin/env python3
"""
check_recheck_dates.py — Fails CI when a `recheck_date` in exchanges/*.json
has passed.

A `recheck_date` marks a value the registry holds on doubt: a day or an hours
change the exchange's own source does not yet confirm (for example a
`verification.coverage.sources` span with `unconfirmed` dates). The date says
when to look again. Without a gate, a recheck date passes silently and the
doubtful value stays in the registry as if confirmed. This turns every such
date into a red build on the day after it.

What is scanned
---------------
Every key named `recheck_date`, at any depth, in every exchanges/*.json file.
Each one is reported with the file's MIC, the date, and the JSON path of the
object it sits on (for example `verification.coverage.sources[1]`), plus that
object's `unconfirmed` list when it has one.

When a date has passed
----------------------
A recheck date D has passed when D is earlier than --today (default: today).
On D itself the check still passes: the recheck is due that day, not overdue.

A recheck date WARN_DAYS (14) days away or less prints a WARNING line; the
exit code does not change (the horizon of ADR 0015 section 5).

Where it runs
-------------
tools/local_gate.sh, so scripts/release.sh and CI's local-gate job (ADR 0016
R14, session 4e2): an overdue recheck date turns the gate red. Before 4e2 it
ran only as a separate CI step.

Exit codes
----------
    0  no recheck date has passed (every date found is printed)
    1  at least one recheck date has passed (each is printed)
    2  usage or parse problem: no exchanges directory, unreadable JSON, or a
       recheck_date that is not a YYYY-MM-DD string

Usage
-----
    python3 tools/check_recheck_dates.py
    python3 tools/check_recheck_dates.py --today 2027-12-01
    python3 tools/check_recheck_dates.py --exchanges path/to/exchanges
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parent.parent / "exchanges"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# A recheck date this many days away or less warns (ADR 0016 R14, 4e2).
WARN_DAYS = 14


class RecheckError(ValueError):
    """A recheck_date that cannot be read as a date."""


@dataclass(frozen=True)
class Recheck:
    mic: str
    recheck: date
    path: str
    unconfirmed: tuple = ()

    def describe(self) -> str:
        extra = f" (unconfirmed: {', '.join(self.unconfirmed)})" if self.unconfirmed else ""
        return f"{self.mic} {self.recheck.isoformat()} at {self.path}{extra}"


def _parse(value, mic: str, path: str) -> date:
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise RecheckError(f"{mic}: recheck_date at {path} is not YYYY-MM-DD: {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecheckError(f"{mic}: recheck_date at {path} is not a valid date: {value!r}") from exc


def _walk(node, mic: str, path: str, found: list) -> None:
    if isinstance(node, dict):
        if "recheck_date" in node:
            unconfirmed = node.get("unconfirmed") or ()
            found.append(Recheck(mic, _parse(node["recheck_date"], mic, path or "<root>"),
                                 path or "<root>", tuple(str(u) for u in unconfirmed)))
        for key, value in node.items():
            _walk(value, mic, f"{path}.{key}" if path else key, found)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _walk(value, mic, f"{path}[{i}]", found)


def collect(exchanges_dir: Path = DEFAULT_DIR) -> list[Recheck]:
    """Every recheck_date in exchanges_dir/*.json, sorted by date then MIC."""
    if not exchanges_dir.is_dir():
        raise FileNotFoundError(f"no exchanges directory: {exchanges_dir}")
    found: list[Recheck] = []
    for path in sorted(exchanges_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        mic = data.get("mic") or path.stem if isinstance(data, dict) else path.stem
        _walk(data, mic, "", found)
    return sorted(found, key=lambda r: (r.recheck, r.mic, r.path))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--today", type=date.fromisoformat, default=date.today(),
                        help="reference date, YYYY-MM-DD (default: today)")
    parser.add_argument("--exchanges", type=Path, default=DEFAULT_DIR,
                        help="directory of exchange JSON files")
    args = parser.parse_args(argv)
    try:
        rechecks = collect(args.exchanges)
    except (OSError, json.JSONDecodeError, RecheckError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    overdue = [r for r in rechecks if r.recheck < args.today]
    for r in rechecks:
        state = "PASSED" if r in overdue else "due"
        print(f"{state}: {r.describe()}")
    for r in rechecks:
        days = (r.recheck - args.today).days
        if 0 <= days <= WARN_DAYS:
            print(f"WARNING: recheck due in {days} day(s): {r.describe()}")
    if overdue:
        print(f"FAIL: {len(overdue)} recheck date(s) before {args.today.isoformat()}; "
              "re-check the value against the exchange's own source, then update "
              "or remove the recheck_date.")
        return 1
    print(f"OK: {len(rechecks)} recheck date(s), none before {args.today.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
