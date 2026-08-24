#!/usr/bin/env python3
"""
test_brv_holidays.py — Ground truth tests for XBRV (BRVM - West Africa Regional Stock Exchange).

Key facts verified:
    - Regular hours: 09:00-14:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Easter Monday, Ascension, Whit Monday (movable)
    - Labour Day (May 1)
    - Assumption Day (Aug 15)
    - All Saints' Day (Nov 1)
    - Christmas Day (Dec 25)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBRV.json)
    2. West African holiday announcements changed (verify against brvm.org)

Run:
    python3 -m pytest tests/test_brv_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbrvm():
    """Load XBRV.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBRV.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbrvm):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbrvm["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBRVProperties:
    def test_code(self, xbrvm):
        assert xbrvm["code"] == "XBRV"

    def test_mic(self, xbrvm):
        assert xbrvm["mic"] == "XBRV"

    def test_name(self, xbrvm):
        assert xbrvm["name"] == "BRVM (West Africa Regional Stock Exchange)"

    def test_timezone(self, xbrvm):
        assert xbrvm["timezone"] == "Africa/Abidjan"

    def test_regular_hours(self, xbrvm):
        assert xbrvm["regular_hours"]["open"] == "09:00"
        assert xbrvm["regular_hours"]["close"] == "14:00"

    def test_no_lunch_break(self, xbrvm):
        lunch = [s for s in xbrvm.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbrvm):
        assert "extended_hours" not in xbrvm or xbrvm.get("extended_hours") is None

    def test_generation_range(self, xbrvm):
        assert "generation_range" in xbrvm
        assert xbrvm["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xbrvm):
        assert xbrvm.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xbrvm):
        """BRVM uses explicit dates only."""
        rules = xbrvm["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXBRVFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_assumption_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday."""
        assert "2025-08-15" in explicit_dates
        assert "Assumption" in explicit_dates["2025-08-15"]["name"]

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-11-01" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXBRVChristmas:
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

class TestXBRVEaster:
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

    def test_ascension_2025(self, explicit_dates):
        """Easter + 39 days — May 29, 2025."""
        assert "2025-05-29" in explicit_dates
        assert "Ascension" in explicit_dates["2025-05-29"]["name"]

    def test_ascension_2028(self, explicit_dates):
        """Easter + 39 days — May 25, 2028."""
        assert "2028-05-25" in explicit_dates

    def test_whit_monday_2025(self, explicit_dates):
        """Easter + 50 days — June 9, 2025."""
        assert "2025-06-09" in explicit_dates
        assert "Whit" in explicit_dates["2025-06-09"]["name"]

    def test_whit_monday_2028(self, explicit_dates):
        """Easter + 50 days — June 5, 2028."""
        assert "2028-06-05" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBRVStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """BRVM weekend is Saturday-Sunday."""
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
        """BRVM has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xbrvm, explicit_dates):
        start = date.fromisoformat(xbrvm["generation_range"][0])
        end = date.fromisoformat(xbrvm["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~35-45 entries (BRVM has fewer holidays)."""
        assert 35 <= len(explicit_dates) <= 50, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "brvm.org" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBRVWeekendPattern:
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

class TestXBRVSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2025-11-01" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 2, f"Expected some observed holidays, got {observed_count}"