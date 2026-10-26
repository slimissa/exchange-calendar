#!/usr/bin/env python3
"""
test_brussels_holidays.py — Ground truth tests for XBRU (Euronext Brussels).

Key facts verified:
    - Regular hours: 09:00-17:30 (Euronext standard)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Euronext Brussels closes only on New Year's Day, Good Friday, Easter
      Monday, Labour Day (May 1), Christmas Day and Boxing Day (Dec 26)
    - Belgian National Day (Jul 21), Assumption (Aug 15), All Saints' Day,
      Armistice Day (Nov 11), Ascension Day and Whit Monday are Belgian
      holidays but FULL TRADING DAYS on Euronext Brussels
    - Weekend holidays are not substituted (Euronext 2026 calendar: Jan 2 and
      Dec 28 are full trading days for Brussels)
    - Source: Euronext "Holiday Calendar for Cash and Derivatives markets",
      2025 and 2026 (live.euronext.com/en/resources/trading-hours-holidays)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBRU.json)
    2. Euronext announcements changed (verify against euronext.com)

Run:
    python3 -m pytest tests/test_brussels_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbru():
    """Load XBRU.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBRU.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbru):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbru["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBRUProperties:
    def test_code(self, xbru):
        assert xbru["code"] == "XBRU"

    def test_mic(self, xbru):
        assert xbru["mic"] == "XBRU"

    def test_name(self, xbru):
        assert xbru["name"] == "Euronext Brussels"

    def test_timezone(self, xbru):
        assert xbru["timezone"] == "Europe/Brussels"

    def test_regular_hours(self, xbru):
        assert xbru["regular_hours"]["open"] == "09:00"
        assert xbru["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xbru):
        lunch = [s for s in xbru.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbru):
        assert "extended_hours" not in xbru or xbru.get("extended_hours") is None

    def test_generation_range(self, xbru):
        assert "generation_range" in xbru
        assert xbru["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xbru):
        assert xbru.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xbru):
        """Belgium uses explicit dates only."""
        rules = xbru["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXBRUFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_no_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday: closed on neither Jan 1 nor Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" not in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_weekend(self, explicit_dates):
        """May 1, 2027 is Saturday: no substitute on Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" not in explicit_dates

    def test_belgian_holidays_are_trading_days(self, explicit_dates):
        """National Day, Assumption, All Saints and Armistice Day do not close Brussels."""
        for day in ("2025-07-21", "2025-08-15", "2025-11-11", "2026-07-21",
                    "2026-11-11", "2027-07-21", "2027-11-01", "2027-11-11",
                    "2028-07-21", "2028-08-15", "2028-11-01", "2029-08-15",
                    "2029-11-01", "2029-11-12"):
            assert day not in explicit_dates, day


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXBRUChristmas:
    def test_christmas_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday: Euronext lists it as closed for every market."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_boxing_day_2028_2029(self, explicit_dates):
        for day in ("2028-12-26", "2029-12-26"):
            assert day in explicit_dates, day

    def test_christmas_2027_no_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday: no Monday Dec 27 closure."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" not in explicit_dates

    def test_boxing_day_2026_no_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday: Euronext lists Dec 28 as a full trading day."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" not in explicit_dates

    def test_boxing_day_2027_no_substitute(self, explicit_dates):
        """Dec 26, 2027 is Sunday: no Tuesday Dec 28 closure."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXBRUEaster:
    def test_good_friday_2025(self, explicit_dates):
        """Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["name"] == "Good Friday"

    def test_good_friday_2026(self, explicit_dates):
        """Easter - 2 days — April 3, 2026."""
        assert "2026-04-03" in explicit_dates
        assert explicit_dates["2026-04-03"]["name"] == "Good Friday"

    def test_good_friday_2027_2029(self, explicit_dates):
        for day in ("2027-03-26", "2028-04-14", "2029-03-30"):
            assert day in explicit_dates, day

    def test_easter_monday_2025(self, explicit_dates):
        """Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["name"] == "Easter Monday"

    def test_easter_monday_2026(self, explicit_dates):
        """Easter + 1 day — April 6, 2026."""
        assert "2026-04-06" in explicit_dates

    def test_easter_monday_2027(self, explicit_dates):
        """Easter + 1 day — March 29, 2027."""
        assert "2027-03-29" in explicit_dates

    def test_ascension_is_a_trading_day(self, explicit_dates):
        """Of the Euronext cash markets only Oslo closes for Ascension Day."""
        for day in ("2025-05-29", "2026-05-14", "2027-05-06", "2028-05-25", "2029-05-10"):
            assert day not in explicit_dates, day

    def test_whit_monday_is_a_trading_day(self, explicit_dates):
        """Of the Euronext cash markets only Oslo closes for Whit Monday."""
        for day in ("2025-06-09", "2026-05-25", "2027-05-17", "2028-06-05", "2029-05-21"):
            assert day not in explicit_dates, day

# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBRUStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Belgium weekend is Saturday-Sunday."""
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
        """Belgium has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xbru, explicit_dates):
        start = date.fromisoformat(xbru["generation_range"][0])
        end = date.fromisoformat(xbru["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """25 closures: the Euronext common calendar, 2025-2029."""
        assert 20 <= len(explicit_dates) <= 30, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "euronext.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBRUWeekendPattern:
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

class TestXBRUSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_no_substitute_holidays(self, explicit_dates):
        """Euronext does not shift weekend holidays to weekdays."""
        bad = [e["name"] for e in explicit_dates.values()
               if "observed" in e["name"].lower() or "substitute" in e["name"].lower()]
        assert bad == []


# ──────────────────────────────────────────────────────────────
# Divergence regression (Phase 2, session 4)
# ──────────────────────────────────────────────────────────────

# Euronext "Holiday Calendar for Cash and Derivatives markets", column for this
# exchange. Closed days only (Dec 24 and Dec 31 are half trading days).
OFFICIAL_CLOSED_2025 = {
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-01",
    "2025-12-25", "2025-12-26",
}
OFFICIAL_CLOSED_2026 = {
    "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-12-25",
}

# The 12 dates tools/divergence_test.py flagged for XBRU.
WRONGLY_CLOSED = [
    "2025-05-29",  # Ascension Day
    "2025-06-09",  # Whit Monday
    "2025-07-21",  # Belgian National Day
    "2025-08-15",  # Assumption Day
    "2025-11-11",  # Armistice Day
    "2026-05-14",  # Ascension Day
    "2026-05-25",  # Whit Monday
    "2026-07-21",  # Belgian National Day
    "2026-11-11",  # Armistice Day
    "2026-12-28",  # substitute for Boxing Day (Dublin only)
]
WRONGLY_OPEN = [
    "2025-04-18",  # Good Friday
    "2026-04-03",  # Good Friday
]


class TestXBRUDivergenceRegression:
    def test_closures_match_euronext_2025(self, explicit_dates):
        assert {d for d in explicit_dates if d.startswith("2025")} == OFFICIAL_CLOSED_2025

    def test_closures_match_euronext_2026(self, explicit_dates):
        assert {d for d in explicit_dates if d.startswith("2026")} == OFFICIAL_CLOSED_2026

    @pytest.mark.parametrize("day", WRONGLY_CLOSED)
    def test_full_trading_day_is_open(self, explicit_dates, day):
        assert date.fromisoformat(day).weekday() < 5
        assert day not in explicit_dates

    @pytest.mark.parametrize("day", WRONGLY_OPEN)
    def test_missing_closure_is_closed(self, explicit_dates, day):
        assert date.fromisoformat(day).weekday() < 5
        assert explicit_dates[day]["status"] == "closed"
        assert explicit_dates[day]["name"] == "Good Friday"

    def test_built_calendar_matches(self):
        """The shipped calendar.json carries the same fix."""
        path = Path(__file__).parent.parent / "calendar.json"
        with open(path) as f:
            cal = json.load(f)
        entry = next(e for e in cal["exchanges"] if e["code"] == "XBRU")
        closed = {
            h["date"]
            for h in entry["holidays"]["explicit"] + entry["holidays"]["generated"]
            if h["status"] == "closed"
        }
        assert {d for d in closed if d.startswith("2025")} == OFFICIAL_CLOSED_2025
        assert {d for d in closed if d.startswith("2026")} == OFFICIAL_CLOSED_2026
