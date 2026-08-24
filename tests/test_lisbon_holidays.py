#!/usr/bin/env python3
"""
test_lisbon_holidays.py — Ground truth tests for XLIS (Euronext Lisbon).

Key facts verified:
    - Regular hours: 09:00-17:30 (Euronext standard)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Freedom Day (Apr 25)
    - Portugal Day (Jun 10)
    - Republic Day (Oct 5)
    - Restoration of Independence (Dec 1)
    - Immaculate Conception (Dec 8)
    - 13 national holidays
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XLIS.json)
    2. Portuguese holiday announcements changed (verify against euronext.com)

Run:
    python3 -m pytest tests/test_lisbon_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xlis():
    """Load XLIS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XLIS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xlis):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xlis["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXLISProperties:
    def test_code(self, xlis):
        assert xlis["code"] == "XLIS"

    def test_mic(self, xlis):
        assert xlis["mic"] == "XLIS"

    def test_name(self, xlis):
        assert xlis["name"] == "Euronext Lisbon"

    def test_timezone(self, xlis):
        assert xlis["timezone"] == "Europe/Lisbon"

    def test_regular_hours(self, xlis):
        assert xlis["regular_hours"]["open"] == "09:00"
        assert xlis["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xlis):
        lunch = [s for s in xlis.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xlis):
        assert "extended_hours" not in xlis or xlis.get("extended_hours") is None

    def test_generation_range(self, xlis):
        assert "generation_range" in xlis
        assert xlis["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xlis):
        assert xlis.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xlis):
        """Portugal uses explicit dates only."""
        rules = xlis["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (January-April)
# ──────────────────────────────────────────────────────────────

class TestXLISFixedHolidaysJanApr:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_freedom_day_2025(self, explicit_dates):
        """Apr 25, 2025 is Friday."""
        assert "2025-04-25" in explicit_dates
        assert "Freedom" in explicit_dates["2025-04-25"]["name"]

    def test_freedom_day_2026(self, explicit_dates):
        """Apr 25, 2026 is Saturday — no explicit entry (no substitution)."""
        assert "2026-04-25" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (May-August)
# ──────────────────────────────────────────────────────────────

class TestXLISFixedHolidaysMayAug:
    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_portugal_day_2025(self, explicit_dates):
        """Jun 10, 2025 is Tuesday."""
        assert "2025-06-10" in explicit_dates
        assert "Portugal" in explicit_dates["2025-06-10"]["name"]

    def test_assumption_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday."""
        assert "2025-08-15" in explicit_dates
        assert "Assumption" in explicit_dates["2025-08-15"]["name"]


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (September-December)
# ──────────────────────────────────────────────────────────────

class TestXLISFixedHolidaysSepDec:
    def test_republic_day_2025(self, explicit_dates):
        """Oct 5, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-10-05" not in explicit_dates

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-11-01" not in explicit_dates

    def test_restoration_2025(self, explicit_dates):
        """Dec 1, 2025 is Monday."""
        assert "2025-12-01" in explicit_dates
        assert "Restoration" in explicit_dates["2025-12-01"]["name"]

    def test_immaculate_conception_2025(self, explicit_dates):
        """Dec 8, 2025 is Monday."""
        assert "2025-12-08" in explicit_dates
        assert "Immaculate" in explicit_dates["2025-12-08"]["name"]


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXLISChristmas:
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

class TestXLISEaster:
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
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXLISStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Portugal weekend is Saturday-Sunday."""
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
        """Portugal has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xlis, explicit_dates):
        start = date.fromisoformat(xlis["generation_range"][0])
        end = date.fromisoformat(xlis["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~60-70 entries."""
        assert 50 <= len(explicit_dates) <= 70, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "euronext.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXLISWeekendPattern:
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

class TestXLISSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2025-10-05" not in explicit_dates  # Sunday

    def test_observed_and_substitute_names(self, explicit_dates):
        count = sum(1 for e in explicit_dates.values() 
                   if "observed" in e["name"].lower() or "substitute" in e["name"].lower())
        assert count >= 3, f"Expected some observed/substitute holidays, got {count}"