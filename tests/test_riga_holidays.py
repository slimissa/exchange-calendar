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
        assert xris["regular_hours"]["open"] == "10:00"
        assert xris["regular_hours"]["close"] == "16:00"

    def test_no_lunch_break(self, xris):
        lunch = [s for s in xris.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xris):
        assert "extended_hours" not in xris or xris.get("extended_hours") is None

    def test_generation_range(self, xris):
        assert "generation_range" in xris
        assert xris["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xris):
        assert xris.get("ad_hoc_closures", []) == []

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
        """~45-60 entries."""
        assert 44 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
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
    """Nasdaq's monthly statistics give Riga's trading days: 19 in May 2025
    (Riga closed 1, 5 and 29 May: Labour Day, the Monday after Restoration of
    Independence Day, and Ascension Day, which every Baltic exchange observes),
    19 in November 2025 (Riga closed on 18 November only) and 19 in December
    2025 (24, 25, 26 and 31 December)."""

    @staticmethod
    def _closed_set(explicit_dates, year):
        return {d for d, e in explicit_dates.items()
                if d.startswith(str(year)) and e["status"] == "closed"}

    def test_2025_closed_set(self, explicit_dates):
        assert self._closed_set(explicit_dates, 2025) == {
            "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-01", "2025-05-05",
            "2025-05-29", "2025-06-23", "2025-06-24", "2025-11-18", "2025-12-24",
            "2025-12-25", "2025-12-26", "2025-12-31"}

    def test_2026_closed_set(self, explicit_dates):
        assert self._closed_set(explicit_dates, 2026) == {
            "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-05-04",
            "2026-05-14", "2026-06-23", "2026-06-24", "2026-11-18", "2026-12-24",
            "2026-12-25", "2026-12-31"}

    @pytest.mark.parametrize("day", ["2025-05-02", "2025-11-17"])
    def test_trading_days(self, explicit_dates, day):
        assert day not in explicit_dates
