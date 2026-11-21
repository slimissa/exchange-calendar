"""Every 2010-2029 disagreement is classified (4c-final).

A disagreement between the registry and the reference libraries is
classified when docs/divergence_triage.json gives it a verdict or the
exchange's verification.coverage lists it in contradicted_by. The committed
docs/DIVERGENCE.md carries the 2010-2029 triage-coverage table that
tools/divergence_report.py renders from the 2010-2029 divergence run; this
test fails if that table is missing, misses a year, does not add up, or
shows any unclassified disagreement.
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def _table():
    text = (ROOT / "docs" / "DIVERGENCE.md").read_text(encoding="utf-8")
    m = re.search(r"^## Triage coverage 2010-2029\n(.*?)(?=^## )", text, re.S | re.M)
    assert m, "DIVERGENCE.md has no 'Triage coverage 2010-2029' section"
    lines = [l for l in m.group(1).splitlines() if l.startswith("| ")]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = {}
    for l in lines[1:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if cells[0].isdigit():
            rows[cells[0]] = dict(zip(header, cells))
    return header, rows


def test_every_year_2010_2029_is_listed():
    _, rows = _table()
    assert sorted(rows) == [str(y) for y in range(2010, 2030)]


def test_no_unclassified_disagreement():
    _, rows = _table()
    left = {y: r["Unclassified"] for y, r in rows.items() if r["Unclassified"] != "0"}
    assert left == {}, f"unclassified disagreements by year: {left}"


def test_columns_add_up():
    header, rows = _table()
    parts = [h for h in header if h not in ("Year", "Disagreements")]
    for y, r in rows.items():
        assert sum(int(r[h]) for h in parts) == int(r["Disagreements"]), y


def test_classifier_counts_verdicts_contradicted_and_leftovers():
    """The classifier itself: a verdict, a contradicted_by date and an
    unclassified date each land in their own column."""
    from divergence_report import classify_history

    def year(*dates):
        return {"sources_compared": ["exchange_calendars", "registry"],
                "disagreements": [{"date": d} for d in dates]}
    history = {"years": [2020], "exchanges": {
        "XAAA": {"years": {"2020": year("2020-01-02", "2020-01-03", "2020-01-06")}}}}
    rows = classify_history(history, {("XAAA", "2020-01-02"): "library_error"},
                            {("XAAA", "2020-01-03")})
    r = rows["2020"]
    assert (r["total"], r["library_error"], r["contradicted_by"]) == (3, 1, 1)
    assert r["unclassified"] == [("XAAA", "2020-01-06")]


def test_triage_entries_name_known_exchanges():
    triage = json.loads((ROOT / "docs" / "divergence_triage.json").read_text(encoding="utf-8"))
    codes = {p.stem for p in (ROOT / "exchanges").glob("*.json")}
    assert {e["exchange"] for e in triage["entries"]} <= codes
