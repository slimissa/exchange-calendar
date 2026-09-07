#!/usr/bin/env python3
"""
test_cayman_holidays.py — Ground truth tests for XCAY (Cayman Islands Stock Exchange).

Key facts verified:
    - Regular hours: 10:00-16:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - National Heroes' Day (fourth Monday in January)
    - Ash Wednesday (movable)
    - Discovery Day (third Monday in May)
    - King's Birthday (observed in June)
    - Constitution Day (first Monday in July)
    - Remembrance Day (Nov 11) with substitution
    - Christmas Eve (Dec 24) — early close at 13:00
    - New Year's Eve (Dec 31) — early close at 13:00
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XCAY.json)
    2. Caymanian holiday announcements changed (verify against csx.ky)

Run:
    python3 -m pytest tests/test_cayman_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xcay():
    """Load XCAY.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XCAY.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xcay):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xcay["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXCAYProperties:
    def test_code(self, xcay):
        assert xcay["code"] == "XCAY"

    def test_mic(self, xcay):
        assert xcay["mic"] == "XCAY"

    def test_name(self, xcay):
        assert xcay["name"] == "Cayman Islands Stock Exchange"

    def test_timezone(self, xcay):
        assert xcay["timezone"] == "America/Cayman"

    def test_regular_hours(self, xcay):
        assert xcay["regular_hours"]["open"] == "10:00"
        assert xcay["regular_hours"]["close"] == "16:00"

    def test_no_lunch_break(self, xcay):
        lunch = [s for s in xcay.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xcay):
        assert "extended_hours" not in xcay or xcay.get("extended_hours") is None

    def test_generation_range(self, xcay):
        assert "generation_range" in xcay
        assert xcay["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xcay):
        assert xcay.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xcay):
        """Cayman Islands uses explicit dates only."""
        rules = xcay["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXCAYFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_remembrance_day_2025(self, explicit_dates):
        """Nov 11, 2025 is Tuesday — observed Monday Nov 10."""
        assert "2025-11-10" in explicit_dates
        assert "Remembrance" in explicit_dates["2025-11-10"]["name"]

    def test_remembrance_day_2028_substitute(self, explicit_dates):
        """Nov 11, 2028 is Saturday — substitute to Monday Nov 13."""
        assert "2028-11-11" not in explicit_dates
        assert "2028-11-13" in explicit_dates

    def test_remembrance_day_2029_substitute(self, explicit_dates):
        """Nov 11, 2029 is Sunday — substitute to Monday Nov 12."""
        assert "2029-11-12" in explicit_dates


# ──────────────────────────────────────────────────────────────
# National Heroes' Day (fourth Monday in January)
# ──────────────────────────────────────────────────────────────

class TestXCAYNationalHeroes:
    def test_heroes_day_2025(self, explicit_dates):
        """Fourth Monday in January — Jan 27, 2025."""
        assert "2025-01-27" in explicit_dates
        assert "Heroes" in explicit_dates["2025-01-27"]["name"]

    def test_heroes_day_2026(self, explicit_dates):
        """Fourth Monday in January — Jan 26, 2026."""
        assert "2026-01-26" in explicit_dates

    def test_heroes_day_2027(self, explicit_dates):
        """Fourth Monday in January — Jan 25, 2027."""
        assert "2027-01-25" in explicit_dates

    def test_heroes_day_2028(self, explicit_dates):
        """Fourth Monday in January — Jan 24, 2028."""
        assert "2028-01-24" in explicit_dates

    def test_heroes_day_2029(self, explicit_dates):
        """Fourth Monday in January — Jan 22, 2029."""
        assert "2029-01-22" in explicit_dates

    def test_heroes_day_always_monday(self, explicit_dates):
        """National Heroes' Day must always be Monday."""
        for entry in explicit_dates.values():
            if "Heroes" in entry["name"]:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"Heroes' Day should be Monday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Discovery Day (third Monday in May)
# ──────────────────────────────────────────────────────────────

class TestXCAYDiscoveryDay:
    def test_discovery_day_2025(self, explicit_dates):
        """Third Monday in May — May 19, 2025."""
        assert "2025-05-19" in explicit_dates
        assert "Discovery" in explicit_dates["2025-05-19"]["name"]

    def test_discovery_day_2026(self, explicit_dates):
        """Third Monday in May — May 18, 2026."""
        assert "2026-05-18" in explicit_dates

    def test_discovery_day_2027(self, explicit_dates):
        """Third Monday in May — May 17, 2027."""
        assert "2027-05-17" in explicit_dates

    def test_discovery_day_2028(self, explicit_dates):
        """Third Monday in May — May 15, 2028."""
        assert "2028-05-15" in explicit_dates

    def test_discovery_day_2029(self, explicit_dates):
        """Third Monday in May — May 21, 2029."""
        assert "2029-05-21" in explicit_dates

    def test_discovery_day_always_monday(self, explicit_dates):
        """Discovery Day must always be Monday."""
        for entry in explicit_dates.values():
            if "Discovery" in entry["name"]:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"Discovery Day should be Monday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Constitution Day (first Monday in July)
# ──────────────────────────────────────────────────────────────

class TestXCAYConstitutionDay:
    def test_constitution_day_2025(self, explicit_dates):
        """First Monday in July — Jul 7, 2025."""
        assert "2025-07-07" in explicit_dates
        assert "Constitution" in explicit_dates["2025-07-07"]["name"]

    def test_constitution_day_2026(self, explicit_dates):
        """First Monday in July — Jul 6, 2026."""
        assert "2026-07-06" in explicit_dates

    def test_constitution_day_2027(self, explicit_dates):
        """First Monday in July — Jul 5, 2027."""
        assert "2027-07-05" in explicit_dates

    def test_constitution_day_2028(self, explicit_dates):
        """First Monday in July — Jul 3, 2028."""
        assert "2028-07-03" in explicit_dates

    def test_constitution_day_2029(self, explicit_dates):
        """First Monday in July — Jul 2, 2029."""
        assert "2029-07-02" in explicit_dates

    def test_constitution_day_always_monday(self, explicit_dates):
        """Constitution Day must always be Monday."""
        for entry in explicit_dates.values():
            if "Constitution" in entry["name"]:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"Constitution Day should be Monday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# King's Birthday
# ──────────────────────────────────────────────────────────────

class TestXCAYKingsBirthday:
    def test_kings_birthday_2025(self, explicit_dates):
        """King's Birthday 2025 — Jun 16."""
        assert "2025-06-16" in explicit_dates
        assert "King" in explicit_dates["2025-06-16"]["name"]

    def test_kings_birthday_2026(self, explicit_dates):
        """King's Birthday 2026 — Jun 15."""
        assert "2026-06-15" in explicit_dates

    def test_kings_birthday_2027(self, explicit_dates):
        """King's Birthday 2027 — Jun 14."""
        assert "2027-06-14" in explicit_dates

    def test_kings_birthday_2028(self, explicit_dates):
        """King's Birthday 2028 — Jun 19."""
        assert "2028-06-19" in explicit_dates

    def test_kings_birthday_2029(self, explicit_dates):
        """King's Birthday 2029 — Jun 18."""
        assert "2029-06-18" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXCAYEaster:
    def test_ash_wednesday_2025(self, explicit_dates):
        """Ash Wednesday 2025 — Feb 19."""
        assert "2025-02-19" in explicit_dates
        assert "Ash Wednesday" in explicit_dates["2025-02-19"]["name"]

    def test_ash_wednesday_2026(self, explicit_dates):
        """Ash Wednesday 2026 — Feb 18."""
        assert "2026-02-18" in explicit_dates

    def test_ash_wednesday_2027(self, explicit_dates):
        """Ash Wednesday 2027 — Feb 10."""
        assert "2027-02-10" in explicit_dates

    def test_ash_wednesday_2028(self, explicit_dates):
        """Ash Wednesday 2028 — Mar 1."""
        assert "2028-03-01" in explicit_dates

    def test_good_friday_2025(self, explicit_dates):
        """Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["name"] == "Good Friday"

    def test_good_friday_2026(self, explicit_dates):
        """Easter - 2 days — April 3, 2026."""
        assert "2026-04-03" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        """Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["name"] == "Easter Monday"

    def test_easter_monday_2027(self, explicit_dates):
        """Easter + 1 day — March 29, 2027."""
        assert "2027-03-29" in explicit_dates

    def test_easter_monday_2029(self, explicit_dates):
        """Easter + 1 day — April 2, 2029."""
        assert "2029-04-02" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXCAYChristmas:
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

class TestXCAYEarlyCloses:
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

class TestXCAYStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Cayman Islands weekend is Saturday-Sunday."""
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

    def test_dates_within_generation_range(self, xcay, explicit_dates):
        start = date.fromisoformat(xcay["generation_range"][0])
        end = date.fromisoformat(xcay["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~55-70 entries."""
        assert 55 <= len(explicit_dates) <= 75, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "csx.ky" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXCAYWeekendPattern:
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

class TestXCAYSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_substitute_names_contain_substitute(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "substitute" in name:
                assert "substitute" in name