#!/usr/bin/env python3
"""
test_buenos_aires_holidays.py — Ground truth tests for XBUE (Buenos Aires Stock Exchange / BYMA).

Key facts verified:
    - Regular hours: 11:00-17:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Argentina uses "next Monday" rule for some holidays
    - Carnival Monday/Tuesday (movable)
    - Good Friday (movable)
    - Christmas Eve (Dec 24) — early close at 13:00
    - New Year's Eve (Dec 31) — early close at 13:00
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBUE.json)
    2. Argentine holiday announcements changed (verify against byma.com.ar)

Run:
    python3 -m pytest tests/test_buenos_aires_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbue():
    """Load XBUE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBUE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbue):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbue["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBUEProperties:
    def test_code(self, xbue):
        assert xbue["code"] == "XBUE"

    def test_mic(self, xbue):
        assert xbue["mic"] == "XBUE"

    def test_name(self, xbue):
        assert xbue["name"] == "Buenos Aires Stock Exchange"

    def test_timezone(self, xbue):
        assert xbue["timezone"] == "America/Argentina/Buenos_Aires"

    def test_regular_hours(self, xbue):
        assert xbue["regular_hours"]["open"] == "11:00"
        assert xbue["regular_hours"]["close"] == "17:00"

    def test_no_lunch_break(self, xbue):
        lunch = [s for s in xbue.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbue):
        assert "extended_hours" not in xbue or xbue.get("extended_hours") is None

    def test_generation_range(self, xbue):
        assert "generation_range" in xbue
        assert xbue["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xbue):
        assert xbue.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xbue):
        """Argentina uses explicit dates only."""
        rules = xbue["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXBUEFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_remembrance_day_2025(self, explicit_dates):
        """Mar 24, 2025 is Monday."""
        assert "2025-03-24" in explicit_dates
        assert "Remembrance" in explicit_dates["2025-03-24"]["name"]

    def test_remembrance_day_2029_substitute(self, explicit_dates):
        """Mar 24, 2029 is Saturday — substitute to Monday Mar 26."""
        assert "2029-03-24" not in explicit_dates
        assert "2029-03-26" in explicit_dates

    def test_malvinas_day_2025(self, explicit_dates):
        """Apr 2, 2025 is Wednesday."""
        assert "2025-04-02" in explicit_dates
        assert "Malvinas" in explicit_dates["2025-04-02"]["name"]

    def test_malvinas_day_2028_substitute(self, explicit_dates):
        """Apr 2, 2028 is Sunday — substitute to Monday Apr 3."""
        assert "2028-04-02" not in explicit_dates
        assert "2028-04-03" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_may_revolution_2025(self, explicit_dates):
        """May 25, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-05-25" not in explicit_dates

    def test_may_revolution_2026(self, explicit_dates):
        """May 25, 2026 is Monday."""
        assert "2026-05-25" in explicit_dates

    def test_flag_day_2025(self, explicit_dates):
        """Jun 20, 2025 is Friday."""
        assert "2025-06-20" in explicit_dates
        assert "Flag" in explicit_dates["2025-06-20"]["name"]

    def test_flag_day_2027_substitute(self, explicit_dates):
        """Jun 20, 2027 is Sunday — substitute to Monday Jun 21."""
        assert "2027-06-21" in explicit_dates

    def test_independence_2025(self, explicit_dates):
        """Jul 9, 2025 is Wednesday."""
        assert "2025-07-09" in explicit_dates
        assert "Independence" in explicit_dates["2025-07-09"]["name"]

    def test_independence_2028_substitute(self, explicit_dates):
        """Jul 9, 2028 is Sunday — substitute to Monday Jul 10."""
        assert "2028-07-09" not in explicit_dates
        assert "2028-07-10" in explicit_dates

    def test_san_martin_2025(self, explicit_dates):
        """Aug 17, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-08-17" not in explicit_dates

    def test_cultural_diversity_2025(self, explicit_dates):
        """Oct 12, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-10-12" not in explicit_dates

    def test_sovereignty_2025(self, explicit_dates):
        """Nov 20, 2025 is Thursday."""
        assert "2025-11-20" in explicit_dates
        assert "Sovereignty" in explicit_dates["2025-11-20"]["name"]

    def test_immaculate_conception_2025(self, explicit_dates):
        """Dec 8, 2025 is Monday."""
        assert "2025-12-08" in explicit_dates
        assert explicit_dates["2025-12-08"]["name"] == "Immaculate Conception"


# ──────────────────────────────────────────────────────────────
# Carnival holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXBUECarnival:
    def test_carnival_2025(self, explicit_dates):
        """Carnival Monday/Tuesday 2025 — Mar 3-4."""
        assert "2025-03-03" in explicit_dates
        assert "Carnival Monday" in explicit_dates["2025-03-03"]["name"]
        assert "2025-03-04" in explicit_dates
        assert "Carnival Tuesday" in explicit_dates["2025-03-04"]["name"]

    def test_carnival_2026(self, explicit_dates):
        """Carnival Monday/Tuesday 2026 — Feb 16-17."""
        assert "2026-02-16" in explicit_dates
        assert "2026-02-17" in explicit_dates

    def test_carnival_2027(self, explicit_dates):
        """Carnival Monday/Tuesday 2027 — Feb 8-9."""
        assert "2027-02-08" in explicit_dates
        assert "2027-02-09" in explicit_dates

    def test_carnival_2028(self, explicit_dates):
        """Carnival Monday/Tuesday 2028 — Feb 28-29."""
        assert "2028-02-28" in explicit_dates
        assert "2028-02-29" in explicit_dates

    def test_carnival_2029(self, explicit_dates):
        """Carnival Monday/Tuesday 2029 — Feb 12-13."""
        assert "2029-02-12" in explicit_dates
        assert "2029-02-13" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Good Friday (movable)
# ──────────────────────────────────────────────────────────────

class TestXBUEGoodFriday:
    def test_good_friday_2025(self, explicit_dates):
        """Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["name"] == "Good Friday"

    def test_good_friday_2026(self, explicit_dates):
        """Easter - 2 days — April 3, 2026."""
        assert "2026-04-03" in explicit_dates

    def test_good_friday_2027(self, explicit_dates):
        """Easter - 2 days — March 26, 2027."""
        assert "2027-03-26" in explicit_dates

    def test_good_friday_2028(self, explicit_dates):
        """Easter - 2 days — April 14, 2028."""
        assert "2028-04-14" in explicit_dates

    def test_good_friday_2029(self, explicit_dates):
        """Easter - 2 days — March 30, 2029."""
        assert "2029-03-30" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXBUEChristmas:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — early close at 13:00."""
        entry = explicit_dates.get("2025-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "13:00"

    def test_christmas_eve_2026(self, explicit_dates):
        """Dec 24, 2026 is Thursday — early close at 13:00."""
        entry = explicit_dates.get("2026-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "13:00"

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_day_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — early close at 13:00."""
        entry = explicit_dates.get("2025-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "13:00"

    def test_new_years_eve_2029(self, explicit_dates):
        """Dec 31, 2029 is Monday — early close at 13:00."""
        entry = explicit_dates.get("2029-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# Early close days
# ──────────────────────────────────────────────────────────────

class TestXBUEarlyCloses:
    def test_no_other_early_closes(self, explicit_dates):
        """Only Christmas Eve and New Year's Eve are early closes."""
        early_closes = [e for e in explicit_dates.values() if e.get("status") == "early_close"]
        early_close_names = {e["name"] for e in early_closes}
        assert early_close_names == {"Christmas Eve", "New Year's Eve"}

    def test_all_early_closes_have_early_close_time(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry.get("status") == "early_close":
                assert "early_close_time" in entry
                assert entry["early_close_time"] == "13:00"

    def test_closed_entries_no_early_close_time(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry.get("status") == "closed":
                assert "early_close_time" not in entry


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBUEStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Argentina weekend is Saturday-Sunday."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str} ({d.strftime('%A')})"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates)), "Duplicate dates found"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"
            assert entry["source_url"].startswith("http")

    def test_all_entries_have_name(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "name" in entry, f"Missing name: {date_str}"
            assert entry["name"], f"Empty name: {date_str}"

    def test_all_entries_have_status(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "status" in entry, f"Missing status: {date_str}"
            assert entry["status"] in ["closed", "early_close"]

    def test_dates_within_generation_range(self, xbue, explicit_dates):
        start = date.fromisoformat(xbue["generation_range"][0])
        end = date.fromisoformat(xbue["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~75-90 entries: 17 holidays × 5 years."""
        assert 70 <= len(explicit_dates) <= 95, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "byma.com.ar" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBUEWeekendPattern:
    def test_saturday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 6, f"Sunday date: {date_str}"

    def test_monday_is_common_substitute(self, explicit_dates):
        monday_count = sum(1 for ds in explicit_dates if date.fromisoformat(ds).weekday() == 0)
        assert monday_count > 15, f"Expected many Monday holidays, got {monday_count}"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXBUESubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count > 20, f"Expected many observed holidays, got {observed_count}"