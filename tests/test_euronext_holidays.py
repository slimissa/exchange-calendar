#!/usr/bin/env python3
"""
test_euronext_holidays.py — Ground truth tests for XPAR (Euronext Paris).

Key facts verified:
    - Euronext Paris stays OPEN on most French public holidays:
      Victory Day (May 8), Ascension Day, Whit Monday, Bastille Day (July 14),
      Assumption Day (Aug 15), All Saints' Day (Nov 1), Armistice Day (Nov 11)
    - Only 6 full closures: New Year, Good Friday, Easter Monday, Labour Day,
      Christmas Day, Boxing Day (St. Stephen's Day)
    - Christmas Eve and New Year's Eve are half-days (early close 14:05 CET)
      when they fall on weekdays
    - No lunch break (continuous trading)
    - Opening auction at 09:00, closing auction at 17:30
    - No weekend observance — French holidays on weekends are NOT observed

Run:
    python3 -m pytest tests/test_euronext_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xpar():
    """Load XPAR.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XPAR.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xpar):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xpar["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXPARProperties:
    def test_code(self, xpar):
        assert xpar["code"] == "XPAR"

    def test_mic(self, xpar):
        assert xpar["mic"] == "XPAR"

    def test_name(self, xpar):
        assert xpar["name"] == "Euronext Paris"

    def test_timezone(self, xpar):
        assert xpar["timezone"] == "Europe/Paris"

    def test_regular_hours(self, xpar):
        assert xpar["regular_hours"]["open"] == "09:00"
        assert xpar["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xpar):
        lunch = [s for s in xpar.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_auction_sessions(self, xpar):
        auctions = [s for s in xpar.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 2
        times = [a["at"] for a in auctions]
        assert "09:00" in times
        assert "17:30" in times

    def test_has_extended_hours(self, xpar):
        assert "extended_hours" in xpar
        assert xpar["extended_hours"]["pre_market"]["open"] == "07:15"


# ──────────────────────────────────────────────────────────────
# French holidays where Euronext is OPEN
# ──────────────────────────────────────────────────────────────

class TestXPAROpenOnFrenchHolidays:
    def test_victory_day_open(self, explicit_dates):
        """May 8 — Euronext OPEN."""
        assert "2025-05-08" not in explicit_dates
        assert "2026-05-08" not in explicit_dates

    def test_ascension_open(self, explicit_dates):
        """Ascension Day — Euronext OPEN."""
        assert "2025-05-29" not in explicit_dates

    def test_whit_monday_open(self, explicit_dates):
        """Whit Monday — Euronext OPEN."""
        assert "2025-06-09" not in explicit_dates

    def test_bastille_day_open(self, explicit_dates):
        """July 14 — Euronext OPEN."""
        assert "2025-07-14" not in explicit_dates
        assert "2026-07-14" not in explicit_dates

    def test_assumption_open(self, explicit_dates):
        """August 15 — Euronext OPEN."""
        assert "2025-08-15" not in explicit_dates
        assert "2026-08-15" not in explicit_dates

    def test_all_saints_open(self, explicit_dates):
        """November 1 — Euronext OPEN."""
        assert "2025-11-01" not in explicit_dates
        assert "2026-11-01" not in explicit_dates

    def test_armistice_open(self, explicit_dates):
        """November 11 — Euronext OPEN."""
        assert "2025-11-11" not in explicit_dates
        assert "2026-11-11" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Actual Euronext closures
# ──────────────────────────────────────────────────────────────

class TestXPARClosed:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["status"] == "closed"

    def test_easter_monday_2025(self, explicit_dates):
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["status"] == "closed"

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["status"] == "closed"

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["status"] == "closed"

    def test_boxing_day_2025(self, explicit_dates):
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["status"] == "closed"

    def test_new_year_2026(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_good_friday_2026(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_easter_monday_2026(self, explicit_dates):
        assert "2026-04-06" in explicit_dates

    def test_labour_day_2026(self, explicit_dates):
        assert "2026-05-01" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Half-days (early close 14:05)
# ──────────────────────────────────────────────────────────────

class TestXPARHalfDays:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — half-day."""
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "early_close"
        assert explicit_dates["2025-12-24"]["early_close_time"] == "14:05"

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — half-day."""
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "early_close"
        assert explicit_dates["2025-12-31"]["early_close_time"] == "14:05"

    def test_christmas_eve_2026(self, explicit_dates):
        """Dec 24, 2026 is Thursday — half-day."""
        assert "2026-12-24" in explicit_dates
        assert explicit_dates["2026-12-24"]["status"] == "early_close"

    def test_new_years_eve_2026(self, explicit_dates):
        """Dec 31, 2026 is Thursday — half-day."""
        assert "2026-12-31" in explicit_dates
        assert explicit_dates["2026-12-31"]["status"] == "early_close"

    def test_no_christmas_eve_2028_sunday(self, explicit_dates):
        """Dec 24, 2028 is Sunday — no half-day."""
        assert "2028-12-24" not in explicit_dates

    def test_no_new_years_eve_2028_sunday(self, explicit_dates):
        """Dec 31, 2028 is Sunday — no half-day."""
        assert "2028-12-31" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXPARStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_early_close_time_1405(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry["status"] == "early_close":
                assert entry["early_close_time"] == "14:05"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source: {date_str}"

    def test_recurrence_rules_no_french_holidays(self, xpar):
        rules = xpar["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Victory Day" not in names
        assert "Ascension Day" not in names
        assert "Whit Monday" not in names
        assert "Bastille Day" not in names
        assert "Assumption Day" not in names
        assert "All Saints' Day" not in names
        assert "Armistice Day" not in names

    def test_recurrence_rules_have_actual_closures(self, xpar):
        rules = xpar["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Good Friday" in names
        assert "Easter Monday" in names
        assert "Labour Day" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names

    def test_holiday_count_reasonable(self, explicit_dates):
        """Should have ~30 entries: 6 closures × 5 years + 8 half-days."""
        assert 25 <= len(explicit_dates) <= 40