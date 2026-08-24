#!/usr/bin/env python3
"""
test_bulgaria_holidays.py — Ground truth tests for XBUL (Bulgarian Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-14:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Liberation Day (Mar 3)
    - St. George's Day (May 6)
    - Culture and Literacy Day (May 24)
    - Orthodox Easter (movable)
    - Christmas Eve (Dec 24) — full closure
    - Bulgaria uses substitution for weekend holidays
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBUL.json)
    2. Bulgarian holiday announcements changed (verify against bse-sofia.bg)

Run:
    python3 -m pytest tests/test_bulgaria_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbul():
    """Load XBUL.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBUL.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbul):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbul["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBULProperties:
    def test_code(self, xbul):
        assert xbul["code"] == "XBUL"

    def test_mic(self, xbul):
        assert xbul["mic"] == "XBUL"

    def test_name(self, xbul):
        assert xbul["name"] == "Bulgarian Stock Exchange"

    def test_timezone(self, xbul):
        assert xbul["timezone"] == "Europe/Sofia"

    def test_regular_hours(self, xbul):
        assert xbul["regular_hours"]["open"] == "09:30"
        assert xbul["regular_hours"]["close"] == "14:00"

    def test_no_lunch_break(self, xbul):
        lunch = [s for s in xbul.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbul):
        assert "extended_hours" not in xbul or xbul.get("extended_hours") is None

    def test_generation_range(self, xbul):
        assert "generation_range" in xbul
        assert xbul["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xbul):
        assert xbul.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xbul):
        """Bulgaria uses explicit dates only."""
        rules = xbul["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXBULFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_liberation_day_2025(self, explicit_dates):
        """Mar 3, 2025 is Monday."""
        assert "2025-03-03" in explicit_dates
        assert "Liberation" in explicit_dates["2025-03-03"]["name"]

    def test_liberation_day_2029_substitute(self, explicit_dates):
        """Mar 3, 2029 is Saturday — substitute to Monday Mar 5."""
        assert "2029-03-03" not in explicit_dates
        assert "2029-03-05" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_st_georges_2025(self, explicit_dates):
        """May 6, 2025 is Tuesday."""
        assert "2025-05-06" in explicit_dates
        assert "George" in explicit_dates["2025-05-06"]["name"]

    def test_st_georges_2029_substitute(self, explicit_dates):
        """May 6, 2029 is Sunday — substitute to Monday May 7."""
        assert "2029-05-06" not in explicit_dates
        assert "2029-05-07" in explicit_dates

    def test_culture_literacy_2025(self, explicit_dates):
        """May 24, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-05-24" not in explicit_dates

    def test_unification_2025(self, explicit_dates):
        """Sep 6, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-09-06" not in explicit_dates

    def test_independence_2025(self, explicit_dates):
        """Sep 22, 2025 is Monday."""
        assert "2025-09-22" in explicit_dates
        assert "Independence" in explicit_dates["2025-09-22"]["name"]

    def test_independence_2029_substitute(self, explicit_dates):
        """Sep 22, 2029 is Saturday — substitute to Monday Sep 24."""
        assert "2029-09-22" not in explicit_dates
        assert "2029-09-24" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Orthodox Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXBULOrthodoxEaster:
    def test_good_friday_2025(self, explicit_dates):
        """Orthodox Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert "Good Friday" in explicit_dates["2025-04-18"]["name"]

    def test_good_friday_2026(self, explicit_dates):
        """Orthodox Easter - 2 days — April 10, 2026."""
        assert "2026-04-10" in explicit_dates

    def test_good_friday_2027(self, explicit_dates):
        """Orthodox Easter - 2 days — April 30, 2027."""
        assert "2027-04-30" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        """Orthodox Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert "Easter Monday" in explicit_dates["2025-04-21"]["name"]

    def test_easter_monday_2026(self, explicit_dates):
        """Orthodox Easter + 1 day — April 13, 2026."""
        assert "2026-04-13" in explicit_dates

    def test_easter_monday_2028(self, explicit_dates):
        """Orthodox Easter + 1 day — April 17, 2028."""
        assert "2028-04-17" in explicit_dates

    def test_easter_monday_2029(self, explicit_dates):
        """Orthodox Easter + 1 day — April 9, 2029."""
        assert "2029-04-09" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXBULChristmas:
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

    def test_boxing_day_2026_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute to Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates

    def test_boxing_day_2027_substitute(self, explicit_dates):
        """Dec 26, 2027 is Sunday — substitute to Tuesday Dec 28."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBULStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Bulgaria weekend is Saturday-Sunday."""
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
        """Bulgaria has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xbul, explicit_dates):
        start = date.fromisoformat(xbul["generation_range"][0])
        end = date.fromisoformat(xbul["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~55-65 entries."""
        assert 50 <= len(explicit_dates) <= 70, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "bse-sofia.bg" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBULWeekendPattern:
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

class TestXBULSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2025-05-24" not in explicit_dates  # Saturday

    def test_observed_and_substitute_names(self, explicit_dates):
        count = sum(1 for e in explicit_dates.values() 
                   if "observed" in e["name"].lower() or "substitute" in e["name"].lower())
        assert count >= 6, f"Expected many observed/substitute holidays, got {count}"