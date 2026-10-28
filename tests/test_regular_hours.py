"""Dated regular_hours: the helper, the schema, the validator and the data."""
import copy
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import regular_hours as rh  # noqa: E402
import validate  # noqa: E402

TOKYO = [
    {"effective_from": "1997-01-01", "open": "09:00", "close": "15:00"},
    {"effective_from": "2024-11-05", "open": "09:00", "close": "15:30"},
]
SCHEMA = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))


def exchange(code):
    return json.loads((ROOT / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))


class TestHelper:
    def test_single_object_is_one_undated_entry(self):
        one = {"open": "09:30", "close": "16:00"}
        assert rh.history(one) == [one]
        assert rh.current(one) == one
        assert rh.on(one, "1990-01-02") == one

    def test_entry_in_force_is_the_latest_not_after_the_date(self):
        assert rh.on(TOKYO, "2020-06-02")["close"] == "15:00"
        assert rh.on(TOKYO, dt.date(2024, 11, 4))["close"] == "15:00"
        assert rh.on(TOKYO, "2024-11-05")["close"] == "15:30"
        assert rh.on(TOKYO, "2026-12-31")["close"] == "15:30"

    def test_a_date_before_the_first_entry_gets_the_first_entry(self):
        assert rh.on(TOKYO, "1980-01-01")["close"] == "15:00"

    def test_current_is_the_latest_even_if_the_list_is_unsorted(self):
        assert rh.current(list(reversed(TOKYO)))["close"] == "15:30"

    def test_problems(self):
        assert rh.problems(TOKYO, "1997-01-01") == []
        assert rh.problems(TOKYO, "1999-01-01") == []   # first entry may start earlier
        assert "after generation_range start" in rh.problems(TOKYO, "1996-01-01")[0]
        assert "ascending" in rh.problems(list(reversed(TOKYO)))[0]
        assert "ascending" in rh.problems([TOKYO[0], TOKYO[0]])[0]
        assert rh.problems([]) == ["regular_hours list is empty"]
        bad = [{"effective_from": "2024-01-01", "open": "16:00", "close": "09:00"}]
        assert "before close" in rh.problems(bad)[0]
        assert "before close" in rh.problems({"open": "16:00", "close": "09:00"})[0]


class TestSchemaAndValidator:
    def _errors(self, regular, start="1997-01-01"):
        ex = copy.deepcopy(exchange("XTKS"))
        ex["regular_hours"] = regular
        ex["generation_range"][0] = start
        return validate.validate_schema(ex, SCHEMA, "XTKS.json") + \
            validate.validate_business_logic(ex, "XTKS.json")

    def test_a_single_object_and_a_dated_list_are_valid(self):
        assert self._errors({"open": "09:00", "close": "15:30"}) == []
        assert self._errors(TOKYO) == []

    def test_list_entries_must_carry_effective_from(self):
        assert self._errors([{"open": "09:00", "close": "15:30"}])

    def test_an_empty_list_is_rejected(self):
        assert self._errors([])

    def test_bad_time_and_bad_date_are_rejected(self):
        assert self._errors([{"effective_from": "1997-01-01", "open": "9:00", "close": "15:30"}])
        assert self._errors([{"effective_from": "1997/01/01", "open": "09:00", "close": "15:30"}])

    def test_unsorted_or_duplicate_dates_are_rejected(self):
        assert self._errors(list(reversed(TOKYO)))
        assert self._errors([TOKYO[0], TOKYO[0]])

    def test_first_entry_may_not_start_after_generation_range(self):
        assert self._errors(TOKYO, start="1990-01-01")  # first entry 1997 > 1990

    def test_open_must_precede_close_in_every_entry(self):
        late = [TOKYO[0], {"effective_from": "2024-11-05", "open": "16:00", "close": "15:30"}]
        assert self._errors(late)


