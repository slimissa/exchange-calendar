#!/usr/bin/env python3
"""
test_lima_holidays.py — Ground truth tests for XLIM (Lima Stock Exchange).

Key facts verified:
    - Regular hours: 09:00-13:30 (morning session)
    - Lunch break: 13:30-14:30
    - Weekend is Saturday-Sunday (Western weekend)
    - Peru uses "next Monday" rule for most holidays
    - 12 national holidays
    - Independence Day (Jul 28-29) — two consecutive days
    - Christmas Eve (Dec 24) — early close at 11:30
    - New Year's Eve (Dec 31) — early close at 11:30
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XLIM.json)
    2. Peruvian holiday announcements changed (verify against bvl.com.pe)

Run:
    python3 -m pytest tests/test_lima_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xlim():
    """Load XLIM.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XLIM.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xlim):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xlim["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXLIMProperties:
    def test_code(self, xlim):
        assert xlim["code"] == "XLIM"

    def test_mic(self, xlim):
        assert xlim["mic"] == "XLIM"

    def test_name(self, xlim):
        assert xlim["name"] == "Lima Stock Exchange"

    def test_timezone(self, xlim):
        assert xlim["timezone"] == "America/Lima"

    def test_regular_hours(self, xlim):
        assert xlim["regular_hours"]["open"] == "09:00"
        assert xlim["regular_hours"]["close"] == "13:30"

    def test_lunch_break(self, xlim):
        lunch = [s for s in xlim.get("sessions", []) if s.get("type") == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "13:30"
        assert lunch[0]["close"] == "14:30"

    def test_no_extended_hours(self, xlim):
        assert "extended_hours" not in xlim or xlim.get("extended_hours") is None

    def test_generation_range(self, xlim):
        assert "generation_range" in xlim
        assert xlim["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xlim):
        assert xlim.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xlim):
        """Peru uses explicit dates only."""
        rules = xlim["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXLIMFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-11-01" not in explicit_dates

    def test_all_saints_2026(self, explicit_dates):
        """Nov 1, 2026 is Sunday — substitute to Monday Nov 2."""
        assert "2026-11-01" not in explicit_dates
        assert "2026-11-02" in explicit_dates

    def test_immaculate_conception_2025(self, explicit_dates):
        """Dec 8, 2025 is Monday."""
        assert "2025-12-08" in explicit_dates
        assert explicit_dates["2025-12-08"]["name"] == "Immaculate Conception"


# ──────────────────────────────────────────────────────────────
# Independence Day (two consecutive days)
# ──────────────────────────────────────────────────────────────

class TestXLIMIndependenceDay:
    def test_independence_day_2025(self, explicit_dates):
        """Jul 28, 2025 is Monday."""
        assert "2025-07-28" in explicit_dates
        assert explicit_dates["2025-07-28"]["name"] == "Independence Day"

    def test_independence_day_second_2025(self, explicit_dates):
        """Jul 29, 2025 is Tuesday."""
        assert "2025-07-29" in explicit_dates
        assert "Independence" in explicit_dates["2025-07-29"]["name"]

    def test_independence_day_2026(self, explicit_dates):
        """Jul 28, 2026 is Tuesday."""
        assert "2026-07-28" in explicit_dates

    def test_independence_day_second_2026(self, explicit_dates):
        """Jul 29, 2026 is Wednesday."""
        assert "2026-07-29" in explicit_dates

    def test_independence_day_2028(self, explicit_dates):
        """Jul 28, 2028 is Friday."""
        assert "2028-07-28" in explicit_dates

    def test_independence_day_second_2028(self, explicit_dates):
        """Jul 29, 2028 is Saturday (weekend) — no explicit entry."""
        assert "2028-07-29" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Holy Week holidays
# ──────────────────────────────────────────────────────────────

class TestXLIMHolyWeek:
    def test_maundy_thursday_2025(self, explicit_dates):
        """Easter - 3 days — April 17, 2025."""
        assert "2025-04-17" in explicit_dates
        assert "Maundy" in explicit_dates["2025-04-17"]["name"]

    def test_maundy_thursday_2026(self, explicit_dates):
        """Easter - 3 days — April 2, 2026."""
        assert "2026-04-02" in explicit_dates

    def test_maundy_thursday_2027(self, explicit_dates):
        """Easter - 3 days — March 25, 2027."""
        assert "2027-03-25" in explicit_dates

    def test_maundy_thursday_2028(self, explicit_dates):
        """Easter - 3 days — April 13, 2028."""
        assert "2028-04-13" in explicit_dates

    def test_good_friday_2025(self, explicit_dates):
        """Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["name"] == "Good Friday"

    def test_good_friday_2027(self, explicit_dates):
        """Easter - 2 days — March 26, 2027."""
        assert "2027-03-26" in explicit_dates

    def test_good_friday_2029(self, explicit_dates):
        """Easter - 2 days — March 30, 2029."""
        assert "2029-03-30" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Observed holidays (moved to Monday)
# ──────────────────────────────────────────────────────────────

class TestXLIMObservedHolidays:
    def test_battle_arica_2025(self, explicit_dates):
        """Jun 7, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-06-07" not in explicit_dates

    def test_battle_arica_2026(self, explicit_dates):
        """Jun 7, 2026 is Sunday — observed Monday Jun 8."""
        assert "2026-06-08" in explicit_dates

    def test_saint_peter_paul_2025(self, explicit_dates):
        """Jun 29, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-06-29" not in explicit_dates

    def test_saint_peter_paul_2026(self, explicit_dates):
        """Jun 29, 2026 is Monday."""
        assert "2026-06-29" in explicit_dates

    def test_air_force_2025(self, explicit_dates):
        """Jul 23, 2025 is Wednesday."""
        assert "2025-07-23" in explicit_dates

    def test_air_force_2028(self, explicit_dates):
        """Jul 23, 2028 is Sunday — observed Monday Jul 24."""
        assert "2028-07-24" in explicit_dates

    def test_battle_junin_2025(self, explicit_dates):
        """Aug 6, 2025 is Wednesday."""
        assert "2025-08-06" in explicit_dates

    def test_saint_rose_2025(self, explicit_dates):
        """Aug 30, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-08-30" not in explicit_dates

    def test_battle_angamos_2025(self, explicit_dates):
        """Oct 8, 2025 is Wednesday."""
        assert "2025-10-08" in explicit_dates

    def test_battle_angamos_2028(self, explicit_dates):
        """Oct 8, 2028 is Sunday — observed Monday Oct 9."""
        assert "2028-10-09" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXLIMChristmas:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — early close at 11:30."""
        entry = explicit_dates.get("2025-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "11:30"

    def test_christmas_eve_2026(self, explicit_dates):
        """Dec 24, 2026 is Thursday — early close at 11:30."""
        entry = explicit_dates.get("2026-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "11:30"

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_day_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — early close at 11:30."""
        entry = explicit_dates.get("2025-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "11:30"

    def test_new_years_eve_2029(self, explicit_dates):
        """Dec 31, 2029 is Monday — early close at 11:30."""
        entry = explicit_dates.get("2029-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# Early close days
# ──────────────────────────────────────────────────────────────

class TestXLIMEarlyCloses:
    def test_no_other_early_closes(self, explicit_dates):
        """Only Christmas Eve and New Year's Eve are early closes."""
        early_closes = [e for e in explicit_dates.values() if e.get("status") == "early_close"]
        early_close_names = {e["name"] for e in early_closes}
        assert early_close_names == {"Christmas Eve", "New Year's Eve"}

    def test_all_early_closes_have_early_close_time(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry.get("status") == "early_close":
                assert "early_close_time" in entry
                assert entry["early_close_time"] == "11:30"

    def test_closed_entries_no_early_close_time(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry.get("status") == "closed":
                assert "early_close_time" not in entry


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXLIMStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Peru weekend is Saturday-Sunday."""
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

    def test_dates_within_generation_range(self, xlim, explicit_dates):
        start = date.fromisoformat(xlim["generation_range"][0])
        end = date.fromisoformat(xlim["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~75-90 entries: 17 holidays × 5 years."""
        assert 70 <= len(explicit_dates) <= 95, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "bvl.com.pe" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXLIMWeekendPattern:
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

class TestXLIMSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count > 25, f"Expected many observed holidays, got {observed_count}"