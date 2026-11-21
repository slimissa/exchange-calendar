"""verification.hours (schema 2.3.0, ADR 0014) and check 6 of
tools/check_verification.py.

Unit tests use synthetic exchanges; the tree tests read the real files.
"""
import copy
import json
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_verification as cv  # noqa: E402

# Check 6 is non-blocking in Phase 4b-lite. Its count of exchanges with
# complete hours evidence may grow, never shrink: raise this floor when an
# exchange gains evidence.
HOURS_EVIDENCE_FLOOR = 1  # 4b1: XBUE


def _item(eff, open_="10:30", close="18:00", status="verified", **extra):
    item = {"effective_from": eff, "open": open_, "close": close,
            "segment": "Renta Variable, Contado 24 hs", "close_rule": "continuous_end",
            "source_url": "https://www.byma.com.ar/", "source_title": "Comunicado",
            "checked_on": "2026-11-21", "status": status}
    item.update(extra)
    return item


def _ex(regular_hours, hours, last_checked="2026-11-21"):
    return {"code": "XTST", "generation_range": ["2010-01-01", "2029-12-31"],
            "regular_hours": regular_hours,
            "verification": {"last_checked": last_checked, "hours": hours}}


DATED = [{"effective_from": "2010-01-01", "open": "11:00", "close": "17:00"},
         {"effective_from": "2026-11-02", "open": "10:30", "close": "18:00"}]
GOOD = [_item("2010-01-01", "11:00", "17:00", "unconfirmed", recheck_date="2026-12-22"),
        _item("2026-11-02")]


# --- check 6 rules --------------------------------------------------------

def test_complete_evidence_has_no_problem():
    assert cv.hours_problems(_ex(DATED, GOOD)) == []


def test_no_hours_is_not_checked():
    d = _ex(DATED, None)
    del d["verification"]["hours"]
    assert cv.hours_problems(d) == []


def test_single_object_is_backed_by_generation_range_start():
    single = {"open": "09:30", "close": "16:00"}
    assert cv.hours_problems(_ex(single, [_item("2010-01-01", "09:30", "16:00")])) == []
    out = cv.hours_problems(_ex(single, [_item("2011-01-01", "09:30", "16:00")]))
    assert any("from 2010-01-01" in p and "no hours evidence" in p for p in out)
    assert any("from 2011-01-01 backs no regular_hours entry" in p for p in out)


def test_entry_without_evidence():
    out = cv.hours_problems(_ex(DATED, GOOD[1:]))
    assert out == ["XTST: regular_hours entry from 2010-01-01 (11:00-17:00) has no hours evidence"]


def test_evidence_must_match_the_entry():
    bad = [GOOD[0], _item("2026-11-02", close="17:00")]
    out = cv.hours_problems(_ex(DATED, bad))
    assert out == ["XTST: hours evidence from 2026-11-02 says 10:30-17:00, regular_hours says 10:30-18:00"]


def test_duplicate_item():
    out = cv.hours_problems(_ex(DATED, GOOD + [_item("2026-11-02")]))
    assert any("two hours items for effective_from 2026-11-02" in p for p in out)


@pytest.mark.parametrize("recheck,ok", [("2027-02-20", True), ("2027-02-21", True),
                                        ("2027-02-22", False)])
def test_unconfirmed_recheck_cap_92_days(recheck, ok):
    hours = [_item("2010-01-01", "11:00", "17:00", "unconfirmed", recheck_date=recheck), GOOD[1]]
    out = cv.hours_problems(_ex(DATED, hours))
    assert (out == []) is ok
    if not ok:
        assert "more than 92 days after last_checked 2026-11-21" in out[0]


def test_unconfirmed_needs_a_recheck_date():
    hours = [_item("2010-01-01", "11:00", "17:00", "unconfirmed"), GOOD[1]]
    assert cv.hours_problems(_ex(DATED, hours)) == [
        "XTST: unconfirmed hours evidence from 2010-01-01 has no recheck_date"]


def test_current_entry_verified():
    assert cv.current_hours_verified(_ex(DATED, GOOD)) is True
    # Before the dated change, the entry in force is the unconfirmed one.
    assert cv.current_hours_verified(_ex(DATED, GOOD, last_checked="2026-10-01")) is False
    # Incomplete evidence never counts.
    assert cv.current_hours_verified(_ex(DATED, GOOD[1:])) is False


# --- schema 2.3.0 ------------------------------------------------------------

SCHEMA = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))
HOURS_SCHEMA = SCHEMA["properties"]["verification"]["properties"]["hours"]


def test_schema_version_is_2_3_0():
    assert SCHEMA["version"] == "2.3.0"


def test_schema_accepts_good_evidence():
    jsonschema.validate(GOOD, HOURS_SCHEMA)


def test_schema_requires_recheck_date_when_unconfirmed():
    bad = copy.deepcopy(GOOD)
    del bad[0]["recheck_date"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, HOURS_SCHEMA)


@pytest.mark.parametrize("key,value", [("close_rule", "vwap"), ("status", "probable"),
                                       ("open", "9:30")])
def test_schema_rejects_bad_values(key, value):
    bad = copy.deepcopy(GOOD)
    bad[1][key] = value
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, HOURS_SCHEMA)


def test_schema_rejects_unknown_keys():
    bad = copy.deepcopy(GOOD)
    bad[1]["source"] = "press"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, HOURS_SCHEMA)


# --- the real tree -----------------------------------------------------------

def test_real_tree_hours_evidence_ratchet():
    findings, n, m, total, total_rc = cv.hours_report(ROOT)
    assert total == 74 and total_rc == 48
    # Non-blocking (ADR 0014): findings on a partly documented exchange do not
    # fail; only a drop in the number with complete evidence does.
    assert n >= HOURS_EVIDENCE_FLOOR, f"hours evidence shrank: {n} < {HOURS_EVIDENCE_FLOOR}"
    assert m <= n


def test_tool_reports_the_hours_line(capsys):
    assert cv.main(["--root", str(ROOT)]) == 0
    out = capsys.readouterr().out
    assert "hours evidence: " in out and " of 74 (" in out and " of 48 reference_compared)" in out
