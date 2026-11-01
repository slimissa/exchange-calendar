#!/usr/bin/env python3
"""
test_luxembourg_holidays.py — Ground truth tests for XLUX (Luxembourg Stock Exchange).

Key facts verified:
    - Regular hours: 09:00-17:30 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Europe Day (May 9) — unique to Luxembourg
    - National Day (Jun 23)
    - Christmas Eve (Dec 24) — full closure
    - Luxembourg uses substitution for weekend holidays
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XLUX.json)
    2. Luxembourg holiday announcements changed (verify against bourse.lu)

Run:
    python3 -m pytest tests/test_luxembourg_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xlux():
    """Load XLUX.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XLUX.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xlux):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xlux["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXLUXProperties:
    def test_code(self, xlux):
        assert xlux["code"] == "XLUX"

    def test_mic(self, xlux):
        assert xlux["mic"] == "XLUX"

    def test_name(self, xlux):
        assert xlux["name"] == "Luxembourg Stock Exchange"

    def test_timezone(self, xlux):
        assert xlux["timezone"] == "Europe/Luxembourg"

    def test_regular_hours(self, xlux):
        assert xlux["regular_hours"]["open"] == "09:00"
        assert xlux["regular_hours"]["close"] == "17:30"

    def test_no_lunch_break(self, xlux):
        lunch = [s for s in xlux.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xlux):
        assert "extended_hours" not in xlux or xlux.get("extended_hours") is None

    def test_generation_range(self, xlux):
        assert "generation_range" in xlux
        assert xlux["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xlux):
        assert xlux.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xlux):
        """Luxembourg uses explicit dates only."""
        rules = xlux["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXLUXFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_saturday_is_not_moved(self, explicit_dates):
        """Jan 1, 2028 is Saturday. LuxSE follows the Euronext/T2 days: no Monday."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" not in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_saturday_is_not_moved(self, explicit_dates):
        """May 1, 2027 is Saturday: LuxSE stays open on Monday 3 May."""
        assert "2027-05-03" not in explicit_dates

    def test_europe_day_2025(self, explicit_dates):
        """May 9, 2025 is Friday."""
        assert "2025-05-09" in explicit_dates
        assert "Europe" in explicit_dates["2025-05-09"]["name"]

    def test_europe_day_2027_is_open(self, explicit_dates):
        """LuxSE trades on Europe Day; it is not a closing day."""
        assert "2027-05-09" not in explicit_dates
        assert "2027-05-10" not in explicit_dates

    def test_national_day_2025(self, explicit_dates):
        """Jun 23, 2025 is Monday."""
        assert "2025-06-23" in explicit_dates
        assert "National" in explicit_dates["2025-06-23"]["name"]

    def test_assumption_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday."""
        assert "2025-08-15" in explicit_dates
        assert "Assumption" in explicit_dates["2025-08-15"]["name"]

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-11-01" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXLUXChristmas:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — full closure."""
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "closed"

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_christmas_2027_saturday_is_not_moved(self, explicit_dates):
        """Dec 25, 2027 is Saturday: no Monday substitute."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" not in explicit_dates

    def test_boxing_day_2026_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute to Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates

    def test_boxing_day_2027_sunday_is_not_moved(self, explicit_dates):
        """Dec 26, 2027 is Sunday: no Tuesday substitute."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXLUXEaster:
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

    def test_ascension_2025(self, explicit_dates):
        """Easter + 39 days — May 29, 2025."""
        assert "2025-05-29" in explicit_dates
        assert "Ascension" in explicit_dates["2025-05-29"]["name"]

    def test_whit_monday_2025(self, explicit_dates):
        """Easter + 50 days — June 9, 2025."""
        assert "2025-06-09" in explicit_dates
        assert "Whit" in explicit_dates["2025-06-09"]["name"]

    def test_whit_monday_2028_is_open(self, explicit_dates):
        """Whit Monday (5 June 2028) is a Luxembourg public holiday on which LuxSE does not close."""
        assert "2028-06-05" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXLUXStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Luxembourg weekend is Saturday-Sunday."""
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
        """Only Christmas Eve and New Year's Eve (from 2027) are early closes."""
        for day, entry in explicit_dates.items():
            if entry["status"] == "early_close":
                assert day[5:] in ("12-24", "12-31")
                assert entry["early_close_time"] == "14:05"
            else:
                assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xlux, explicit_dates):
        start = date.fromisoformat(xlux["generation_range"][0])
        end = date.fromisoformat(xlux["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~35-45 entries: 2025 and 2026 plus the closing days for 2027-2029."""
        assert 30 <= len(explicit_dates) <= 50, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "bourse.lu" in entry["source_url"] or "luxse.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXLUXWeekendPattern:
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

class TestXLUXSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday
        assert "2025-11-01" not in explicit_dates  # Saturday

    def test_observed_and_substitute_names(self, explicit_dates):
        # No 2027-2029 substitute days: LuxSE does not move a weekend holiday.
        later = [d for d, e in explicit_dates.items() if d >= "2027"
                 and ("observed" in e["name"].lower() or "substitute" in e["name"].lower())]
        assert later == []


# ──────────────────────────────────────────────────────────────
# Future-year fixes (v2.23.5)
# ──────────────────────────────────────────────────────────────

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import generate_dates as _gd


def _closed(code, year):
    """Closed weekdays the registry produces for one year (explicit plus rules)."""
    e = json.loads((Path(__file__).parent.parent / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    days = list(e["holidays"]["explicit"]) + _gd.expand_exchange(e)
    return {d["date"] for d in days
            if d["date"].startswith(str(year)) and d["status"] == "closed"
            and date.fromisoformat(d["date"]).weekday() < 5}


def _early(code, year):
    e = json.loads((Path(__file__).parent.parent / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    return {d["date"]: d["early_close_time"] for d in e["holidays"]["explicit"]
            if d["date"].startswith(str(year)) and d["status"] == "early_close"}


class TestFutureYearClosingDays:
    """LuxSE publishes its closing days on luxse.com: the Euronext/T2 days
    (New Year, Good Friday, Easter Monday, Labour Day, Christmas, Boxing Day)
    and early closes at 14:05 on 24 and 31 December. It says explicitly that
    it stays open on public holidays such as National Day (23 June)."""

    def test_2027(self):
        assert _closed("XLUX", 2027) == {"2027-01-01", "2027-03-26", "2027-03-29"}

    def test_2028(self):
        assert _closed("XLUX", 2028) == {"2028-04-14", "2028-04-17", "2028-05-01",
                                         "2028-12-25", "2028-12-26"}

    def test_2029(self):
        assert _closed("XLUX", 2029) == {"2029-01-01", "2029-03-30", "2029-04-02",
                                         "2029-05-01", "2029-12-25", "2029-12-26"}

    @pytest.mark.parametrize("year,days", [
        (2027, {"2027-12-24": "14:05", "2027-12-31": "14:05"}),
        (2029, {"2029-12-24": "14:05", "2029-12-31": "14:05"}),
    ])
    def test_early_closes(self, year, days):
        assert _early("XLUX", year) == days

    @pytest.mark.parametrize("day", ["2027-06-23", "2028-06-23", "2027-05-06", "2029-11-01",
                                     "2028-08-15", "2029-05-09", "2027-06-23"])
    def test_luxembourg_public_holidays_are_trading_days(self, day):
        assert day not in _closed("XLUX", int(day[:4]))
