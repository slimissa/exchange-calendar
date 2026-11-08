#!/usr/bin/env python3
"""
tools/derive_verification.py

Derive the ``verification`` object on every exchange from its
``fetcher_status`` and from ``docs/DIVERGENCE.md`` (which exchanges have at
least one reference library). Derived, not authored.

    fetcher_status   reference library   class               basis
    implemented      yes                 reference_verified  divergence_report
    implemented      no                  source_verified     fetcher:implemented
    ci_unreachable   any                 ci_unreachable      ci_network
    blocked / none   yes                 reference_verified  divergence_report
    blocked / none   no                  single_source       BLOCKED.md

"Reference library" means the exchange's row in the Summary table of
docs/DIVERGENCE.md has a number under PMC (pandas_market_calendars) or EC
(exchange_calendars), not "No reference data". The report's own line
"Exchanges with at least one reference library: N" must equal the count read
from the table, or the tool stops: that is the guard against the table
changing shape.

reference_verified says a reference library covers the exchange and the
registry is compared with it. It does not say the two agree, and it is not a
check against the exchange's own calendar.

reference_note
    reference_verified: the libraries that cover the exchange, as a sentence
    (no numbers: the report is regenerated every week).
    ci_unreachable, single_source: the Verdict line of the exchange's entry in
    BLOCKED.md (its first sentence, at most 300 characters). The tool stops if the entry or its verdict is missing.
    source_verified: a fixed sentence about the fetcher (an exchange that has a
    fetcher may still have an old, superseded verdict in BLOCKED.md; it is not used).

last_checked is the date the class was derived (--date, default today). It is
not part of --check: a stale date alone is not drift.

Usage:
    derive_verification.py                   # write all exchanges/*.json
    derive_verification.py --check           # exit 1 if any file would change
    derive_verification.py --date 2026-11-08

Exit codes: 0 ok, 1 --check found drift, 2 fatal (missing input, bad format).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NO_REFERENCE = "No reference data"
LIBRARIES = (("exchange_calendars", 3), ("pandas_market_calendars", 2))  # (name, column)
VERDICT_MAX = 300

SUPERSEDED_NOTE = "The Verdict in BLOCKED.md is marked superseded; see the entry for the current finding."

SOURCE_VERIFIED_NOTE = (
    "fetcher_status is implemented: CI checks the registry against the "
    "exchange's own page on every run; no reference library covers it."
)


class DeriveError(Exception):
    pass


def reference_libraries(text: str, expected_codes: set[str]) -> dict[str, tuple[str, ...]]:
    """Exchanges with at least one reference library -> the libraries."""
    start = text.find("## Summary")
    end = text.find("\n- Exchanges in the registry", start)
    if start < 0 or end < 0:
        raise DeriveError("docs/DIVERGENCE.md: Summary table not found")
    rows: dict[str, list[str]] = {}
    for line in text[start:end].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and re.fullmatch(r"[A-Z0-9]{4}", cells[0]) and len(cells) >= 4:
            rows[cells[0]] = cells
    if set(rows) != expected_codes:
        raise DeriveError(
            "docs/DIVERGENCE.md: Summary rows differ from exchanges/: "
            f"only in report {sorted(set(rows) - expected_codes)}, "
            f"only in exchanges {sorted(expected_codes - set(rows))}")
    found: dict[str, tuple[str, ...]] = {}
    for code, cells in rows.items():
        libs = tuple(name for name, col in LIBRARIES if cells[col] != NO_REFERENCE)
        if libs:
            found[code] = libs
    m = re.search(r"Exchanges with at least one reference library: (\d+)", text)
    if not m or int(m.group(1)) != len(found):
        raise DeriveError(
            f"docs/DIVERGENCE.md says {m.group(1) if m else 'nothing'} exchanges have a "
            f"reference library; the Summary table has {len(found)}")
    return found


def blocked_verdicts(text: str) -> dict[str, str]:
    """MIC -> Verdict text of its BLOCKED.md entry (entries that have one).

    A verdict marked "superseded" is history, not a verdict: an entry whose only
    verdicts are superseded gets SUPERSEDED_NOTE instead of the old text.
    """
    verdicts: dict[str, str] = {}
    sections = re.split(r"(?m)^## ([A-Z0-9]{4}) — .*$", text)
    for code, body in zip(sections[1::2], sections[2::2]):
        lines = body.splitlines()
        for i, line in enumerate(lines):
            if not line.startswith("- **Verdict"):
                continue
            if re.match(r"- \*\*Verdict[^*]*superseded", line, re.IGNORECASE):
                verdicts.setdefault(code, SUPERSEDED_NOTE)
                continue
            chunk = [line]
            for nxt in lines[i + 1:]:
                if not nxt.strip() or nxt.startswith(("- ", "<a ", "#")):
                    break
                chunk.append(nxt.strip())
            verdict = " ".join(chunk)
            verdict = re.sub(r"^- \*\*Verdict:?\s*", "", verdict)
            verdict = verdict.replace("**", "").strip()
            verdict = re.sub(r"\s+", " ", verdict).lstrip("— ").strip()
            first = re.split(r"(?<=[.!?])\s", verdict, maxsplit=1)[0]
            if len(first) >= 20:
                verdict = first  # the verdict's first sentence
            if len(verdict) > VERDICT_MAX:
                verdict = verdict[:VERDICT_MAX].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
            verdicts[code] = verdict
            break
    return verdicts


def derive(code: str, status: str, refs: dict[str, tuple[str, ...]],
           verdicts: dict[str, str], last_checked: str) -> dict:
    if status == "ci_unreachable":
        cls, basis = "ci_unreachable", "ci_network"
        note = verdicts.get(code)
    elif code in refs:
        cls, basis = "reference_verified", "divergence_report"
        note = "Compared in docs/DIVERGENCE.md with " + " and ".join(refs[code]) + "."
    elif status == "implemented":
        cls, basis = "source_verified", "fetcher:implemented"
        note = SOURCE_VERIFIED_NOTE  # an old BLOCKED.md verdict here is history
    elif status in ("blocked", "none"):
        cls, basis = "single_source", "BLOCKED.md"
        note = verdicts.get(code)
    else:
        raise DeriveError(f"{code}: unknown fetcher_status {status!r}")
    if not note:
        raise DeriveError(f"{code}: BLOCKED.md has no entry with a Verdict line "
                          f"(needed for class {cls})")
    return {"class": cls, "basis": basis, "last_checked": last_checked, "reference_note": note}


def load_inputs(root: Path):
    files = sorted((root / "exchanges").glob("*.json"))
    if not files:
        raise DeriveError("exchanges/: no *.json files")
    data = {}
    for f in files:
        try:
            data[f] = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise DeriveError(f"cannot read {f.name}: {exc}") from None
    try:
        divergence = (root / "docs" / "DIVERGENCE.md").read_text(encoding="utf-8")
        blocked = (root / "BLOCKED.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise DeriveError(f"cannot read input: {exc}") from None
    refs = reference_libraries(divergence, {d["code"] for d in data.values()})
    return data, refs, blocked_verdicts(blocked)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    p.add_argument("--check", action="store_true", help="exit 1 if any file would change")
    p.add_argument("--date", default=None, help="last_checked to write (default: today)")
    args = p.parse_args(argv)
    last_checked = args.date or date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", last_checked):
        print(f"error: --date {last_checked!r} is not YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        data, refs, verdicts = load_inputs(args.root)
        drift, written = [], 0
        for f, d in data.items():
            new = derive(d["code"], d["fetcher_status"], refs, verdicts, last_checked)
            old = d.get("verification")
            same = isinstance(old, dict) and all(old.get(k) == new[k]
                                                 for k in ("class", "basis", "reference_note")) \
                and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(old.get("last_checked", ""))) is not None
            if same:
                continue
            drift.append(d["code"])
            if not args.check:
                d["verification"] = new
                f.write_text(json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                             encoding="utf-8")
                written += 1
    except DeriveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.check:
        if drift:
            print(f"verification out of date in {len(drift)} file(s): {', '.join(drift)}")
            print("Run tools/derive_verification.py.")
            return 1
        print(f"OK: verification current in {len(data)} file(s)")
        return 0
    print(f"wrote verification to {written} of {len(data)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
