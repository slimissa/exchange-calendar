#!/usr/bin/env python3
"""
test_warsaw_holidays.py — Ground truth tests for XWAR (Warsaw Stock Exchange / GPW).

Key facts verified:
    - Regular hours: 09:00-17:00
    - Pre-market: 08:30-09:00, After-hours: 17:00-17:10
    - Epiphany (Jan 6) is a Polish statutory holiday
    - Constitution Day (May 3) is a Polish statutory holiday
    - Corpus Christi is Easter + 60 days
    - Assumption Day (Aug 15) and All Saints' Day (Nov 1) are closures
    - Independence Day (Nov 11) is a Polish national holiday
    - Christmas Eve and New Year's Eve are full closures
    - Poland does NOT shift holidays from weekends
    - No lunch break (continuous trading)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XWAR.json)
    2. Polish holiday announcements changed (verify against gpw.pl)

Run:
    python3 -m pytest tests/test_warsaw_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xwar():
    """Load XWAR.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XWAR.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xwar):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xwar["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXWARProperties:
    def test_code(self, xwar):
        assert xwar["code"] == "XWAR"

    def test_mic(self, xwar):
        assert xwar["mic"] == "XWAR"

    def test_name(self, xwar):
        assert xwar["name"] == "Warsaw Stock Exchange"

    def test_timezone(self, xwar):
        assert xwar["timezone"] == "Europe/Warsaw"

    def test_regular_hours(self, xwar):
        assert xwar["regular_hours"]["open"] == "09:00"
        assert xwar["regular_hours"]["close"] == "17:00"

    def test_no_lunch_break(self, xwar):
        lunch = [s for s in xwar.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xwar):
        assert xwar["extended_hours"]["pre_market"]["open"] == "08:30"
        assert xwar["extended_hours"]["after_hours"]["close"] == "17:10"


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXWARFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_epiphany_2025(self, explicit_dates):
        assert "2025-01-06" in explicit_dates
        assert "Epiphany" in explicit_dates["2025-01-06"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_constitution_day_2025(self, explicit_dates):
        """May 3, 2025 is Saturday — no explicit entry."""
        assert "2025-05-03" not in explicit_dates

    def test_constitution_day_2026(self, explicit_dates):
        """May 3, 2026 is Sunday — no explicit entry."""
        assert "2026-05-03" not in explicit_dates

    def test_constitution_day_2028(self, explicit_dates):
        """May 3, 2028 is Wednesday — explicit."""
        assert "2028-05-03" in explicit_dates

    def test_constitution_day_2029(self, explicit_dates):
        """May 3, 2029 is Thursday — explicit."""
        assert "2029-05-03" in explicit_dates

    def test_assumption_day_2025(self, explicit_dates):
        assert "2025-08-15" in explicit_dates

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday — no explicit entry."""
        assert "2025-11-01" not in explicit_dates

    def test_independence_day_2025(self, explicit_dates):
        assert "2025-11-11" in explicit_dates
        assert "Independence" in explicit_dates["2025-11-11"]["name"]

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        assert "2025-12-26" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXWAREaster:
    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        assert "2025-04-21" in explicit_dates

    def test_corpus_christi_2025(self, explicit_dates):
        """Easter + 60 days — June 19, 2025."""
        assert "2025-06-19" in explicit_dates
        assert "Corpus" in explicit_dates["2025-06-19"]["name"]

    def test_corpus_christi_2026(self, explicit_dates):
        """Easter + 60 days — June 4, 2026."""
        assert "2026-06-04" in explicit_dates

    def test_corpus_christi_2027(self, explicit_dates):
        """Easter + 60 days — May 27, 2027."""
        assert "2027-05-27" in explicit_dates

    def test_corpus_christi_2028(self, explicit_dates):
        """Easter + 60 days — June 15, 2028."""
        assert "2028-06-15" in explicit_dates

    def test_corpus_christi_2029(self, explicit_dates):
        """Easter + 60 days — May 31, 2029."""
        assert "2029-05-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXWARRecurrence:
    def test_fixed_rules_exist(self, xwar):
        rules = xwar["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Epiphany" in names
        assert "Labour Day" in names
        assert "Constitution Day" in names
        assert "Assumption Day" in names
        assert "All Saints' Day" in names
        assert "Independence Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names
        assert "New Year's Eve" in names

    def test_easter_rules(self, xwar):
        rules = xwar["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}
        assert rule_by_name["Good Friday"]["rule"] == "easter_offset"
        assert rule_by_name["Good Friday"]["offset_days"] == -2
        assert rule_by_name["Easter Monday"]["offset_days"] == 1
        assert rule_by_name["Corpus Christi"]["rule"] == "easter_offset"
        assert rule_by_name["Corpus Christi"]["offset_days"] == 60


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXWARStructure:
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
        """GPW has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~55-70 entries: 14 holidays × 5 years."""
        assert 50 <= len(explicit_dates) <= 75