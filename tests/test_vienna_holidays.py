#!/usr/bin/env python3
"""
test_vienna_holidays.py — Ground truth tests for XWBO (Vienna Stock Exchange / Wiener Börse).

Key facts verified:
    - Regular hours: 09:00-17:30
    - No lunch break (continuous trading)
    - No extended hours sessions
    - Austria does NOT shift holidays from weekends
    - Dec 24 (Christmas Eve) and Dec 31 (New Year's Eve) — CLOSED, not early
      closes (Wiener Börse "Börsenfeiertage 2025/2026": handelsfrei)
    - Good Friday (Easter - 2) and Easter Monday (Easter + 1) — closed
    - National Day (Oct 26) — closed, no substitution
    - Epiphany, Ascension Day, Whit Monday, Corpus Christi, Assumption Day,
      All Saints' Day and Immaculate Conception are Austrian public holidays
      but "Zusätzliche Handelstage": the exchange is OPEN. They must not be
      closures.

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
def closed_dates(xwbo):
    """Closed dates after recurrence rules are expanded, as build.py does."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
    from generate_dates import expand_exchange

    entries = list(xwbo["holidays"]["explicit"]) + expand_exchange(xwbo)
    return {e["date"] for e in entries if e["status"] == "closed"}


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
        """Jan 6, 2025 is Monday — an additional trading day, not a closure."""
        assert "2025-01-06" not in explicit_dates

    def test_epiphany_2026(self, explicit_dates):
        """Jan 6, 2026 is Tuesday."""
        assert "2026-01-06" not in explicit_dates  # right-column — exchange open

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2026(self, explicit_dates):
        """May 1, 2026 is Friday."""
        assert "2026-05-01" in explicit_dates

    def test_assumption_day_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday — an additional trading day, not a closure."""
        assert "2025-08-15" not in explicit_dates

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
        """Dec 8, 2025 is Monday — an additional trading day, not a closure."""
        assert "2025-12-08" not in explicit_dates

    def test_immaculate_conception_2026(self, explicit_dates):
        """Dec 8, 2026 is a right-column entry — the exchange is
        open. It must NOT appear in explicit_dates."""
        assert "2026-12-08" not in explicit_dates

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

class TestXWBOEveClosures:
    """Dec 24 and Dec 31 are "handelsfrei" (closed all day), not half days."""

    @pytest.mark.parametrize("day,name", [
        ("2025-12-24", "Christmas Eve"),
        ("2025-12-31", "New Year's Eve"),
        ("2026-12-24", "Christmas Eve"),
        ("2026-12-31", "New Year's Eve"),
    ])
    def test_closed_all_day(self, explicit_dates, day, name):
        entry = explicit_dates.get(day)
        assert entry is not None
        assert entry["name"] == name
        assert entry["status"] == "closed"
        assert "early_close_time" not in entry

    def test_no_early_closes(self, explicit_dates, recurrence_rules):
        assert not [e for e in explicit_dates.values() if e["status"] == "early_close"]
        assert not [r for r in recurrence_rules.values() if r["status"] == "early_close"]


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

    def test_good_friday_2025(self, closed_dates):
        """Easter - 2 days — April 18, 2025 (a closure; not an explicit row)."""
        assert "2025-04-18" in closed_dates

    def test_good_friday_2026(self, closed_dates):
        """Easter - 2 days — April 3, 2026."""
        assert "2026-04-03" in closed_dates

    def test_ascension_2025(self, explicit_dates):
        """Easter + 39 days — May 29, 2025. Additional trading day: open."""
        assert "2025-05-29" not in explicit_dates

    def test_ascension_2026(self, explicit_dates):
        """Easter + 39 days — May 14, 2026."""
        assert "2026-05-14" not in explicit_dates  # right-column — exchange open

    def test_whit_monday_2025(self, explicit_dates):
        """Easter + 50 days — June 9, 2025. Additional trading day: open."""
        assert "2025-06-09" not in explicit_dates

    def test_whit_monday_2026(self, explicit_dates):
        """Easter + 50 days — May 25, 2026."""
        assert "2026-05-25" not in explicit_dates  # right-column — exchange open

    def test_corpus_christi_2025(self, explicit_dates):
        """Easter + 60 days — June 19, 2025. Additional trading day: open."""
        assert "2025-06-19" not in explicit_dates

    def test_corpus_christi_2026(self, explicit_dates):
        """Easter + 60 — June 4, 2026. Right-column entry; the
        exchange is open. Must NOT be a closure."""
        assert "2026-06-04" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXWBORecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "New Year's Day",
            "Labour Day",
            "National Day",
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

        assert recurrence_rules["Good Friday"]["rule"] == "easter_offset"
        assert recurrence_rules["Good Friday"]["offset_days"] == -2
        assert recurrence_rules["Good Friday"]["status"] == "closed"

    def test_additional_trading_days_have_no_closure_rule(self, recurrence_rules):
        """Austrian public holidays on which Wiener Börse trades."""
        for name in ("Epiphany", "Ascension Day", "Whit Monday", "Corpus Christi",
                     "Assumption Day", "All Saints' Day", "Immaculate Conception"):
            assert name not in recurrence_rules, f"{name} is a trading day"

    def test_national_day_no_substitution(self, recurrence_rules):
        """Austria does NOT shift National Day from weekends."""
        rule = recurrence_rules["National Day"]
        assert rule["rule"] == "fixed_date"
        assert rule["month"] == 10
        assert rule["day"] == 26

    def test_eve_rules_are_closures(self, recurrence_rules):
        for name in ["Christmas Eve", "New Year's Eve"]:
            rule = recurrence_rules[name]
            assert rule["status"] == "closed"
            assert "early_close_time" not in rule

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
        """~30-45 entries: 9 closures × 5 years (minus weekends)."""
        assert 25 <= len(explicit_dates) <= 45, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """All source URLs should be from wienerborse.at."""
        for entry in explicit_dates.values():
            assert "wienerborse.at" in entry["source_url"], f"Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Calendar calculation cross-checks
# ──────────────────────────────────────────────────────────────

class TestXWBOCalendarCrossChecks:
    def test_easter_2025_calculations(self, explicit_dates, closed_dates):
        """Verify Easter-based dates are internally consistent for 2025."""
        # Easter Sunday 2025 is April 20
        assert "2025-04-18" in closed_dates    # Good Friday (-2)
        assert "2025-04-21" in explicit_dates  # Easter Monday (+1)
        assert "2025-05-29" not in closed_dates  # Ascension (+39): open
        assert "2025-06-09" not in closed_dates  # Whit Monday (+50): open
        assert "2025-06-19" not in closed_dates  # Corpus Christi (+60): open

    def test_easter_2026_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2026."""
        # Easter Sunday 2026 is April 5
        assert "2026-04-06" in explicit_dates  # Easter Monday (+1)
        assert "2026-05-14" not in explicit_dates  # Ascension (+39), right-column — exchange open
        assert "2026-05-25" not in explicit_dates  # Whit Monday (+50), right-column — exchange open
        assert "2026-06-04" not in explicit_dates  # Corpus Christi — right column, open

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


