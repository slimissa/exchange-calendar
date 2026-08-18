#!/usr/bin/env python3
"""
test_bogota_holidays.py — Ground truth tests for XBOG (Colombia Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-15:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Colombia uses "next Monday" rule (Emiliani Law) for most holidays
    - 16 national holidays (one of the most in the world)
    - Christmas Eve (Dec 24) — early close at 11:30
    - New Year's Eve (Dec 31) — early close at 11:30
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBOG.json)
    2. Colombian holiday announcements changed (verify against bvc.com.co)

Run:
    python3 -m pytest tests/test_bogota_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbog():
    """Load XBOG.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBOG.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbog):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbog["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBOGProperties:
    def test_code(self, xbog):
        assert xbog["code"] == "XBOG"

    def test_mic(self, xbog):
        assert xbog["mic"] == "XBOG"

    def test_name(self, xbog):
        assert xbog["name"] == "Colombia Stock Exchange"

    def test_timezone(self, xbog):
        assert xbog["timezone"] == "America/Bogota"

    def test_regular_hours(self, xbog):
        assert xbog["regular_hours"]["open"] == "09:30"
        assert xbog["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xbog):
        lunch = [s for s in xbog.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbog):
        assert "extended_hours" not in xbog or xbog.get("extended_hours") is None

    def test_generation_range(self, xbog):
        assert "generation_range" in xbog
        assert xbog["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xbog):
        assert xbog.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xbog):
        """Colombia uses explicit dates only (Emiliani Law complexity)."""
        rules = xbog["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXBOGFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_epiphany_2025(self, explicit_dates):
        """Jan 6, 2025 is Monday — observed."""
        assert "2025-01-06" in explicit_dates
        assert "Epiphany" in explicit_dates["2025-01-06"]["name"]

    def test_epiphany_2026(self, explicit_dates):
        """Jan 6, 2026 is Tuesday — observed to Monday Jan 12."""
        assert "2026-01-12" in explicit_dates

    def test_saint_joseph_2025(self, explicit_dates):
        """Mar 19, 2025 is Wednesday — observed to Monday Mar 24."""
        assert "2025-03-24" in explicit_dates
        assert "Saint Joseph" in explicit_dates["2025-03-24"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_independence_2025(self, explicit_dates):
        """Jul 20, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-07-20" not in explicit_dates

    def test_independence_2026(self, explicit_dates):
        """Jul 20, 2026 is Monday."""
        assert "2026-07-20" in explicit_dates
        assert explicit_dates["2026-07-20"]["name"] == "Independence Day"

    def test_battle_boyaca_2025(self, explicit_dates):
        """Aug 7, 2025 is Thursday."""
        assert "2025-08-07" in explicit_dates
        assert "Boyacá" in explicit_dates["2025-08-07"]["name"]

    def test_immaculate_conception_2025(self, explicit_dates):
        """Dec 8, 2025 is Monday."""
        assert "2025-12-08" in explicit_dates
        assert explicit_dates["2025-12-08"]["name"] == "Immaculate Conception"


# ──────────────────────────────────────────────────────────────
# Emiliani Law holidays (moved to Monday)
# ──────────────────────────────────────────────────────────────

class TestXBOGEmilianiLaw:
    def test_ascension_2025(self, explicit_dates):
        """Ascension Day — observed Monday Jun 2, 2025."""
        assert "2025-06-02" in explicit_dates
        assert "Ascension" in explicit_dates["2025-06-02"]["name"]

    def test_corpus_christi_2025(self, explicit_dates):
        """Corpus Christi — observed Monday Jun 23, 2025."""
        assert "2025-06-23" in explicit_dates
        assert "Corpus" in explicit_dates["2025-06-23"]["name"]

    def test_sacred_heart_2025(self, explicit_dates):
        """Sacred Heart — observed Monday Jun 30, 2025."""
        assert "2025-06-30" in explicit_dates
        assert "Sacred Heart" in explicit_dates["2025-06-30"]["name"]

    def test_saint_peter_paul_2025(self, explicit_dates):
        """Saint Peter and Paul — observed Monday Jul 1, 2025."""
        assert "2025-07-01" in explicit_dates

    def test_assumption_2025(self, explicit_dates):
        """Assumption — observed Monday Aug 18, 2025."""
        assert "2025-08-18" in explicit_dates
        assert "Assumption" in explicit_dates["2025-08-18"]["name"]

    def test_columbus_2025(self, explicit_dates):
        """Columbus Day — observed Monday Oct 13, 2025."""
        assert "2025-10-13" in explicit_dates
        assert "Columbus" in explicit_dates["2025-10-13"]["name"]

    def test_all_saints_2025(self, explicit_dates):
        """All Saints' Day — observed Monday Nov 3, 2025."""
        assert "2025-11-03" in explicit_dates
        assert "All Saints" in explicit_dates["2025-11-03"]["name"]

    def test_cartagena_2025(self, explicit_dates):
        """Independence of Cartagena — observed Monday Nov 17, 2025."""
        assert "2025-11-17" in explicit_dates
        assert "Cartagena" in explicit_dates["2025-11-17"]["name"]


# ──────────────────────────────────────────────────────────────
# Easter holidays
# ──────────────────────────────────────────────────────────────

class TestXBOGHolyWeek:
    def test_maundy_thursday_2025(self, explicit_dates):
        """Easter - 3 days — April 17, 2025."""
        assert "2025-04-17" in explicit_dates
        assert "Maundy" in explicit_dates["2025-04-17"]["name"]

    def test_maundy_thursday_2026(self, explicit_dates):
        """Easter - 3 days — April 2, 2026."""
        assert "2026-04-02" in explicit_dates

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
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXBOGChristmas:
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

class TestXBOGEarlyCloses:
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

class TestXBOGStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Colombia weekend is Saturday-Sunday."""
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

    def test_dates_within_generation_range(self, xbog, explicit_dates):
        start = date.fromisoformat(xbog["generation_range"][0])
        end = date.fromisoformat(xbog["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~90-105 entries: 18 holidays × 5 years."""
        assert 85 <= len(explicit_dates) <= 110, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "bvc.com.co" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBOGWeekendPattern:
    def test_saturday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 6, f"Sunday date: {date_str}"

    def test_monday_is_common_substitute(self, explicit_dates):
        """Many holidays are moved to Monday (Emiliani Law)."""
        monday_count = sum(1 for ds in explicit_dates if date.fromisoformat(ds).weekday() == 0)
        assert monday_count > 20, f"Expected many Monday holidays, got {monday_count}"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXBOGSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        """Many Colombian holidays use 'observed' in name."""
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count > 30, f"Expected many observed holidays, got {observed_count}"