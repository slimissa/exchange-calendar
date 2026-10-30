#!/usr/bin/env python3
"""
test_toronto_holidays.py — Ground truth tests for XTSE (Toronto Stock Exchange).

Key facts verified:
    - Victoria Day is Monday preceding May 25 (NOT last Monday of May)
    - Christmas Eve is a half-day (early close 13:00 ET) on weekdays
    - Canada observes holidays on adjacent weekdays when they fall on weekends
    - Family Day: 3rd Monday February
    - Thanksgiving: 2nd Monday October
    - Civic Holiday: 1st Monday August
    - No lunch break (continuous trading)
    - Timezone: America/Toronto

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XTSE.json)
    2. Canadian holiday law changed (verify against tsx.com)

Run:
    python3 -m pytest tests/test_toronto_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xtse():
    """Load XTSE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XTSE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xtse):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xtse["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXTSEProperties:
    def test_code(self, xtse):
        assert xtse["code"] == "XTSE"

    def test_mic(self, xtse):
        assert xtse["mic"] == "XTSE"

    def test_name(self, xtse):
        assert xtse["name"] == "Toronto Stock Exchange"

    def test_timezone(self, xtse):
        assert xtse["timezone"] == "America/Toronto"

    def test_regular_hours(self, xtse):
        assert xtse["regular_hours"]["open"] == "09:30"
        assert xtse["regular_hours"]["close"] == "16:00"

    def test_no_lunch_break(self, xtse):
        lunch = [s for s in xtse.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_auction_sessions(self, xtse):
        auctions = [s for s in xtse.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 2

    def test_has_extended_hours(self, xtse):
        assert "extended_hours" in xtse


# ──────────────────────────────────────────────────────────────
# Victoria Day — the tricky one
# ──────────────────────────────────────────────────────────────

class TestXTSEVictoriaDay:
    def test_victoria_day_2025(self, explicit_dates):
        """May 19, 2025 — third Monday."""
        assert "2025-05-19" in explicit_dates

    def test_victoria_day_2026(self, explicit_dates):
        """May 18, 2026 — third Monday."""
        assert "2026-05-18" in explicit_dates

    def test_victoria_day_2027_correct(self, explicit_dates):
        """
        Victoria Day 2027 is May 24 (Monday preceding May 25).
        The last Monday of May 2027 is May 31 — WRONG.
        """
        assert "2027-05-24" in explicit_dates
        assert "2027-05-31" not in explicit_dates

    def test_victoria_day_2028(self, explicit_dates):
        """May 22, 2028 — Monday preceding May 25."""
        assert "2028-05-22" in explicit_dates

    def test_victoria_day_2029(self, explicit_dates):
        """May 21, 2029 — Monday preceding May 25."""
        assert "2029-05-21" in explicit_dates

    def test_no_victoria_day_in_recurrence(self, xtse):
        """Victoria Day must be explicit-only (not last_weekday rule)."""
        rules = xtse["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Victoria Day" not in names


# ──────────────────────────────────────────────────────────────
# Christmas Eve half-days (early close 13:00 ET)
# ──────────────────────────────────────────────────────────────

class TestXTSEHalfDays:
    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "early_close"
        assert explicit_dates["2025-12-24"]["early_close_time"] == "13:00"

    def test_christmas_eve_2026(self, explicit_dates):
        assert "2026-12-24" in explicit_dates
        assert explicit_dates["2026-12-24"]["status"] == "early_close"
        assert explicit_dates["2026-12-24"]["early_close_time"] == "13:00"

    def test_christmas_eve_2027(self, explicit_dates):
        assert "2027-12-24" in explicit_dates
        assert explicit_dates["2027-12-24"]["status"] == "early_close"

    def test_no_christmas_eve_2028_sunday(self, explicit_dates):
        """Dec 24, 2028 is Sunday — no half-day."""
        assert "2028-12-24" not in explicit_dates

    def test_christmas_eve_2029(self, explicit_dates):
        assert "2029-12-24" in explicit_dates
        assert explicit_dates["2029-12-24"]["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# Christmas / Boxing Day 2027 observation shift
# ──────────────────────────────────────────────────────────────

class TestXTSE2027ChristmasShift:
    def test_christmas_observed_2027(self, explicit_dates):
        """
        Dec 25, 2027 is Saturday. Christmas observed Monday Dec 27.
        """
        assert "2027-12-25" not in explicit_dates  # Saturday, no explicit
        assert "2027-12-27" in explicit_dates
        assert "Christmas" in explicit_dates["2027-12-27"]["name"]
        assert explicit_dates["2027-12-27"]["status"] == "closed"

    def test_boxing_day_observed_2027(self, explicit_dates):
        """
        Dec 26, 2027 is Sunday. Boxing Day observed Tuesday Dec 28.
        """
        assert "2027-12-28" in explicit_dates
        assert "Boxing" in explicit_dates["2027-12-28"]["name"]
        assert explicit_dates["2027-12-28"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2025 holidays
# ──────────────────────────────────────────────────────────────

class TestXTSE2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates

    def test_family_day(self, explicit_dates):
        assert "2025-02-17" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_canada_day(self, explicit_dates):
        assert "2025-07-01" in explicit_dates

    def test_civic_holiday(self, explicit_dates):
        assert "2025-08-04" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2025-09-01" in explicit_dates

    def test_thanksgiving(self, explicit_dates):
        assert "2025-10-13" in explicit_dates

    def test_christmas(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day(self, explicit_dates):
        assert "2025-12-26" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXTSEStructure:
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

    def test_early_close_time_1300(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry["status"] == "early_close":
                assert entry["early_close_time"] == "13:00"

    def test_recurrence_rules_exist(self, xtse):
        rules = xtse["holidays"].get("recurrence_rules", [])
        assert len(rules) > 0

    def test_recurrence_rules_no_victoria_day(self, xtse):
        rules = xtse["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Victoria Day" not in names

    def test_recurrence_rules_have_main_holidays(self, xtse):
        rules = xtse["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Family Day" in names
        assert "Good Friday" in names
        assert "Canada Day" in names
        assert "Civic Holiday" in names
        assert "Labour Day" in names
        assert "Thanksgiving Day" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names

    def test_holiday_count_reasonable(self, explicit_dates):
        """~53 entries: 10 holidays × 5 years + 4 half-days + shifts."""
        assert 45 <= len(explicit_dates) <= 65


# ──────────────────────────────────────────────────────────────
# Future-year fixes (v2.23.4)
# ──────────────────────────────────────────────────────────────

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import generate_dates as _gd


def _closed_weekdays(exchange, year):
    """Closed weekdays the registry produces for one year (explicit plus rules)."""
    days = list(exchange["holidays"]["explicit"]) + _gd.expand_exchange(exchange)
    return {d["date"] for d in days
            if d["date"].startswith(str(year)) and d["status"] == "closed"
            and date.fromisoformat(d["date"]).weekday() < 5}


class TestFutureYearFixes:
    """TMX closes on the Monday in lieu of a Saturday holiday (TSX closed
    Monday 3 Jan 2022 in lieu of Saturday 1 Jan 2022) and stays open on the
    Friday before it."""

    def test_new_year_2028_is_observed_on_monday_3_jan(self, explicit_dates):
        assert explicit_dates["2028-01-03"]["status"] == "closed"
        assert "observed" in explicit_dates["2028-01-03"]["name"]

    @pytest.mark.parametrize("day", ["2027-12-31", "2028-06-30"])
    def test_friday_before_a_saturday_holiday_is_open(self, xtse, day):
        assert date.fromisoformat(day).weekday() == 4
        assert day not in _closed_weekdays(xtse, int(day[:4]))

    def test_canada_day_2028_is_observed_on_monday_3_july(self, xtse):
        assert "2028-07-03" in _closed_weekdays(xtse, 2028)

    def test_new_year_and_canada_day_rules_do_not_shift_to_friday(self, xtse):
        rules = {r["name"]: r["rule"] for r in xtse["holidays"]["recurrence_rules"]}
        assert rules["New Year's Day"] == "fixed_date"
        assert rules["Canada Day"] == "fixed_date"
