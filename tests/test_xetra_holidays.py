#!/usr/bin/env python3
"""
test_xetra_holidays.py — Ground truth tests for XETR (Deutsche Börse / Xetra).

Key facts verified:
    - Germany has NO substitute holiday shifts (Kein Feiertagsausgleich)
    - Xetra is OPEN on: Ascension Day, Whit Monday, Corpus Christi,
      German Unity Day (Oct 3), All Saints' Day (Nov 1)
    - Full closures: New Year, Good Friday, Easter Monday, Labour Day,
      Christmas Eve, Christmas Day, Boxing Day, New Year's Eve
    - No lunch break (continuous trading)
    - No weekend observation — holidays on weekends are NOT shifted
    - Christmas Eve and New Year's Eve are FULL closures (not half-days)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XETR.json)
    2. German holiday law changed (verify against deutsche-boerse.com)

Run:
    python3 -m pytest tests/test_xetra_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xetr():
    """Load XETR.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XETR.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xetr):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xetr["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXETRProperties:
    def test_code(self, xetr):
        assert xetr["code"] == "XETR"

    def test_mic(self, xetr):
        assert xetr["mic"] == "XETR"

    def test_name(self, xetr):
        assert xetr["name"] == "Deutsche Börse"

    def test_timezone(self, xetr):
        assert xetr["timezone"] == "Europe/Berlin"

    def test_regular_hours(self, xetr):
        assert xetr["regular_hours"]["open"] == "09:00"
        assert xetr["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xetr):
        lunch = [s for s in xetr.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_auction_sessions(self, xetr):
        auctions = [s for s in xetr.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 2

    def test_has_extended_hours(self, xetr):
        assert "extended_hours" in xetr


# ──────────────────────────────────────────────────────────────
# German holidays where Xetra is OPEN
# ──────────────────────────────────────────────────────────────

class TestXETROpenOnGermanHolidays:
    def test_ascension_open(self, explicit_dates):
        """Christi Himmelfahrt — Xetra OPEN."""
        assert "2025-05-29" not in explicit_dates

    def test_whit_monday_open(self, explicit_dates):
        """Pfingstmontag — Xetra OPEN."""
        assert "2025-06-09" not in explicit_dates

    def test_german_unity_open(self, explicit_dates):
        """Tag der Deutschen Einheit (Oct 3) — Xetra OPEN."""
        assert "2025-10-03" not in explicit_dates
        assert "2026-10-03" not in explicit_dates

    def test_all_saints_open(self, explicit_dates):
        """Allerheiligen (Nov 1) — Xetra OPEN."""
        assert "2025-11-01" not in explicit_dates
        assert "2026-11-01" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Actual Xetra closures
# ──────────────────────────────────────────────────────────────

class TestXETRClosed2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["status"] == "closed"

    def test_easter_monday(self, explicit_dates):
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["status"] == "closed"

    def test_labour_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["status"] == "closed"

    def test_christmas_eve(self, explicit_dates):
        """Christmas Eve is a FULL closure, not a half-day."""
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "closed"

    def test_christmas_day(self, explicit_dates):
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["status"] == "closed"

    def test_boxing_day(self, explicit_dates):
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["status"] == "closed"

    def test_new_years_eve(self, explicit_dates):
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "closed"


class TestXETRClosed2026:
    def test_new_year(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_easter_monday(self, explicit_dates):
        assert "2026-04-06" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2026-05-01" in explicit_dates

    def test_christmas_eve(self, explicit_dates):
        assert "2026-12-24" in explicit_dates

    def test_christmas_day(self, explicit_dates):
        assert "2026-12-25" in explicit_dates

    def test_new_years_eve(self, explicit_dates):
        assert "2026-12-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# No substitute holidays (Kein Feiertagsausgleich)
# ──────────────────────────────────────────────────────────────

class TestXETRNoSubstitutes:
    def test_no_boxing_day_observed_2027(self, explicit_dates):
        """
        Dec 26, 2027 is Sunday. Germany does NOT observe Boxing Day
        on Monday Dec 27. Monday is a normal trading day.
        """
        assert "2027-12-27" not in explicit_dates

    def test_no_labour_day_observed_2027(self, explicit_dates):
        """
        May 1, 2027 is Saturday. Germany does NOT shift Labour Day
        to Friday or Monday.
        """
        assert "2027-05-01" not in explicit_dates

    def test_no_christmas_observed_2027(self, explicit_dates):
        """
        Dec 25, 2027 is Saturday. No observed holiday on Friday or Monday.
        """
        assert "2027-12-24" in explicit_dates  # Christmas Eve is Friday
        assert "2027-12-25" not in explicit_dates  # Saturday, no explicit

    def test_no_new_year_observed_2028(self, explicit_dates):
        """
        Jan 1, 2028 is Saturday. No observed holiday on Friday Dec 31, 2027
        or Monday Jan 3, 2028.
        """
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXETRStructure:
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
        """Xetra has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", \
                f"Unexpected status: {entry['date']}: {entry['status']}"

    def test_recurrence_rules_exist(self, xetr):
        rules = xetr["holidays"].get("recurrence_rules", [])
        assert len(rules) > 0

    def test_recurrence_rules_no_german_holidays(self, xetr):
        rules = xetr["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Ascension Day" not in names
        assert "Whit Monday" not in names
        assert "German Unity Day" not in names
        assert "All Saints' Day" not in names

    def test_recurrence_rules_have_closures(self, xetr):
        rules = xetr["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Good Friday" in names
        assert "Easter Monday" in names
        assert "Labour Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names
        assert "New Year's Eve" in names

    def test_holiday_count_reasonable(self, explicit_dates):
        """~33 entries: 8 closures × 5 years, minus weekend occurrences."""
        assert 30 <= len(explicit_dates) <= 40