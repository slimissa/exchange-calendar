#!/usr/bin/env python3
"""
test_vienna_holidays.py — Ground truth tests for XWBO (Vienna Stock Exchange / Wiener Börse).

Key facts verified:
    - Regular hours: 09:00-17:30
    - No lunch break (continuous trading)
    - No extended hours sessions
    - Austria does NOT shift holidays from weekends
    - Dec 24 (Christmas Eve) — early close at 12:00
    - Dec 31 (New Year's Eve) — early close at 12:00
    - Ascension Day (Easter + 39 days)
    - Whit Monday (Easter + 50 days)
    - Corpus Christi (Easter + 60 days)
    - National Day (Oct 26) — no substitution
    - All Saints' Day (Nov 1)
    - Immaculate Conception (Dec 8)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XWBO.json)
    2. Austrian holiday announcements changed (verify against wienerborse.at)

Run:
    python3 -m pytest tests/test_vienna_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xwbo():
    """Load XWBO.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XWBO.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xwbo):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xwbo["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xwbo):
    """Return dict of name -> rule."""
    rules = xwbo["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXWBOProperties:
    def test_code(self, xwbo):
        assert xwbo["code"] == "XWBO"

    def test_mic(self, xwbo):
        assert xwbo["mic"] == "XWBO"

    def test_name(self, xwbo):
        assert xwbo["name"] == "Vienna Stock Exchange"

    def test_timezone(self, xwbo):
        assert xwbo["timezone"] == "Europe/Vienna"

    def test_regular_hours(self, xwbo):
        assert xwbo["regular_hours"]["open"] == "09:00"
        assert xwbo["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xwbo):
        lunch = [s for s in xwbo.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xwbo):
        """Vienna Stock Exchange does not model separate extended hours sessions."""
        assert "extended_hours" not in xwbo or xwbo.get("extended_hours") is None

    def test_generation_range(self, xwbo):
        assert "generation_range" in xwbo
        assert xwbo["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xwbo):
        assert xwbo.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXWBOFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2026(self, explicit_dates):
        """Jan 1, 2026 is Thursday."""
        assert "2026-01-01" in explicit_dates

    def test_epiphany_2025(self, explicit_dates):
        """Jan 6, 2025 is Monday."""
        assert "2025-01-06" in explicit_dates
        assert explicit_dates["2025-01-06"]["name"] == "Epiphany"

    def test_epiphany_2026(self, explicit_dates):
        """Jan 6, 2026 is Tuesday."""
        assert "2026-01-06" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2026(self, explicit_dates):
        """May 1, 2026 is Friday."""
        assert "2026-05-01" in explicit_dates

    def test_assumption_day_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday."""
        assert "2025-08-15" in explicit_dates
        assert explicit_dates["2025-08-15"]["name"] == "Assumption Day"

    def test_assumption_day_2026_weekend(self, explicit_dates):
        """Aug 15, 2026 is Saturday — no explicit entry (no substitution)."""
        assert "2026-08-15" not in explicit_dates

    def test_all_saints_2025_weekend(self, explicit_dates):
        """Nov 1, 2025 is Saturday — no explicit entry (no substitution)."""
        assert "2025-11-01" not in explicit_dates

    def test_all_saints_2026_weekend(self, explicit_dates):
        """Nov 1, 2026 is Sunday — no explicit entry (no substitution)."""
        assert "2026-11-01" not in explicit_dates

    def test_national_day_2025_weekend(self, explicit_dates):
        """Oct 26, 2025 is Sunday — no explicit entry (no substitution)."""
        assert "2025-10-26" not in explicit_dates
        assert "2025-10-27" not in explicit_dates  # No observed day

    def test_national_day_2026(self, explicit_dates):
        """Oct 26, 2026 is Monday — explicit entry."""
        assert "2026-10-26" in explicit_dates
        assert explicit_dates["2026-10-26"]["name"] == "National Day"

    def test_immaculate_conception_2025(self, explicit_dates):
        """Dec 8, 2025 is Monday."""
        assert "2025-12-08" in explicit_dates
        assert explicit_dates["2025-12-08"]["name"] == "Immaculate Conception"

    def test_immaculate_conception_2026(self, explicit_dates):
        """Dec 8, 2026 is Tuesday."""
        assert "2026-12-08" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_2026(self, explicit_dates):
        """Dec 25, 2026 is Friday."""
        assert "2026-12-25" in explicit_dates

    def test_st_stephens_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "St. Stephen's Day"

    def test_st_stephens_2026_weekend(self, explicit_dates):
        """Dec 26, 2026 is Saturday — no explicit entry (no substitution)."""
        assert "2026-12-26" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Early close days
# ──────────────────────────────────────────────────────────────

class TestXWBOEarlyCloses:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — early close at 12:00."""
        entry = explicit_dates.get("2025-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:00"

    def test_christmas_eve_2026(self, explicit_dates):
        """Dec 24, 2026 is Thursday — early close at 12:00."""
        entry = explicit_dates.get("2026-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:00"

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — early close at 12:00."""
        entry = explicit_dates.get("2025-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:00"

    def test_new_years_eve_2026(self, explicit_dates):
        """Dec 31, 2026 is Thursday — early close at 12:00."""
        entry = explicit_dates.get("2026-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:00"

    def test_no_other_early_closes(self, explicit_dates):
        """Only Christmas Eve and New Year's Eve are early closes."""
        early_closes = [e for e in explicit_dates.values() if e.get("status") == "early_close"]
        early_close_names = {e["name"] for e in early_closes}
        assert early_close_names == {"Christmas Eve", "New Year's Eve"}


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXWBOEaster:
    def test_easter_monday_2025(self, explicit_dates):
        """Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["name"] == "Easter Monday"

    def test_easter_monday_2026(self, explicit_dates):
        """Easter + 1 day — April 6, 2026."""
        assert "2026-04-06" in explicit_dates

    def test_ascension_2025(self, explicit_dates):
        """Easter + 39 days — May 29, 2025."""
        assert "2025-05-29" in explicit_dates
        assert explicit_dates["2025-05-29"]["name"] == "Ascension Day"

    def test_ascension_2026(self, explicit_dates):
        """Easter + 39 days — May 14, 2026."""
        assert "2026-05-14" in explicit_dates

    def test_whit_monday_2025(self, explicit_dates):
        """Easter + 50 days — June 9, 2025."""
        assert "2025-06-09" in explicit_dates
        assert explicit_dates["2025-06-09"]["name"] == "Whit Monday"

    def test_whit_monday_2026(self, explicit_dates):
        """Easter + 50 days — May 25, 2026."""
        assert "2026-05-25" in explicit_dates

    def test_corpus_christi_2025(self, explicit_dates):
        """Easter + 60 days — June 19, 2025."""
        assert "2025-06-19" in explicit_dates
        assert explicit_dates["2025-06-19"]["name"] == "Corpus Christi"

    def test_corpus_christi_2026(self, explicit_dates):
        """Easter + 60 days — June 4, 2026."""
        assert "2026-06-04" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXWBORecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "New Year's Day",
            "Epiphany",
            "Labour Day",
            "Assumption Day",
            "National Day",
            "All Saints' Day",
            "Immaculate Conception",
            "Christmas Eve",
            "Christmas Day",
            "St. Stephen's Day",
            "New Year's Eve",
        }
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_easter_rules(self, recurrence_rules):
        assert recurrence_rules["Easter Monday"]["rule"] == "easter_offset"
        assert recurrence_rules["Easter Monday"]["offset_days"] == 1

        assert recurrence_rules["Ascension Day"]["rule"] == "easter_offset"
        assert recurrence_rules["Ascension Day"]["offset_days"] == 39

        assert recurrence_rules["Whit Monday"]["rule"] == "easter_offset"
        assert recurrence_rules["Whit Monday"]["offset_days"] == 50

        assert recurrence_rules["Corpus Christi"]["rule"] == "easter_offset"
        assert recurrence_rules["Corpus Christi"]["offset_days"] == 60

    def test_national_day_no_substitution(self, recurrence_rules):
        """Austria does NOT shift National Day from weekends."""
        rule = recurrence_rules["National Day"]
        assert rule["rule"] == "fixed_date"
        assert rule["month"] == 10
        assert rule["day"] == 26

    def test_early_close_rules(self, recurrence_rules):
        for name in ["Christmas Eve", "New Year's Eve"]:
            rule = recurrence_rules[name]
            assert rule["status"] == "early_close"
            assert rule["early_close_time"] == "12:00"

    def test_closed_rules_have_no_early_close_time(self, recurrence_rules):
        """Full closure rules should not have early_close_time."""
        for name, rule in recurrence_rules.items():
            if rule.get("status") == "closed":
                assert "early_close_time" not in rule, f"{name} should not have early_close_time"

    def test_fixed_date_rules_format(self, recurrence_rules):
        """All fixed_date rules must have month and day."""
        for name, rule in recurrence_rules.items():
            if rule["rule"] == "fixed_date":
                assert "month" in rule, f"{name}: missing month"
                assert "day" in rule, f"{name}: missing day"
                assert 1 <= rule["month"] <= 12, f"{name}: invalid month"
                assert 1 <= rule["day"] <= 31, f"{name}: invalid day"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXWBOStructure:
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

    def test_dates_within_generation_range(self, xwbo, explicit_dates):
        start = date.fromisoformat(xwbo["generation_range"][0])
        end = date.fromisoformat(xwbo["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end, f"Date outside range: {date_str}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-65 entries: 15 holidays × 5 years (minus weekends)."""
        assert 50 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """All source URLs should be from wienerborse.at."""
        for entry in explicit_dates.values():
            assert "wienerborse.at" in entry["source_url"], f"Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Calendar calculation cross-checks
# ──────────────────────────────────────────────────────────────

class TestXWBOCalendarCrossChecks:
    def test_easter_2025_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2025."""
        # Easter Sunday 2025 is April 20
        assert "2025-04-21" in explicit_dates  # Easter Monday (+1)
        assert "2025-05-29" in explicit_dates  # Ascension (+39)
        assert "2025-06-09" in explicit_dates  # Whit Monday (+50)
        assert "2025-06-19" in explicit_dates  # Corpus Christi (+60)

    def test_easter_2026_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2026."""
        # Easter Sunday 2026 is April 5
        assert "2026-04-06" in explicit_dates  # Easter Monday (+1)
        assert "2026-05-14" in explicit_dates  # Ascension (+39)
        assert "2026-05-25" in explicit_dates  # Whit Monday (+50)
        assert "2026-06-04" in explicit_dates  # Corpus Christi (+60)

    def test_no_observed_holidays(self, explicit_dates):
        """Austria does not observe substitute holidays for weekend dates."""
        # Check that no holiday name contains 'observed' or 'substitute'
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            assert "observed" not in name, f"Observed holiday found: {entry['name']}"
            assert "substitute" not in name, f"Substitute holiday found: {entry['name']}"

    def test_weekend_holidays_absent(self, explicit_dates):
        """Verify known weekend holidays are correctly absent."""
        weekend_holidays = [
            ("2025-10-26", "National Day (Sunday)"),
            ("2025-11-01", "All Saints' Day (Saturday)"),
            ("2026-08-15", "Assumption Day (Saturday)"),
            ("2026-12-26", "St. Stephen's Day (Saturday)"),
        ]
        for date_str, name in weekend_holidays:
            assert date_str not in explicit_dates, f"{name} should not be in explicit dates"