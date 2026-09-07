#!/usr/bin/env python3
"""
test_asx_holidays.py — Ground truth tests for XASX (Australian Securities Exchange).

Key facts verified:
    - ASX is OPEN on NSW Bank Holiday (first Monday of August)
    - ANZAC Day on Saturday does NOT shift to Monday
    - ANZAC Day on Sunday IS observed Monday (NSW rule)
    - Christmas Eve and New Year's Eve are half-days (early close 14:10 AEDT/AEST)
    - Australia observes holidays on Monday when they fall on Sunday
    - No lunch break (continuous trading)
    - Timezone: Australia/Sydney
    - Regular hours: 10:00-16:00

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XASX.json)
    2. Australian holiday law changed (verify against asx.com.au)

Run:
    python3 -m pytest tests/test_asx_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xasx():
    """Load XASX.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XASX.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xasx):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xasx["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXASXProperties:
    def test_code(self, xasx):
        assert xasx["code"] == "XASX"

    def test_mic(self, xasx):
        assert xasx["mic"] == "XASX"

    def test_name(self, xasx):
        assert xasx["name"] == "Australian Securities Exchange"

    def test_timezone(self, xasx):
        assert xasx["timezone"] == "Australia/Sydney"

    def test_regular_hours(self, xasx):
        assert xasx["regular_hours"]["open"] == "10:00"
        assert xasx["regular_hours"]["close"] == "16:00"

    def test_no_lunch_break(self, xasx):
        lunch = [s for s in xasx.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_auction_sessions(self, xasx):
        auctions = [s for s in xasx.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 2
        times = [a["at"] for a in auctions]
        assert "10:00" in times
        assert "16:00" in times

    def test_has_extended_hours(self, xasx):
        assert "extended_hours" in xasx


# ──────────────────────────────────────────────────────────────
# ASX is OPEN on NSW Bank Holiday
# ──────────────────────────────────────────────────────────────

class TestXASXOpenOnBankHoliday:
    def test_no_bank_holiday_2025(self, explicit_dates):
        """First Monday of August 2025 — ASX OPEN."""
        assert "2025-08-04" not in explicit_dates

    def test_no_bank_holiday_2026(self, explicit_dates):
        """First Monday of August 2026 — ASX OPEN."""
        assert "2026-08-03" not in explicit_dates

    def test_no_bank_holiday_2027(self, explicit_dates):
        """First Monday of August 2027 — ASX OPEN."""
        assert "2027-08-02" not in explicit_dates

    def test_no_bank_holiday_2028(self, explicit_dates):
        """First Monday of August 2028 — ASX OPEN."""
        assert "2028-08-07" not in explicit_dates

    def test_no_bank_holiday_2029(self, explicit_dates):
        """First Monday of August 2029 — ASX OPEN."""
        assert "2029-08-06" not in explicit_dates

    def test_no_bank_holiday_in_recurrence(self, xasx):
        rules = xasx["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Bank Holiday (NSW)" not in names


# ──────────────────────────────────────────────────────────────
# ANZAC Day rules
# ──────────────────────────────────────────────────────────────

class TestXASXANZAC:
    def test_anzac_2025_weekday(self, explicit_dates):
        """April 25, 2025 is Friday — closed."""
        assert "2025-04-25" in explicit_dates
        assert explicit_dates["2025-04-25"]["status"] == "closed"

    def test_no_anzac_observed_2026_saturday(self, explicit_dates):
        """
        April 25, 2026 is Saturday.
        Under ASX rules, NO Monday observation for Saturday ANZAC.
        """
        assert "2026-04-25" not in explicit_dates  # Saturday, no explicit
        assert "2026-04-27" not in explicit_dates  # No Monday shift

    def test_anzac_observed_2027_sunday(self, explicit_dates):
        """
        April 25, 2027 is Sunday.
        NSW law observes Monday April 26.
        """
        assert "2027-04-25" not in explicit_dates  # Sunday, no explicit
        assert "2027-04-26" in explicit_dates
        assert "ANZAC" in explicit_dates["2027-04-26"]["name"]

    def test_anzac_2028_weekday(self, explicit_dates):
        """April 25, 2028 is Tuesday — closed."""
        assert "2028-04-25" in explicit_dates

    def test_anzac_2029_weekday(self, explicit_dates):
        """April 25, 2029 is Wednesday — closed."""
        assert "2029-04-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Half-days (early close 14:10)
# ──────────────────────────────────────────────────────────────

class TestXASXHalfDays:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — half-day."""
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "early_close"
        assert explicit_dates["2025-12-24"]["early_close_time"] == "14:10"

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — half-day."""
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "early_close"
        assert explicit_dates["2025-12-31"]["early_close_time"] == "14:10"

    def test_christmas_eve_2026(self, explicit_dates):
        """Dec 24, 2026 is Thursday — half-day."""
        assert "2026-12-24" in explicit_dates
        assert explicit_dates["2026-12-24"]["status"] == "early_close"

    def test_new_years_eve_2026(self, explicit_dates):
        """Dec 31, 2026 is Thursday — half-day."""
        assert "2026-12-31" in explicit_dates
        assert explicit_dates["2026-12-31"]["status"] == "early_close"

    def test_christmas_eve_2027(self, explicit_dates):
        """Dec 24, 2027 is Friday — half-day."""
        assert "2027-12-24" in explicit_dates
        assert explicit_dates["2027-12-24"]["status"] == "early_close"

    def test_new_years_eve_2027(self, explicit_dates):
        """Dec 31, 2027 is Friday — half-day."""
        assert "2027-12-31" in explicit_dates
        assert explicit_dates["2027-12-31"]["status"] == "early_close"

    def test_no_christmas_eve_2028_sunday(self, explicit_dates):
        """Dec 24, 2028 is Sunday — no half-day."""
        assert "2028-12-24" not in explicit_dates

    def test_no_new_years_eve_2028_sunday(self, explicit_dates):
        """Dec 31, 2028 is Sunday — no half-day."""
        assert "2028-12-31" not in explicit_dates

    def test_christmas_eve_2029(self, explicit_dates):
        """Dec 24, 2029 is Monday — half-day."""
        assert "2029-12-24" in explicit_dates
        assert explicit_dates["2029-12-24"]["status"] == "early_close"

    def test_new_years_eve_2029(self, explicit_dates):
        """Dec 31, 2029 is Monday — half-day."""
        assert "2029-12-31" in explicit_dates
        assert explicit_dates["2029-12-31"]["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# Main closures
# ──────────────────────────────────────────────────────────────

class TestXASXClosures2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates

    def test_australia_day_observed(self, explicit_dates):
        """Jan 26, 2025 is Sunday — observed Monday Jan 27."""
        assert "2025-01-26" not in explicit_dates
        assert "2025-01-27" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_easter_monday(self, explicit_dates):
        assert "2025-04-21" in explicit_dates

    def test_kings_birthday(self, explicit_dates):
        assert "2025-06-09" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2025-10-06" in explicit_dates

    def test_christmas_day(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day(self, explicit_dates):
        assert "2025-12-26" in explicit_dates


class TestXASXClosures2026:
    def test_new_year(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_australia_day(self, explicit_dates):
        assert "2026-01-26" in explicit_dates

    def test_boxing_day_observed(self, explicit_dates):
        """Dec 26, 2026 is Saturday — observed Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXASXStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source: {date_str}"

    def test_early_close_time_1410(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry["status"] == "early_close":
                assert entry["early_close_time"] == "14:10"

    def test_recurrence_rules_exist(self, xasx):
        rules = xasx["holidays"].get("recurrence_rules", [])
        assert len(rules) > 0

    def test_recurrence_rules_no_bank_holiday(self, xasx):
        rules = xasx["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Bank Holiday (NSW)" not in names

    def test_recurrence_rules_have_main_holidays(self, xasx):
        rules = xasx["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Australia Day" in names
        assert "Good Friday" in names
        assert "Easter Monday" in names
        assert "ANZAC Day" in names
        assert "King's Birthday" in names
        assert "Labour Day" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names

    def test_holiday_count_reasonable(self, explicit_dates):
        """~51 entries: 9 main closures × 5 years + 8 half-days."""
        assert 45 <= len(explicit_dates) <= 60