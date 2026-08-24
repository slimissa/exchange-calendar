#!/usr/bin/env python3
"""
test_ghana_holidays.py — Ground truth tests for XGSE (Ghana Stock Exchange).

Key facts verified:
    - Regular hours: 10:00-15:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Constitution Day (Jan 7)
    - Independence Day (Mar 6)
    - Founders' Day (Aug 4)
    - Kwame Nkrumah Memorial Day (Sep 21)
    - Farmers' Day (first Friday in December)
    - Christmas Day and Boxing Day
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XGSE.json)
    2. Ghanaian holiday announcements changed (verify against gse.com.gh)

Run:
    python3 -m pytest tests/test_ghana_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xgse():
    """Load XGSE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XGSE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xgse):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xgse["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXGSEProperties:
    def test_code(self, xgse):
        assert xgse["code"] == "XGSE"

    def test_mic(self, xgse):
        assert xgse["mic"] == "XGSE"

    def test_name(self, xgse):
        assert xgse["name"] == "Ghana Stock Exchange"

    def test_timezone(self, xgse):
        assert xgse["timezone"] == "Africa/Accra"

    def test_regular_hours(self, xgse):
        assert xgse["regular_hours"]["open"] == "10:00"
        assert xgse["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xgse):
        lunch = [s for s in xgse.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xgse):
        assert "extended_hours" not in xgse or xgse.get("extended_hours") is None

    def test_generation_range(self, xgse):
        assert "generation_range" in xgse
        assert xgse["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xgse):
        assert xgse.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xgse):
        """Ghana uses explicit dates only."""
        rules = xgse["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (January-March)
# ──────────────────────────────────────────────────────────────

class TestXGSEFixedHolidaysJanMar:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_constitution_2025(self, explicit_dates):
        """Jan 7, 2025 is Tuesday."""
        assert "2025-01-07" in explicit_dates
        assert "Constitution" in explicit_dates["2025-01-07"]["name"]

    def test_constitution_2029_substitute(self, explicit_dates):
        """Jan 7, 2029 is Sunday — substitute to Monday Jan 8."""
        assert "2029-01-07" not in explicit_dates
        assert "2029-01-08" in explicit_dates

    def test_independence_2025(self, explicit_dates):
        """Mar 6, 2025 is Thursday."""
        assert "2025-03-06" in explicit_dates
        assert "Independence" in explicit_dates["2025-03-06"]["name"]


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (May-September)
# ──────────────────────────────────────────────────────────────

class TestXGSEFixedHolidaysMaySep:
    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_founders_2025(self, explicit_dates):
        """Aug 4, 2025 is Monday."""
        assert "2025-08-04" in explicit_dates
        assert "Founders" in explicit_dates["2025-08-04"]["name"]

    def test_founders_2029_substitute(self, explicit_dates):
        """Aug 4, 2029 is Saturday — substitute to Monday Aug 6."""
        assert "2029-08-04" not in explicit_dates
        assert "2029-08-06" in explicit_dates

    def test_kwame_nkrumah_2025(self, explicit_dates):
        """Sep 21, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-09-21" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Farmers' Day (first Friday in December)
# ──────────────────────────────────────────────────────────────

class TestXGSEFarmersDay:
    def test_farmers_day_2025(self, explicit_dates):
        """First Friday in December — Dec 5, 2025."""
        assert "2025-12-05" in explicit_dates
        assert "Farmers" in explicit_dates["2025-12-05"]["name"]

    def test_farmers_day_2026(self, explicit_dates):
        """First Friday in December — Dec 4, 2026."""
        assert "2026-12-04" in explicit_dates

    def test_farmers_day_2027(self, explicit_dates):
        """First Friday in December — Dec 3, 2027."""
        assert "2027-12-03" in explicit_dates

    def test_farmers_day_2028(self, explicit_dates):
        """First Friday in December — Dec 1, 2028."""
        assert "2028-12-01" in explicit_dates

    def test_farmers_day_2029(self, explicit_dates):
        """First Friday in December — Dec 7, 2029."""
        assert "2029-12-07" in explicit_dates

    def test_farmers_day_always_friday(self, explicit_dates):
        for entry in explicit_dates.values():
            if "Farmers" in entry["name"]:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 4, f"Farmers' Day should be Friday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXGSEChristmas:
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


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXGSEEaster:
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


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXGSEStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Ghana weekend is Saturday-Sunday."""
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
        """Ghana has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xgse, explicit_dates):
        start = date.fromisoformat(xgse["generation_range"][0])
        end = date.fromisoformat(xgse["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries."""
        assert 50 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "gse.com.gh" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXGSEWeekendPattern:
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

class TestXGSESubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2025-09-21" not in explicit_dates  # Sunday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 4, f"Expected some observed holidays, got {observed_count}"