#!/usr/bin/env python3
"""
update_facts.py — Derives the countable facts about the registry and writes
them to docs/facts.json.

docs/facts.json is the one place the numbers that prose repeats (how many
exchanges, how many fetchers, how many export files) are recorded. It is
generated, never edited by hand. tools/check_doc_facts.py compares the claims
in the markdown against it, and `--check` here compares it against the tree.

Sources
-------
    calendar.json            exchange count and fetcher_status counts
    repository root          *.sql, *.csv, *.tsv and *.parquet export files
    tests/                   per-exchange test files, and the test count from
                             `pytest --collect-only -q`

Derived facts
-------------
    exchanges_total          len(calendar.json["exchanges"])
    fetchers_implemented     fetcher_status == "implemented"
    fetchers_ci_unreachable  fetcher_status == "ci_unreachable"
    fetchers_blocked         fetcher_status == "blocked"
    exchanges_no_fetcher     fetcher_status == "none"
    fetchers_registered      implemented + ci_unreachable + blocked
    exchanges_blocked_total  blocked + none (every exchange BLOCKED.md files)
    sql_files, csv_tsv_files, parquet_files
    test_files_count         files matching tests/test_*_holidays.py
    exchanges_from_2010      generation_range starts on or before 2010-01-01
    exchanges_from_2021      generation_range starts after 2010-01-01 and before 2025-01-01
    exchanges_from_2025      generation_range starts on 2025-01-01 (no backfill)
    exchanges_hours_verified Current hours verified: the regular_hours entry in
                             force on the evaluation day has `verified` evidence
                             with verified_from on or before that day (ADR 0014
                             section 7; the same test as check 6)
    exchanges_hours_history_verified
                             History verified: every regular_hours entry has
                             `verified` evidence with verified_from equal to its
                             effective_from (schema 2.3.2, 4b3)
    tests_total

calendar.json must be current: run tools/build.py first. tests_total comes
from collecting the whole suite (`pytest --collect-only`, about two seconds),
which needs the dependencies the tests import.

`--check` compares every fact, tests_total included. Until session 4c-R5 it
skipped tests_total unless `--with-tests` was given, and CI ran the bare
`--check`, so a stale count (5718 recorded, 5720 in the tree) passed with
"OK ... (11 facts)". `--no-tests` still skips it where the suite cannot be
collected; the result line then says that tests_total was not compared.
`--with-tests` is kept as a no-op alias for older scripts.

Exit codes
----------
    0  facts written, or (--check) facts.json matches the tree
    1  --check found a difference (each is printed)
    2  a source could not be read, or collection failed

Usage
-----
    python3 tools/update_facts.py               # write docs/facts.json
    python3 tools/update_facts.py --check       # fail if any fact is out of date
    python3 tools/update_facts.py --check --no-tests   # skip tests_total (says so)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FACTS_PATH = REPO_ROOT / "docs" / "facts.json"
STATUSES = ("implemented", "ci_unreachable", "blocked", "none")
COLLECTED_RE = re.compile(r"(\d+) tests? collected")


class FactsError(Exception):
    """Raised for anything that should exit 2."""


def count_tests(root: Path) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        cwd=root, capture_output=True, text=True,
    )
    m = COLLECTED_RE.search(proc.stdout)
    if proc.returncode != 0 or not m:
        raise FactsError(
            "pytest --collect-only failed "
            f"(exit {proc.returncode}): {(proc.stdout + proc.stderr).strip()[-300:]}"
        )
    return int(m.group(1))


def _hours_verified(exchange: dict) -> bool:
    """Current regular_hours entry verified (ADR 0014); shared with check 6."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_verification  # noqa: E402  (tools/check_verification.py)
    return check_verification.current_hours_verified(exchange)


