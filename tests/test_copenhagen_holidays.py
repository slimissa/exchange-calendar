#!/usr/bin/env python3
"""
test_copenhagen_holidays.py — Ground truth tests for XCSE (Nasdaq Copenhagen).

Key facts verified:
    - Maundy Thursday (Easter - 3) is a Danish market closure
    - Constitution Day (June 5) is a Danish statutory holiday
    - 2028: Constitution Day and Whit Monday both fall on June 5 (merged)
    - Christmas Eve, Christmas Day, Boxing Day, New Year's Eve are closures
    - Denmark does NOT shift holidays from weekends
    - No lunch break (continuous trading)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XCSE.json)
    2. Danish holiday announcements changed (verify against nasdaqomxnordic.com)

Run:
    python3 -m pytest tests/test_copenhagen_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xcse():
    """Load XCSE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XCSE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xcse):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xcse["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXCSEProperties:
    def test_code(self, xcse):
        assert xcse["code"] == "XCSE"

    def test_mic(self, xcse):
        assert xcse["mic"] == "XCSE"

    def test_name(self, xcse):
        assert xcse["name"] == "Nasdaq Copenhagen"

    def test_timezone(self, xcse):
        assert xcse["timezone"] == "Europe/Copenhagen"

    def test_regular_hours(self, xcse):
        assert xcse["regular_hours"]["open"] == "09:00"
        assert xcse["regular_hours"]["close"] == "17:00"

    def test_no_lunch_break(self, xcse):
        lunch = [s for s in xcse.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xcse):
        assert xcse["extended_hours"]["pre_market"]["open"] == "08:00"
        assert xcse["extended_hours"]["after_hours"]["close"] == "17:20"


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXCSEFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_labour_day_2025_is_not_a_closing_day(self, explicit_dates):
        """Nasdaq's 2025 schedule for Copenhagen has no 1 May closure."""
        assert "2025-05-01" not in explicit_dates

    def test_constitution_day_2025(self, explicit_dates):
        assert "2025-06-05" in explicit_dates
        assert "Constitution" in explicit_dates["2025-06-05"]["name"]

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        assert "2025-12-26" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates

    def test_constitution_day_2026(self, explicit_dates):
        assert "2026-06-05" in explicit_dates

    def test_constitution_day_2029(self, explicit_dates):
        assert "2029-06-05" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2028 merged Constitution Day / Whit Monday
# ──────────────────────────────────────────────────────────────

class TestXCSE2028Merged:
    def test_merged_date(self, explicit_dates):
        """June 5, 2028 — both Constitution Day and Whit Monday."""
        assert "2028-06-05" in explicit_dates
        name = explicit_dates["2028-06-05"]["name"]
        assert "Constitution" in name
        assert "Whit Monday" in name

    def test_no_duplicate(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert dates.count("2028-06-05") == 1

    def test_only_one_june5_2028(self, xcse):
        """No duplicate entries for 2028-06-05 in the raw data."""
        entries = [e for e in xcse["holidays"]["explicit"] if e["date"] == "2028-06-05"]
        assert len(entries) == 1


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXCSEEaster:
    def test_maundy_thursday_2025(self, explicit_dates):
        assert "2025-04-17" in explicit_dates
        assert "Maundy" in explicit_dates["2025-04-17"]["name"]

    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        assert "2025-04-21" in explicit_dates

    def test_ascension_2025(self, explicit_dates):
        assert "2025-05-29" in explicit_dates

    def test_whit_monday_2025(self, explicit_dates):
        assert "2025-06-09" in explicit_dates

    def test_maundy_thursday_2026(self, explicit_dates):
        assert "2026-04-02" in explicit_dates

    def test_whit_monday_2026(self, explicit_dates):
        assert "2026-05-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXCSERecurrence:
    def test_fixed_rules_exist(self, xcse):
        rules = xcse["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        # Nasdaq Copenhagen trades on 1 May: no Labour Day rule (explicit 2025-2026 entries remain).
        assert "Labour Day" not in names
        assert "Constitution Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names
        assert "New Year's Eve" in names

    def test_easter_rules(self, xcse):
        rules = xcse["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}
        assert rule_by_name["Maundy Thursday"]["rule"] == "easter_offset"
        assert rule_by_name["Maundy Thursday"]["offset_days"] == -3
        assert rule_by_name["Good Friday"]["offset_days"] == -2
        assert rule_by_name["Easter Monday"]["offset_days"] == 1
        assert rule_by_name["Ascension Day"]["offset_days"] == 39
        assert rule_by_name["Whit Monday"]["offset_days"] == 50


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXCSEStructure:
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
        """Nasdaq Copenhagen has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries: 12 holidays × 5 years."""
        assert 45 <= len(explicit_dates) <= 65


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


class TestFutureYearFixes:
    """Nasdaq Copenhagen's 2026 list closes the Friday after Ascension Day and
    does not close on 1 May."""

    @pytest.mark.parametrize("day", ["2027-05-07", "2028-05-26", "2029-05-11"])
    def test_day_after_ascension_is_closed(self, day):
        assert day in _closed("XCSE", int(day[:4]))

    @pytest.mark.parametrize("day", ["2028-05-01", "2029-05-01"])
    def test_labour_day_is_a_trading_day(self, day):
        assert day not in _closed("XCSE", int(day[:4]))


class TestMayFirstIsATradingDay:
    """Nasdaq's holiday schedule lists no 1 May closure for Copenhagen in 2025 or
    2026, and closes the Friday after Ascension Day."""

    @pytest.mark.parametrize("day", ["2025-05-01", "2026-05-01", "2028-05-01", "2029-05-01"])
    def test_may_first_is_a_trading_day(self, day):
        assert day not in _closed("XCSE", int(day[:4]))

    @pytest.mark.parametrize("day", ["2025-05-30", "2026-05-15"])
    def test_day_after_ascension_is_closed(self, day):
        assert day in _closed("XCSE", int(day[:4]))