# ──────────────────────────────────────────────────────────────
# Regression: dates found by tools/divergence_test.py
# Registry and both reference libraries disagreed on 17 dates. The Wiener
# Börse's own "Börsenfeiertage & Feiertagshandel" lists (2025, 2026) side
# with the libraries on all 17.
# ──────────────────────────────────────────────────────────────

# Handelsfreie Feiertage, exactly as published by Wiener Börse.
OFFICIAL_CLOSED_2025 = {
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-01",
    "2025-12-24", "2025-12-25", "2025-12-26", "2025-12-31",
}
OFFICIAL_CLOSED_2026 = {
    "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01",
    "2026-10-26", "2026-12-24", "2026-12-25", "2026-12-31",
}

# "Zusätzliche Handelstage": Austrian public holidays, exchange open.
OFFICIAL_TRADING_HOLIDAYS = [
    "2025-01-06", "2025-05-29", "2025-06-09", "2025-06-19", "2025-08-15",
    "2025-12-08",
    "2026-01-06", "2026-05-14", "2026-05-25", "2026-06-04", "2026-12-08",
]


class TestXWBODivergenceRegression:
    def test_closures_match_wiener_boerse_2025(self, closed_dates):
        assert {d for d in closed_dates if d.startswith("2025")} == OFFICIAL_CLOSED_2025

    def test_closures_match_wiener_boerse_2026(self, closed_dates):
        assert {d for d in closed_dates if d.startswith("2026")} == OFFICIAL_CLOSED_2026

    @pytest.mark.parametrize("day", OFFICIAL_TRADING_HOLIDAYS)
    def test_additional_trading_day_is_open(self, closed_dates, day):
        assert date.fromisoformat(day).weekday() < 5
        assert day not in closed_dates

    @pytest.mark.parametrize("day", [
        "2025-04-18", "2026-04-03",  # Good Friday
        "2025-12-24", "2025-12-31", "2026-12-24", "2026-12-31",  # eves
    ])
    def test_missing_closure_is_closed(self, closed_dates, day):
        assert day in closed_dates

    def test_later_years_follow_the_same_pattern(self, closed_dates):
        """2027-2029 are predictions from the same rules."""
        for day in ("2027-03-26", "2028-04-14", "2029-03-30"):  # Good Friday
            assert day in closed_dates
        for day in ("2027-05-06", "2028-05-25", "2029-05-10",   # Ascension
                    "2027-11-01", "2028-11-01", "2029-11-01"):  # All Saints'
            assert day not in closed_dates

    def test_built_calendar_matches(self):
        """The shipped calendar.json carries the same fix."""
        import json as _json
        path = Path(__file__).parent.parent / "calendar.json"
        with open(path) as f:
            cal = _json.load(f)
        entry = next(e for e in cal["exchanges"] if e["code"] == "XWBO")
        closed = {
            h["date"]
            for h in entry["holidays"]["explicit"] + entry["holidays"]["generated"]
            if h["status"] == "closed"
        }
        assert {d for d in closed if d.startswith("2025")} == OFFICIAL_CLOSED_2025
        assert {d for d in closed if d.startswith("2026")} == OFFICIAL_CLOSED_2026
