"""verification.hours (schema 2.3.0; schema_limited since 2.3.1; ADR 0014) and check 6 of
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
HOURS_EVIDENCE_FLOOR = 22  # 4b1: XBUE; 4b2: XHKG, XMOS, Euronext (6), batch A (8), XBDA XBUD XJSE XNZE, XKAR


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


# --- schema_limited (schema 2.3.1) ------------------------------------------

LIMITED = _item("2010-01-01", "09:30", "15:30", "schema_limited",
                limitation="Fridays: two sessions, 09:17-12:00 and 14:32-16:30",
                backlog_item="Weekday-specific sessions")
SINGLE = {"open": "09:30", "close": "15:30"}
TITLES = {"Weekday-specific sessions", "Seasonal (Ramadan) hours"}


def test_schema_limited_complete_has_no_problem():
    assert cv.hours_problems(_ex(SINGLE, [LIMITED]), TITLES) == []


def test_schema_limited_needs_a_limitation():
    item = dict(LIMITED, limitation=" ")
    assert cv.hours_problems(_ex(SINGLE, [item]), TITLES) == [
        "XTST: schema_limited hours evidence from 2010-01-01 has no limitation"]


def test_schema_limited_needs_a_backlog_item():
    item = dict(LIMITED)
    del item["backlog_item"]
    assert cv.hours_problems(_ex(SINGLE, [item]), TITLES) == [
        "XTST: schema_limited hours evidence from 2010-01-01 has no backlog_item"]


def test_schema_limited_backlog_item_must_exist():
    item = dict(LIMITED, backlog_item="Weekday schedules")
    out = cv.hours_problems(_ex(SINGLE, [item]), TITLES)
    assert len(out) == 1 and "is not an item of docs/phase-4f-schema-backlog.md" in out[0]


def test_schema_limited_backlog_item_ignores_final_full_stop():
    item = dict(LIMITED, backlog_item="Weekday-specific sessions.")
    assert cv.hours_problems(_ex(SINGLE, [item]), TITLES) == []


def test_schema_limited_has_no_recheck_cap():
    item = dict(LIMITED, recheck_date="2028-01-01")
    assert cv.hours_problems(_ex(SINGLE, [item]), TITLES) == []


def test_schema_limited_must_still_match_the_entry():
    item = dict(LIMITED, open="09:17")
    out = cv.hours_problems(_ex(SINGLE, [item]), TITLES)
    assert out == ["XTST: hours evidence from 2010-01-01 says 09:17-15:30, regular_hours says 09:30-15:30"]


def test_schema_limited_is_not_verified():
    # ADR 0014 section 6: evidence, not verification; facts do not count it.
    assert cv.current_hours_verified(_ex(SINGLE, [LIMITED])) is False


def test_real_backlog_has_the_weekday_item():
    assert "Weekday-specific sessions" in cv.backlog_titles()


def test_schema_accepts_schema_limited():
    jsonschema.validate([LIMITED], HOURS_SCHEMA)


@pytest.mark.parametrize("key", ["limitation", "backlog_item"])
def test_schema_requires_limitation_and_backlog_item(key):
    bad = dict(LIMITED)
    del bad[key]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate([bad], HOURS_SCHEMA)


def test_status_counts_on_the_tree():
    sc = cv.hours_status_counts(ROOT)
    assert set(sc) == {"verified", "schema_limited", "unconfirmed"}
    assert sc["verified"] >= HOURS_EVIDENCE_FLOOR


# --- schema 2.3.0 ------------------------------------------------------------

SCHEMA = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))
HOURS_SCHEMA = SCHEMA["properties"]["verification"]["properties"]["hours"]


def test_schema_version_is_2_3_1():
    assert SCHEMA["version"] == "2.3.1"


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
    assert " verified, " in out and " schema_limited, " in out and " unconfirmed" in out


def test_4b2_current_entries_verified():
    """4b2: the current entry of each exchange documented in this session is
    verified; XKAR's is unconfirmed (no PSX notice dates its 09:32 open)."""
    verified = {"XBUE", "XHKG", "XMOS", "XAMS", "XBRU", "XPAR", "XLIS", "XDUB", "XOSL",
                "XCSE", "XETR", "XHEL", "XICE", "XLIT", "XLUX", "XNYS", "XPRA",
                "XBDA", "XBUD", "XJSE", "XNZE"}
    for code in sorted(verified | {"XKAR"}):
        d = json.loads((ROOT / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
        assert cv.hours_problems(d) == [], code
        assert cv.current_hours_verified(d) is (code != "XKAR"), code


def test_euronext_items_name_the_appendix_and_local_times():
    for code, hours in {"XAMS": ("09:00", "17:35"), "XBRU": ("09:00", "17:35"),
                        "XPAR": ("09:00", "17:35"), "XLIS": ("08:00", "16:35"),
                        "XDUB": ("08:00", "16:30"), "XOSL": ("09:00", "16:25")}.items():
        d = json.loads((ROOT / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
        cur = d["verification"]["hours"][-1]
        assert (cur["open"], cur["close"]) == hours, code
        assert "Appendix of Trading Manual 4-01" in cur["source_title"], code
        assert cur["close_rule"] == "closing_auction_end", code

