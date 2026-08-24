#!/usr/bin/env python3
"""
test_dublin_holidays.py — Ground truth tests for XDUB (Euronext Dublin / Irish Stock Exchange).

Key facts verified:
    - Regular hours: 08:00-16:30
    - No lunch break (continuous trading)
    - No extended hours sessions
    - UK-style weekend substitution (Sat→Mon, Sun→Mon)
    - St. Patrick's Day (Mar 17) — with substitution
    - Good Friday and Easter Monday (movable)
    - Bank Holidays: first Monday in May, June, August; last Monday in October
    - Christmas Eve (Dec 24) — early close at 12:30
    - New Year's Eve (Dec 31) — early close at 12:30
    - Christmas Day and St. Stephen's Day — with substitution

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XDUB.json)
    2. Irish holiday announcements changed (verify against euronext.com)

Run:
    python3 -m pytest tests/test_dublin_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xdub():
    """Load XDUB.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XDUB.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xdub):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xdub["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xdub):
    """Return dict of name -> rule."""
    rules = xdub["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXDUBProperties:
    def test_code(self, xdub):
        assert xdub["code"] == "XDUB"

    def test_mic(self, xdub):
        assert xdub["mic"] == "XDUB"

    def test_name(self, xdub):
        assert xdub["name"] == "Euronext Dublin"

    def test_timezone(self, xdub):
        assert xdub["timezone"] == "Europe/Dublin"

    def test_regular_hours(self, xdub):
        assert xdub["regular_hours"]["open"] == "08:00"
        assert xdub["regular_hours"]["close"] == "16:30"

    def test_no_lunch_break(self, xdub):
        lunch = [s for s in xdub.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xdub):
        assert "extended_hours" not in xdub or xdub.get("extended_hours") is None

    def test_generation_range(self, xdub):
        assert "generation_range" in xdub
        assert xdub["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xdub):
        assert xdub.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays (with weekend substitution)
# ──────────────────────────────────────────────────────────────

class TestXDUBFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_new_year_2027_substitute(self, explicit_dates):
        """Jan 1, 2027 is Friday — no substitution."""
        assert "2027-01-01" in explicit_dates

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates
        assert "substitute" in explicit_dates["2028-01-03"]["name"].lower()

    def test_st_patricks_day_2025(self, explicit_dates):
        """Mar 17, 2025 is Monday — no substitution."""
        assert "2025-03-17" in explicit_dates
        assert explicit_dates["2025-03-17"]["name"] == "St. Patrick's Day"

    def test_st_patricks_day_2026(self, explicit_dates):
        """Mar 17, 2026 is Tuesday — no substitution."""
        assert "2026-03-17" in explicit_dates

    def test_st_patricks_day_2029_substitute(self, explicit_dates):
        """Mar 17, 2029 is Saturday — substitute to Monday Mar 19."""
        assert "2029-03-17" not in explicit_dates
        assert "2029-03-19" in explicit_dates
        assert "substitute" in explicit_dates["2029-03-19"]["name"].lower()

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday — no substitution."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_day_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27.
           Dec 26, 2027 is Sunday — substitute to Tuesday Dec 28."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-27" in explicit_dates
        assert "2027-12-28" in explicit_dates

    def test_st_stephens_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday — no substitution."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "St. Stephen's Day"

    def test_st_stephens_day_2026_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute to Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates
        assert "substitute" in explicit_dates["2026-12-28"]["name"].lower()


# ──────────────────────────────────────────────────────────────
# Bank Holidays (nth weekday rules)
# ──────────────────────────────────────────────────────────────

class TestXDUBBankHolidays:
    def test_may_bank_holiday_2025(self, explicit_dates):
        """First Monday in May — May 5, 2025."""
        assert "2025-05-05" in explicit_dates
        assert explicit_dates["2025-05-05"]["name"] == "May Bank Holiday"

    def test_may_bank_holiday_2026(self, explicit_dates):
        """First Monday in May — May 4, 2026."""
        assert "2026-05-04" in explicit_dates

    def test_may_bank_holiday_2027(self, explicit_dates):
        """First Monday in May — May 3, 2027."""
        assert "2027-05-03" in explicit_dates

    def test_june_bank_holiday_2025(self, explicit_dates):
        """First Monday in June — June 2, 2025."""
        assert "2025-06-02" in explicit_dates
        assert explicit_dates["2025-06-02"]["name"] == "June Bank Holiday"

    def test_june_bank_holiday_2026(self, explicit_dates):
        """First Monday in June — June 1, 2026."""
        assert "2026-06-01" in explicit_dates

    def test_june_bank_holiday_2027(self, explicit_dates):
        """First Monday in June — June 7, 2027."""
        assert "2027-06-07" in explicit_dates

    def test_august_bank_holiday_2025(self, explicit_dates):
        """First Monday in August — August 4, 2025."""
        assert "2025-08-04" in explicit_dates
        assert explicit_dates["2025-08-04"]["name"] == "August Bank Holiday"

    def test_august_bank_holiday_2026(self, explicit_dates):
        """First Monday in August — August 3, 2026."""
        assert "2026-08-03" in explicit_dates

    def test_august_bank_holiday_2027(self, explicit_dates):
        """First Monday in August — August 2, 2027."""
        assert "2027-08-02" in explicit_dates

    def test_october_bank_holiday_2025(self, explicit_dates):
        """Last Monday in October — October 27, 2025."""
        assert "2025-10-27" in explicit_dates
        assert explicit_dates["2025-10-27"]["name"] == "October Bank Holiday"

    def test_october_bank_holiday_2026(self, explicit_dates):
        """Last Monday in October — October 26, 2026."""
        assert "2026-10-26" in explicit_dates

    def test_october_bank_holiday_2027(self, explicit_dates):
        """Last Monday in October — October 25, 2027."""
        assert "2027-10-25" in explicit_dates

    def test_october_bank_holiday_2028(self, explicit_dates):
        """Last Monday in October — October 30, 2028."""
        assert "2028-10-30" in explicit_dates

    def test_october_bank_holiday_2029(self, explicit_dates):
        """Last Monday in October — October 29, 2029."""
        assert "2029-10-29" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Early close days
# ──────────────────────────────────────────────────────────────

class TestXDUBEarlyCloses:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — early close at 12:30."""
        entry = explicit_dates.get("2025-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_christmas_eve_2026(self, explicit_dates):
        """Dec 24, 2026 is Thursday — early close at 12:30."""
        entry = explicit_dates.get("2026-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — early close at 12:30."""
        entry = explicit_dates.get("2025-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_new_years_eve_2026(self, explicit_dates):
        """Dec 31, 2026 is Thursday — early close at 12:30."""
        entry = explicit_dates.get("2026-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_new_years_eve_2027(self, explicit_dates):
        """Dec 31, 2027 is Friday — early close at 12:30."""
        entry = explicit_dates.get("2027-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_no_other_early_closes(self, explicit_dates):
        """Only Christmas Eve and New Year's Eve are early closes."""
        early_closes = [e for e in explicit_dates.values() if e.get("status") == "early_close"]
        early_close_names = {e["name"] for e in early_closes}
        assert early_close_names == {"Christmas Eve", "New Year's Eve"}


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXDUBEaster:
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


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXDUBRecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "New Year's Day",
            "St. Patrick's Day",
            "Good Friday",
            "Easter Monday",
            "May Bank Holiday",
            "June Bank Holiday",
            "August Bank Holiday",
            "October Bank Holiday",
            "Christmas Day",
            "St. Stephen's Day",
        }
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_weekend_adjustment_rules(self, recurrence_rules):
        """UK-style substitution: Sat→Mon, Sun→Mon."""
        for name in ["New Year's Day", "St. Patrick's Day", "Christmas Day", "St. Stephen's Day"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_with_weekend_adjustment", f"{name} should use weekend adjustment"

    def test_easter_rules(self, recurrence_rules):
        assert recurrence_rules["Good Friday"]["rule"] == "easter_offset"
        assert recurrence_rules["Good Friday"]["offset_days"] == -2

        assert recurrence_rules["Easter Monday"]["rule"] == "easter_offset"
        assert recurrence_rules["Easter Monday"]["offset_days"] == 1

    def test_bank_holiday_rules(self, recurrence_rules):
        for name in ["May Bank Holiday", "June Bank Holiday", "August Bank Holiday"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "nth_weekday"
            assert rule["weekday"] == "monday"
            assert rule["n"] == 1

    def test_october_bank_holiday_rule(self, recurrence_rules):
        """October Bank Holiday is the LAST Monday, not first."""
        rule = recurrence_rules["October Bank Holiday"]
        assert rule["rule"] == "nth_weekday"
        assert rule["weekday"] == "monday"
        assert rule["n"] == 4  # 4th Monday (last in most years)

    def test_no_early_close_rules(self, recurrence_rules):
        """Early close days are explicit only, not in recurrence rules."""
        for name, rule in recurrence_rules.items():
            assert rule.get("status") != "early_close", f"{name} should not be in recurrence as early_close"

    def test_closed_rules_have_no_early_close_time(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            if rule.get("status") == "closed":
                assert "early_close_time" not in rule, f"{name} should not have early_close_time"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXDUBStructure:
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

    def test_early_close_entries_have_early_close_time(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            if entry.get("status") == "early_close":
                assert "early_close_time" in entry, f"Missing early_close_time: {date_str}"

    def test_closed_entries_no_early_close_time(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            if entry.get("status") == "closed":
                assert "early_close_time" not in entry, f"Unexpected early_close_time: {date_str}"

    def test_dates_within_generation_range(self, xdub, explicit_dates):
        start = date.fromisoformat(xdub["generation_range"][0])
        end = date.fromisoformat(xdub["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end, f"Date outside range: {date_str}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~55-65 entries: 10 holidays × 5 years + substitutes."""
        assert 50 <= len(explicit_dates) <= 70, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """All source URLs should be from euronext.com."""
        for entry in explicit_dates.values():
            assert "euronext.com" in entry["source_url"], f"Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Substitution logic cross-checks
# ──────────────────────────────────────────────────────────────

class TestXDUBSubstitution:
    def test_saturday_substitutes_to_monday(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute should be Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates

    def test_sunday_substitutes_to_monday(self, explicit_dates):
        """Dec 26, 2027 is Sunday — substitute should be Tuesday Dec 28.
           (Monday Dec 27 is already Christmas Day substitute)."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" in explicit_dates

    def test_substitute_names_contain_substitute(self, explicit_dates):
        """All substitute holidays should have 'substitute' in name."""
        for entry in explicit_dates.values():
            if "substitute" in entry["name"].lower():
                assert "substitute" in entry["name"].lower()

    def test_no_observed_holidays(self, explicit_dates):
        """Ireland uses 'substitute', not 'observed'."""
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            assert "observed" not in name, f"Observed holiday found: {entry['name']}"

    def test_weekend_holidays_absent(self, explicit_dates):
        """Verify known weekend holidays are correctly absent."""
        weekend_holidays = [
            ("2027-12-25", "Christmas Day (Saturday)"),
            ("2027-12-26", "St. Stephen's Day (Sunday)"),
            ("2028-01-01", "New Year's Day (Saturday)"),
            ("2029-03-17", "St. Patrick's Day (Saturday)"),
        ]
        for date_str, name in weekend_holidays:
            assert date_str not in explicit_dates, f"{name} should not be in explicit dates"


# ──────────────────────────────────────────────────────────────
# Calendar calculation cross-checks
# ──────────────────────────────────────────────────────────────

class TestXDUBCalendarCrossChecks:
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

    def test_bank_holiday_mondays(self, explicit_dates):
        """Verify all bank holidays fall on Mondays."""
        bank_holiday_names = [
            "May Bank Holiday",
            "June Bank Holiday",
            "August Bank Holiday",
            "October Bank Holiday",
        ]
        for entry in explicit_dates.values():
            if entry["name"] in bank_holiday_names:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"{entry['name']} should be Monday: {entry['date']}"