def _hours_history_verified(exchange: dict) -> bool:
    """Every regular_hours entry verified from its own effective_from (4b3)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_verification  # noqa: E402
    return check_verification.history_hours_verified(exchange)


def derive(root: Path = REPO_ROOT, with_tests: bool = True) -> dict:
    try:
        exchanges = json.loads((root / "calendar.json").read_text(encoding="utf-8"))["exchanges"]
    except (OSError, ValueError, KeyError) as exc:
        raise FactsError(f"cannot read exchanges from calendar.json: {exc}") from None
    counts = {s: 0 for s in STATUSES}
    for ex in exchanges:
        status = ex.get("fetcher_status")
        if status not in counts:
            raise FactsError(f"{ex.get('code')}: fetcher_status {status!r} not in {STATUSES}")
        counts[status] += 1

    # Exchanges without a generation_range (minimal test trees) are not counted.
    starts = [ex["generation_range"][0] for ex in exchanges if ex.get("generation_range")]

    def n(pattern: str) -> int:
        return len(list(root.glob(pattern)))

    facts = {
        "csv_tsv_files": n("*.csv") + n("*.tsv"),
        "exchanges_blocked_total": counts["blocked"] + counts["none"],
        "exchanges_from_2010": sum(1 for g in starts if g <= "2010-01-01"),
        "exchanges_from_2021": sum(1 for g in starts if "2010-01-01" < g < "2025-01-01"),
        "exchanges_from_2025": sum(1 for g in starts if g == "2025-01-01"),
        "exchanges_hours_history_verified": sum(1 for ex in exchanges if _hours_history_verified(ex)),
        "exchanges_hours_verified": sum(1 for ex in exchanges if _hours_verified(ex)),
        "exchanges_no_fetcher": counts["none"],
        "exchanges_total": len(exchanges),
        "fetchers_blocked": counts["blocked"],
        "fetchers_ci_unreachable": counts["ci_unreachable"],
        "fetchers_implemented": counts["implemented"],
        "fetchers_registered": counts["implemented"] + counts["ci_unreachable"] + counts["blocked"],
        "parquet_files": n("*.parquet"),
        "sql_files": n("*.sql"),
        "test_files_count": n("tests/test_*_holidays.py"),
    }
    if with_tests:
        facts["tests_total"] = count_tests(root)
    return dict(sorted(facts.items()))


def render(facts: dict) -> str:
    return json.dumps(facts, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--check", action="store_true", help="compare facts.json with the tree")
    p.add_argument("--no-tests", action="store_true",
                   help="with --check, do not collect the suite or compare tests_total")
    p.add_argument("--with-tests", action="store_true",
                   help="no-op alias kept for older scripts: --check compares tests_total by default")
    p.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root (for tests)")
    args = p.parse_args(argv)
    path = args.root / "docs" / "facts.json"
    try:
        if not args.check:
            path.write_text(render(derive(args.root)), encoding="utf-8")
            print(f"Wrote {path.relative_to(args.root)}")
            return 0
        # calendar.json errors first, then facts.json, then the (slower)
        # collection, so each failure reports its own cause.
        facts = derive(args.root, with_tests=False)
        try:
            recorded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise FactsError(f"cannot read {path.name}: {exc}") from None
        if not args.no_tests:
            facts = dict(sorted({**facts, "tests_total": count_tests(args.root)}.items()))
    except FactsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.no_tests:
        recorded = {k: v for k, v in recorded.items() if k != "tests_total"}
    diffs = [
        f"{k}: facts.json has {recorded.get(k)!r}, the tree has {facts.get(k)!r}"
        for k in sorted(set(facts) | set(recorded))
        if facts.get(k) != recorded.get(k)
    ]
    for d in diffs:
        print(f"DIFF  {d}")
    if diffs:
        print("\ndocs/facts.json is out of date. Run: python3 tools/update_facts.py")
        return 1
    skipped = " (tests_total not compared: --no-tests)" if args.no_tests else ""
    print(f"OK: docs/facts.json matches the tree ({len(facts)} facts){skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
