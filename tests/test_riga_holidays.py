#!/usr/bin/env python3
"""
test_riga_holidays.py — Ground truth tests for XRIS (Nasdaq Riga).

Key facts verified:
    - Regular hours: 10:00-16:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Restoration of Independence Day (May 4)
    - Midsummer Eve and Midsummer Day (Jun 23-24)
    - Republic Day (Nov 18) with substitution
    - Christmas Eve (Dec 24) — full closure
    - New Year's Eve (Dec 31) — full closure
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XRIS.json)
    2. Latvian holiday announcements changed (verify against nasdaqbaltic.com)

Run:
    python3 -m pytest tests/test_riga_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xris():
    """Load XRIS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XRIS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xris):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xris["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXRISProperties:
    def test_code(self, xris):
        assert xris["code"] == "XRIS"

    def test_mic(self, xris):
        assert xris["mic"] == "XRIS"

    def test_name(self, xris):
        assert xris["name"] == "Nasdaq Riga"

    def test_timezone(self, xris):
        assert xris["timezone"] == "Europe/Riga"

    def test_regular_hours(self, xris):
        """4c12, ADR 0013: closing call 15:59:30-16:00:00 with a random
        uncross (Nasdaq Baltic trading-day structure); 16:00, one dated entry."""
        assert xris["regular_hours"] == [
            {"close": "16:00", "effective_from": "2010-01-01", "open": "10:00"}]

    def test_no_lunch_break(self, xris):
        lunch = [s for s in xris.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xris):
        assert "extended_hours" not in xris or xris.get("extended_hours") is None

    def test_generation_range(self, xris):
        assert "generation_range" in xris
        assert xris["generation_range"] == ["2010-01-01", "2029-12-31"]  # 4c12 backfill

    def test_ad_hoc_closures(self, xris):
        """4c12: Cabinet transfer days and the two one-off public holidays of
        2018 and 2023 (exact list; sources pinned in the classes below)."""
        assert [c["date"] for c in xris["ad_hoc_closures"]] == [
            "2010-05-03", "2010-06-25", "2010-11-19", "2015-01-02", "2018-09-24",
            "2023-05-05", "2024-12-23", "2024-12-30", "2025-05-02",
            "2025-11-17", "2026-06-22"]
        assert {c["status"] for c in xris["ad_hoc_closures"]} == {"closed"}

    def test_no_recurrence_rules(self, xris):
        """Latvia uses explicit dates only."""
        rules = xris["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXRISFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_saturday_is_not_moved(self, explicit_dates):
        """Jan 1, 2028 is Saturday: Nasdaq Baltic does not move it to Monday."""
        assert "2028-01-03" not in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_restoration_independence_2025(self, explicit_dates):
        """May 4, 2025 is Sunday: Latvia gives Monday 5 May off."""
        assert "2025-05-04" not in explicit_dates
        assert "Restoration" in explicit_dates["2025-05-05"]["name"]

    def test_restoration_independence_2026(self, explicit_dates):
        """May 4, 2026 is Monday."""
        assert "2026-05-04" in explicit_dates
        assert "Restoration" in explicit_dates["2026-05-04"]["name"]

    def test_republic_day_2025(self, explicit_dates):
        """Nov 18, 2025 is Tuesday."""
        assert "2025-11-18" in explicit_dates
        assert "Republic" in explicit_dates["2025-11-18"]["name"]

    def test_republic_day_2028_substitute(self, explicit_dates):
        """Nov 18, 2028 is Saturday — substitute to Monday Nov 20."""
        assert "2028-11-18" not in explicit_dates
        assert "2028-11-20" in explicit_dates

    def test_republic_day_2029_substitute(self, explicit_dates):
        """Nov 18, 2029 is Sunday — substitute to Monday Nov 19."""
        assert "2029-11-19" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Midsummer holidays
# ──────────────────────────────────────────────────────────────

class TestXRISMidsummer:
    def test_midsummer_eve_2025(self, explicit_dates):
        """Jun 23, 2025 is Monday."""
        assert "2025-06-23" in explicit_dates
        assert "Midsummer Eve" in explicit_dates["2025-06-23"]["name"]

    def test_midsummer_day_2025(self, explicit_dates):
        """Jun 24, 2025 is Tuesday."""
        assert "2025-06-24" in explicit_dates
        assert "Midsummer Day" in explicit_dates["2025-06-24"]["name"]

    def test_midsummer_eve_2026(self, explicit_dates):
        """Jun 23, 2026 is Tuesday."""
        assert "2026-06-23" in explicit_dates

    def test_midsummer_day_2026(self, explicit_dates):
        """Jun 24, 2026 is Wednesday."""
        assert "2026-06-24" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXRISChristmas:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — full closure."""
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "closed"

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — full closure."""
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["name"] == "New Year's Eve"

    def test_christmas_2027_saturday_is_not_moved(self, explicit_dates):
        """Dec 25, 2027 is Saturday: no Monday substitute."""
        assert "2027-12-27" not in explicit_dates

    def test_boxing_day_2027_sunday_is_not_moved(self, explicit_dates):
        """Dec 26, 2027 is Sunday: no Tuesday substitute."""
        assert "2027-12-28" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXRISEaster:
    def test_good_friday_2025(self, explicit_dates):
        """Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["name"] == "Good Friday"

    def test_good_friday_2026(self, explicit_dates):
        """Easter - 2 days — April 3, 2026."""
        assert "2026-04-03" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        """Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["name"] == "Easter Monday"

    def test_easter_monday_2027(self, explicit_dates):
        """Easter + 1 day — March 29, 2027."""
        assert "2027-03-29" in explicit_dates

    def test_easter_monday_2029(self, explicit_dates):
        """Easter + 1 day — April 2, 2029."""
        assert "2029-04-02" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXRISStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Latvia weekend is Saturday-Sunday."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str} ({d.strftime('%A')})"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates)), "Duplicate dates found"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"
            if entry["source_url"] == "github.com/gerrymanoim/exchange_calendars":
                assert date_str < "2025"  # 4c12 backfill (repository convention)
                continue
            assert entry["source_url"].startswith("http")

    def test_all_entries_have_name(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "name" in entry, f"Missing name: {date_str}"
            assert entry["name"], f"Empty name: {date_str}"

    def test_all_entries_have_status(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "status" in entry, f"Missing status: {date_str}"
            assert entry["status"] in ["closed", "early_close"]

    def test_all_statuses_closed(self, explicit_dates):
        """Latvia has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xris, explicit_dates):
        start = date.fromisoformat(xris["generation_range"][0])
        end = date.fromisoformat(xris["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """Scoped to 2025-2029: 55 (unchanged by 4c12). 2010-2024 backfill:
        153 exchange_calendars closures - 2018-05-09 - 3 transfer days moved
        to ad_hoc_closures + 9 Christmas Days + 2018-07-09 = 159."""
        assert len([d for d in explicit_dates if d >= "2025"]) == 55
        assert len([d for d in explicit_dates if d < "2025"]) == 159

    def test_christmas_day_2010_2024(self, explicit_dates):
        """4c12: exchange_calendars has no Christmas Day for XRIS. Latvia's
        holidays law lists 25 December; every weekday 25 December 2010-2024
        is closed and named so."""
        xmas = sorted(d for d, e in explicit_dates.items()
                      if d < "2025" and d.endswith("-12-25"))
        assert xmas == ["2012-12-25", "2013-12-25", "2014-12-25", "2015-12-25",
                        "2017-12-25", "2018-12-25", "2019-12-25", "2020-12-25",
                        "2023-12-25", "2024-12-25"]
        assert {explicit_dates[d]["name"] for d in xmas} == {"Christmas Day"}

    def test_2018_bulletin_counts(self, explicit_dates):
        """4c12: Nasdaq Baltic's May 2018 bulletin (Riga 20 = 23 - 1, 4, 10
        May) leaves no room for exchange_calendars' 2018-05-09; the July 2018
        bulletin (21 of 22) leaves 9 July, the day off after the Song and
        Dance Celebration closing day."""
        assert "2018-05-09" not in explicit_dates
        assert sorted(d for d in explicit_dates if d.startswith("2018-05")) == [
            "2018-05-01", "2018-05-04", "2018-05-10"]
        assert sorted(d for d in explicit_dates if d.startswith("2018-07")) == ["2018-07-09"]

    def test_source_url_consistency(self, explicit_dates):
        law = "https://likumi.lv/ta/en/en/id/72608"
        for d, entry in explicit_dates.items():
            if d < "2025":
                if d in ("2012-12-25", "2013-12-25", "2014-12-25", "2015-12-25", "2017-12-25",
                         "2018-12-25", "2019-12-25", "2020-12-25"):
                    assert entry["source_url"] == law
                elif d == "2024-12-25":
                    assert entry["source_url"].startswith("https://view.news.eu.nasdaq.com/")
                elif d == "2018-07-09":
                    assert entry["source_url"] == "https://nasdaqbaltic.com/statistics/en/bulletins?bbid=334"
                else:  # 4c12 backfill cites exchange_calendars
                    assert entry["source_url"] == "github.com/gerrymanoim/exchange_calendars"
                continue
            assert "nasdaqbaltic.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXRISWeekendPattern:
    def test_saturday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 6, f"Sunday date: {date_str}"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXRISSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2028-11-18" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 2, f"Unexpected observed count: {observed_count}"


# ──────────────────────────────────────────────────────────────
# Future-year fixes (v2.23.5)
# ──────────────────────────────────────────────────────────────

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import generate_dates as _gd


def _closed(code, year):
    """Closed weekdays the registry produces for one year (explicit plus rules)."""
    e = json.loads((Path(__file__).parent.parent / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    days = list(e["holidays"]["explicit"]) + _gd.expand_exchange(e)
    return {d["date"] for d in days
            if d["date"].startswith(str(year)) and d["status"] == "closed"
            and date.fromisoformat(d["date"]).weekday() < 5}


def _early(code, year):
    e = json.loads((Path(__file__).parent.parent / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    return {d["date"]: d["early_close_time"] for d in e["holidays"]["explicit"]
            if d["date"].startswith(str(year)) and d["status"] == "early_close"}


class TestFutureYearFixes:
    """Nasdaq Baltic does not move a weekend holiday to a weekday and is closed on
    31 December."""

    @pytest.mark.parametrize("day", ["2027-05-03", "2027-12-27", "2027-12-28", "2028-01-03"])
    def test_weekend_holidays_leave_no_weekday_closure(self, day):
        assert day not in _closed("XRIS", int(day[:4]))

    def test_new_years_eve_2027_is_closed(self):
        assert "2027-12-31" in _closed("XRIS", 2027)

    @pytest.mark.parametrize("day", ["2028-12-25", "2029-12-25"])
    def test_christmas_day_is_closed(self, day):
        # Nasdaq CSD lists 25 December as a T2S/T2 closing day for the Baltics.
        assert day in _closed("XRIS", int(day[:4]))


# ──────────────────────────────────────────────────────────────
# Future-year fixes (v2.23.5)
# ──────────────────────────────────────────────────────────────

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import generate_dates as _gd


def _closed(code, year):
    """Closed weekdays the registry produces for one year (explicit plus rules)."""
    e = json.loads((Path(__file__).parent.parent / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    days = list(e["holidays"]["explicit"]) + _gd.expand_exchange(e)
    return {d["date"] for d in days
            if d["date"].startswith(str(year)) and d["status"] == "closed"
            and date.fromisoformat(d["date"]).weekday() < 5}


def _early(code, year):
    e = json.loads((Path(__file__).parent.parent / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    return {d["date"]: d["early_close_time"] for d in e["holidays"]["explicit"]
            if d["date"].startswith(str(year)) and d["status"] == "early_close"}


class TestLatvianProclamationDayCarryOver:
    """Latvia's Proclamation Day (18 November) on a weekend carries to Monday."""

    @pytest.mark.parametrize("day", ["2028-11-20", "2029-11-19"])
    def test_monday_after_a_weekend_18_november(self, day):
        assert day in _closed("XRIS", int(day[:4]))


# ──────────────────────────────────────────────────────────────
# Nasdaq Riga trading days, 2025 and 2026
# ──────────────────────────────────────────────────────────────

class TestXRISTradingDays2025And2026:
    """Nasdaq Baltic's monthly bulletins (maintainer's saved copies, 4c12)
    give Riga's equities trading days: 18 in May 2025 (closed 1, 2, 5 and 29
    May: Labour Day, the Cabinet transfer day, the Monday after Restoration
    of Independence Day, and Ascension Day), 18 in November 2025 (closed 17
    and 18 November: transfer day and Proclamation Day) and 19 in June 2026
    (closed 22, 23 and 24 June). This replaces the 2025 counts taken from
    Nasdaq's Nordic and Baltic statistics summaries (19 and 19), which the
    bulletins contradict. 4c13: the January 2026 bulletin (bbid=451) gives
    Riga 21 = 22 weekdays - 1 January, so 2026-01-02 traded, although
    Nasdaq Baltic's calendar listed it closed."""

    @staticmethod
    def _closed_set(xris, explicit_dates, year):
        days = {d for d, e in explicit_dates.items()
                if d.startswith(str(year)) and e["status"] == "closed"}
        days |= {c["date"] for c in xris["ad_hoc_closures"]
                 if c["date"].startswith(str(year)) and c["status"] == "closed"}
        return days

    def test_2025_closed_set(self, xris, explicit_dates):
        assert self._closed_set(xris, explicit_dates, 2025) == {
            "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-01", "2025-05-02",
            "2025-05-05", "2025-05-29", "2025-06-23", "2025-06-24", "2025-11-17",
            "2025-11-18", "2025-12-24", "2025-12-25", "2025-12-26", "2025-12-31"}

    def test_2026_closed_set(self, xris, explicit_dates):
        assert self._closed_set(xris, explicit_dates, 2026) == {
            "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01",
            "2026-05-04", "2026-05-14", "2026-06-22", "2026-06-23", "2026-06-24",
            "2026-11-18", "2026-12-24", "2026-12-25", "2026-12-31"}

    @pytest.mark.parametrize("day,bbid", [("2025-05-02", 440), ("2025-11-17", 448),
                                          ("2026-06-22", 456)])
    def test_transfer_days_cite_the_bulletins(self, xris, day, bbid):
        (c,) = [c for c in xris["ad_hoc_closures"] if c["date"] == day]
        assert c["source_url"] == f"https://nasdaqbaltic.com/statistics/en/bulletins?bbid={bbid}"

    def test_2026_01_02_is_a_trading_day(self, xris, explicit_dates):
        """4c13: January 2026 bulletin (bbid=451): Riga 21 of 22 weekdays,
        only 1 January closed. The 4c12 unconfirmed marker and its recheck
        date are gone."""
        span = xris["verification"]["coverage"]["sources"][1]
        assert span["from"] == "2025-01-01" and span["to"] == "2026-12-31"
        assert "unconfirmed" not in span and "recheck_date" not in span
        assert "2026-01-02" not in explicit_dates
        assert "2026-01-02" not in {c["date"] for c in xris["ad_hoc_closures"]}

    def test_may_2023_bulletin(self, xris, explicit_dates):
        """4c13: May 2023 bulletin (bbid=413): Riga 19 = 23 weekdays - 1, 4,
        5 and 18 May. Week 18/2023 calendar: 04-05.05.2023 trading holiday
        RIG. Nasdaq Riga's notice of 29 May 2023: trading open that day."""
        days = {d for d in explicit_dates if d.startswith("2023-05")}
        days |= {c["date"] for c in xris["ad_hoc_closures"] if c["date"].startswith("2023-05")}
        assert days == {"2023-05-01", "2023-05-04", "2023-05-05", "2023-05-18"}
        (c,) = [c for c in xris["ad_hoc_closures"] if c["date"] == "2023-05-05"]
        assert c["source_url"] == "https://view.news.eu.nasdaq.com/view?id=b13fe0b7d88c8b102a08c1045ffc13b9d&lang=en"

    def test_december_2024_bulletin(self, xris):
        """4c13: December 2024 bulletin (bbid=433): Riga 16 = 22 weekdays -
        23, 24, 25, 26, 30 and 31 December."""
        (c,) = [c for c in xris["ad_hoc_closures"] if c["date"] == "2024-12-30"]
        assert c["source_url"] == "https://nasdaqbaltic.com/statistics/en/bulletins?bbid=433"


class TestXRISTransferDays2010To2024:
    """4c12: transfer days on the exchange's own word (2010 notice; investor
    calendars for weeks 1/2015 and 52/2024), plus exchange_calendars' 2023
    and 2024 ones. Others are leads and stay open."""

    def test_transfer_days(self, xris):
        assert sorted(c["date"] for c in xris["ad_hoc_closures"]
                      if c["name"].startswith("Cabinet transfer day") and c["date"] < "2025") == [
            "2010-05-03", "2010-06-25", "2010-11-19", "2015-01-02", "2023-05-05",
            "2024-12-23", "2024-12-30"]

    @pytest.mark.parametrize("day", ["2012-04-30", "2014-05-02", "2014-11-17", "2015-06-22",
                                     "2017-05-05", "2018-04-30", "2020-06-22", "2021-05-03",
                                     "2021-06-25", "2021-11-19"])
    def test_unread_transfer_days_stay_open(self, xris, explicit_dates, day):
        assert day not in explicit_dates
        assert day not in {c["date"] for c in xris["ad_hoc_closures"]}

    def test_contradicted_by(self, xris):
        assert xris["verification"]["coverage"]["sources"][0]["contradicted_by"] == [
            "2010-05-03", "2010-06-25", "2010-11-19", "2012-12-25", "2013-12-25",
            "2014-12-25", "2015-01-02", "2015-12-25", "2017-12-25", "2018-05-09",
            "2018-07-09", "2018-09-24", "2018-12-25", "2019-12-25", "2020-12-25",
            "2024-12-25"]
