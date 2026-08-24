#!/usr/bin/env python3
"""
test_zagreb_holidays.py — Ground truth tests for XZAG (Zagreb Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-16:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Statehood Day (May 30)
    - Anti-Fascist Struggle Day (Jun 22)
    - Victory Day (Aug 5)
    - Independence Day (Oct 8)
    - Croatia uses substitution for some weekend holidays
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XZAG.json)
    2. Croatian holiday announcements changed (verify against zse.hr)

Run:
    python3 -m pytest tests/test_zagreb_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xzag():
    """Load XZAG.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XZAG.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xzag):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xzag["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXZAGProperties:
    def test_code(self, xzag):
        assert xzag["code"] == "XZAG"

    def test_mic(self, xzag):
        assert xzag["mic"] == "XZAG"

    def test_name(self, xzag):
        assert xzag["name"] == "Zagreb Stock Exchange"

    def test_timezone(self, xzag):
        assert xzag["timezone"] == "Europe/Zagreb"

    def test_regular_hours(self, xzag):
        assert xzag["regular_hours"]["open"] == "09:30"
        assert xzag["regular_hours"]["close"] == "16:00"

    def test_no_lunch_break(self, xzag):
        lunch = [s for s in xzag.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xzag):
        assert "extended_hours" not in xzag or xzag.get("extended_hours") is None

    def test_generation_range(self, xzag):
        assert "generation_range" in xzag
        assert xzag["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xzag):
        assert xzag.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xzag):
        """Croatia uses explicit dates only."""
        rules = xzag["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (January-May)
# ──────────────────────────────────────────────────────────────

class TestXZAGFixedHolidaysJanMay:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_epiphany_2025(self, explicit_dates):
        """Jan 6, 2025 is Monday."""
        assert "2025-01-06" in explicit_dates
        assert "Epiphany" in explicit_dates["2025-01-06"]["name"]

    def test_epiphany_2029_substitute(self, explicit_dates):
        """Jan 6, 2029 is Saturday — substitute to Monday Jan 8."""
        assert "2029-01-06" not in explicit_dates
        assert "2029-01-08" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_statehood_2025(self, explicit_dates):
        """May 30, 2025 is Friday."""
        assert "2025-05-30" in explicit_dates
        assert "Statehood" in explicit_dates["2025-05-30"]["name"]


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (June-December)
# ──────────────────────────────────────────────────────────────

class TestXZAGFixedHolidaysJunDec:
    def test_anti_fascist_2025(self, explicit_dates):
        """Jun 22, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-06-22" not in explicit_dates

    def test_victory_day_2025(self, explicit_dates):
        """Aug 5, 2025 is Tuesday."""
        assert "2025-08-05" in explicit_dates
        assert "Victory" in explicit_dates["2025-08-05"]["name"]

    def test_assumption_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday."""
        assert "2025-08-15" in explicit_dates
        assert "Assumption" in explicit_dates["2025-08-15"]["name"]

    def test_independence_2025(self, explicit_dates):
        """Oct 8, 2025 is Wednesday."""
        assert "2025-10-08" in explicit_dates
        assert "Independence" in explicit_dates["2025-10-08"]["name"]

    def test_independence_2028_substitute(self, explicit_dates):
        """Oct 8, 2028 is Sunday — substitute to Monday Oct 9."""
        assert "2028-10-08" not in explicit_dates
        assert "2028-10-09" in explicit_dates

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-11-01" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXZAGEaster:
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

    def test_corpus_christi_2025(self, explicit_dates):
        """Easter + 60 days — June 19, 2025."""
        assert "2025-06-19" in explicit_dates
        assert "Corpus" in explicit_dates["2025-06-19"]["name"]

    def test_corpus_christi_2028(self, explicit_dates):
        """Easter + 60 days — June 15, 2028."""
        assert "2028-06-15" in explicit_dates

    def test_corpus_christi_2029(self, explicit_dates):
        """Easter + 60 days — May 31, 2029."""
        assert "2029-05-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXZAGChristmas:
    def test_christmas_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_st_stephens_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert "Stephen" in explicit_dates["2025-12-26"]["name"]

    def test_christmas_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates

    def test_st_stephens_2027_substitute(self, explicit_dates):
        """Dec 26, 2027 is Sunday — substitute to Tuesday Dec 28."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXZAGStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Croatia weekend is Saturday-Sunday."""
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
        """Croatia has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xzag, explicit_dates):
        start = date.fromisoformat(xzag["generation_range"][0])
        end = date.fromisoformat(xzag["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~60-70 entries."""
        assert 55 <= len(explicit_dates) <= 75, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "zse.hr" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXZAGWeekendPattern:
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

class TestXZAGSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 4, f"Expected some observed holidays, got {observed_count}"