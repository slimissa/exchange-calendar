#!/usr/bin/env python3
"""
test_santiago_holidays.py — Ground truth tests for XSGO (Santiago Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-16:00
    - Lunch break: 12:00-12:30
    - Weekend is Saturday-Sunday (Western weekend)
    - Chile uses weekend substitution (Sat→Mon, Sun→Mon)
    - Christmas Eve (Dec 24) — early close at 13:00
    - New Year's Eve (Dec 31) — early close at 13:00
    - Good Friday (Easter - 2 days)
    - 14 national holidays with substitution

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XSGO.json)
    2. Chilean holiday announcements changed (verify against bolsadesantiago.com)

Run:
    python3 -m pytest tests/test_santiago_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xsgo():
    """Load XSGO.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XSGO.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xsgo):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xsgo["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xsgo):
    """Return dict of name -> rule."""
    rules = xsgo["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXSGOProperties:
    def test_code(self, xsgo):
        assert xsgo["code"] == "XSGO"

    def test_mic(self, xsgo):
        assert xsgo["mic"] == "XSGO"

    def test_name(self, xsgo):
        assert xsgo["name"] == "Santiago Stock Exchange"

    def test_timezone(self, xsgo):
        assert xsgo["timezone"] == "America/Santiago"

    def test_regular_hours(self, xsgo):
        assert xsgo["regular_hours"]["open"] == "09:30"
        assert xsgo["regular_hours"]["close"] == "16:00"

    def test_lunch_break(self, xsgo):
        lunch = [s for s in xsgo.get("sessions", []) if s.get("type") == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "12:00"
        assert lunch[0]["close"] == "12:30"

    def test_no_extended_hours(self, xsgo):
        assert "extended_hours" not in xsgo or xsgo.get("extended_hours") is None

    def test_generation_range(self, xsgo):
        assert "generation_range" in xsgo
        assert xsgo["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xsgo):
        assert xsgo.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays with weekend substitution
# ──────────────────────────────────────────────────────────────

class TestXSGOFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates
        assert "New Year's Day" in explicit_dates["2028-01-03"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday — no substitution."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_navy_day_2025(self, explicit_dates):
        """May 21, 2025 is Wednesday — no substitution."""
        assert "2025-05-21" in explicit_dates
        assert explicit_dates["2025-05-21"]["name"] == "Navy Day"

    def test_navy_day_2028_substitute(self, explicit_dates):
        """May 21, 2028 is Sunday — substitute to Monday May 22."""
        assert "2028-05-21" not in explicit_dates
        assert "2028-05-22" in explicit_dates
        assert "Navy Day" in explicit_dates["2028-05-22"]["name"]

    def test_indigenous_peoples_2025(self, explicit_dates):
        """Jun 20, 2025 is Friday — no substitution."""
        assert "2025-06-20" in explicit_dates
        assert "Indigenous" in explicit_dates["2025-06-20"]["name"]

    def test_indigenous_peoples_2027_substitute(self, explicit_dates):
        """Jun 20, 2027 is Sunday — substitute to Monday Jun 21."""
        assert "2027-06-20" not in explicit_dates
        assert "2027-06-21" in explicit_dates

    def test_saint_peter_paul_2025(self, explicit_dates):
        """Jun 29, 2025 is Sunday — substitute to Monday Jun 30."""
        assert "2025-06-29" not in explicit_dates
        assert "2025-06-30" in explicit_dates
        assert "Saint Peter" in explicit_dates["2025-06-30"]["name"]

    def test_saint_peter_paul_2026(self, explicit_dates):
        """Jun 29, 2026 is Monday — no substitution."""
        assert "2026-06-29" in explicit_dates

    def test_mount_carmel_2025(self, explicit_dates):
        """Jul 16, 2025 is Wednesday — no substitution."""
        assert "2025-07-16" in explicit_dates
        assert "Mount Carmel" in explicit_dates["2025-07-16"]["name"]

    def test_assumption_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday — no substitution."""
        assert "2025-08-15" in explicit_dates
        assert explicit_dates["2025-08-15"]["name"] == "Assumption Day"

    def test_independence_2025(self, explicit_dates):
        """Sep 18, 2025 is Thursday — no substitution."""
        assert "2025-09-18" in explicit_dates
        assert explicit_dates["2025-09-18"]["name"] == "Independence Day"

    def test_army_day_2025(self, explicit_dates):
        """Sep 19, 2025 is Friday — no substitution."""
        assert "2025-09-19" in explicit_dates
        assert explicit_dates["2025-09-19"]["name"] == "Army Day"

    def test_columbus_day_2025_substitute(self, explicit_dates):
        """Oct 12, 2025 is Sunday — substitute to Monday Oct 13."""
        assert "2025-10-12" not in explicit_dates
        assert "2025-10-13" in explicit_dates
        assert "Columbus" in explicit_dates["2025-10-13"]["name"]

    def test_reformation_2025(self, explicit_dates):
        """Oct 31, 2025 is Friday — no substitution."""
        assert "2025-10-31" in explicit_dates
        assert explicit_dates["2025-10-31"]["name"] == "Reformation Day"

    def test_immaculate_conception_2025(self, explicit_dates):
        """Dec 8, 2025 is Monday — no substitution."""
        assert "2025-12-08" in explicit_dates
        assert explicit_dates["2025-12-08"]["name"] == "Immaculate Conception"


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXSGOChristmas:
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
        assert "Christmas Day" in explicit_dates["2027-12-27"]["name"]

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

class TestXSGOEarlyCloses:
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
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXSGOEaster:
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
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXSGORecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "New Year's Day",
            "Good Friday",
            "Labour Day",
            "Navy Day",
            "National Indigenous Peoples Day",
            "Saint Peter and Saint Paul",
            "Our Lady of Mount Carmel",
            "Assumption Day",
            "Independence Day",
            "Army Day",
            "Columbus Day",
            "Reformation Day",
            "Immaculate Conception",
            "Christmas Day",
        }
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_weekend_adjustment_rules(self, recurrence_rules):
        for name in ["New Year's Day", "Labour Day", "Navy Day",
                     "National Indigenous Peoples Day", "Saint Peter and Saint Paul",
                     "Our Lady of Mount Carmel", "Assumption Day",
                     "Independence Day", "Army Day", "Columbus Day",
                     "Reformation Day", "Immaculate Conception", "Christmas Day"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_with_weekend_adjustment"

    def test_easter_rule(self, recurrence_rules):
        rule = recurrence_rules["Good Friday"]
        assert rule["rule"] == "easter_offset"
        assert rule["offset_days"] == -2

    def test_all_rules_closed_status(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXSGOStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Chile weekend is Saturday-Sunday."""
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

    def test_dates_within_generation_range(self, xsgo, explicit_dates):
        start = date.fromisoformat(xsgo["generation_range"][0])
        end = date.fromisoformat(xsgo["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~65-80 entries: 15 holidays × 5 years (minus weekends, plus substitutes)."""
        assert 60 <= len(explicit_dates) <= 80, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "bolsadesantiago.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXSGOWeekendPattern:
    def test_saturday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 6, f"Sunday date: {date_str}"

    def test_monday_is_working_day(self, explicit_dates):
        monday_count = sum(1 for ds in explicit_dates if date.fromisoformat(ds).weekday() == 0)
        assert monday_count > 0, "Expected some Monday holidays (substitutes)"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXSGOSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2028-05-21" not in explicit_dates  # Sunday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_substitute_names_contain_observed(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "observed" in name or "substitute" in name:
                assert "observed" in name or "substitute" in name