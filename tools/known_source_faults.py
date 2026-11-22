#!/usr/bin/env python3
"""Expiring known-source-fault entries for the live fetcher check (4b4).

A known fault is a defect in an exchange's own page (not in the fetcher)
that makes the fetcher fail for a while: the entry lets the weekly check
show the failure without escalating it, and forces a second look when it
expires (at most 70 days after it was opened).

Rules (applied by tools/live_fetcher_check.py):
  - a FAIL or TRANSIENT whose reason matches an active entry for its MIC
    -> KNOWN (shown, not escalated, not failing the job);
  - the same after `expires` -> FAIL ("known fault expired on ...");
  - a failure of a listed MIC that does not match its entry -> FAIL;
  - a listed MIC that passes -> PASS with the warning "fault cleared,
    remove the entry".

Usage: python3 tools/known_source_faults.py --check   (validate the file)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "tools" / "known_source_faults.json"
MAX_DAYS = 70
FIELDS = ("mic", "match", "reason", "evidence", "opened", "expires")


def load(path: Path = PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")).get("faults", [])


def problems(entries: list[dict]) -> list[str]:
    out: list[str] = []
    for n, e in enumerate(entries):
        tag = f"entry {n} ({e.get('mic', '?')})"
        missing = [f for f in FIELDS if not e.get(f)]
        if missing:
            out.append(f"{tag}: missing {', '.join(missing)}")
            continue
        extra = sorted(set(e) - set(FIELDS))
        if extra:
            out.append(f"{tag}: unknown field(s) {', '.join(extra)}")
        if not re.fullmatch(r"X[A-Z0-9]{3}|[A-Z]{4}", e["mic"]):
            out.append(f"{tag}: mic {e['mic']!r} is not a MIC")
        try:
            re.compile(e["match"])
        except re.error as err:
            out.append(f"{tag}: match is not a regular expression ({err})")
        try:
            opened = dt.date.fromisoformat(e["opened"])
            expires = dt.date.fromisoformat(e["expires"])
        except ValueError:
            out.append(f"{tag}: opened and expires must be ISO dates")
            continue
        if expires < opened:
            out.append(f"{tag}: expires {expires} is before opened {opened}")
        elif (expires - opened).days > MAX_DAYS:
            out.append(f"{tag}: expires {expires} is more than {MAX_DAYS} days after opened {opened}")
    mics = [e.get("mic") for e in entries]
    for m in sorted({m for m in mics if mics.count(m) > 1}):
        out.append(f"{m}: more than one entry")
    return out


def apply(result: dict, entries: list[dict], today: dt.date) -> dict:
    """Return the result with the known-fault rules applied (a new dict)."""
    entry = next((e for e in entries if e.get("mic") == result.get("mic")), None)
    if entry is None:
        return result
    r = dict(result)
    status = r.get("status")
    if status == "PASS":
        r["warning"] = (f"fault cleared, remove the entry for {entry['mic']} from "
                        f"tools/known_source_faults.json (opened {entry['opened']})")
        return r
    if status not in ("FAIL", "TRANSIENT"):
        return r
    reason = r.get("reason") or ""
    if not re.search(entry["match"], reason):
        r["status"] = "FAIL"
        r["reason"] = f"{reason} (differs from the known fault listed for {entry['mic']})"
        return r
    if today > dt.date.fromisoformat(entry["expires"]):
        r["status"] = "FAIL"
        r["reason"] = f"known fault expired on {entry['expires']}: {reason}"
        return r
    r["status"] = "KNOWN"
    r["known_fault"] = {k: entry[k] for k in ("reason", "opened", "expires")}
    return r


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="validate the file")
    ap.add_argument("--path", type=Path, default=PATH)
    args = ap.parse_args(argv)
    entries = load(args.path)
    found = problems(entries)
    for p in found:
        print(f"error: {p}")
    if found:
        return 1
    print(f"OK: {len(entries)} known source fault(s), each expiring within {MAX_DAYS} days of opening")
    return 0


if __name__ == "__main__":
    sys.exit(main())
