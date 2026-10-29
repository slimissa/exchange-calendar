"""2027-2029: the dates the divergence check found wrong, and the rule behind one of them.

Each fact cites the exchange or the law it comes from. Dates for 2028 and 2029
that no exchange has published yet are marked as such.
"""
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import divergence_test as dv  # noqa: E402
import generate_dates as gd  # noqa: E402

HAS_REFS = (importlib.util.find_spec("pandas_market_calendars") is not None
            and importlib.util.find_spec("exchange_calendars") is not None)
needs_refs = pytest.mark.skipif(not HAS_REFS, reason="reference libraries are dev-only")


def explicit(code):
    e = json.loads((ROOT / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    return {h["date"]: h for h in e["holidays"]["explicit"]}


class TestSundayObservanceRule:
    RULE = {"rule": "fixed_with_sunday_observance", "month": 1, "day": 1}

    def test_weekday_stays(self):
        assert gd.generate_dates_for_rule(self.RULE, 2027) == dt.date(2027, 1, 1)   # Friday

    def test_sunday_moves_to_monday(self):
        assert gd.generate_dates_for_rule(self.RULE, 2023) == dt.date(2023, 1, 2)   # Sunday

    def test_saturday_is_not_moved_to_friday(self):
        # 2028-01-01 is a Saturday: the date stays on the weekend, so nothing is generated.
        assert gd.generate_dates_for_rule(self.RULE, 2028) == dt.date(2028, 1, 1)
        entry = {"weekend_days": [5, 6], "generation_range": ["2027-01-01", "2029-12-31"],
                 "holidays": {"explicit": [], "recurrence_rules": [
                     dict(self.RULE, name="New Year's Day", status="closed")]}}
        dates = {d["date"] for d in gd.expand_exchange(entry)}
        assert "2027-12-31" not in dates and "2028-01-01" not in dates

    def test_nyse_and_nasdaq_use_it_for_new_years_day(self):
        for code in ("XNYS", "XNAS"):
            e = json.loads((ROOT / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
            rule = next(r for r in e["holidays"]["recurrence_rules"] if r["name"] == "New Year's Day")
            assert rule["rule"] == "fixed_with_sunday_observance", code


class TestNyseAndNasdaq:
    """ICE announcement of 2026-2028 holidays (2025-12-23): Christmas observed
    Friday 2027-12-24; no New Year's Day holiday in 2028."""

    @pytest.mark.parametrize("code", ["XNYS", "XNAS"])
    def test_2027_year_end(self, code):
        days = explicit(code)
        assert days["2027-12-24"]["status"] == "closed"
        assert "2027-12-31" not in days

    def test_built_calendar_has_no_generated_new_year_friday(self):
        built = {e["code"]: e for e in json.loads((ROOT / "calendar.json").read_text("utf-8"))["exchanges"]}
        for code in ("XNYS", "XNAS"):
            generated = {h["date"] for h in built[code]["holidays"].get("generated", [])}
            assert "2027-12-31" not in generated


class TestXasxAndXlon:
    def test_asx_new_years_day_2028_is_observed_monday(self):
        # ASX 24 trading calendar 2028: 3 January, New Year's Day holiday, closed.
        assert explicit("XASX")["2028-01-03"]["status"] == "closed"

    def test_asx_last_business_days_of_2028_close_early(self):
        # ASX: the last business day before Christmas and of the year close at 14:10.
        days = explicit("XASX")
        for day in ("2028-12-22", "2028-12-29"):
            assert (days[day]["status"], days[day]["early_close_time"]) == ("early_close", "14:10")

    def test_lse_last_working_days_of_2028_close_at_1230(self):
        # Christmas Eve and New Year's Eve are Sundays in 2028, so the Fridays before
        # them close early (LSE Stock Exchange Notice N49/00 and 2023's equivalent).
        days = explicit("XLON")
        for day in ("2028-12-22", "2028-12-29"):
            assert (days[day]["status"], days[day]["early_close_time"]) == ("early_close", "12:30")


class TestXtks:
    """JPX market holidays 2027 and the Act on National Holidays."""

    def test_2027(self):
        days = explicit("XTKS")
        assert "2027-01-04" not in days                      # trading resumes Monday 4 January
        assert days["2027-07-19"]["name"] == "Marine Day"    # third Monday of July
        assert "2027-07-20" not in days
        assert days["2027-09-23"]["name"] == "Autumnal Equinox Day"
        assert "2027-09-21" not in days

    def test_2028_last_trading_day_is_the_29th(self):
        assert "2028-12-29" not in explicit("XTKS")          # 31 December is the first closure

    def test_2029(self):
        days = explicit("XTKS")
        assert "2029-05-07" not in days                      # Saturday holidays get no substitute
        assert days["2029-09-24"]["status"] == "closed"      # equinox on Sunday 23 September (predicted)


class TestXhkg:
    def test_2027_matches_the_hkex_circular(self):
        # SEHK circular CT/077/26: holiday schedule for 2027.
        days = explicit("XHKG")
        assert days["2027-09-16"]["status"] == "closed" and "2027-09-15" not in days
        assert days["2027-02-08"]["name"].startswith("Third Day")
        assert days["2027-02-09"]["name"].startswith("Fourth Day")
        for day in ("2027-02-05", "2027-12-24", "2027-12-31"):
            assert days[day]["status"] == "early_close" and days[day]["early_close_time"] == "12:00"

    def test_2028_festival_dates(self):
        # Computed from the lunisolar calendar and the sun's longitude in Hong Kong
        # time; the Government publishes the 2028 list in mid-2027.
        days = explicit("XHKG")
        assert days["2028-04-04"]["name"] == "Ching Ming Festival"
        assert days["2028-05-29"]["status"] == "closed"      # Tuen Ng is Sunday 28 May
        assert days["2028-10-04"]["status"] == "closed" and "2028-10-03" not in days
        assert days["2028-01-25"]["status"] == "early_close"

    def test_2029_festival_dates(self):
        days = explicit("XHKG")
        assert days["2029-10-16"]["name"] == "Chung Yeung Festival" and "2029-10-15" not in days
        assert days["2029-02-12"]["status"] == "early_close"

    def test_2029_open_questions_are_still_the_registry_value(self):
        # Ching Ming 2029 falls on 5 April by the sun's longitude (both libraries say the
        # 4th); the day after Mid-Autumn is Sunday 23 September, so Monday the 24th
        # (Employment Ordinance rule; both libraries leave it open). See BLOCKED.md, XHKG.
        days = explicit("XHKG")
        assert days["2029-04-05"]["status"] == "closed" and "2029-04-04" not in days
        assert days["2029-09-24"]["status"] == "closed"


@needs_refs
class TestAgainstTheLibraries:
    OPEN_XHKG_2029 = {"2029-04-04", "2029-04-05", "2029-09-24"}

    @pytest.mark.parametrize("code", ["XNYS", "XNAS", "XLON", "XASX", "XTKS", "XHKG"])
    def test_2027_to_2029_trading_days(self, code):
        found = set()
        for year in (2027, 2028, 2029):
            found |= {d["date"] for d in dv.run_exchange(code, year)["disagreements"]}
        assert found == (self.OPEN_XHKG_2029 if code == "XHKG" else set())

    @pytest.mark.parametrize("code", ["XNYS", "XNAS", "XLON", "XASX", "XTKS"])
    def test_2027_to_2029_sessions(self, code):
        for year in (2027, 2028, 2029):
            assert dv.run_exchange_sessions(code, year)["disagreements"] == []
