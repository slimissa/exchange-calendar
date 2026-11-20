"""Expected ad_hoc_closures rows, derived from exchanges/*.json (4c11).

The export tests used to pin every live ad_hoc_closures row by hand, so each
session that added a closure had to edit nine tests. This module builds the
expected rows straight from the source files, independently of the
exporters (it does not call export_sql.build_tables), so a test can compare
an export to it exactly: same rows, same order, same columns, same values.

The row contract is ADR 0012 section 5: one row per entry, columns
(exchange_code, date, seq, name, status, early_close_time, source_url),
seq counting from 1 per (exchange_code, date) in the file's order, and rows
sorted by (exchange_code, date, seq). A missing early_close_time is None.

AD_HOC_ROW_COUNT is the one fixed sanity pin. Any session that adds or
removes an ad hoc closure updates it here, and nowhere else.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXCHANGES = REPO / "exchanges"

# 4c11: XBKK 2, XLIM 8, XSGO 6, XTAI 2, XZAG 3. Update when a session adds or removes rows.
AD_HOC_ROW_COUNT = 21

COLUMNS = ("exchange_code", "date", "seq", "name", "status", "early_close_time", "source_url")


def expected_rows(exchanges_dir: Path = EXCHANGES) -> list[tuple]:
    """Every ad hoc closure in exchanges/*.json as an export row tuple."""
    rows = []
    for path in sorted(exchanges_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        code = data["code"]
        seen: dict[str, int] = {}
        for entry in data.get("ad_hoc_closures", []):
            seen[entry["date"]] = seen.get(entry["date"], 0) + 1
            rows.append((code, entry["date"], seen[entry["date"]], entry["name"],
                         entry["status"], entry.get("early_close_time"), entry["source_url"]))
    return sorted(rows, key=lambda r: (r[0], r[1], r[2]))


def expected_with(extra: list[tuple]) -> list[tuple]:
    """The live rows plus synthetic rows, in export order."""
    return sorted(expected_rows() + list(extra), key=lambda r: (r[0], r[1], r[2]))


def diff(actual: list[tuple], expected: list[tuple]) -> list[str]:
    """Human-readable differences between two row lists; empty when equal."""
    problems = []
    if len(actual) != len(expected):
        problems.append(f"{len(actual)} rows exported, {len(expected)} expected")
    for i, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            problems.append(f"row {i}: exported {a!r}, expected {e!r}")
    if len(actual) > len(expected):
        problems += [f"extra row {r!r}" for r in actual[len(expected):]]
    elif len(expected) > len(actual):
        problems += [f"missing row {r!r}" for r in expected[len(actual):]]
    return problems


def assert_rows_match(actual: list[tuple], expected: list[tuple] | None = None) -> None:
    expected = expected_rows() if expected is None else expected
    problems = diff(list(actual), expected)
    assert not problems, "\n".join(problems[:10])


# Mutations used by the negative tests: each turns the exporter's input
# registry (calendar.json) into one that makes the exporter drop, add or
# alter one ad hoc row, while the expectation still comes from exchanges/.
def _first_with_closures(registry: dict) -> dict:
    return next(e for e in registry["exchanges"] if e.get("ad_hoc_closures"))


def drop_one(registry: dict) -> None:
    _first_with_closures(registry)["ad_hoc_closures"].pop(0)


def add_one(registry: dict) -> None:
    _first_with_closures(registry)["ad_hoc_closures"].append(
        {"date": "2099-01-01", "name": "Injected", "status": "closed",
         "source_url": "https://example.org/injected"})


def alter_one(registry: dict) -> None:
    _first_with_closures(registry)["ad_hoc_closures"][0]["name"] += " (altered)"


MUTATIONS = {"drop": drop_one, "add": add_one, "alter": alter_one}
