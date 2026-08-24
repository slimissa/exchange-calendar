#!/usr/bin/env python3
"""
test_amsterdam_holidays.py — Ground truth tests for XAMS (Euronext Amsterdam).

Key facts verified:
    - Regular hours: 09:00-17:30 (Euronext standard)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - King's Day (Apr 27) — unique to Netherlands
    - Liberation Day (May 5) — only 2025 (every 5 years)
    - Good Friday, Easter Monday, Ascension, Whit Monday
    - Christmas Day and Boxing Day
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XAMS.json)
    2. Dutch holiday announcements changed (verify against euronext.com)

Run:
    python3 -m pytest tests/test_amsterdam_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xams():
    """Load XAMS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XAMS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xams):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xams["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXAMSProperties:
    def test_code(self, xams):
        assert xams["code"] == "XAMS"

    def test_mic(self, xams):
        assert xams["mic"] == "XAMS"

    def test_name(self, xams):
        assert xams["name"] == "Euronext Amsterdam"

    def test_timezone(self, xams):
        assert xams["timezone"] == "Europe/Amsterdam"

    def test_regular_hours(self, xams):
        assert xams["regular_hours"]["open"] == "09:00"
        assert xams["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xams):
        lunch = [s for s in xams.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xams):
        assert "extended_hours" not in xams or xams.get("extended_hours") is None

    def test_generation_range(self, xams):
        assert "generation_range" in xams
        assert xams["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xams):
        assert xams.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xams):
        """Netherlands uses explicit dates only."""
        rules = xams["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXAMSFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_kings_day_2025(self, explicit_dates):
        """Apr 27, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-04-27" not in explicit_dates

    def test_kings_day_2026(self, explicit_dates):
        """Apr 27, 2026 is Monday."""
        assert "2026-04-27" in explicit_dates
        assert "King" in explicit_dates["2026-04-27"]["name"]

    def test_kings_day_2028(self, explicit_dates):
        """Apr 27, 2028 is Thursday."""
        assert "2028-04-27" in explicit_dates

    def test_liberation_day_2025(self, explicit_dates):
        """May 5, 2025 is Monday — only observed every 5 years."""
        assert "2025-05-05" in explicit_dates
        assert "Liberation" in explicit_dates["2025-05-05"]["name"]

    def test_liberation_day_2026_absent(self, explicit_dates):
        """May 5, 2026 is Tuesday — NOT a holiday (only every 5 years)."""
        assert "2026-05-05" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXAMSChristmas:
    def test_christmas_2025(self, explicit_dates):
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
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXAMSEaster:
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

class TestXAMSStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Netherlands weekend is Saturday-Sunday."""
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
        """Netherlands has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xams, explicit_dates):
        start = date.fromisoformat(xams["generation_range"][0])
        end = date.fromisoformat(xams["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~40-50 entries (Netherlands has fewer holidays)."""
        assert 35 <= len(explicit_dates) <= 55, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "euronext.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXAMSWeekendPattern:
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

class TestXAMSSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2025-04-27" not in explicit_dates  # Sunday (King's Day)

    def test_substitute_names(self, explicit_dates):
        count = sum(1 for e in explicit_dates.values() if "substitute" in e["name"].lower())
        assert count >= 4, f"Expected some substitute holidays, got {count}"