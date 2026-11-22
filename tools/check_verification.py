#!/usr/bin/env python3
"""
tools/check_verification.py

Fail when an exchange's ``verification`` object disagrees with its
fetcher_status and docs/DIVERGENCE.md. The expected class and basis are
written out here as a table, separately from tools/derive_verification.py, so
a mistake in the derivation does not hide itself; only the parsing of the
"at least one reference library" list is shared.

Checks, for every exchanges/*.json:
  1. a `verification` object exists with class, basis, last_checked and a
     non-empty reference_note;
  2. class and basis match the table for (fetcher_status, has reference);
  3. last_checked is a YYYY-MM-DD date that is not in the future, and every
     file carries the same date (they are written in one run);
  4. the four classes add up to the number of files.
  5. coverage spans (exchanges that have verification.coverage), Phase 4d:
     a. coverage.from/to equal generation_range, and the sources spans tile
        it exactly: sorted, no gap, no overlap, none outside the range;
     b. a span's source label does not contradict the data it covers:
        - a span holding an explicit entry or ad hoc closure with
          `predicted: true`, or a date that docs/divergence_triage.json
          gives the verdict `unpublished`, must say so in its label
          (predict, pattern or estimat), or be labelled "not covered",
          or be a date held on doubt: listed in that span's `unconfirmed`,
          the span carrying a YYYY-MM-DD `recheck_date` (which
          tools/check_recheck_dates.py fails once it passes) no more than
          RECHECK_CAP_DAYS (92) days after the file's
          `verification.last_checked`, and a label that says
          "unconfirmed" (Phase 4d.1; the cap since 4d2, so a far-off
          recheck date cannot park a guess under a publications label);
        - a span naming exchange_calendars or pandas_market_calendars must
          not cover an exchange that library has no data for, nor years
          after the last one docs/DIVERGENCE.md says it records;
     c. every date in a span's contradicted_by and unconfirmed lies inside
        that span.
     Whether every disagreement has a verdict or a contradicted_by is
     tests/test_divergence_classified.py's job, not this tool's.
     Coverage findings fail the tool (blocking since session 4d.1; Phase 4d
     added them as warnings while 13 exchanges failed). --strict-coverage is
     still accepted and has no further effect.
  6. hours evidence (exchanges that have verification.hours; schema 2.3.0,
     ADR 0014): one item per regular_hours entry (effective_from = the
     entry's effective_from, or generation_range[0] for a single object), no
     item without an entry, the item's open/close equal to the entry's, and
     an `unconfirmed` item carries a recheck_date at most RECHECK_CAP_DAYS
     (92) after verification.last_checked. A `schema_limited` item (schema
     2.3.1: the exchange's own document gives hours regular_hours cannot
     express, such as a weekday schedule) carries `limitation` and a
     `backlog_item` naming a bold item title in
     docs/phase-4f-schema-backlog.md; it has no recheck cap. Reported as
     "hours evidence: N of 74 (M of 48 reference_compared); items: V
     verified, S schema_limited, U unconfirmed", N being the exchanges whose
     evidence passes. NON-BLOCKING in Phase 4b-lite (findings print as "WARNING hours:";
     --strict-hours fails on them); it becomes blocking for every
     reference_compared exchange at the end of 4b-lite (ADR 0014).
     A `verified` item carries `verified_from` (schema 2.3.2): the earliest
     date its cited document proves those hours, never before the entry's
     effective_from. Two facts follow (ADR 0014 section 7):
       Current hours verified: the entry in force on the exchange's
         evaluation day (the later of last_checked and the item's
         checked_on) is verified with verified_from on or before that day.
       History verified: every entry is verified with verified_from equal
         to its effective_from.
     Printed as "Current hours verified: N of 74" and "History verified: M
     of 74" (docs/facts.json exchanges_hours_verified and
     exchanges_hours_history_verified). The end-of-4b-lite blocking rule
     applies to current hours; history is Phase 4b full.
--date YYYY-MM-DD additionally requires last_checked to be exactly that date.
A date fixed in the tool would fail on the first regeneration after it, so
the default is the consistency rules above.

--check is accepted so this tool takes the same flag as derive_verification.py;
it has no other effect.

Exit codes: 0 consistent, 1 inconsistencies, 2 fatal (missing input).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import derive_verification as dv  # noqa: E402
import regular_hours as rh  # noqa: E402

# (fetcher_status, has reference library) -> (class, basis); None matches any
EXPECTED = (
    ("ci_unreachable", None, "ci_unreachable", "ci_network"),
    ("implemented", True, "reference_compared", "divergence_report"),
    ("implemented", False, "source_verified", "fetcher:implemented"),
    ("blocked", True, "reference_compared", "divergence_report"),
    ("blocked", False, "single_source", "BLOCKED.md"),
    ("none", True, "reference_compared", "divergence_report"),
    ("none", False, "single_source", "BLOCKED.md"),
)
CLASSES = ("reference_compared", "source_verified", "single_source", "ci_unreachable")

# Check 5b: the unconfirmed exception holds only while the span's recheck_date
# is at most this many days after verification.last_checked (4d2).
RECHECK_CAP_DAYS = 92

# Coverage-span label vocabulary (check 5b).
PREDICTED_LABEL = re.compile(r"predict|pattern|estimat", re.IGNORECASE)
NOT_COVERED_LABEL = re.compile(r"^\s*not covered", re.IGNORECASE)
LIBRARY_LABELS = ("exchange_calendars", "pandas_market_calendars")
# "| XBOM | available | ValueError: The XBOM holidays are only recorded to the year 2026, c..."
_LIB_END = {
    "exchange_calendars": re.compile(
        r"^\| ([A-Z0-9]{4}) \| [^|]*\| ValueError: The \1 holidays are only recorded "
        r"to the year (\d{4})", re.MULTILINE),
    "pandas_market_calendars": re.compile(
        r"^\| ([A-Z0-9]{4}) \| ValueError: The \1 holidays are only recorded "
        r"to the year (\d{4})", re.MULTILINE),
}


def library_end_years(divergence: str) -> dict[str, dict[str, int]]:
    """{library: {MIC: last year it records}} from DIVERGENCE.md's No reference data table."""
    return {lib: {m.group(1): int(m.group(2)) for m in rx.finditer(divergence)}
            for lib, rx in _LIB_END.items()}


