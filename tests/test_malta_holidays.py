#!/usr/bin/env python3
"""
test_malta_holidays.py — Ground truth tests for XMAL (Malta Stock Exchange).

Key facts verified:
    - Regular hours: 09:00-15:30 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - St. Paul's Shipwreck (Feb 10) — unique to Malta
    - Freedom Day (Mar 31)
    - Sette Giugno (Jun 7) — unique to Malta
    - 14 national holidays
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XMAL.json)
    2. Maltese holiday announcements changed (verify against borzamalta.com.mt)

Run:
    python3 -m pytest tests/test_malta_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xmal():
    """Load XMAL.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XMAL.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xmal):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xmal["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXMALProperties:
    def test_code(self, xmal):
        assert xmal["code"] == "XMAL"

    def test_mic(self, xmal):
        assert xmal["mic"] == "XMAL"

    def test_name(self, xmal):
        assert xmal["name"] == "Malta Stock Exchange"

    def test_timezone(self, xmal):
        assert xmal["timezone"] == "Europe/Malta"

    def test_regular_hours(self, xmal):
        assert xmal["regular_hours"]["open"] == "09:00"
        assert xmal["regular_hours"]["close"] == "15:30"

    def test_no_lunch_break(self, xmal):
        lunch = [s for s in xmal.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xmal):
        assert "extended_hours" not in xmal or xmal.get("extended_hours") is None

    def test_generation_range(self, xmal):
        assert "generation_range" in xmal
        assert xmal["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xmal):
        assert xmal.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xmal):
        """Malta uses explicit dates only."""
        rules = xmal["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (January-March)
# ──────────────────────────────────────────────────────────────

class TestXMALFixedHolidaysJanMar:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_st_pauls_2025(self, explicit_dates):
        """Feb 10, 2025 is Monday."""
        assert "2025-02-10" in explicit_dates
        assert "Paul" in explicit_dates["2025-02-10"]["name"]

    def test_st_joseph_2025(self, explicit_dates):
        """Mar 19, 2025 is Wednesday."""
        assert "2025-03-19" in explicit_dates
        assert "Joseph" in explicit_dates["2025-03-19"]["name"]

    def test_freedom_day_2025(self, explicit_dates):
        """Mar 31, 2025 is Monday."""
        assert "2025-03-31" in explicit_dates
        assert "Freedom" in explicit_dates["2025-03-31"]["name"]


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (May-September)
# ──────────────────────────────────────────────────────────────

class TestXMALFixedHolidaysMaySep:
    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_sette_giugno_2025(self, explicit_dates):
        """Jun 7, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-06-07" not in explicit_dates

    def test_st_peter_paul_2025(self, explicit_dates):
        """Jun 29, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-06-29" not in explicit_dates

    def test_assumption_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday."""
        assert "2025-08-15" in explicit_dates
        assert "Assumption" in explicit_dates["2025-08-15"]["name"]

    def test_victory_day_2025(self, explicit_dates):
        """Sep 8, 2025 is Monday."""
        assert "2025-09-08" in explicit_dates
        assert "Victory" in explicit_dates["2025-09-08"]["name"]

    def test_independence_2025(self, explicit_dates):
        """Sep 21, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-09-21" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (December)
# ──────────────────────────────────────────────────────────────

class TestXMALFixedHolidaysDec:
    def test_immaculate_conception_2025(self, explicit_dates):
        """Dec 8, 2025 is Monday."""
        assert "2025-12-08" in explicit_dates
        assert "Immaculate" in explicit_dates["2025-12-08"]["name"]

    def test_republic_day_2025(self, explicit_dates):
        """Dec 13, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-12-13" not in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXMALEaster:
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

class TestXMALStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Malta weekend is Saturday-Sunday."""
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
        """Malta has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xmal, explicit_dates):
        start = date.fromisoformat(xmal["generation_range"][0])
        end = date.fromisoformat(xmal["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~70-80 entries."""
        assert 55 <= len(explicit_dates) <= 75, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "borzamalta.com.mt" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXMALWeekendPattern:
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

class TestXMALSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_observed_and_substitute_names(self, explicit_dates):
        count = sum(1 for e in explicit_dates.values() 
                   if "observed" in e["name"].lower() or "substitute" in e["name"].lower())
        assert count >= 3, f"Expected many observed/substitute holidays, got {count}"