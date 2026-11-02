#!/usr/bin/env python3
"""
test_istanbul_holidays.py — Ground truth tests for XIST (Borsa Istanbul).

Key facts verified:
    - Turkey does NOT shift weekend holidays to Monday
    - Republic Day Eve (Oct 28) is a half-day (early close 13:00)
    - Fixed national holidays use fixed_date (no weekend adjustment)
    - No lunch break (continuous trading)
    - Weekend: Saturday-Sunday

Note: Islamic holidays (Ramadan Feast, Sacrifice Feast) are NOT included
in this test because their dates require official Diyanet announcements.
They must be added explicitly when the dates are confirmed.

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XIST.json)
    2. Turkish holiday announcements changed (verify against borsaistanbul.com)

Run:
    python3 -m pytest tests/test_istanbul_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xist():
    """Load XIST.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XIST.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xist):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xist["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXISTProperties:
    def test_code(self, xist):
        assert xist["code"] == "XIST"

    def test_mic(self, xist):
        assert xist["mic"] == "XIST"

    def test_name(self, xist):
        assert xist["name"] == "Borsa Istanbul"

    def test_timezone(self, xist):
        assert xist["timezone"] == "Europe/Istanbul"

    def test_regular_hours(self, xist):
        assert xist["regular_hours"]["open"] == "10:00"
        assert xist["regular_hours"]["close"] == "18:00"

    def test_no_lunch_break(self, xist):
        lunch = [s for s in xist.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xist):
        assert xist["extended_hours"]["pre_market"]["open"] == "09:40"
        assert xist["extended_hours"]["after_hours"]["close"] == "18:10"


# ──────────────────────────────────────────────────────────────
# 2025 holidays
# ──────────────────────────────────────────────────────────────

class TestXIST2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_national_sovereignty(self, explicit_dates):
        assert "2025-04-23" in explicit_dates
        assert "Sovereignty" in explicit_dates["2025-04-23"]["name"]

    def test_labour_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_ataturk_youth_sports(self, explicit_dates):
        assert "2025-05-19" in explicit_dates
        assert "Atatürk" in explicit_dates["2025-05-19"]["name"]

    def test_democracy_day(self, explicit_dates):
        assert "2025-07-15" in explicit_dates
        assert "Democracy" in explicit_dates["2025-07-15"]["name"]

    def test_victory_day_saturday(self, explicit_dates):
        """Aug 30, 2025 is Saturday — no explicit entry."""
        assert "2025-08-30" not in explicit_dates

    def test_republic_day_eve_half_day(self, explicit_dates):
        """Oct 28, 2025 is Tuesday — half-day."""
        assert "2025-10-28" in explicit_dates
        assert explicit_dates["2025-10-28"]["status"] == "early_close"
        assert explicit_dates["2025-10-28"]["early_close_time"] == "13:00"

    def test_republic_day(self, explicit_dates):
        assert "2025-10-29" in explicit_dates
        assert explicit_dates["2025-10-29"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2026 holidays
# ──────────────────────────────────────────────────────────────

class TestXIST2026:
    def test_new_year(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_national_sovereignty(self, explicit_dates):
        assert "2026-04-23" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2026-05-01" in explicit_dates

    def test_ataturk(self, explicit_dates):
        assert "2026-05-19" in explicit_dates

    def test_democracy(self, explicit_dates):
        assert "2026-07-15" in explicit_dates

    def test_victory_day_sunday(self, explicit_dates):
        """Aug 30, 2026 is Sunday — no explicit entry."""
        assert "2026-08-30" not in explicit_dates

    def test_republic_day_eve(self, explicit_dates):
        assert "2026-10-28" in explicit_dates
        assert explicit_dates["2026-10-28"]["status"] == "early_close"

    def test_republic_day(self, explicit_dates):
        assert "2026-10-29" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2027 holidays
# ──────────────────────────────────────────────────────────────

class TestXIST2027:
    def test_new_year(self, explicit_dates):
        assert "2027-01-01" in explicit_dates

    def test_national_sovereignty(self, explicit_dates):
        assert "2027-04-23" in explicit_dates

    def test_no_labour_day_saturday(self, explicit_dates):
        """May 1, 2027 is Saturday — no explicit entry."""
        assert "2027-05-01" not in explicit_dates

    def test_ataturk(self, explicit_dates):
        assert "2027-05-19" in explicit_dates

    def test_democracy(self, explicit_dates):
        assert "2027-07-15" in explicit_dates

    def test_republic_day_eve(self, explicit_dates):
        assert "2027-10-28" in explicit_dates
        assert explicit_dates["2027-10-28"]["status"] == "early_close"

    def test_republic_day(self, explicit_dates):
        assert "2027-10-29" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2028 holidays
# ──────────────────────────────────────────────────────────────

class TestXIST2028:
    def test_no_new_year_saturday(self, explicit_dates):
        """Jan 1, 2028 is Saturday — no explicit entry."""
        assert "2028-01-01" not in explicit_dates

    def test_no_national_sovereignty_sunday(self, explicit_dates):
        """Apr 23, 2028 is Sunday — no explicit entry."""
        assert "2028-04-23" not in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2028-05-01" in explicit_dates

    def test_ataturk(self, explicit_dates):
        assert "2028-05-19" in explicit_dates

    def test_no_democracy_saturday(self, explicit_dates):
        """Jul 15, 2028 is Saturday — no explicit entry."""
        assert "2028-07-15" not in explicit_dates

    def test_republic_day_eve(self, explicit_dates):
        assert "2028-10-27" in explicit_dates
        assert explicit_dates["2028-10-27"]["status"] == "early_close"

    def test_no_republic_day_sunday(self, explicit_dates):
        """Oct 29, 2028 is Sunday — no explicit entry."""
        assert "2028-10-29" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2029 holidays
# ──────────────────────────────────────────────────────────────

class TestXIST2029:
    def test_new_year(self, explicit_dates):
        assert "2029-01-01" in explicit_dates

    def test_national_sovereignty(self, explicit_dates):
        assert "2029-04-23" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2029-05-01" in explicit_dates

    def test_no_ataturk_saturday(self, explicit_dates):
        """May 19, 2029 is Saturday — no explicit entry."""
        assert "2029-05-19" not in explicit_dates

    def test_democracy(self, explicit_dates):
        """Jul 15, 2029 is Sunday — no explicit entry."""
        assert "2029-07-15" not in explicit_dates

    def test_republic_day_eve(self, explicit_dates):
        assert "2029-10-26" in explicit_dates
        assert explicit_dates["2029-10-26"]["status"] == "early_close"

    def test_republic_day(self, explicit_dates):
        assert "2029-10-29" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXISTRecurrence:
    def test_fixed_rules_exist(self, xist):
        rules = xist["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "National Sovereignty and Children's Day" in names
        assert "Labour Day" in names
        assert "Commemoration of Atatürk, Youth and Sports Day" in names
        assert "Democracy and National Unity Day" in names
        assert "Victory Day" in names
        assert "Republic Day" in names

    def test_all_use_fixed_date(self, xist):
        """Turkey does NOT shift holidays — all fixed_date."""
        rules = xist["holidays"].get("recurrence_rules", [])
        for r in rules:
            assert r["rule"] == "fixed_date", \
                f"{r['name']} should use fixed_date, not {r['rule']}"

    def test_no_islamic_rules(self, xist):
        """Islamic holidays are NOT in recurrence rules (lunisolar)."""
        rules = xist["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Ramadan Feast" not in names
        assert "Sacrifice Feast" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXISTStructure:
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

    def test_early_close_time_1300(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry["status"] == "early_close":
                assert entry["early_close_time"] == "13:00"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50 entries: the national days plus the Bayram closures and eves for 2027-2029."""
        assert 35 <= len(explicit_dates) <= 65


# ──────────────────────────────────────────────────────────────
# Future-year fixes (v2.23.6)
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


class TestBayramClosures:
    """Diyanet's 2027 religious days calendar: Ramazan Bayrami 9-11 March (eve
    Monday 8 March, half day), Kurban Bayrami 16-19 May (eve Saturday 15 May).
    2028-2029 follow the same astronomical calculation."""

    @pytest.mark.parametrize("day", ["2027-03-09", "2027-03-10", "2027-03-11",
                                     "2027-05-17", "2027-05-18", "2027-05-19",
                                     "2028-02-28", "2028-05-05", "2028-05-08",
                                     "2029-02-14", "2029-02-15", "2029-02-16",
                                     "2029-04-24", "2029-04-25", "2029-04-26", "2029-04-27"])
    def test_bayram_days_are_closed(self, day):
        assert day in _closed("XIST", int(day[:4]))

    @pytest.mark.parametrize("year,days", [
        (2027, {"2027-03-08": "13:00", "2027-10-28": "13:00"}),
        (2028, {"2028-02-25": "13:00", "2028-05-04": "13:00", "2028-10-27": "13:00"}),
        (2029, {"2029-02-13": "13:00", "2029-10-26": "13:00"}),
    ])
    def test_eves_are_half_days(self, year, days):
        assert _early("XIST", year) == days
