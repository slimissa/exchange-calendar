"""The README's coverage statement matches the data (4c-final).

docs/facts.json carries the counts (exchanges_from_2010, _2021, _2025) and
tools/check_doc_facts.py checks the sentences that state them. This test
checks what a count cannot: the 23 MICs the README lists as having data from
2025 only are exactly the exchanges whose generation_range starts on
2025-01-01, none of them has a reference library, and the Phase 4h section of
docs/phase-4d-backlog.md lists the same MICs.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _calendar():
    return json.loads((ROOT / "calendar.json").read_text(encoding="utf-8"))["exchanges"]


def _from_2025():
    return sorted(e["code"] for e in _calendar() if e["generation_range"][0] == "2025-01-01")


def _listed(text, anchor):
    i = text.index(anchor)
    line = text[i:text.index("\n", i)]
    return sorted(set(re.findall(r"\b(?:X[A-Z]{3}|DSMD)\b", line)) - {"XSAU"})


def test_readme_lists_the_2025_only_exchanges():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert _listed(text, "23 exchanges have data from 2025 only") == _from_2025()


def test_backlog_phase_4h_lists_the_same_exchanges():
    text = (ROOT / "docs" / "phase-4d-backlog.md").read_text(encoding="utf-8")
    section = text[text.index("## Phase 4h"):]
    found = sorted(set(re.findall(r"\b(?:X[A-Z]{3}|DSMD)\b", section.split("\n## ")[0])) - {"XSAU"})
    assert found == _from_2025()


def test_partition_of_start_years():
    starts = [e["generation_range"][0] for e in _calendar()]
    assert (sum(g <= "2010-01-01" for g in starts),
            sum("2010-01-01" < g < "2025-01-01" for g in starts),
            sum(g == "2025-01-01" for g in starts)) == (50, 1, 23)
    assert len(starts) == 74
