#!/usr/bin/env python3
"""
test_amsterdam_holidays.py — Ground truth tests for XAMS (Euronext Amsterdam).

Key facts verified:
    - Regular hours: 09:00-17:30 (Euronext standard)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Euronext Amsterdam closes only on New Year's Day, Good Friday, Easter
      Monday, Labour Day (May 1), Christmas Day and Boxing Day (Dec 26)
    - King's Day (Apr 27), Liberation Day (May 5), Ascension Day and Whit
      Monday are Dutch holidays but FULL TRADING DAYS on Euronext Amsterdam
    - Weekend holidays are not substituted (Euronext 2026 calendar: Dec 28 and
      Jan 2 are full trading days for Amsterdam)
    - Source: Euronext "Holiday Calendar for Cash and Derivatives markets",
      2025 and 2026 (live.euronext.com/en/resources/trading-hours-holidays)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XAMS.json)
    2. Dutch holiday announcements changed (verify against euronext.com)

Run:
    python3 -m pytest tests/test_amsterdam_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xams():
    """Load XAMS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XAMS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xams):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xams["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXAMSProperties:
    def test_code(self, xams):
        assert xams["code"] == "XAMS"

    def test_mic(self, xams):
        assert xams["mic"] == "XAMS"

    def test_name(self, xams):
        assert xams["name"] == "Euronext Amsterdam"

    def test_timezone(self, xams):
        assert xams["timezone"] == "Europe/Amsterdam"

    def test_regular_hours(self, xams):
        assert xams["regular_hours"]["open"] == "09:00"
        assert xams["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xams):
        lunch = [s for s in xams.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xams):
        assert "extended_hours" not in xams or xams.get("extended_hours") is None

    def test_generation_range(self, xams):
        assert "generation_range" in xams
        assert xams["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xams):
        assert xams.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xams):
        """Netherlands uses explicit dates only."""
        rules = xams["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXAMSFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_no_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — Euronext does not substitute."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" not in explicit_dates

    def test_kings_day_is_a_trading_day(self, explicit_dates):
        """King's Day is not a Euronext Amsterdam closure in any year."""
        for year in range(2025, 2030):
            assert f"{year}-04-27" not in explicit_dates
        assert not [e for e in explicit_dates.values() if "King" in e["name"]]

    def test_liberation_day_is_a_trading_day(self, explicit_dates):
        """May 5, 2025 is Monday — Liberation Day, but Euronext is open."""
        assert "2025-05-05" not in explicit_dates
        assert not [e for e in explicit_dates.values() if "Liberation" in e["name"]]

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday — Euronext closed."""
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"
        assert explicit_dates["2025-05-01"]["status"] == "closed"

    def test_labour_day_2026(self, explicit_dates):
        """May 1, 2026 is Friday — Euronext closed."""
        assert explicit_dates["2026-05-01"]["name"] == "Labour Day"
        assert explicit_dates["2026-05-01"]["status"] == "closed"

    def test_labour_day_2027_weekend(self, explicit_dates):
        """May 1, 2027 is Saturday — no entry, no substitute."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" not in explicit_dates

    def test_labour_day_2028_2029(self, explicit_dates):
        """Predicted: May 1 on Monday (2028) and Tuesday (2029)."""
        assert "2028-05-01" in explicit_dates
        assert "2029-05-01" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXAMSChristmas:
    def test_christmas_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_christmas_2027_no_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — no substitute Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" not in explicit_dates

    def test_boxing_day_2026_no_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday. Euronext lists Monday Dec 28, 2026 as a
        full trading day for Amsterdam (the substitute applies to Dublin)."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" not in explicit_dates

    def test_boxing_day_2027_no_substitute(self, explicit_dates):
        """Dec 26, 2027 is Sunday — no substitute Tuesday Dec 28."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXAMSEaster:
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

    def test_ascension_is_a_trading_day(self, explicit_dates):
        """Easter + 39 days: Euronext Amsterdam is open (only Oslo closes)."""
        for day in ("2025-05-29", "2026-05-14", "2027-05-06", "2028-05-25", "2029-05-10"):
            assert day not in explicit_dates
        assert not [e for e in explicit_dates.values() if "Ascension" in e["name"]]

    def test_whit_monday_is_a_trading_day(self, explicit_dates):
        """Easter + 50 days: Euronext Amsterdam is open (only Oslo closes)."""
        for day in ("2025-06-09", "2026-05-25", "2027-05-17", "2028-06-05", "2029-05-21"):
            assert day not in explicit_dates
        assert not [e for e in explicit_dates.values() if "Whit" in e["name"]]


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXAMSStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Netherlands weekend is Saturday-Sunday."""
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

    def test_all_statuses_closed(self, explicit_dates):
        """Netherlands has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xams, explicit_dates):
        start = date.fromisoformat(xams["generation_range"][0])
        end = date.fromisoformat(xams["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~25 entries: 6 closures x 5 years, minus weekends."""
        assert 20 <= len(explicit_dates) <= 35, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "euronext.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXAMSWeekendPattern:
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

class TestXAMSSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday (Labour Day)

    def test_no_substitute_holidays(self, explicit_dates):
        """Euronext Amsterdam does not move weekend holidays."""
        names = [e["name"] for e in explicit_dates.values() if "substitute" in e["name"].lower()]
        assert names == []


# ──────────────────────────────────────────────────────────────
# Regression: dates found by tools/divergence_test.py
# Registry and both reference libraries disagreed on 9 dates. Euronext's own
# 2025 and 2026 calendars side with the libraries on all 9.
# ──────────────────────────────────────────────────────────────

# Euronext Amsterdam "Closed" rows, 2025 and 2026 (half days on Dec 24 and
# Dec 31 are trading days).
OFFICIAL_CLOSED_2025 = {
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-01",
    "2025-12-25", "2025-12-26",
}
OFFICIAL_CLOSED_2026 = {
    "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-12-25",
}


class TestXAMSDivergenceRegression:
    def test_labour_day_2026_is_closed(self, explicit_dates):
        """The date the divergence report flagged first: Friday 2026-05-01."""
        assert date.fromisoformat("2026-05-01").weekday() == 4
        assert explicit_dates["2026-05-01"]["status"] == "closed"

    def test_closures_match_euronext_2025(self, explicit_dates):
        assert {d for d in explicit_dates if d.startswith("2025")} == OFFICIAL_CLOSED_2025

    def test_closures_match_euronext_2026(self, explicit_dates):
        assert {d for d in explicit_dates if d.startswith("2026")} == OFFICIAL_CLOSED_2026

    @pytest.mark.parametrize("day", [
        "2025-05-05",  # Liberation Day
        "2025-05-29",  # Ascension Day
        "2025-06-09",  # Whit Monday
        "2026-04-27",  # King's Day
        "2026-05-14",  # Ascension Day
        "2026-05-25",  # Whit Monday
        "2026-12-28",  # substitute for Boxing Day (Dublin only)
    ])
    def test_full_trading_day_is_open(self, explicit_dates, day):
        assert date.fromisoformat(day).weekday() < 5
        assert day not in explicit_dates

    def test_built_calendar_matches(self):
        """The shipped calendar.json carries the same fix."""
        path = Path(__file__).parent.parent / "calendar.json"
        with open(path) as f:
            cal = json.load(f)
        entry = next(e for e in cal["exchanges"] if e["code"] == "XAMS")
        closed = {
            h["date"]
            for h in entry["holidays"]["explicit"] + entry["holidays"]["generated"]
            if h["status"] == "closed"
        }
        assert {d for d in closed if d.startswith("2025")} == OFFICIAL_CLOSED_2025
        assert {d for d in closed if d.startswith("2026")} == OFFICIAL_CLOSED_2026