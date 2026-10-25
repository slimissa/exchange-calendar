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
    tests_total

calendar.json must be current: run tools/build.py first. tests_total depends
on collecting the whole suite, which needs the dev dependencies installed and
moves on every added test, so `--check` leaves it out unless `--with-tests` is
given. Regenerate it with a plain run before a release.

Exit codes
----------
    0  facts written, or (--check) facts.json matches the tree
    1  --check found a difference (each is printed)
    2  a source could not be read, or collection failed

Usage
-----
    python3 tools/update_facts.py               # write docs/facts.json
    python3 tools/update_facts.py --check       # fail if it is out of date
    python3 tools/update_facts.py --check --with-tests
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

    def n(pattern: str) -> int:
        return len(list(root.glob(pattern)))

    facts = {
        "csv_tsv_files": n("*.csv") + n("*.tsv"),
        "exchanges_blocked_total": counts["blocked"] + counts["none"],
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
    p.add_argument("--with-tests", action="store_true", help="with --check, also compare tests_total")
    p.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root (for tests)")
    args = p.parse_args(argv)
    path = args.root / "docs" / "facts.json"
    try:
        if not args.check:
            path.write_text(render(derive(args.root)), encoding="utf-8")
            print(f"Wrote {path.relative_to(args.root)}")
            return 0
        facts = derive(args.root, with_tests=args.with_tests)
        try:
            recorded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise FactsError(f"cannot read {path.name}: {exc}") from None
    except FactsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not args.with_tests:
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
    print(f"OK: docs/facts.json matches the tree ({len(facts)} facts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
