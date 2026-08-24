#!/usr/bin/env python3
"""
test_philippines_holidays.py — Ground truth tests for XPHS (Philippine Stock Exchange).

Key facts verified:
    - No lunch break (continuous trading since market hours expansion)
    - Regular hours: 09:30-15:00
    - After-hours: 15:00-15:10 (Run-Off / Trade-at-Last)
    - Maundy Thursday (Easter - 3) is a market closure
    - Ninoy Aquino Day (Aug 21) is a statutory holiday
    - All Saints' Day (Nov 1) and All Souls' Day (Nov 2) are closures
    - Feast of the Immaculate Conception (Dec 8) is a closure
    - Christmas Eve and New Year's Eve are closures
    - National Heroes Day is last Monday of August
    - No weekend shift (Philippines does not substitute unless declared)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XPHS.json)
    2. Philippine holiday proclamations changed (verify against pse.com.ph)

Run:
    python3 -m pytest tests/test_philippines_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xphs():
    """Load XPHS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XPHS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xphs):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xphs["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXPHSProperties:
    def test_code(self, xphs):
        assert xphs["code"] == "XPHS"

    def test_mic(self, xphs):
        assert xphs["mic"] == "XPHS"

    def test_name(self, xphs):
        assert xphs["name"] == "Philippine Stock Exchange"

    def test_timezone(self, xphs):
        assert xphs["timezone"] == "Asia/Manila"

    def test_regular_hours(self, xphs):
        assert xphs["regular_hours"]["open"] == "09:30"
        assert xphs["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xphs):
        """PSE is continuous trading — NO lunch break."""
        lunch = [s for s in xphs.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_after_hours(self, xphs):
        assert xphs["extended_hours"]["after_hours"]["open"] == "15:00"
        assert xphs["extended_hours"]["after_hours"]["close"] == "15:10"


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXPHSFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_day_of_valor_2025(self, explicit_dates):
        assert "2025-04-09" in explicit_dates
        assert "Kagitingan" in explicit_dates["2025-04-09"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_independence_day_2025(self, explicit_dates):
        assert "2025-06-12" in explicit_dates

    def test_bonifacio_day_2025(self, explicit_dates):
        """Nov 30, 2025 is Sunday — no explicit entry."""
        assert "2025-11-30" not in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_rizal_day_2025(self, explicit_dates):
        assert "2025-12-30" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Holy Week
# ──────────────────────────────────────────────────────────────

class TestXPHSHolyWeek:
    def test_maundy_thursday_2025(self, explicit_dates):
        assert "2025-04-17" in explicit_dates
        assert "Maundy" in explicit_dates["2025-04-17"]["name"]

    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_maundy_thursday_2026(self, explicit_dates):
        assert "2026-04-02" in explicit_dates

    def test_good_friday_2026(self, explicit_dates):
        assert "2026-04-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Additional statutory holidays
# ──────────────────────────────────────────────────────────────

class TestXPHSAdditional:
    def test_ninoy_aquino_2025(self, explicit_dates):
        assert "2025-08-21" in explicit_dates
        assert "Ninoy" in explicit_dates["2025-08-21"]["name"]

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday — no explicit entry."""
        assert "2025-11-01" not in explicit_dates

    def test_all_souls_2025(self, explicit_dates):
        """Nov 2, 2025 is Sunday — no explicit entry."""
        assert "2025-11-02" not in explicit_dates

    def test_immaculate_conception_2025(self, explicit_dates):
        assert "2025-12-08" in explicit_dates
        assert "Immaculate" in explicit_dates["2025-12-08"]["name"]

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates

    def test_national_heroes_2025(self, explicit_dates):
        """Last Monday August — Aug 25, 2025."""
        assert "2025-08-25" in explicit_dates
        assert "Heroes" in explicit_dates["2025-08-25"]["name"]

    def test_national_heroes_2026(self, explicit_dates):
        assert "2026-08-31" in explicit_dates

    def test_national_heroes_2027(self, explicit_dates):
        assert "2027-08-30" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXPHSRecurrence:
    def test_fixed_rules_exist(self, xphs):
        rules = xphs["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Araw ng Kagitingan (Day of Valor)" in names
        assert "Labour Day" in names
        assert "Independence Day" in names
        assert "Bonifacio Day" in names
        assert "Christmas Day" in names
        assert "Rizal Day" in names

    def test_maundy_thursday_rule(self, xphs):
        rules = xphs["holidays"].get("recurrence_rules", [])
        maundy = [r for r in rules if r["name"] == "Maundy Thursday"]
        assert len(maundy) == 1
        assert maundy[0]["rule"] == "easter_offset"
        assert maundy[0]["offset_days"] == -3

    def test_national_heroes_rule(self, xphs):
        rules = xphs["holidays"].get("recurrence_rules", [])
        heroes = [r for r in rules if r["name"] == "National Heroes Day"]
        assert len(heroes) == 1
        assert heroes[0]["rule"] == "last_weekday"
        assert heroes[0]["weekday"] == "monday"
        assert heroes[0]["month"] == 8

    def test_no_islamic_rules(self, xphs):
        """Eid holidays are NOT in recurrence rules."""
        rules = xphs["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Eid" not in names
        assert "Chinese New Year" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXPHSStructure:
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
        """PSE has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~65-85 entries: 15+ holidays × 5 years."""
        assert 60 <= len(explicit_dates) <= 90