#!/usr/bin/env python3
"""
test_mexico_holidays.py — Ground truth tests for XMEX (Mexican Stock Exchange).

Key facts verified:
    - Mexico observes holidays on Monday (Ley Federal del Trabajo):
      Constitution Day (1st Monday Feb), Benito Juárez (3rd Monday Mar),
      Revolution Day (3rd Monday Nov)
    - Holy Thursday (Easter - 3 days) is a market closure
    - Day of the Virgin of Guadalupe (Dec 12) is a BMV closure
    - Independence Day (Sep 16) is a fixed-date closure
    - No lunch break (continuous trading)
    - Pre-market: 07:30-08:30, Post-market: 15:00-15:30

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XMEX.json)
    2. Mexican holiday announcements changed (verify against bmv.com.mx)

Run:
    python3 -m pytest tests/test_mexico_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xmex():
    """Load XMEX.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XMEX.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xmex):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xmex["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXMEXProperties:
    def test_code(self, xmex):
        assert xmex["code"] == "XMEX"

    def test_mic(self, xmex):
        assert xmex["mic"] == "XMEX"

    def test_name(self, xmex):
        assert xmex["name"] == "Mexican Stock Exchange"

    def test_timezone(self, xmex):
        assert xmex["timezone"] == "America/Mexico_City"

    def test_regular_hours(self, xmex):
        assert xmex["regular_hours"]["open"] == "08:30"
        assert xmex["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xmex):
        lunch = [s for s in xmex.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xmex):
        assert xmex["extended_hours"]["pre_market"]["open"] == "07:30"
        assert xmex["extended_hours"]["after_hours"]["close"] == "15:30"


# ──────────────────────────────────────────────────────────────
# 2025 holidays
# ──────────────────────────────────────────────────────────────

class TestXMEX2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_constitution_day_observed(self, explicit_dates):
        """First Monday February — Feb 3, 2025."""
        assert "2025-02-03" in explicit_dates
        assert "Constitution" in explicit_dates["2025-02-03"]["name"]

    def test_benito_juarez_observed(self, explicit_dates):
        """Third Monday March — Mar 17, 2025."""
        assert "2025-03-17" in explicit_dates
        assert "Juárez" in explicit_dates["2025-03-17"]["name"]

    def test_holy_thursday(self, explicit_dates):
        assert "2025-04-17" in explicit_dates
        assert "Holy" in explicit_dates["2025-04-17"]["name"]

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_independence_day(self, explicit_dates):
        assert "2025-09-16" in explicit_dates

    def test_revolution_day_observed(self, explicit_dates):
        """Third Monday November — Nov 17, 2025."""
        assert "2025-11-17" in explicit_dates
        assert "Revolution" in explicit_dates["2025-11-17"]["name"]

    def test_virgin_guadalupe(self, explicit_dates):
        assert "2025-12-12" in explicit_dates

    def test_christmas(self, explicit_dates):
        assert "2025-12-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2026 holidays
# ──────────────────────────────────────────────────────────────

class TestXMEX2026:
    def test_new_year(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_constitution_day(self, explicit_dates):
        assert "2026-02-02" in explicit_dates

    def test_benito_juarez(self, explicit_dates):
        assert "2026-03-16" in explicit_dates

    def test_holy_thursday(self, explicit_dates):
        assert "2026-04-02" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_revolution_day(self, explicit_dates):
        assert "2026-11-16" in explicit_dates

    def test_christmas(self, explicit_dates):
        assert "2026-12-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2027 holidays
# ──────────────────────────────────────────────────────────────

class TestXMEX2027:
    def test_constitution_day(self, explicit_dates):
        assert "2027-02-01" in explicit_dates

    def test_benito_juarez(self, explicit_dates):
        assert "2027-03-15" in explicit_dates

    def test_holy_thursday(self, explicit_dates):
        assert "2027-03-25" in explicit_dates

    def test_revolution_day(self, explicit_dates):
        assert "2027-11-15" in explicit_dates

    def test_no_virgin_guadalupe_sunday(self, explicit_dates):
        """Dec 12, 2027 is Sunday — no explicit entry."""
        assert "2027-12-12" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2028 holidays
# ──────────────────────────────────────────────────────────────

class TestXMEX2028:
    def test_constitution_day(self, explicit_dates):
        assert "2028-02-07" in explicit_dates

    def test_benito_juarez(self, explicit_dates):
        assert "2028-03-20" in explicit_dates

    def test_holy_thursday(self, explicit_dates):
        assert "2028-04-13" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2028-04-14" in explicit_dates

    def test_revolution_day(self, explicit_dates):
        assert "2028-11-20" in explicit_dates

    def test_christmas(self, explicit_dates):
        assert "2028-12-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2029 holidays
# ──────────────────────────────────────────────────────────────

class TestXMEX2029:
    def test_constitution_day(self, explicit_dates):
        assert "2029-02-05" in explicit_dates

    def test_benito_juarez(self, explicit_dates):
        assert "2029-03-19" in explicit_dates

    def test_holy_thursday(self, explicit_dates):
        assert "2029-03-29" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2029-03-30" in explicit_dates

    def test_revolution_day(self, explicit_dates):
        assert "2029-11-19" in explicit_dates

    def test_christmas(self, explicit_dates):
        assert "2029-12-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXMEXRecurrence:
    def test_monday_observed_rules(self, xmex):
        """Constitution, Juárez, Revolution use nth_weekday (Monday)."""
        rules = xmex["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}

        assert rule_by_name["Constitution Day"]["rule"] == "nth_weekday"
        assert rule_by_name["Constitution Day"]["weekday"] == "monday"
        assert rule_by_name["Constitution Day"]["n"] == 1

        assert rule_by_name["Benito Juárez Day"]["rule"] == "nth_weekday"
        assert rule_by_name["Benito Juárez Day"]["weekday"] == "monday"
        assert rule_by_name["Benito Juárez Day"]["n"] == 3

        assert rule_by_name["Revolution Day"]["rule"] == "nth_weekday"
        assert rule_by_name["Revolution Day"]["weekday"] == "monday"
        assert rule_by_name["Revolution Day"]["n"] == 3

    def test_holy_thursday_rule(self, xmex):
        rules = xmex["holidays"].get("recurrence_rules", [])
        holy_thursday = [r for r in rules if r["name"] == "Holy Thursday"]
        assert len(holy_thursday) == 1
        assert holy_thursday[0]["rule"] == "easter_offset"
        assert holy_thursday[0]["offset_days"] == -3

    def test_fixed_date_rules(self, xmex):
        rules = xmex["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}

        for name in ["New Year's Day", "Labour Day", "Independence Day",
                      "Day of the Virgin of Guadalupe", "Christmas Day"]:
            assert rule_by_name[name]["rule"] == "fixed_date", \
                f"{name} should use fixed_date"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXMEXStructure:
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
        """Mexico has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~48 entries: 10 holidays × 5 years, minus weekend overlaps."""
        assert 40 <= len(explicit_dates) <= 60