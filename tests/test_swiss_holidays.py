#!/usr/bin/env python3
"""
test_swiss_holidays.py — Ground truth tests for XSWX (SIX Swiss Exchange).

Key facts verified:
    - Switzerland has NO substitute holidays (Kein Feiertagsausgleich)
    - Fixed holidays on weekends are NOT shifted to Monday
    - Closures: New Year, Berchtoldstag, Good Friday, Easter Monday,
      Labour Day, Ascension, Whit Monday, Swiss National Day,
      Christmas Eve, Christmas Day, St. Stephen's Day, New Year's Eve
    - No lunch break (continuous trading)
    - Christmas Eve and New Year's Eve are FULL closures (not half-days)
    - Auctions at 09:00 and 17:30

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XSWX.json)
    2. Swiss holiday law changed (verify against six-group.com)

Run:
    python3 -m pytest tests/test_swiss_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xswx():
    """Load XSWX.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XSWX.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xswx):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xswx["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXSWXProperties:
    def test_code(self, xswx):
        assert xswx["code"] == "XSWX"

    def test_mic(self, xswx):
        assert xswx["mic"] == "XSWX"

    def test_name(self, xswx):
        assert xswx["name"] == "SIX Swiss Exchange"

    def test_timezone(self, xswx):
        assert xswx["timezone"] == "Europe/Zurich"

    def test_regular_hours(self, xswx):
        assert xswx["regular_hours"]["open"] == "09:00"
        assert xswx["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xswx):
        lunch = [s for s in xswx.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_auction_sessions(self, xswx):
        auctions = [s for s in xswx.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 2
        times = [a["at"] for a in auctions]
        assert "09:00" in times
        assert "17:30" in times

    def test_has_extended_hours(self, xswx):
        assert "extended_hours" in xswx


# ──────────────────────────────────────────────────────────────
# 2025 closures
# ──────────────────────────────────────────────────────────────

class TestXSWXClosed2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_berchtoldstag(self, explicit_dates):
        assert "2025-01-02" in explicit_dates
        assert explicit_dates["2025-01-02"]["status"] == "closed"

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["status"] == "closed"

    def test_easter_monday(self, explicit_dates):
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["status"] == "closed"

    def test_labour_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["status"] == "closed"

    def test_ascension(self, explicit_dates):
        assert "2025-05-29" in explicit_dates
        assert explicit_dates["2025-05-29"]["status"] == "closed"

    def test_whit_monday(self, explicit_dates):
        assert "2025-06-09" in explicit_dates
        assert explicit_dates["2025-06-09"]["status"] == "closed"

    def test_national_day(self, explicit_dates):
        assert "2025-08-01" in explicit_dates
        assert explicit_dates["2025-08-01"]["status"] == "closed"

    def test_christmas_eve(self, explicit_dates):
        """Christmas Eve is a FULL closure."""
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "closed"

    def test_christmas_day(self, explicit_dates):
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["status"] == "closed"

    def test_st_stephen(self, explicit_dates):
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["status"] == "closed"

    def test_new_years_eve(self, explicit_dates):
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2026 closures
# ──────────────────────────────────────────────────────────────

class TestXSWXClosed2026:
    def test_new_year(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_berchtoldstag(self, explicit_dates):
        assert "2026-01-02" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_easter_monday(self, explicit_dates):
        assert "2026-04-06" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2026-05-01" in explicit_dates

    def test_ascension(self, explicit_dates):
        assert "2026-05-14" in explicit_dates

    def test_whit_monday(self, explicit_dates):
        assert "2026-05-25" in explicit_dates

    def test_christmas_eve(self, explicit_dates):
        assert "2026-12-24" in explicit_dates

    def test_christmas_day(self, explicit_dates):
        assert "2026-12-25" in explicit_dates

    def test_new_years_eve(self, explicit_dates):
        assert "2026-12-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# No substitute holidays (Kein Feiertagsausgleich)
# ──────────────────────────────────────────────────────────────

class TestXSWXNoSubstitutes:
    def test_no_national_day_observed_2027(self, explicit_dates):
        """Aug 1, 2027 is Sunday — NO Monday shift."""
        assert "2027-08-02" not in explicit_dates

    def test_no_berchtoldstag_observed_2027(self, explicit_dates):
        """Jan 2, 2027 is Saturday — NO Monday shift."""
        assert "2027-01-04" not in explicit_dates

    def test_no_st_stephen_observed_2027(self, explicit_dates):
        """Dec 26, 2027 is Sunday — NO Monday shift."""
        assert "2027-12-27" not in explicit_dates

    def test_no_new_year_observed_2028(self, explicit_dates):
        """Jan 1, 2028 is Saturday — NO Friday or Monday shift."""
        # Dec 31, 2027 is New Year's Eve, a separate closure (Friday)
        # So it IS in explicit — but as New Year's Eve, not observed New Year
        assert "2028-01-03" not in explicit_dates  # No Monday observation

    def test_no_national_day_observed_2026(self, explicit_dates):
        """Aug 1, 2026 is Saturday — NO Monday shift."""
        assert "2026-08-03" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXSWXStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source: {date_str}"

    def test_all_statuses_closed(self, explicit_dates):
        """XSWX has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", \
                f"Unexpected status: {entry['date']}: {entry['status']}"

    def test_no_observed_entries(self, explicit_dates):
        """Switzerland has no substitute holidays."""
        for entry in explicit_dates.values():
            assert "observed" not in entry["name"].lower(), \
                f"Observed entry found: {entry['date']}: {entry['name']}"

    def test_recurrence_rules_exist(self, xswx):
        rules = xswx["holidays"].get("recurrence_rules", [])
        assert len(rules) > 0

    def test_recurrence_rules_have_closures(self, xswx):
        rules = xswx["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Berchtoldstag" in names
        assert "Good Friday" in names
        assert "Easter Monday" in names
        assert "Labour Day" in names
        assert "Ascension Day" in names
        assert "Whit Monday" in names
        assert "Swiss National Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "St. Stephen's Day" in names
        assert "New Year's Eve" in names

    def test_holiday_count_reasonable(self, explicit_dates):
        """~49 entries: 12 closures × 5 years, minus weekend occurrences."""
        assert 45 <= len(explicit_dates) <= 55