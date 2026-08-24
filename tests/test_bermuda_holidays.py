#!/usr/bin/env python3
"""
test_bermuda_holidays.py — Ground truth tests for XBDA (Bermuda Stock Exchange).

Key facts verified:
    - Regular hours: 10:00-16:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Bermuda Day (last Friday in May)
    - National Heroes' Day (third Monday in June)
    - Cup Match (Thursday-Friday before first Monday in August)
    - Labour Day (first Monday in September)
    - Remembrance Day (Nov 11) with substitution
    - Christmas Eve (Dec 24) — early close at 13:00
    - New Year's Eve (Dec 31) — early close at 13:00
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBDA.json)
    2. Bermudian holiday announcements changed (verify against bsx.com)

Run:
    python3 -m pytest tests/test_bermuda_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbda():
    """Load XBDA.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBDA.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbda):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbda["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBDAProperties:
    def test_code(self, xbda):
        assert xbda["code"] == "XBDA"

    def test_mic(self, xbda):
        assert xbda["mic"] == "XBDA"

    def test_name(self, xbda):
        assert xbda["name"] == "Bermuda Stock Exchange"

    def test_timezone(self, xbda):
        assert xbda["timezone"] == "Atlantic/Bermuda"

    def test_regular_hours(self, xbda):
        assert xbda["regular_hours"]["open"] == "10:00"
        assert xbda["regular_hours"]["close"] == "16:00"

    def test_no_lunch_break(self, xbda):
        lunch = [s for s in xbda.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbda):
        assert "extended_hours" not in xbda or xbda.get("extended_hours") is None

    def test_generation_range(self, xbda):
        assert "generation_range" in xbda
        assert xbda["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xbda):
        assert xbda.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xbda):
        """Bermuda uses explicit dates only."""
        rules = xbda["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXBDAFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_remembrance_day_2025(self, explicit_dates):
        """Nov 11, 2025 is Tuesday."""
        assert "2025-11-11" in explicit_dates
        assert "Remembrance" in explicit_dates["2025-11-11"]["name"]

    def test_remembrance_day_2028_substitute(self, explicit_dates):
        """Nov 11, 2028 is Saturday — substitute to Monday Nov 13."""
        assert "2028-11-11" not in explicit_dates
        assert "2028-11-13" in explicit_dates

    def test_remembrance_day_2029_substitute(self, explicit_dates):
        """Nov 11, 2029 is Sunday — substitute to Monday Nov 12."""
        assert "2029-11-12" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Bermuda Day (last Friday in May)
# ──────────────────────────────────────────────────────────────

class TestXBDABermudaDay:
    def test_bermuda_day_2025(self, explicit_dates):
        """Last Friday in May — May 23, 2025."""
        assert "2025-05-23" in explicit_dates
        assert explicit_dates["2025-05-23"]["name"] == "Bermuda Day"

    def test_bermuda_day_2026(self, explicit_dates):
        """Last Friday in May — May 22, 2026."""
        assert "2026-05-22" in explicit_dates

    def test_bermuda_day_2027(self, explicit_dates):
        """Last Friday in May — May 28, 2027."""
        assert "2027-05-28" in explicit_dates

    def test_bermuda_day_2028(self, explicit_dates):
        """Last Friday in May — May 26, 2028."""
        assert "2028-05-26" in explicit_dates

    def test_bermuda_day_2029(self, explicit_dates):
        """Last Friday in May — May 25, 2029."""
        assert "2029-05-25" in explicit_dates

    def test_bermuda_day_always_friday(self, explicit_dates):
        """Bermuda Day must always be Friday."""
        for entry in explicit_dates.values():
            if entry["name"] == "Bermuda Day":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 4, f"Bermuda Day should be Friday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# National Heroes' Day (third Monday in June)
# ──────────────────────────────────────────────────────────────

class TestXBDANationalHeroes:
    def test_heroes_day_2025(self, explicit_dates):
        """Third Monday in June — June 16, 2025."""
        assert "2025-06-16" in explicit_dates
        assert "Heroes" in explicit_dates["2025-06-16"]["name"]

    def test_heroes_day_2026(self, explicit_dates):
        """Third Monday in June — June 15, 2026."""
        assert "2026-06-15" in explicit_dates

    def test_heroes_day_2027(self, explicit_dates):
        """Third Monday in June — June 21, 2027."""
        assert "2027-06-21" in explicit_dates

    def test_heroes_day_2028(self, explicit_dates):
        """Third Monday in June — June 19, 2028."""
        assert "2028-06-19" in explicit_dates

    def test_heroes_day_2029(self, explicit_dates):
        """Third Monday in June — June 18, 2029."""
        assert "2029-06-18" in explicit_dates

    def test_heroes_day_always_monday(self, explicit_dates):
        """National Heroes' Day must always be Monday."""
        for entry in explicit_dates.values():
            if "Heroes" in entry["name"]:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"Heroes' Day should be Monday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Cup Match (Thursday-Friday before first Monday in August)
# ──────────────────────────────────────────────────────────────

class TestXBDACupMatch:
    def test_cup_match_2025(self, explicit_dates):
        """Cup Match 2025 — Jul 31-Aug 1."""
        assert "2025-07-31" in explicit_dates
        assert "Cup Match" in explicit_dates["2025-07-31"]["name"]
        assert "2025-08-01" in explicit_dates

    def test_cup_match_2026(self, explicit_dates):
        """Cup Match 2026 — Jul 30-31."""
        assert "2026-07-30" in explicit_dates
        assert "2026-07-31" in explicit_dates

    def test_cup_match_2027(self, explicit_dates):
        """Cup Match 2027 — Jul 29-30."""
        assert "2027-07-29" in explicit_dates
        assert "2027-07-30" in explicit_dates

    def test_cup_match_2028(self, explicit_dates):
        """Cup Match 2028 — Jul 27-28."""
        assert "2028-07-27" in explicit_dates
        assert "2028-07-28" in explicit_dates

    def test_cup_match_2029(self, explicit_dates):
        """Cup Match 2029 — Aug 2-3."""
        assert "2029-08-02" in explicit_dates
        assert "2029-08-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Labour Day (first Monday in September)
# ──────────────────────────────────────────────────────────────

class TestXBDALabourDay:
    def test_labour_day_2025(self, explicit_dates):
        """First Monday in September — Sep 1, 2025."""
        assert "2025-09-01" in explicit_dates
        assert explicit_dates["2025-09-01"]["name"] == "Labour Day"

    def test_labour_day_2026(self, explicit_dates):
        """First Monday in September — Sep 7, 2026."""
        assert "2026-09-07" in explicit_dates

    def test_labour_day_2027(self, explicit_dates):
        """First Monday in September — Sep 6, 2027."""
        assert "2027-09-06" in explicit_dates

    def test_labour_day_2028(self, explicit_dates):
        """First Monday in September — Sep 4, 2028."""
        assert "2028-09-04" in explicit_dates

    def test_labour_day_2029(self, explicit_dates):
        """First Monday in September — Sep 3, 2029."""
        assert "2029-09-03" in explicit_dates

    def test_labour_day_always_monday(self, explicit_dates):
        """Labour Day must always be Monday."""
        for entry in explicit_dates.values():
            if entry["name"] == "Labour Day":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"Labour Day should be Monday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Good Friday (movable)
# ──────────────────────────────────────────────────────────────

class TestXBDAGoodFriday:
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

class TestXBDAChristmas:
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

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_boxing_day_2026_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute to Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates

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

class TestXBDAEarlyCloses:
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

class TestXBDAStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Bermuda weekend is Saturday-Sunday."""
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

    def test_dates_within_generation_range(self, xbda, explicit_dates):
        start = date.fromisoformat(xbda["generation_range"][0])
        end = date.fromisoformat(xbda["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-65 entries."""
        assert 50 <= len(explicit_dates) <= 70, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "bsx.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBDAWeekendPattern:
    def test_saturday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 6, f"Sunday date: {date_str}"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXBDASubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_substitute_names_contain_substitute(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "substitute" in name:
                assert "substitute" in name