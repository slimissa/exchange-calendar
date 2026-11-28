#!/usr/bin/env python3
"""Expiring hours-evidence exemptions for check 6 (ADR 0015, session 4b13).

An exemption carries a reference_compared exchange whose official hours
could not be read, so check 6 (tools/check_verification.py) can block for
every other exchange. It records what was tried and expires at most 70
days after it was added. It is never evidence: it changes no data and
raises no count.

Rules (applied by tools/check_verification.py through problems()):
  errors (the check fails)
    - a required field is missing or empty; a source record or a lead lacks
      its parts; a lead is not labelled "unread lead";
    - added / expires are not ISO dates, expires is before added, or more
      than 70 days after it;
    - the exemption has expired (today is after expires);
    - the MIC is not an exchange of the registry, or not reference_compared;
    - the MIC already has verified current hours or a schema_limited item
      for the entry in force (stale exemption: remove it);
    - a MIC has more than one exemption.
  warnings (the check passes)
    - the exemption expires within 14 days.

`today` is a parameter everywhere, so tests fix the date.

Usage: python3 tools/hours_evidence_exemptions.py --check [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "tools" / "hours_evidence_exemptions.json"
MAX_DAYS = 70
WARN_DAYS = 14
FIELDS = ("mic", "reason", "sources_tried", "leads", "added", "expires", "next_action")
SOURCE_FIELDS = ("source", "tried", "outcome")
LEAD_FIELDS = ("label", "pointer")
LEAD_LABEL = "unread lead"


def load(path: Path = PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")).get("exemptions", [])


def _date(text) -> dt.date | None:
    try:
        return dt.date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def shape_problems(entries: list[dict]) -> list[str]:
    """Problems with the records themselves, independent of today and of the
    exchanges' data."""
    out: list[str] = []
    for n, e in enumerate(entries):
        tag = f"exemption {n} ({e.get('mic', '?')})"
        # leads may be an empty list; every other field must be non-empty
        missing = [f for f in FIELDS if f not in e or (f != "leads" and not e.get(f))]
        if missing:
            out.append(f"{tag}: missing {', '.join(missing)}")
            continue
        extra = sorted(set(e) - set(FIELDS))
        if extra:
            out.append(f"{tag}: unknown field(s) {', '.join(extra)}")
        if not re.fullmatch(r"X[A-Z0-9]{3}|[A-Z]{4}", str(e["mic"])):
            out.append(f"{tag}: mic {e['mic']!r} is not a MIC")
        if not isinstance(e["sources_tried"], list):
            out.append(f"{tag}: sources_tried is not a list")
        else:
            for k, s in enumerate(e["sources_tried"]):
                gone = [f for f in SOURCE_FIELDS if not (isinstance(s, dict) and s.get(f))]
                if gone:
                    out.append(f"{tag}: sources_tried[{k}] lacks {', '.join(gone)}")
                elif _date(s["tried"]) is None:
                    out.append(f"{tag}: sources_tried[{k}].tried {s['tried']!r} is not YYYY-MM-DD")
        if not isinstance(e["leads"], list):
            out.append(f"{tag}: leads is not a list")
        else:
            for k, lead in enumerate(e["leads"]):
                gone = [f for f in LEAD_FIELDS if not (isinstance(lead, dict) and lead.get(f))]
                if gone:
                    out.append(f"{tag}: leads[{k}] lacks {', '.join(gone)}")
                elif lead["label"] != LEAD_LABEL:
                    out.append(f"{tag}: leads[{k}].label is {lead['label']!r}, expected {LEAD_LABEL!r}")
        added, expires = _date(e["added"]), _date(e["expires"])
        if added is None or expires is None:
            out.append(f"{tag}: added and expires must be ISO dates")
        elif expires < added:
            out.append(f"{tag}: expires {expires} is before added {added}")
        elif (expires - added).days > MAX_DAYS:
            out.append(f"{tag}: expires {expires} is more than {MAX_DAYS} days after added {added}")
    mics = [e.get("mic") for e in entries]
    for m in sorted({m for m in mics if mics.count(m) > 1}):
        out.append(f"{m}: more than one exemption")
    return out


def problems(entries: list[dict], today: dt.date,
             exchanges: dict[str, dict] | None = None,
             satisfied: set[str] | None = None) -> tuple[list[str], list[str]]:
    """(errors, warnings) for the exemption list on `today`.

    exchanges: {MIC: verification class}; when given, an exemption must name
    a reference_compared exchange. satisfied: MICs that already meet check 6
    without an exemption (verified current hours or a schema_limited item);
    an exemption for one of them is stale."""
    errors = shape_problems(entries)
    warnings: list[str] = []
    for e in entries:
        mic = e.get("mic")
        expires = _date(e.get("expires"))
        if expires is not None:
            if today > expires:
                errors.append(f"{mic}: exemption expired on {expires} (today {today}); "
                              f"read the evidence or renew it with a new record of what was tried")
            elif (expires - today).days <= WARN_DAYS:
                warnings.append(f"{mic}: exemption expires on {expires}, "
                                f"{(expires - today).days} day(s) from {today}")
        if exchanges is not None:
            if mic not in exchanges:
                errors.append(f"{mic}: exemption names no exchange of the registry")
            elif exchanges[mic] != "reference_compared":
                errors.append(f"{mic}: exemption for an exchange that is not reference_compared "
                              f"({exchanges[mic]}); check 6 does not require it")
        if satisfied is not None and mic in satisfied:
            errors.append(f"{mic}: stale exemption: the exchange already has verified current hours "
                          f"or a schema_limited item; remove it from tools/hours_evidence_exemptions.json")
    return errors, warnings


def nearest(entries: list[dict]) -> dict | None:
    """The exemption that expires first (None for an empty list)."""
    dated = [e for e in entries if _date(e.get("expires"))]
    return min(dated, key=lambda e: e["expires"]) if dated else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="validate the file")
    ap.add_argument("--path", type=Path, default=PATH)
    ap.add_argument("--today", default=None, help="the date to check against (default: today)")
    args = ap.parse_args(argv)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    entries = load(args.path)
    errors, warnings = problems(entries, today)
    for w in warnings:
        print(f"warning: {w}")
    for p in errors:
        print(f"error: {p}")
    if errors:
        return 1
    first = nearest(entries)
    print(f"OK: {len(entries)} hours-evidence exemption(s), each expiring within {MAX_DAYS} days of being added"
          + (f"; nearest expiry {first['expires']} ({first['mic']})" if first else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
