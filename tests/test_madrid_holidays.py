#!/usr/bin/env python3
"""
test_madrid_holidays.py — Ground truth tests for XMAD (Bolsa de Madrid / BME).

Key facts verified:
    - BME is OPEN on most Spanish civil holidays:
      Epiphany (Jan 6), Easter Monday, Assumption (Aug 15),
      Hispanic Day (Oct 12), All Saints (Nov 1),
      Constitution Day (Dec 6), Immaculate Conception (Dec 8)
    - Only 5 full closures: New Year, Good Friday, Labour Day,
      Christmas Day, Boxing Day (Dec 26)
    - Christmas Eve and New Year's Eve are half-days (early close 14:00 CET)
    - No lunch break (continuous trading)
    - No weekend observation — Spanish holidays on weekends are NOT shifted
    - BME follows the Euronext harmonized calendar model

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XMAD.json)
    2. Spanish/BME holiday rules changed (verify against bolsasymercados.es)

Run:
    python3 -m pytest tests/test_madrid_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xmad():
    """Load XMAD.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XMAD.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xmad):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xmad["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXMADProperties:
    def test_code(self, xmad):
        assert xmad["code"] == "XMAD"

    def test_mic(self, xmad):
        assert xmad["mic"] == "XMAD"

    def test_name(self, xmad):
        assert xmad["name"] == "Bolsa de Madrid"

    def test_timezone(self, xmad):
        assert xmad["timezone"] == "Europe/Madrid"

    def test_regular_hours(self, xmad):
        assert xmad["regular_hours"]["open"] == "09:00"
        assert xmad["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xmad):
        lunch = [s for s in xmad.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_auction_sessions(self, xmad):
        auctions = [s for s in xmad.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 2
        times = [a["at"] for a in auctions]
        assert "09:00" in times
        assert "17:30" in times

    def test_has_extended_hours(self, xmad):
        assert "extended_hours" in xmad


# ──────────────────────────────────────────────────────────────
# BME is OPEN on Spanish civil holidays
# ──────────────────────────────────────────────────────────────

class TestXMADOpenOnSpanishHolidays:
    def test_epiphany_open(self, explicit_dates):
        """January 6 — BME OPEN."""
        assert "2025-01-06" not in explicit_dates
        assert "2026-01-06" not in explicit_dates

    def test_easter_monday_open(self, explicit_dates):
        """Easter Monday — BME OPEN (unlike UK/France)."""
        assert "2025-04-21" not in explicit_dates

    def test_assumption_open(self, explicit_dates):
        """August 15 — BME OPEN."""
        assert "2025-08-15" not in explicit_dates
        assert "2026-08-15" not in explicit_dates

    def test_hispanic_day_open(self, explicit_dates):
        """October 12 — BME OPEN."""
        assert "2025-10-12" not in explicit_dates
        assert "2025-10-13" not in explicit_dates  # No observed Monday

    def test_all_saints_open(self, explicit_dates):
        """November 1 — BME OPEN."""
        assert "2025-11-01" not in explicit_dates
        assert "2026-11-01" not in explicit_dates

    def test_constitution_open(self, explicit_dates):
        """December 6 — BME OPEN."""
        assert "2025-12-06" not in explicit_dates
        assert "2026-12-07" not in explicit_dates  # No observed Monday

    def test_immaculate_open(self, explicit_dates):
        """December 8 — BME OPEN."""
        assert "2025-12-08" not in explicit_dates
        assert "2026-12-08" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Actual BME closures
# ──────────────────────────────────────────────────────────────

class TestXMADClosed2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["status"] == "closed"

    def test_labour_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["status"] == "closed"

    def test_christmas_day(self, explicit_dates):
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["status"] == "closed"

    def test_boxing_day(self, explicit_dates):
        """BME closes on Dec 26 (harmonized with European markets)."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["status"] == "closed"


class TestXMADClosed2026:
    def test_new_year(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2026-05-01" in explicit_dates

    def test_christmas_day(self, explicit_dates):
        assert "2026-12-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Half-days (early close 14:00)
# ──────────────────────────────────────────────────────────────

class TestXMADHalfDays:
    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "early_close"
        assert explicit_dates["2025-12-24"]["early_close_time"] == "14:00"

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "early_close"
        assert explicit_dates["2025-12-31"]["early_close_time"] == "14:00"

    def test_christmas_eve_2026(self, explicit_dates):
        assert "2026-12-24" in explicit_dates
        assert explicit_dates["2026-12-24"]["status"] == "early_close"

    def test_new_years_eve_2026(self, explicit_dates):
        assert "2026-12-31" in explicit_dates
        assert explicit_dates["2026-12-31"]["status"] == "early_close"

    def test_christmas_eve_2027(self, explicit_dates):
        assert "2027-12-24" in explicit_dates
        assert explicit_dates["2027-12-24"]["status"] == "early_close"

    def test_new_years_eve_2027(self, explicit_dates):
        assert "2027-12-31" in explicit_dates
        assert explicit_dates["2027-12-31"]["status"] == "early_close"

    def test_no_christmas_eve_2028_sunday(self, explicit_dates):
        assert "2028-12-24" not in explicit_dates

    def test_no_new_years_eve_2028_sunday(self, explicit_dates):
        assert "2028-12-31" not in explicit_dates

    def test_christmas_eve_2029(self, explicit_dates):
        assert "2029-12-24" in explicit_dates
        assert explicit_dates["2029-12-24"]["status"] == "early_close"

    def test_new_years_eve_2029(self, explicit_dates):
        assert "2029-12-31" in explicit_dates
        assert explicit_dates["2029-12-31"]["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXMADStructure:
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

    def test_early_close_time_1400(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry["status"] == "early_close":
                assert entry["early_close_time"] == "14:00"

    def test_recurrence_rules_exist(self, xmad):
        rules = xmad["holidays"].get("recurrence_rules", [])
        assert len(rules) > 0

    def test_recurrence_rules_no_spanish_holidays(self, xmad):
        rules = xmad["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Epiphany" not in names
        assert "Easter Monday" not in names
        assert "Assumption Day" not in names
        assert "Hispanic Day" not in names
        assert "All Saints' Day" not in names
        assert "Constitution Day" not in names
        assert "Immaculate Conception" not in names

    def test_recurrence_rules_have_closures(self, xmad):
        rules = xmad["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Good Friday" in names
        assert "Labour Day" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names

    def test_holiday_count_reasonable(self, explicit_dates):
        """~27 entries: 5 closures × 5 years + 8 half-days."""
        assert 25 <= len(explicit_dates) <= 35