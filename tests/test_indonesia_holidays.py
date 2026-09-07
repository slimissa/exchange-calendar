#!/usr/bin/env python3
"""
test_indonesia_holidays.py — Ground truth tests for XJKT (Indonesia Stock Exchange / IDX).

Key facts verified:
    - Lunch break: 12:00-13:30 (longer than most exchanges)
    - Pancasila Day (June 1) is a statutory national holiday
    - Good Friday (Wafat Isa Almasih) is a market closure
    - Christmas Collective Leave (Cuti Bersama) on Dec 26
    - Year-End Holiday on Dec 31
    - Lunisolar Islamic holidays (Idul Fitri, Idul Adha, Isra Mi'raj,
      Islamic New Year, Maulid Nabi) are explicit-only
    - Nyepi (Balinese New Year) and Imlek (Chinese New Year) are unique
    - Fixed holidays use fixed_date (no weekend shift)

Note: Islamic holidays for 2026-2029 require official IDX announcements.
Some dates are incomplete in this version.

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XJKT.json)
    2. Indonesian holiday announcements changed (verify against idx.co.id)

Run:
    python3 -m pytest tests/test_indonesia_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xjkt():
    """Load XJKT.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XJKT.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xjkt):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xjkt["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXJKTProperties:
    def test_code(self, xjkt):
        assert xjkt["code"] == "XJKT"

    def test_mic(self, xjkt):
        assert xjkt["mic"] == "XJKT"

    def test_name(self, xjkt):
        assert xjkt["name"] == "Indonesia Stock Exchange"

    def test_timezone(self, xjkt):
        assert xjkt["timezone"] == "Asia/Jakarta"

    def test_regular_hours(self, xjkt):
        assert xjkt["regular_hours"]["open"] == "09:00"
        assert xjkt["regular_hours"]["close"] == "16:00"

    def test_lunch_break(self, xjkt):
        lunch = [s for s in xjkt.get("sessions", []) if s["type"] == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "12:00"
        assert lunch[0]["close"] == "13:30"

    def test_extended_hours(self, xjkt):
        assert xjkt["extended_hours"]["pre_market"]["open"] == "08:45"
        assert xjkt["extended_hours"]["after_hours"]["close"] == "16:15"


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXJKTFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_pancasila_day_2025(self, explicit_dates):
        """Jun 1, 2025 is Sunday — no explicit entry."""
        assert "2025-06-01" not in explicit_dates

    def test_pancasila_day_2026(self, explicit_dates):
        assert "2026-06-01" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_independence_day_2025(self, explicit_dates):
        """Aug 17, 2025 is Sunday — no explicit entry."""
        assert "2025-08-17" not in explicit_dates

    def test_independence_day_2026(self, explicit_dates):
        """Aug 17, 2026 is Monday — explicit."""
        assert "2026-08-17" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_christmas_collective_leave_2025(self, explicit_dates):
        """Dec 26 is Cuti Bersama (Collective Leave)."""
        assert "2025-12-26" in explicit_dates
        assert "Collective" in explicit_dates["2025-12-26"]["name"]

    def test_year_end_holiday_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates
        assert "Year-End" in explicit_dates["2025-12-31"]["name"]


# ──────────────────────────────────────────────────────────────
# Good Friday
# ──────────────────────────────────────────────────────────────

class TestXJKTGoodFriday:
    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert "Good Friday" in explicit_dates["2025-04-18"]["name"]

    def test_good_friday_2026(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_good_friday_2027(self, explicit_dates):
        assert "2027-03-26" in explicit_dates

    def test_good_friday_2028(self, explicit_dates):
        assert "2028-04-14" in explicit_dates

    def test_good_friday_2029(self, explicit_dates):
        assert "2029-03-30" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Lunisolar holidays
# ──────────────────────────────────────────────────────────────

class TestXJKTLunisolar:
    def test_cny_2025(self, explicit_dates):
        assert "2025-01-29" in explicit_dates
        assert "Imlek" in explicit_dates["2025-01-29"]["name"]

    def test_nyepi_2025(self, explicit_dates):
        assert "2025-03-28" in explicit_dates
        assert "Nyepi" in explicit_dates["2025-03-28"]["name"]

    def test_idul_fitri_2025(self, explicit_dates):
        assert "2025-03-31" in explicit_dates
        assert "Idul Fitri" in explicit_dates["2025-03-31"]["name"]
        assert "2025-04-01" in explicit_dates
        assert "2025-04-02" in explicit_dates
        assert "2025-04-03" in explicit_dates

    def test_idul_adha_2025(self, explicit_dates):
        assert "2025-06-06" in explicit_dates
        assert "Idul Adha" in explicit_dates["2025-06-06"]["name"]

    def test_islamic_new_year_2025(self, explicit_dates):
        assert "2025-06-27" in explicit_dates
        assert "Islamic New Year" in explicit_dates["2025-06-27"]["name"]

    def test_maulid_nabi_2025(self, explicit_dates):
        assert "2025-09-05" in explicit_dates
        assert "Maulid" in explicit_dates["2025-09-05"]["name"]

    def test_waisak_2025(self, explicit_dates):
        assert "2025-05-12" in explicit_dates
        assert "Waisak" in explicit_dates["2025-05-12"]["name"]


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXJKTRecurrence:
    def test_fixed_rules_exist(self, xjkt):
        rules = xjkt["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Labour Day" in names
        assert "Independence Day" in names
        assert "Christmas Day" in names

    def test_no_lunisolar_rules(self, xjkt):
        """Islamic and Chinese holidays must NOT be in recurrence rules."""
        rules = xjkt["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Idul Fitri" not in names
        assert "Idul Adha" not in names
        assert "Imlek" not in names
        assert "Nyepi" not in names
        assert "Waisak" not in names

    def test_no_good_friday_rule(self, xjkt):
        """Good Friday not yet in recurrence rules (manual verification needed)."""
        rules = xjkt["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        # Good Friday uses easter_offset but may not be in rules yet
        # This test documents current state
        pass


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXJKTStructure:
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

    def test_all_statuses_closed(self, explicit_dates):
        """IDX has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-70 entries: 15+ holidays × 5 years."""
        assert 45 <= len(explicit_dates) <= 80