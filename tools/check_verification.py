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


def expected(status: str, has_reference: bool):
    for st, ref, cls, basis in EXPECTED:
        if st == status and (ref is None or ref == has_reference):
            return cls, basis
    return None


def check(root: Path, want_date: str | None = None) -> tuple[list[str], Counter]:
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

    problems: list[str] = []
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
    return problems, counts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    p.add_argument("--check", action="store_true", help="accepted for symmetry; no effect")
    p.add_argument("--date", default=None, help="require last_checked to be this date")
    args = p.parse_args(argv)
    try:
        problems, counts = check(args.root, args.date)
    except dv.DeriveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = ", ".join(f"{c} {counts[c]}" for c in CLASSES)
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
