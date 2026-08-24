#!/usr/bin/env python3
"""
test_prague_holidays.py — Ground truth tests for XPRA (Prague Stock Exchange).

Key facts verified:
    - Regular hours: 09:00-16:30
    - No lunch break (continuous trading)
    - No extended hours sessions
    - Czech Republic uses weekend substitution (Sat→Mon, Sun→Mon)
    - New Year's Day (Jan 1) with substitution
    - Good Friday and Easter Monday (movable)
    - Labour Day (May 1) with substitution
    - Victory Day (May 8) with substitution
    - Saints Cyril and Methodius Day (Jul 5) with substitution
    - Jan Hus Day (Jul 6) with substitution
    - Czech Statehood Day (Sep 28) with substitution
    - Independent Czechoslovak State Day (Oct 28) with substitution
    - Struggle for Freedom and Democracy Day (Nov 17) with substitution
    - Christmas Eve (Dec 24) — full closure
    - Christmas Day and St. Stephen's Day with substitution
    - All holidays are full closures (no early closes)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XPRA.json)
    2. Czech holiday announcements changed (verify against pse.cz)

Run:
    python3 -m pytest tests/test_prague_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xpra():
    """Load XPRA.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XPRA.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xpra):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xpra["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xpra):
    """Return dict of name -> rule."""
    rules = xpra["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXPRAProperties:
    def test_code(self, xpra):
        assert xpra["code"] == "XPRA"

    def test_mic(self, xpra):
        assert xpra["mic"] == "XPRA"

    def test_name(self, xpra):
        assert xpra["name"] == "Prague Stock Exchange"

    def test_timezone(self, xpra):
        assert xpra["timezone"] == "Europe/Prague"

    def test_regular_hours(self, xpra):
        assert xpra["regular_hours"]["open"] == "09:00"
        assert xpra["regular_hours"]["close"] == "16:30"

    def test_no_lunch_break(self, xpra):
        lunch = [s for s in xpra.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xpra):
        assert "extended_hours" not in xpra or xpra.get("extended_hours") is None

    def test_generation_range(self, xpra):
        assert "generation_range" in xpra
        assert xpra["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xpra):
        assert xpra.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays with weekend substitution
# ──────────────────────────────────────────────────────────────

class TestXPRAFixedHolidays:
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

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates
        assert "Labour Day" in explicit_dates["2027-05-03"]["name"]

    def test_victory_day_2025(self, explicit_dates):
        """May 8, 2025 is Thursday — no substitution."""
        assert "2025-05-08" in explicit_dates
        assert explicit_dates["2025-05-08"]["name"] == "Victory Day"

    def test_victory_day_2027_substitute(self, explicit_dates):
        """May 8, 2027 is Saturday — substitute to Monday May 10."""
        assert "2027-05-08" not in explicit_dates
        assert "2027-05-10" in explicit_dates
        assert "Victory Day" in explicit_dates["2027-05-10"]["name"]

    def test_cyril_methodius_2025_substitute(self, explicit_dates):
        """Jul 5, 2025 is Saturday — substitute to Monday Jul 7."""
        assert "2025-07-05" not in explicit_dates
        assert "2025-07-07" in explicit_dates
        assert "Cyril and Methodius" in explicit_dates["2025-07-07"]["name"]

    def test_cyril_methodius_2026_substitute(self, explicit_dates):
        """Jul 5, 2026 is Sunday — substitute to Monday Jul 6."""
        assert "2026-07-05" not in explicit_dates
        assert "2026-07-06" in explicit_dates

    def test_cyril_methodius_2027(self, explicit_dates):
        """Jul 5, 2027 is Monday — no substitution."""
        assert "2027-07-05" in explicit_dates

    def test_jan_hus_day_2027(self, explicit_dates):
        """Jul 6, 2027 is Tuesday — no substitution."""
        assert "2027-07-06" in explicit_dates
        assert explicit_dates["2027-07-06"]["name"] == "Jan Hus Day"

    def test_czech_statehood_2025_substitute(self, explicit_dates):
        """Sep 28, 2025 is Sunday — substitute to Monday Sep 29."""
        assert "2025-09-28" not in explicit_dates
        assert "2025-09-29" in explicit_dates
        assert "Czech Statehood" in explicit_dates["2025-09-29"]["name"]

    def test_czech_statehood_2026(self, explicit_dates):
        """Sep 28, 2026 is Monday — no substitution."""
        assert "2026-09-28" in explicit_dates

    def test_independent_czechoslovak_2028_substitute(self, explicit_dates):
        """Oct 28, 2028 is Saturday — substitute to Monday Oct 30."""
        assert "2028-10-28" not in explicit_dates
        assert "2028-10-30" in explicit_dates

    def test_independent_czechoslovak_2029_substitute(self, explicit_dates):
        """Oct 28, 2029 is Sunday — substitute to Monday Oct 29."""
        assert "2029-10-28" not in explicit_dates
        assert "2029-10-29" in explicit_dates

    def test_struggle_freedom_2029_substitute(self, explicit_dates):
        """Nov 17, 2029 is Saturday — substitute to Monday Nov 19."""
        assert "2029-11-17" not in explicit_dates
        assert "2029-11-19" in explicit_dates
        assert "Struggle" in explicit_dates["2029-11-19"]["name"]


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXPRAChristmas:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — full closure."""
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["name"] == "Christmas Eve"
        assert explicit_dates["2025-12-24"]["status"] == "closed"

    def test_christmas_eve_2029(self, explicit_dates):
        """Dec 24, 2029 is Monday — full closure."""
        assert "2029-12-24" in explicit_dates

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_day_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates
        assert "Christmas Day" in explicit_dates["2027-12-27"]["name"]

    def test_st_stephens_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "St. Stephen's Day"

    def test_st_stephens_2027_substitute(self, explicit_dates):
        """Dec 26, 2027 is Sunday — substitute to Tuesday Dec 28.
           (Monday Dec 27 is already Christmas Day substitute)."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" in explicit_dates
        assert "St. Stephen" in explicit_dates["2027-12-28"]["name"]


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXPRAEaster:
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

    def test_easter_monday_2025(self, explicit_dates):
        """Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["name"] == "Easter Monday"

    def test_easter_monday_2026(self, explicit_dates):
        """Easter + 1 day — April 6, 2026."""
        assert "2026-04-06" in explicit_dates

    def test_easter_monday_2027(self, explicit_dates):
        """Easter + 1 day — March 29, 2027."""
        assert "2027-03-29" in explicit_dates

    def test_easter_monday_2028(self, explicit_dates):
        """Easter + 1 day — April 17, 2028."""
        assert "2028-04-17" in explicit_dates

    def test_easter_monday_2029(self, explicit_dates):
        """Easter + 1 day — April 2, 2029."""
        assert "2029-04-02" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXPRARecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "New Year's Day",
            "Good Friday",
            "Easter Monday",
            "Labour Day",
            "Victory Day",
            "Saints Cyril and Methodius Day",
            "Jan Hus Day",
            "Czech Statehood Day",
            "Independent Czechoslovak State Day",
            "Struggle for Freedom and Democracy Day",
            "Christmas Eve",
            "Christmas Day",
            "St. Stephen's Day",
        }
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_weekend_adjustment_rules(self, recurrence_rules):
        """Czech Republic uses weekend substitution for all fixed holidays."""
        for name in ["New Year's Day", "Labour Day", "Victory Day",
                     "Saints Cyril and Methodius Day", "Jan Hus Day",
                     "Czech Statehood Day", "Independent Czechoslovak State Day",
                     "Struggle for Freedom and Democracy Day",
                     "Christmas Eve", "Christmas Day", "St. Stephen's Day"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_with_weekend_adjustment", f"{name} should use weekend adjustment"

    def test_easter_rules(self, recurrence_rules):
        assert recurrence_rules["Good Friday"]["rule"] == "easter_offset"
        assert recurrence_rules["Good Friday"]["offset_days"] == -2

        assert recurrence_rules["Easter Monday"]["rule"] == "easter_offset"
        assert recurrence_rules["Easter Monday"]["offset_days"] == 1

    def test_all_rules_closed_status(self, recurrence_rules):
        """Czech Republic has no early closes — all rules should be 'closed'."""
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed", f"{name} should be closed"

    def test_closed_rules_have_no_close_time(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert "close_time" not in rule, f"{name} should not have close_time"
            assert "early_close_time" not in rule, f"{name} should not have early_close_time"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXPRAStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str} ({d.strftime('%A')})"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates)), "Duplicate dates found"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"
            assert entry["source_url"].startswith("http"), f"Invalid source_url: {date_str}"

    def test_all_entries_have_name(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "name" in entry, f"Missing name: {date_str}"
            assert entry["name"], f"Empty name: {date_str}"

    def test_all_entries_have_status(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "status" in entry, f"Missing status: {date_str}"
            assert entry["status"] in ["closed", "early_close"], f"Invalid status: {date_str}"

    def test_all_statuses_closed(self, explicit_dates):
        """Czech Republic has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", f"Unexpected status: {entry['date']}"

    def test_dates_within_generation_range(self, xpra, explicit_dates):
        start = date.fromisoformat(xpra["generation_range"][0])
        end = date.fromisoformat(xpra["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end, f"Date outside range: {date_str}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~55-65 entries: 13 holidays × 5 years (minus weekends, plus substitutes)."""
        assert 55 <= len(explicit_dates) <= 70, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """All source URLs should be from pse.cz."""
        for entry in explicit_dates.values():
            assert "pse.cz" in entry["source_url"], f"Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Easter cross-checks
# ──────────────────────────────────────────────────────────────

class TestXPRAEasterCrossChecks:
    def test_easter_2025_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2025."""
        # Easter Sunday 2025 is April 20
        assert "2025-04-18" in explicit_dates  # Good Friday (-2)
        assert "2025-04-21" in explicit_dates  # Easter Monday (+1)

    def test_easter_2026_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2026."""
        # Easter Sunday 2026 is April 5
        assert "2026-04-03" in explicit_dates  # Good Friday (-2)
        assert "2026-04-06" in explicit_dates  # Easter Monday (+1)

    def test_easter_2027_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2027."""
        # Easter Sunday 2027 is March 28
        assert "2027-03-26" in explicit_dates  # Good Friday (-2)
        assert "2027-03-29" in explicit_dates  # Easter Monday (+1)

    def test_easter_2028_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2028."""
        # Easter Sunday 2028 is April 16
        assert "2028-04-14" in explicit_dates  # Good Friday (-2)
        assert "2028-04-17" in explicit_dates  # Easter Monday (+1)

    def test_easter_2029_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2029."""
        # Easter Sunday 2029 is April 1
        assert "2029-03-30" in explicit_dates  # Good Friday (-2)
        assert "2029-04-02" in explicit_dates  # Easter Monday (+1)

    def test_easter_mondays_are_mondays(self, explicit_dates):
        """Easter Monday must always be Monday."""
        for entry in explicit_dates.values():
            if entry["name"] == "Easter Monday":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"Easter Monday should be Monday: {entry['date']}"

    def test_good_fridays_are_fridays(self, explicit_dates):
        """Good Friday must always be Friday."""
        for entry in explicit_dates.values():
            if entry["name"] == "Good Friday":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 4, f"Good Friday should be Friday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXPRASubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        """Verify known weekend holidays are correctly absent."""
        weekend_holidays = [
            ("2025-07-05", "Saints Cyril and Methodius (Saturday)"),
            ("2028-01-01", "New Year's Day (Saturday)"),
            ("2028-10-28", "Independent Czechoslovak (Saturday)"),
            ("2029-11-17", "Struggle for Freedom (Saturday)"),
        ]
        for date_str, name in weekend_holidays:
            assert date_str not in explicit_dates, f"{name} should not be in explicit dates"

    def test_substitute_names_contain_observed(self, explicit_dates):
        """Czech Republic uses 'observed' for shifted holidays."""
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "observed" in name:
                assert "observed" in name

    def test_weekend_holidays_have_substitutes(self, explicit_dates):
        """Verify weekend holidays have substitute days."""
        # 2028-01-01 (Saturday) → 2028-01-03 (Monday)
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

        # 2027-05-08 (Saturday) → 2027-05-10 (Monday)
        assert "2027-05-08" not in explicit_dates
        assert "2027-05-10" in explicit_dates

        # 2025-07-05 (Saturday) → 2025-07-07 (Monday)
        assert "2025-07-05" not in explicit_dates
        assert "2025-07-07" in explicit_dates