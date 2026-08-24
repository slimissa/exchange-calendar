#!/usr/bin/env python3
"""
test_oslo_holidays.py — Ground truth tests for XOSL (Oslo Børs).

Key facts verified:
    - Maundy Thursday (Easter - 3) is a Norwegian market closure
    - Constitution Day (May 17) is Norwegian National Day
    - 2027: Constitution Day and Whit Monday both fall on May 17 (merged)
    - Christmas Eve, Christmas Day, Boxing Day, New Year's Eve are closures
    - Norway does NOT shift holidays from weekends
    - No lunch break (continuous trading)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XOSL.json)
    2. Norwegian holiday announcements changed (verify against euronext.com)

Run:
    python3 -m pytest tests/test_oslo_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xosl():
    """Load XOSL.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XOSL.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xosl):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xosl["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXOSLProperties:
    def test_code(self, xosl):
        assert xosl["code"] == "XOSL"

    def test_mic(self, xosl):
        assert xosl["mic"] == "XOSL"

    def test_name(self, xosl):
        assert xosl["name"] == "Oslo Børs"

    def test_timezone(self, xosl):
        assert xosl["timezone"] == "Europe/Oslo"

    def test_regular_hours(self, xosl):
        assert xosl["regular_hours"]["open"] == "09:00"
        assert xosl["regular_hours"]["close"] == "16:30"

    def test_no_lunch_break(self, xosl):
        lunch = [s for s in xosl.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xosl):
        assert xosl["extended_hours"]["pre_market"]["open"] == "08:15"
        assert xosl["extended_hours"]["after_hours"]["close"] == "16:45"


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXOSLFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_constitution_day_2025(self, explicit_dates):
        """May 17, 2025 is Saturday — no explicit entry."""
        assert "2025-05-17" not in explicit_dates

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        assert "2025-12-26" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates

    def test_constitution_day_2026(self, explicit_dates):
        """May 17, 2026 is Sunday — no explicit entry."""
        assert "2026-05-17" not in explicit_dates

    def test_constitution_day_2028(self, explicit_dates):
        """May 17, 2028 is Wednesday — explicit."""
        assert "2028-05-17" in explicit_dates

    def test_constitution_day_2029(self, explicit_dates):
        """May 17, 2029 is Thursday — explicit."""
        assert "2029-05-17" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2027 merged Constitution Day / Whit Monday
# ──────────────────────────────────────────────────────────────

class TestXOSL2027Merged:
    def test_merged_date(self, explicit_dates):
        """May 17, 2027 — both Constitution Day and Whit Monday."""
        assert "2027-05-17" in explicit_dates
        name = explicit_dates["2027-05-17"]["name"]
        assert "Constitution" in name
        assert "Whit Monday" in name

    def test_no_duplicate(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert dates.count("2027-05-17") == 1


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXOSLEaster:
    def test_maundy_thursday_2025(self, explicit_dates):
        assert "2025-04-17" in explicit_dates
        assert "Maundy" in explicit_dates["2025-04-17"]["name"]

    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        assert "2025-04-21" in explicit_dates

    def test_ascension_2025(self, explicit_dates):
        assert "2025-05-29" in explicit_dates

    def test_whit_monday_2025(self, explicit_dates):
        assert "2025-06-09" in explicit_dates

    def test_maundy_thursday_2026(self, explicit_dates):
        assert "2026-04-02" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXOSLRecurrence:
    def test_fixed_rules_exist(self, xosl):
        rules = xosl["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Labour Day" in names
        assert "Constitution Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names
        assert "New Year's Eve" in names

    def test_easter_rules(self, xosl):
        rules = xosl["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}
        assert rule_by_name["Maundy Thursday"]["rule"] == "easter_offset"
        assert rule_by_name["Maundy Thursday"]["offset_days"] == -3
        assert rule_by_name["Good Friday"]["offset_days"] == -2
        assert rule_by_name["Easter Monday"]["offset_days"] == 1
        assert rule_by_name["Ascension Day"]["offset_days"] == 39
        assert rule_by_name["Whit Monday"]["offset_days"] == 50


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXOSLStructure:
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
        """Oslo Børs has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~49 entries: 12 holidays × 5 years, minus weekend overlaps."""
        assert 40 <= len(explicit_dates) <= 60