class TestData:
    def test_xtks_close_moved_on_2024_11_05(self):
        hours = exchange("XTKS")["regular_hours"]
        assert [(h["effective_from"], h["open"], h["close"]) for h in hours] == [
            ("1997-01-01", "09:00", "15:00"), ("2024-11-05", "09:00", "15:30")]

    def test_xhkg_open_moved_on_2011_03_07(self):
        hours = exchange("XHKG")["regular_hours"]
        assert [(h["effective_from"], h["open"], h["close"]) for h in hours] == [
            ("1990-01-01", "10:00", "16:00"), ("2011-03-07", "09:30", "16:00")]

    def test_other_exchanges_keep_a_single_object(self):
        for code in ("XNYS", "XLON", "XASX"):
            assert isinstance(exchange(code)["regular_hours"], dict)

    def test_first_entry_covers_the_start_of_the_generation_range(self):
        for code in ("XTKS", "XHKG"):
            ex = exchange(code)
            assert ex["regular_hours"][0]["effective_from"] <= ex["generation_range"][0]

    def test_sessions_describe_the_hours_in_force_now(self):
        for code in ("XTKS", "XHKG"):
            ex = exchange(code)
            now = rh.current(ex["regular_hours"])
            regular = next(s for s in ex["sessions"] if s["type"] == "regular")
            assert (regular["open"], regular["close"]) == (now["open"], now["close"])

    def test_built_calendar_carries_the_list_through(self):
        built = {e["code"]: e for e in json.loads((ROOT / "calendar.json").read_text("utf-8"))["exchanges"]}
        assert built["XTKS"]["regular_hours"] == exchange("XTKS")["regular_hours"]
        assert isinstance(built["XNYS"]["regular_hours"], dict)

    def test_flat_exports_carry_the_hours_in_force_now(self):
        sql = (ROOT / "exchange_calendar.sqlite.sql").read_text(encoding="utf-8")
        con = sqlite3.connect(":memory:")
        con.executescript(sql)
        cols = [r[1] for r in con.execute("PRAGMA table_info(exchanges)")]
        row = con.execute("SELECT * FROM exchanges WHERE code = 'XTKS'").fetchone()
        got = dict(zip(cols, row))
        assert (got["regular_open"], got["regular_close"]) == ("09:00", "15:30")
        row = con.execute("SELECT * FROM exchanges WHERE code = 'XHKG'").fetchone()
        assert dict(zip(cols, row))["regular_open"] == "09:30"

    def test_xhkg_2026_matches_the_hkex_circular(self):
        entries = {h["date"]: h for h in exchange("XHKG")["holidays"]["explicit"]}
        assert entries["2026-04-07"]["status"] == "closed"        # day following Easter Monday
        assert entries["2026-10-19"]["status"] == "closed"        # day following Chung Yeung
        assert "2026-09-25" not in entries                        # Mid-Autumn holiday is the 26th, a Saturday
        for day in ("2025-01-28", "2026-02-16"):                  # Eve of Lunar New Year, half day
            assert entries[day]["status"] == "early_close"
            assert entries[day]["early_close_time"] == "12:00"


class TestDivergenceEngineUsesDatedHours:
    def test_registry_sessions_follow_the_regime_in_force(self):
        import divergence_test as dv
        xtks = dv.load_registry_entry("XTKS")
        days = dv.registry_sessions(xtks, dt.date(2024, 11, 1), dt.date(2024, 11, 6))
        assert days[dt.date(2024, 11, 1)]["close"] == "15:00"
        assert days[dt.date(2024, 11, 5)]["close"] == "15:30"
        xhkg = dv.load_registry_entry("XHKG")
        days = dv.registry_sessions(xhkg, dt.date(2011, 3, 3), dt.date(2011, 3, 8))
        assert days[dt.date(2011, 3, 4)]["open"] == "10:00"
        assert days[dt.date(2011, 3, 7)]["open"] == "09:30"

    def test_break_counts_only_if_the_market_reopens_after_it(self):
        import divergence_test as dv
        assert dv._break_text("12:00", "13:00", "16:00") == "12:00-13:00"
        assert dv._break_text("12:00", "13:00", "12:00") is None   # half day closes at the break
        assert dv._break_text("12:00", "12:30", "12:30") is None   # clipped by the close
        assert dv._break_text("12:00", "12:00", "16:00") is None   # zero length
        assert dv._break_text(None, None, "16:00") is None
