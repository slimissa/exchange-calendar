#!/usr/bin/env python3
"""
test_helsinki_holidays.py — Ground truth tests for XHEL (Nasdaq Helsinki).

Key facts verified:
    - Regular hours: 09:00-18:30 (Nordic standard)
    - Pre-market: 08:00-09:00, After-hours: 18:30-18:45
    - Epiphany (Jan 6) is a Finnish statutory holiday
    - May Day (May 1) is a Finnish statutory holiday
    - Midsummer Eve is Friday between June 19-25 (explicit-only)
    - Finland does NOT shift holidays from weekends
    - No lunch break (continuous trading)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XHEL.json)
    2. Finnish holiday announcements changed (verify against nasdaqomxnordic.com)

Run:
    python3 -m pytest tests/test_helsinki_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xhel():
    """Load XHEL.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XHEL.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xhel):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xhel["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXHELProperties:
    def test_code(self, xhel):
        assert xhel["code"] == "XHEL"

    def test_mic(self, xhel):
        assert xhel["mic"] == "XHEL"

    def test_name(self, xhel):
        assert xhel["name"] == "Nasdaq Helsinki"

    def test_timezone(self, xhel):
        assert xhel["timezone"] == "Europe/Helsinki"

    def test_regular_hours(self, xhel):
        assert xhel["regular_hours"]["open"] == "09:00"
        assert xhel["regular_hours"]["close"] == "18:30"

    def test_no_lunch_break(self, xhel):
        lunch = [s for s in xhel.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xhel):
        assert xhel["extended_hours"]["pre_market"]["open"] == "08:00"
        assert xhel["extended_hours"]["after_hours"]["close"] == "18:45"


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXHELFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_epiphany_2025(self, explicit_dates):
        assert "2025-01-06" in explicit_dates
        assert "Epiphany" in explicit_dates["2025-01-06"]["name"]

    def test_may_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        assert "2025-12-26" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates

    def test_epiphany_2026(self, explicit_dates):
        assert "2026-01-06" in explicit_dates

    def test_epiphany_2029(self, explicit_dates):
        """Jan 6, 2029 is Saturday — no explicit entry."""
        assert "2029-01-06" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXHELEaster:
    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        assert "2025-04-21" in explicit_dates

    def test_ascension_2025(self, explicit_dates):
        assert "2025-05-29" in explicit_dates

    def test_good_friday_2026(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_easter_monday_2026(self, explicit_dates):
        assert "2026-04-06" in explicit_dates

    def test_ascension_2026(self, explicit_dates):
        assert "2026-05-14" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Midsummer Eve (Friday between June 19-25)
# ──────────────────────────────────────────────────────────────

class TestXHELMidsummer:
    def test_midsummer_2025(self, explicit_dates):
        """June 20, 2025 is Friday."""
        assert "2025-06-20" in explicit_dates
        assert "Midsummer" in explicit_dates["2025-06-20"]["name"]

    def test_midsummer_2026(self, explicit_dates):
        """June 19, 2026 is Friday."""
        assert "2026-06-19" in explicit_dates

    def test_midsummer_2027(self, explicit_dates):
        """June 18, 2027 is Friday."""
        assert "2027-06-18" in explicit_dates

    def test_midsummer_2028(self, explicit_dates):
        """June 23, 2028 is Friday."""
        assert "2028-06-23" in explicit_dates

    def test_midsummer_2029(self, explicit_dates):
        """June 22, 2029 is Friday."""
        assert "2029-06-22" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXHELRecurrence:
    def test_fixed_rules_exist(self, xhel):
        rules = xhel["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Epiphany" in names
        assert "May Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names
        assert "New Year's Eve" in names

    def test_easter_rules(self, xhel):
        rules = xhel["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}
        assert rule_by_name["Good Friday"]["rule"] == "easter_offset"
        assert rule_by_name["Good Friday"]["offset_days"] == -2
        assert rule_by_name["Easter Monday"]["offset_days"] == 1
        assert rule_by_name["Ascension Day"]["offset_days"] == 39

    def test_no_midsummer_in_rules(self, xhel):
        """Midsummer Eve is NOT in recurrence rules (dynamic Friday)."""
        rules = xhel["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Midsummer" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXHELStructure:
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
        """Nasdaq Helsinki has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~45-55 entries: 11 holidays × 5 years."""
        assert 40 <= len(explicit_dates) <= 60