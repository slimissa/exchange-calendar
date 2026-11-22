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
HOURS_EVIDENCE_FLOOR = 37  # 4b4: + XMEX (schema_limited), XKLS, XASX
#   4b3: batch B (8), XPHS XSES XTAI XZAG


def _item(eff, open_="10:30", close="18:00", status="verified", **extra):
    item = {"effective_from": eff, "open": open_, "close": close,
            "segment": "Renta Variable, Contado 24 hs", "close_rule": "continuous_end",
            "source_url": "https://www.byma.com.ar/", "source_title": "Comunicado",
            "checked_on": "2026-11-21", "status": status}
    if status == "verified":
        # schema 2.3.2: verified items carry verified_from (default: the
        # entry's own date, i.e. the document proves the entry from its start).
        item["verified_from"] = eff
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
    # (4b3: the evaluation day is the later of last_checked and checked_on,
    # so the read must also predate the change for this case.)
    early = [dict(i, checked_on="2026-10-01") for i in GOOD]
    assert cv.current_hours_verified(_ex(DATED, early, last_checked="2026-10-01")) is False
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
    assert SCHEMA["version"] == "2.3.2"


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
    # 4b3 (verified_from): XAMS, XBRU, XPAR and XLIS keep verified evidence,
    # but the edition read takes effect on 2026-11-23, after their evaluation
    # day, so their current hours are not verified yet.
    verified = {"XBUE", "XHKG", "XMOS", "XDUB", "XOSL",
                "XCSE", "XETR", "XHEL", "XICE", "XLIT", "XLUX", "XNYS", "XPRA",
                "XBDA", "XBUD", "XJSE", "XNZE"}
    later = {"XAMS", "XBRU", "XPAR", "XLIS"}
    for code in sorted(verified | later | {"XKAR"}):
        d = json.loads((ROOT / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
        assert cv.hours_problems(d) == [], code
        assert cv.current_hours_verified(d) is (code in verified), code
        if code in later:
            assert d["verification"]["hours"][-1]["status"] == "verified", code


def test_euronext_items_name_the_appendix_and_local_times():
    for code, hours in {"XAMS": ("09:00", "17:35"), "XBRU": ("09:00", "17:35"),
                        "XPAR": ("09:00", "17:35"), "XLIS": ("08:00", "16:35"),
                        "XDUB": ("08:00", "16:30"), "XOSL": ("09:00", "16:25")}.items():
        d = json.loads((ROOT / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
        cur = d["verification"]["hours"][-1]
        assert (cur["open"], cur["close"]) == hours, code
        assert "Appendix of Trading Manual 4-01" in cur["source_title"], code
        assert cur["close_rule"] == "closing_auction_end", code


# --- verified_from (schema 2.3.2, ADR 0014 section 7) ------------------------

def test_verified_needs_verified_from():
    it = _item("2026-11-02")
    del it["verified_from"]
    assert cv.hours_problems(_ex(DATED, [GOOD[0], it])) == [
        "XTST: verified hours evidence from 2026-11-02 has no verified_from"]


def test_verified_from_not_before_effective_from():
    out = cv.hours_problems(_ex(DATED, [GOOD[0], _item("2026-11-02", verified_from="2026-11-01")]))
    assert out == ["XTST: hours evidence from 2026-11-02: verified_from 2026-11-01 is before the entry's effective_from"]


def test_verified_from_only_on_verified_items():
    bad = _item("2010-01-01", "11:00", "17:00", "unconfirmed", recheck_date="2026-12-22",
                verified_from="2010-01-01")
    out = cv.hours_problems(_ex(DATED, [bad, GOOD[1]]))
    assert out == ["XTST: hours evidence from 2010-01-01: verified_from on a 'unconfirmed' item (verified only)"]


def test_schema_requires_verified_from_on_verified_only():
    jsonschema.validate([_item("2026-11-02")], HOURS_SCHEMA)
    it = _item("2026-11-02")
    del it["verified_from"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate([it], HOURS_SCHEMA)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate([_item("2010-01-01", status="unconfirmed", recheck_date="2026-12-22",
                                   verified_from="2010-01-01")], HOURS_SCHEMA)


def test_current_needs_verified_from_on_or_before_the_evaluation_day():
    single = {"open": "09:00", "close": "17:35"}
    # Read on 22 Nov, document effective 23 Nov: not current yet (Euronext, 4b3).
    future = [_item("2010-01-01", "09:00", "17:35", checked_on="2026-11-22", verified_from="2026-11-23")]
    assert cv.hours_problems(_ex(single, future)) == []
    assert cv.current_hours_verified(_ex(single, future)) is False
    # A later last_checked makes the same evidence current.
    assert cv.current_hours_verified(_ex(single, future, last_checked="2026-11-23")) is True
    # A page read after last_checked proves the read day (evaluation day = checked_on).
    page = [_item("2010-01-01", "09:00", "17:35", checked_on="2026-11-22", verified_from="2026-11-22")]
    assert cv.current_hours_verified(_ex(single, page, last_checked="2026-11-21")) is True


def test_history_verified_needs_every_entry_from_its_own_date():
    both = [_item("2010-01-01", "11:00", "17:00"), _item("2026-11-02")]
    assert cv.history_hours_verified(_ex(DATED, both)) is True
    late = [_item("2010-01-01", "11:00", "17:00", verified_from="2019-07-23"), _item("2026-11-02")]
    assert cv.history_hours_verified(_ex(DATED, late)) is False
    assert cv.current_hours_verified(_ex(DATED, late)) is True
    assert cv.history_hours_verified(_ex(DATED, GOOD)) is False  # 2010 unconfirmed


def test_real_tree_facts_4b3():
    cur, hist, total = cv.hours_facts(ROOT)
    assert total == 74
    # 4b3: 17 current (Euronext AMS/BRU/PAR/LIS read only in the edition
    # effective 23 November 2026); no exchange's whole history is proven.
    assert cur >= 29 and hist >= 0  # 4b3: 17 after verified_from; + batch B (8) and XPHS XSES XTAI XZAG
    for code in ("XAMS", "XBRU", "XPAR", "XLIS"):
        d = json.loads((ROOT / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
        assert d["verification"]["hours"][-1]["verified_from"] == "2026-11-23", code


def test_xmex_seasonal_hours_are_schema_limited():
    """4b4: BMV runs 07:30-14:00 during US daylight saving time and
    08:30-15:00 otherwise (Manual Operativo 1.1.3); regular_hours keeps the
    latter and the evidence says the schema cannot express the season."""
    d = json.loads((ROOT / "exchanges" / "XMEX.json").read_text(encoding="utf-8"))
    assert d["regular_hours"] == {"open": "08:30", "close": "15:00"}
    (item,) = d["verification"]["hours"]
    assert item["status"] == "schema_limited" and "verified_from" not in item
    assert item["backlog_item"] == "Sessions that follow another market's daylight saving time"
    assert "7:30-14:00" in item["limitation"] and item["close_rule"] == "continuous_end"
    assert cv.hours_problems(d) == [] and cv.current_hours_verified(d) is False


def test_4b4_saved_pages_evidence():
    kls = json.loads((ROOT / "exchanges" / "XKLS.json").read_text(encoding="utf-8"))
    assert cv.current_hours_verified(kls) is True
    asx = json.loads((ROOT / "exchanges" / "XASX.json").read_text(encoding="utf-8"))
    (item,) = asx["verification"]["hours"]
    # ASX's closing auction ends 16:11 (ADR 0013); the registry holds 16:00
    # until a notice dates the timetable: evidence records the contradiction.
    assert item["status"] == "unconfirmed" and "16:10:00^ - 16:11:00" in item["note"]
    assert cv.hours_problems(asx) == []

