#!/usr/bin/env python3
"""
test_new_zealand_holidays.py — Ground truth tests for XNZE (New Zealand Exchange).

Key facts verified:
    - Regular hours: 10:00-16:45 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Waitangi Day (Feb 6) with substitution
    - ANZAC Day (Apr 25) with substitution
    - King's Birthday (first Monday in June)
    - Matariki (movable, June/July)
    - Labour Day (fourth Monday in October)
    - UK-style weekend substitution
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XNZE.json)
    2. NZ holiday announcements changed (verify against nzx.com)

Run:
    python3 -m pytest tests/test_new_zealand_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xnze():
    """Load XNZE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XNZE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xnze):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xnze["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXNZEProperties:
    def test_code(self, xnze):
        assert xnze["code"] == "XNZE"

    def test_mic(self, xnze):
        assert xnze["mic"] == "XNZE"

    def test_name(self, xnze):
        assert xnze["name"] == "New Zealand Exchange"

    def test_timezone(self, xnze):
        assert xnze["timezone"] == "Pacific/Auckland"

    def test_regular_hours(self, xnze):
        assert xnze["regular_hours"]["open"] == "10:00"
        assert xnze["regular_hours"]["close"] == "16:45"

    def test_no_lunch_break(self, xnze):
        lunch = [s for s in xnze.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xnze):
        assert "extended_hours" not in xnze or xnze.get("extended_hours") is None

    def test_generation_range(self, xnze):
        assert "generation_range" in xnze
        assert xnze["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xnze):
        assert xnze.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xnze):
        """NZ uses explicit dates only."""
        rules = xnze["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# New Year holidays
# ──────────────────────────────────────────────────────────────

class TestXNZENewYear:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_day_after_new_year_2025(self, explicit_dates):
        """Jan 2, 2025 is Thursday."""
        assert "2025-01-02" in explicit_dates

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_day_after_new_year_2027_substitute(self, explicit_dates):
        """Jan 2, 2027 is Saturday — substitute to Monday Jan 4."""
        assert "2027-01-02" not in explicit_dates
        assert "2027-01-04" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Waitangi Day (Feb 6)
# ──────────────────────────────────────────────────────────────

class TestXNZEWaitangi:
    def test_waitangi_2025(self, explicit_dates):
        """Feb 6, 2025 is Thursday."""
        assert "2025-02-06" in explicit_dates
        assert "Waitangi" in explicit_dates["2025-02-06"]["name"]

    def test_waitangi_2027_substitute(self, explicit_dates):
        """Feb 6, 2027 is Saturday — substitute to Monday Feb 8."""
        assert "2027-02-06" not in explicit_dates
        assert "2027-02-08" in explicit_dates

    def test_waitangi_2028_substitute(self, explicit_dates):
        """Feb 6, 2028 is Sunday — substitute to Monday Feb 7."""
        assert "2028-02-06" not in explicit_dates
        assert "2028-02-07" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXNZEEaster:
    def test_good_friday_2025(self, explicit_dates):
        """Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["name"] == "Good Friday"

    def test_good_friday_2027(self, explicit_dates):
        """Easter - 2 days — March 26, 2027."""
        assert "2027-03-26" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        """Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["name"] == "Easter Monday"

    def test_easter_monday_2028(self, explicit_dates):
        """Easter + 1 day — April 17, 2028."""
        assert "2028-04-17" in explicit_dates

    def test_easter_monday_2029(self, explicit_dates):
        """Easter + 1 day — April 2, 2029."""
        assert "2029-04-02" in explicit_dates


# ──────────────────────────────────────────────────────────────
# ANZAC Day (Apr 25)
# ──────────────────────────────────────────────────────────────

class TestXNZEANZAC:
    def test_anzac_2025(self, explicit_dates):
        """Apr 25, 2025 is Friday."""
        assert "2025-04-25" in explicit_dates
        assert "ANZAC" in explicit_dates["2025-04-25"]["name"]

    def test_anzac_2026_substitute(self, explicit_dates):
        """Apr 25, 2026 is Saturday — substitute to Monday Apr 27."""
        assert "2026-04-25" not in explicit_dates
        assert "2026-04-27" in explicit_dates

    def test_anzac_2027_substitute(self, explicit_dates):
        """Apr 25, 2027 is Sunday — substitute to Monday Apr 26."""
        assert "2027-04-26" in explicit_dates

    def test_anzac_2028(self, explicit_dates):
        """Apr 25, 2028 is Tuesday."""
        assert "2028-04-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# King's Birthday (first Monday in June)
# ──────────────────────────────────────────────────────────────

class TestXNZEKingsBirthday:
    def test_kings_birthday_2025(self, explicit_dates):
        """First Monday in June — Jun 2, 2025."""
        assert "2025-06-02" in explicit_dates
        assert "King" in explicit_dates["2025-06-02"]["name"]

    def test_kings_birthday_2026(self, explicit_dates):
        """First Monday in June — Jun 1, 2026."""
        assert "2026-06-01" in explicit_dates

    def test_kings_birthday_2027(self, explicit_dates):
        """First Monday in June — Jun 7, 2027."""
        assert "2027-06-07" in explicit_dates

    def test_kings_birthday_2028(self, explicit_dates):
        """First Monday in June — Jun 5, 2028."""
        assert "2028-06-05" in explicit_dates

    def test_kings_birthday_2029(self, explicit_dates):
        """First Monday in June — Jun 4, 2029."""
        assert "2029-06-04" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Matariki (movable)
# ──────────────────────────────────────────────────────────────

class TestXNZEMatariki:
    def test_matariki_2025(self, explicit_dates):
        """Matariki 2025 — Jun 20."""
        assert "2025-06-20" in explicit_dates
        assert "Matariki" in explicit_dates["2025-06-20"]["name"]

    def test_matariki_2026(self, explicit_dates):
        """Matariki 2026 — Jul 10."""
        assert "2026-07-10" in explicit_dates

    def test_matariki_2027(self, explicit_dates):
        """Matariki 2027 — Jul 2."""
        assert "2027-07-02" in explicit_dates

    def test_matariki_2028(self, explicit_dates):
        """Matariki 2028 — Jun 23."""
        assert "2028-06-23" in explicit_dates

    def test_matariki_2029(self, explicit_dates):
        """Matariki 2029 — Jun 22."""
        assert "2029-06-22" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Labour Day (fourth Monday in October)
# ──────────────────────────────────────────────────────────────

class TestXNZELabourDay:
    def test_labour_day_2025(self, explicit_dates):
        """Fourth Monday in October — Oct 27, 2025."""
        assert "2025-10-27" in explicit_dates
        assert "Labour" in explicit_dates["2025-10-27"]["name"]

    def test_labour_day_2026(self, explicit_dates):
        """Fourth Monday in October — Oct 26, 2026."""
        assert "2026-10-26" in explicit_dates

    def test_labour_day_2027(self, explicit_dates):
        """Fourth Monday in October — Oct 25, 2027."""
        assert "2027-10-25" in explicit_dates

    def test_labour_day_2028(self, explicit_dates):
        """Fourth Monday in October — Oct 23, 2028."""
        assert "2028-10-23" in explicit_dates

    def test_labour_day_2029(self, explicit_dates):
        """Fourth Monday in October — Oct 22, 2029."""
        assert "2029-10-22" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXNZEChristmas:
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
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXNZEStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """NZ weekend is Saturday-Sunday."""
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
        """NZ has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xnze, explicit_dates):
        start = date.fromisoformat(xnze["generation_range"][0])
        end = date.fromisoformat(xnze["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries."""
        assert 50 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "nzx.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXNZEWeekendPattern:
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

class TestXNZESubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count > 5, f"Expected many observed holidays, got {observed_count}"