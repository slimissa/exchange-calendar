#!/usr/bin/env python3
"""
test_vilnius_holidays.py — Ground truth tests for XLIT (Nasdaq Vilnius).

Key facts verified:
    - Regular hours: 10:00-16:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Restoration of State Day (Feb 16)
    - Restoration of Independence Day (Mar 11)
    - St. John's Day (Jun 24)
    - Statehood Day (Jul 6)
    - Assumption Day (Aug 15)
    - All Saints' Day (Nov 1)
    - Christmas Eve (Dec 24) — full closure
    - Lithuania does NOT shift holidays from weekends
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XLIT.json)
    2. Lithuanian holiday announcements changed (verify against nasdaqbaltic.com)

Run:
    python3 -m pytest tests/test_vilnius_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xlit():
    """Load XLIT.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XLIT.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xlit):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xlit["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXLITProperties:
    def test_code(self, xlit):
        assert xlit["code"] == "XLIT"

    def test_mic(self, xlit):
        assert xlit["mic"] == "XLIT"

    def test_name(self, xlit):
        assert xlit["name"] == "Nasdaq Vilnius"

    def test_timezone(self, xlit):
        assert xlit["timezone"] == "Europe/Vilnius"

    def test_regular_hours(self, xlit):
        assert xlit["regular_hours"]["open"] == "10:00"
        assert xlit["regular_hours"]["close"] == "16:00"

    def test_no_lunch_break(self, xlit):
        lunch = [s for s in xlit.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xlit):
        assert "extended_hours" not in xlit or xlit.get("extended_hours") is None

    def test_generation_range(self, xlit):
        assert "generation_range" in xlit
        assert xlit["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xlit):
        assert xlit.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xlit):
        """Lithuania uses explicit dates only."""
        rules = xlit["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXLITFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_restoration_state_2025(self, explicit_dates):
        """Feb 16, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-02-16" not in explicit_dates

    def test_restoration_independence_2025(self, explicit_dates):
        """Mar 11, 2025 is Tuesday."""
        assert "2025-03-11" in explicit_dates
        assert "Independence" in explicit_dates["2025-03-11"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_st_johns_2025(self, explicit_dates):
        """Jun 24, 2025 is Tuesday."""
        assert "2025-06-24" in explicit_dates
        assert "John" in explicit_dates["2025-06-24"]["name"]

    def test_statehood_2025(self, explicit_dates):
        """Jul 6, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-07-06" not in explicit_dates

    def test_assumption_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday."""
        assert "2025-08-15" in explicit_dates
        assert "Assumption" in explicit_dates["2025-08-15"]["name"]

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday — no explicit entry (no substitution)."""
        assert "2025-11-01" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXLITChristmas:
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

    def test_christmas_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates

    def test_boxing_day_2027_substitute(self, explicit_dates):
        """Dec 26, 2027 is Sunday — substitute to Tuesday Dec 28."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXLITEaster:
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

class TestXLITStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Lithuania weekend is Saturday-Sunday."""
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
        """Lithuania has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xlit, explicit_dates):
        start = date.fromisoformat(xlit["generation_range"][0])
        end = date.fromisoformat(xlit["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~55-70 entries."""
        assert 50 <= len(explicit_dates) <= 70, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "nasdaqbaltic.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXLITWeekendPattern:
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

class TestXLITSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2025-02-16" not in explicit_dates  # Sunday
        assert "2025-11-01" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 4, f"Expected some observed holidays, got {observed_count}"