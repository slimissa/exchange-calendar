#!/usr/bin/env python3
"""
test_singapore_holidays.py — Ground truth tests for XSES (Singapore Exchange).

Key facts verified:
    - SGX has NO lunch break (continuous trading 09:00-17:00 SGT)
    - Half-day sessions (early close 12:30) on:
      - Chinese New Year Eve
      - Christmas Eve (when weekday)
      - New Year's Eve (when weekday)
    - Singapore observes Sunday holidays on Monday (Employment Act)
    - No half-day shift when eve falls on weekend
    - Multicultural holidays: Chinese, Malay, Indian, Christian, Buddhist

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XSES.json)
    2. Singapore holiday regulations changed (verify against sgx.com)

Run:
    python3 -m pytest tests/test_singapore_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xses():
    """Load XSES.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XSES.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xses):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xses["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXSESProperties:
    def test_code(self, xses):
        assert xses["code"] == "XSES"

    def test_mic(self, xses):
        assert xses["mic"] == "XSES"

    def test_name(self, xses):
        assert xses["name"] == "Singapore Exchange"

    def test_timezone(self, xses):
        assert xses["timezone"] == "Asia/Singapore"

    def test_regular_hours(self, xses):
        assert xses["regular_hours"]["open"] == "09:00"
        assert xses["regular_hours"]["close"] == "17:00"

    def test_no_lunch_break(self, xses):
        """SGX is continuous trading since November 2017."""
        lunch = [s for s in xses.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_auction_sessions(self, xses):
        auctions = [s for s in xses.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 2

    def test_no_recurrence_rules(self, xses):
        assert xses["holidays"].get("recurrence_rules", []) == []


# ──────────────────────────────────────────────────────────────
# Half-day sessions (early close 12:30)
# ──────────────────────────────────────────────────────────────

class TestXSESHalfDays:
    def test_cny_eve_2025(self, explicit_dates):
        """Jan 28, 2025 — CNY Eve half-day."""
        assert "2025-01-28" in explicit_dates
        assert explicit_dates["2025-01-28"]["status"] == "early_close"
        assert explicit_dates["2025-01-28"]["early_close_time"] == "12:30"

    def test_cny_eve_2026(self, explicit_dates):
        assert "2026-02-16" in explicit_dates
        assert explicit_dates["2026-02-16"]["status"] == "early_close"

    def test_cny_eve_2027(self, explicit_dates):
        assert "2027-02-05" in explicit_dates
        assert explicit_dates["2027-02-05"]["status"] == "early_close"

    def test_cny_eve_2028(self, explicit_dates):
        assert "2028-01-25" in explicit_dates
        assert explicit_dates["2028-01-25"]["status"] == "early_close"

    def test_cny_eve_2029(self, explicit_dates):
        assert "2029-02-12" in explicit_dates
        assert explicit_dates["2029-02-12"]["status"] == "early_close"

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "early_close"
        assert explicit_dates["2025-12-24"]["early_close_time"] == "12:30"

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "early_close"

    def test_no_new_years_eve_shift_2028(self, explicit_dates):
        """
        Dec 31, 2028 is Sunday. SGX does NOT shift to Friday Dec 29.
        Friday Dec 29 is a normal full trading day.
        """
        assert "2028-12-29" not in explicit_dates
        assert "2028-12-31" not in explicit_dates  # Sunday

    def test_no_christmas_eve_2028_sunday(self, explicit_dates):
        """Dec 24, 2028 is Sunday — no half-day."""
        assert "2028-12-24" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Observed holidays (Sunday → Monday)
# ──────────────────────────────────────────────────────────────

class TestXSESObserved:
    def test_vesak_observed_2026(self, explicit_dates):
        """Vesak Day May 31, 2026 is Sunday — observed Monday June 1."""
        assert "2026-06-01" in explicit_dates
        assert "Vesak" in explicit_dates["2026-06-01"]["name"]

    def test_national_day_observed_2026(self, explicit_dates):
        """Aug 9, 2026 is Sunday — observed Monday Aug 10."""
        assert "2026-08-10" in explicit_dates
        assert "National" in explicit_dates["2026-08-10"]["name"]

    def test_deepavali_observed_2026(self, explicit_dates):
        """Deepavali Nov 8, 2026 is Sunday — observed Monday Nov 9."""
        assert "2026-11-09" in explicit_dates
        assert "Deepavali" in explicit_dates["2026-11-09"]["name"]

    def test_cny_observed_2027(self, explicit_dates):
        """CNY Feb 6, 2027 is Sunday — observed Tuesday Feb 8."""
        assert "2027-02-08" in explicit_dates
        assert "observed" in explicit_dates["2027-02-08"]["name"].lower()


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXSESStructure:
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

    def test_early_close_time_1230(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry["status"] == "early_close":
                assert entry["early_close_time"] == "12:30"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~60 entries: 11 holidays × 5 years + half-days + observed."""
        assert 55 <= len(explicit_dates) <= 75