def unpublished_dates(triage: dict) -> dict[str, set[str]]:
    """{MIC: dates} that docs/divergence_triage.json marks unpublished (predictions)."""
    out: dict[str, set[str]] = {}
    for e in triage.get("entries", []):
        if e.get("verdict") == "unpublished":
            out.setdefault(e["exchange"], set()).update(e.get("dates", []))
    return out


def _day(text: str) -> date | None:
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def coverage_problems(d: dict, libraries: tuple[str, ...], lib_end: dict[str, dict[str, int]],
                      unpublished: set[str]) -> list[str]:
    """Check 5 for one exchange; [] when it has no coverage or the coverage is consistent."""
    cov = (d.get("verification") or {}).get("coverage")
    if not isinstance(cov, dict):
        return []
    code = d.get("code", "?")
    problems: list[str] = []
    gr = d.get("generation_range") or [None, None]
    start, end = _day(gr[0]), _day(gr[1])
    if start is None or end is None:
        return [f"{code}: coverage present but generation_range is not two dates"]

    # 5a: the spans tile generation_range exactly.
    if cov.get("from") != gr[0]:
        problems.append(f"{code}: coverage.from {cov.get('from')} is not the generation_range "
                        f"start {gr[0]}")
    if cov.get("to") != gr[1]:
        problems.append(f"{code}: coverage.to {cov.get('to')} is not the generation_range "
                        f"end {gr[1]}")
    spans = cov.get("sources") or []
    if not spans:
        problems.append(f"{code}: coverage has no sources spans")
        return problems
    parsed = []
    for s in spans:
        a, b = _day(s.get("from")), _day(s.get("to"))
        if a is None or b is None or a > b:
            problems.append(f"{code}: span {s.get('from')}..{s.get('to')} is not a date range")
            continue
        parsed.append((a, b, s))
    expect = start
    for i, (a, b, s) in enumerate(parsed):
        where = f"{s['from']}..{s['to']}"
        if a < start or b > end:
            problems.append(f"{code}: span {where} lies outside generation_range {gr[0]}..{gr[1]}")
        if a > expect:
            problems.append(f"{code}: gap {expect.isoformat()}..{date.fromordinal(a.toordinal() - 1)} "
                            f"before span {where}")
        elif a < expect and i > 0:
            problems.append(f"{code}: span {where} overlaps the span before it")
        expect = max(expect, date.fromordinal(b.toordinal() + 1))
    if parsed and expect <= end:
        problems.append(f"{code}: gap {expect.isoformat()}..{gr[1]} after the last span")

    # 5b, 5c: per span.
    entries = list((d.get("holidays") or {}).get("explicit", [])) + list(d.get("ad_hoc_closures", []))
    predicted = sorted(e["date"] for e in entries if e.get("predicted"))
    unpub = sorted(unpublished)
    checked = _day((d.get("verification") or {}).get("last_checked"))
    for _, _, s in parsed:
        lo, hi, label = s["from"], s["to"], s.get("source", "")
        where = f"{lo}..{hi}"
        # A date held on doubt, said so: listed unconfirmed, with a recheck date
        # at most RECHECK_CAP_DAYS after last_checked (4d2), under a label that
        # says "unconfirmed" (4d.1).
        recheck = _day(s.get("recheck_date"))
        honest = bool(re.search(r"unconfirmed", label, re.IGNORECASE))
        capped = (recheck is not None and checked is not None
                  and (recheck - checked).days <= RECHECK_CAP_DAYS)
        on_doubt = set(s.get("unconfirmed") or []) if (recheck and honest and capped) else set()
        if recheck and honest and not capped:
            # Reported once, with the reason: the cap, not the label.
            leaning = [x for x in (s.get("unconfirmed") or [])
                       if lo <= x <= hi and (x in predicted or x in unpub)]
            on_doubt = set(leaning)
            if leaning:
                problems.append(
                    f"{code}: span {where} holds {', '.join(leaning)} on doubt, but its recheck_date "
                    f"{s['recheck_date']} is more than {RECHECK_CAP_DAYS} days after last_checked "
                    f"{(d.get('verification') or {}).get('last_checked')}")
        inside = [x for x in predicted if lo <= x <= hi and x not in on_doubt]
        if inside and not (PREDICTED_LABEL.search(label) or NOT_COVERED_LABEL.match(label)):
            problems.append(f"{code}: span {where} holds {len(inside)} predicted entr"
                            f"{'y' if len(inside) == 1 else 'ies'} ({', '.join(inside[:4])}"
                            f"{', ...' if len(inside) > 4 else ''}) but its label "
                            f"does not say predicted/pattern: {label[:80]!r}")
        inside = [x for x in unpub if lo <= x <= hi and x not in on_doubt]
        if inside and not (PREDICTED_LABEL.search(label) or NOT_COVERED_LABEL.match(label)):
            problems.append(f"{code}: span {where} holds {len(inside)} date"
                            f"{'' if len(inside) == 1 else 's'} triaged unpublished "
                            f"({', '.join(inside[:4])}{', ...' if len(inside) > 4 else ''}) "
                            f"but its label does not say predicted/pattern: {label[:80]!r}")
        if not NOT_COVERED_LABEL.match(label):
            for lib in LIBRARY_LABELS:
                if lib not in label:
                    continue
                if lib not in libraries:
                    problems.append(f"{code}: span {where} names {lib}, which has no data for "
                                    f"{code} in docs/DIVERGENCE.md")
                elif code in lib_end[lib] and int(hi[:4]) > lib_end[lib][code]:
                    problems.append(f"{code}: span {where} names {lib}, which records {code} "
                                    f"only to {lib_end[lib][code]}")
        for key in ("contradicted_by", "unconfirmed"):
            for x in s.get(key) or []:
                if not (isinstance(x, str) and lo <= x <= hi and _day(x)):
                    problems.append(f"{code}: {key} {x} lies outside its span {where}")
    return problems


def expected(status: str, has_reference: bool):
    for st, ref, cls, basis in EXPECTED:
        if st == status and (ref is None or ref == has_reference):
            return cls, basis
    return None


def check(root: Path, want_date: str | None = None) -> tuple[list[str], Counter, list[str]]:
    files = sorted((root / "exchanges").glob("*.json"))
    if not files:
        raise dv.DeriveError("exchanges/: no *.json files")
    data = {}
    for f in files:
        try:
            data[f] = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise dv.DeriveError(f"cannot read {f.name}: {exc}") from None
    try:
        divergence = (root / "docs" / "DIVERGENCE.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise dv.DeriveError(f"cannot read docs/DIVERGENCE.md: {exc}") from None
    refs = dv.reference_libraries(divergence, {d["code"] for d in data.values()})
    try:
        triage = json.loads((root / "docs" / "divergence_triage.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        triage = {}
    except (OSError, ValueError) as exc:
        raise dv.DeriveError(f"cannot read docs/divergence_triage.json: {exc}") from None
    lib_end = library_end_years(divergence)
    unpublished = unpublished_dates(triage)

    problems: list[str] = []
    coverage: list[str] = []
    counts: Counter = Counter()
    dates: Counter = Counter()
    today = date.today().isoformat()
    for f, d in data.items():
        code, v = d.get("code", f.stem), d.get("verification")
        if not isinstance(v, dict):
            problems.append(f"{f.name}: no verification object")
            continue
        for key in ("class", "basis", "last_checked", "reference_note"):
            if not v.get(key):
                problems.append(f"{f.name}: verification.{key} is missing or empty")
        want = expected(d.get("fetcher_status"), code in refs)
        if want is None:
            problems.append(f"{f.name}: fetcher_status {d.get('fetcher_status')!r} has no expected class")
        elif (v.get("class"), v.get("basis")) != want:
            problems.append(
                f"{f.name}: fetcher_status {d['fetcher_status']}, "
                f"{'in' if code in refs else 'not in'} the reference list: expected "
                f"{want[0]}/{want[1]}, found {v.get('class')}/{v.get('basis')}")
        counts[v.get("class")] += 1
        coverage += coverage_problems(d, refs.get(code, ()), lib_end, unpublished.get(code, set()))
        last = v.get("last_checked")
        if isinstance(last, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", last):
            dates[last] += 1
            if last > today:
                problems.append(f"{f.name}: last_checked {last} is in the future")
            if want_date and last != want_date:
                problems.append(f"{f.name}: last_checked is {last}, expected {want_date}")
        elif last:
            problems.append(f"{f.name}: last_checked {last!r} is not YYYY-MM-DD")
    if len(dates) > 1:
        problems.append("last_checked differs between files: "
                        + ", ".join(f"{k} x{n}" for k, n in sorted(dates.items())))
    if sum(counts[c] for c in CLASSES) != len(files):
        problems.append("classes add up to "
                        f"{sum(counts[c] for c in CLASSES)}, expected {len(files)}")
    return problems, counts, coverage


BACKLOG = REPO_ROOT / "docs" / "phase-4f-schema-backlog.md"
HOURS_STATUSES = ("verified", "schema_limited", "unconfirmed")


def backlog_titles(path: Path = BACKLOG) -> set[str]:
    """Bold item titles of the 4f backlog ("- **Title.**"), without the final
    full stop: the values a schema_limited item's backlog_item may take."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    return {m.group(1).rstrip(".").strip()
            for m in re.finditer(r"^- \*\*(.+?)\*\*", text, re.MULTILINE)}


def hours_entries(d: dict) -> list[tuple[str, dict]]:
    """[(effective_from the evidence must name, entry)] for regular_hours.

    A single object is backed by one item dated generation_range[0]."""
    rh_value = d.get("regular_hours")
    if isinstance(rh_value, list):
        return [(e.get("effective_from"), e) for e in rh.history(rh_value)]
    if isinstance(rh_value, dict):
        return [((d.get("generation_range") or [None])[0], rh_value)]
    return []


def hours_problems(d: dict, backlog: set[str] | None = None) -> list[str]:
    """Check 6 for one exchange; [] when it has no verification.hours or the
    evidence is complete and consistent. backlog: the 4f backlog titles
    (default: read from docs/phase-4f-schema-backlog.md)."""
    v = d.get("verification") or {}
    items = v.get("hours")
    if items is None:
        return []
    code = d.get("code", "?")
    if not isinstance(items, list) or not items:
        return [f"{code}: verification.hours is not a non-empty list"]
    out: list[str] = []
    checked = _day(v.get("last_checked"))
    by_date: dict = {}
    for item in items:
        key = item.get("effective_from")
        if key in by_date:
            out.append(f"{code}: two hours items for effective_from {key}")
        by_date[key] = item
    entries = hours_entries(d)
    wanted = {k for k, _ in entries}
    for key, entry in entries:
        item = by_date.get(key)
        if item is None:
            out.append(f"{code}: regular_hours entry from {key} "
                       f"({entry.get('open')}-{entry.get('close')}) has no hours evidence")
            continue
        if (item.get("open"), item.get("close")) != (entry.get("open"), entry.get("close")):
            out.append(f"{code}: hours evidence from {key} says {item.get('open')}-{item.get('close')}, "
                       f"regular_hours says {entry.get('open')}-{entry.get('close')}")
        if item.get("status") == "unconfirmed":
            recheck = _day(item.get("recheck_date"))
            if recheck is None:
                out.append(f"{code}: unconfirmed hours evidence from {key} has no recheck_date")
            elif checked is None or (recheck - checked).days > RECHECK_CAP_DAYS:
                out.append(f"{code}: hours evidence from {key}: recheck_date {item.get('recheck_date')} "
                           f"is more than {RECHECK_CAP_DAYS} days after last_checked {v.get('last_checked')}")
        elif item.get("status") == "schema_limited":
            if not (item.get("limitation") or "").strip():
                out.append(f"{code}: schema_limited hours evidence from {key} has no limitation")
            ref = (item.get("backlog_item") or "").strip().rstrip(".")
            if not ref:
                out.append(f"{code}: schema_limited hours evidence from {key} has no backlog_item")
            else:
                titles = backlog_titles() if backlog is None else backlog
                if ref not in titles:
                    out.append(f"{code}: schema_limited hours evidence from {key}: backlog_item "
                               f"{item.get('backlog_item')!r} is not an item of docs/phase-4f-schema-backlog.md")
        elif item.get("status") == "verified":
            vf = _day(item.get("verified_from"))
            eff = _day(key)
            if vf is None:
                out.append(f"{code}: verified hours evidence from {key} has no verified_from")
            elif eff is not None and vf < eff:
                out.append(f"{code}: hours evidence from {key}: verified_from {item.get('verified_from')} "
                           f"is before the entry's effective_from")
        else:
            out.append(f"{code}: hours evidence from {key} has status {item.get('status')!r}")
        if item.get("status") != "verified" and "verified_from" in item:
            out.append(f"{code}: hours evidence from {key}: verified_from on a "
                       f"{item.get('status')!r} item (verified only)")
    for key in by_date:
        if key not in wanted:
            out.append(f"{code}: hours evidence from {key} backs no regular_hours entry")
    return out


def _in_force(entries: list[tuple[str, dict]], day: str) -> str:
    in_force = entries[0][0]
    for key, _ in entries:
        if key is not None and key <= day:
            in_force = key
    return in_force


def current_hours_verified(d: dict) -> bool:
    """Current hours verified (docs/facts.json exchanges_hours_verified,
    ADR 0014 section 7): the regular_hours entry in force on the evaluation
    day has a verified item whose verified_from is on or before that day.
    The evaluation day is the later of verification.last_checked and the
    item's checked_on: a document read on a day proves the hours of that
    day, and last_checked can lag behind the read. Both are recorded dates,
    so the fact does not move with the clock."""
    v = d.get("verification") or {}
    items = v.get("hours")
    if not isinstance(items, list) or hours_problems(d):
        return False
    last = v.get("last_checked") or "0000-00-00"
    entries = hours_entries(d)
    for item in items:
        if item.get("status") != "verified":
            continue
        day = max(last, item.get("checked_on") or last)
        if item.get("effective_from") == _in_force(entries, day) and item.get("verified_from", "9999") <= day:
            return True
    return False


def history_hours_verified(d: dict) -> bool:
    """History verified (docs/facts.json exchanges_hours_history_verified):
    every regular_hours entry has a verified item whose verified_from equals
    its effective_from (the cited documents prove the hours from the day the
    entry starts)."""
    v = d.get("verification") or {}
    items = v.get("hours")
    if not isinstance(items, list) or hours_problems(d):
        return False
    by_date = {i.get("effective_from"): i for i in items}
    for key, _ in hours_entries(d):
        item = by_date.get(key) or {}
        if item.get("status") != "verified" or item.get("verified_from") != key:
            return False
    return True


def hours_facts(root: Path) -> tuple[int, int, int]:
    """(current hours verified, history verified, total exchanges)."""
    cur = hist = total = 0
    for f in sorted((root / "exchanges").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        total += 1
        cur += current_hours_verified(d)
        hist += history_hours_verified(d)
    return cur, hist, total


def hours_report(root: Path) -> tuple[list[str], int, int, int, int]:
    """(findings, N passing, M passing among reference_compared, total, total
    reference_compared) for check 6."""
    findings: list[str] = []
    n = m = total = total_rc = 0
    for f in sorted((root / "exchanges").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        total += 1
        rc = (d.get("verification") or {}).get("class") == "reference_compared"
        total_rc += rc
        if (d.get("verification") or {}).get("hours") is None:
            continue
        found = hours_problems(d)
        findings += found
        if not found:
            n += 1
            m += rc
    return findings, n, m, total, total_rc


def hours_status_counts(root: Path) -> dict[str, int]:
    """Evidence items by status across all exchanges (check 6 report)."""
    counts = {k: 0 for k in HOURS_STATUSES}
    for f in sorted((root / "exchanges").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for item in (d.get("verification") or {}).get("hours") or []:
            st = item.get("status")
            if st in counts:
                counts[st] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    p.add_argument("--check", action="store_true", help="accepted for symmetry; no effect")
    p.add_argument("--date", default=None, help="require last_checked to be this date")
    p.add_argument("--strict-coverage", action="store_true",
                   help="accepted for compatibility; coverage findings block by default (4d.1)")
    p.add_argument("--strict-hours", action="store_true",
                   help="fail on hours-evidence findings (check 6; non-blocking in 4b-lite)")
    args = p.parse_args(argv)
    try:
        problems, counts, coverage = check(args.root, args.date)
    except dv.DeriveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = ", ".join(f"{c} {counts[c]}" for c in CLASSES)
    if coverage:
        problems = problems + [f"coverage: {line}" for line in coverage]
    hours, n, m, total, total_rc = hours_report(args.root)
    tag = "" if args.strict_hours else "WARNING "
    for line in hours:
        print(f"{tag}hours: {line}")
    sc = hours_status_counts(args.root)
    print(f"hours evidence: {n} of {total} ({m} of {total_rc} reference_compared); "
          f"items: {sc['verified']} verified, {sc['schema_limited']} schema_limited, "
          f"{sc['unconfirmed']} unconfirmed"
          + ("" if args.strict_hours else "; non-blocking until the end of Phase 4b-lite"))
    cur, hist, _ = hours_facts(args.root)
    print(f"Current hours verified: {cur} of {total} (blocking for reference_compared at the end of 4b-lite)")
    print(f"History verified: {hist} of {total} (Phase 4b full)")
    if args.strict_hours:
        problems = problems + [f"hours: {line}" for line in hours]
    if problems:
        for line in problems:
            print(line)
        print(f"\n{len(problems)} inconsistenc{'y' if len(problems) == 1 else 'ies'} "
              f"in verification ({summary}).")
        return 1
    print(f"OK: 0 inconsistencies; {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
