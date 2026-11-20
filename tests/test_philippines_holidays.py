#!/usr/bin/env python3
"""
test_philippines_holidays.py — Ground truth tests for XPHS (Philippine Stock Exchange).

Key facts verified:
    - Market recess 12:00-13:00 (CN-2022-0009, 4c13)
    - Regular hours: 09:30-14:50 from 2022-03-01 (close = end of pre-close auction, ADR 0013)
    - Run-off / trading at last 14:50-15:00 (post_market)
    - Maundy Thursday (Easter - 3) is a market closure
    - Ninoy Aquino Day (Aug 21) is a statutory holiday
    - All Saints' Day (Nov 1) and All Souls' Day (Nov 2) are closures
    - Feast of the Immaculate Conception (Dec 8) is a closure
    - Christmas Eve and New Year's Eve are closures
    - National Heroes Day is last Monday of August
    - No weekend shift (Philippines does not substitute unless declared)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XPHS.json)
    2. Philippine holiday proclamations changed (verify against pse.com.ph)

Run:
    python3 -m pytest tests/test_philippines_holidays.py -v
"""

import json
import sys
import pytest
from datetime import date
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xphs():
    """Load XPHS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XPHS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xphs):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xphs["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXPHSProperties:
    def test_code(self, xphs):
        assert xphs["code"] == "XPHS"

    def test_mic(self, xphs):
        assert xphs["mic"] == "XPHS"

    def test_name(self, xphs):
        assert xphs["name"] == "Philippine Stock Exchange"

    def test_timezone(self, xphs):
        assert xphs["timezone"] == "Asia/Manila"

    def test_regular_hours(self, xphs):
        """4c13, ADR 0013: PSE CN-2022-0009 (effective 2022-03-01): pre-close
        14:45-14:50, run-off/trading at last 14:50-15:00, so the close is
        14:50. The 2010 entry is the pre-4c13 value, unconfirmed."""
        assert xphs["regular_hours"] == [
            {"close": "15:00", "effective_from": "2010-01-01", "open": "09:30"},
            {"close": "14:50", "effective_from": "2022-03-01", "open": "09:30"}]
        assert "2010-01-01" in xphs["verification"]["coverage"]["sources"][0]["unconfirmed"]

    def test_lunch_break(self, xphs):
        """4c13: CN-2022-0009 gives a market recess 12:00-13:00 (replaces the
        pre-4c13 'continuous trading, no lunch break' pin, which PSE's own
        notice contradicts)."""
        lunch = [s for s in xphs.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == [{"close": "13:00", "open": "12:00", "type": "lunch_break"}]

    def test_sessions(self, xphs):
        assert xphs["sessions"] == [
            {"close": "09:30", "open": "09:00", "type": "pre_market"},
            {"close": "14:50", "open": "09:30", "type": "regular"},
            {"close": "13:00", "open": "12:00", "type": "lunch_break"},
            {"close": "15:00", "open": "14:50", "type": "post_market"}]

    def test_after_hours(self, xphs):
        """Run-off / trading at last 14:50-15:00 (CN-2022-0009)."""
        assert xphs["extended_hours"]["after_hours"] == {"close": "15:00", "open": "14:50"}

class TestXPHSFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_day_of_valor_2025(self, explicit_dates):
        assert "2025-04-09" in explicit_dates
        assert "Kagitingan" in explicit_dates["2025-04-09"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_independence_day_2025(self, explicit_dates):
        assert "2025-06-12" in explicit_dates

    def test_bonifacio_day_2025(self, explicit_dates):
        """Nov 30, 2025 is Sunday — no explicit entry."""
        assert "2025-11-30" not in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_rizal_day_2025(self, explicit_dates):
        assert "2025-12-30" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Holy Week
# ──────────────────────────────────────────────────────────────

class TestXPHSHolyWeek:
    def test_maundy_thursday_2025(self, explicit_dates):
        assert "2025-04-17" in explicit_dates
        assert "Maundy" in explicit_dates["2025-04-17"]["name"]

    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_maundy_thursday_2026(self, explicit_dates):
        assert "2026-04-02" in explicit_dates

    def test_good_friday_2026(self, explicit_dates):
        assert "2026-04-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Additional statutory holidays
# ──────────────────────────────────────────────────────────────

class TestXPHSAdditional:
    def test_ninoy_aquino_2025(self, explicit_dates):
        assert "2025-08-21" in explicit_dates
        assert "Ninoy" in explicit_dates["2025-08-21"]["name"]

    def test_all_saints_2025(self, explicit_dates):
        """Nov 1, 2025 is Saturday — no explicit entry."""
        assert "2025-11-01" not in explicit_dates

    def test_all_souls_2025(self, explicit_dates):
        """Nov 2, 2025 is Sunday — no explicit entry."""
        assert "2025-11-02" not in explicit_dates

    def test_immaculate_conception_2025(self, explicit_dates):
        assert "2025-12-08" in explicit_dates
        assert "Immaculate" in explicit_dates["2025-12-08"]["name"]

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates

    def test_national_heroes_2025(self, explicit_dates):
        """Last Monday August — Aug 25, 2025."""
        assert "2025-08-25" in explicit_dates
        assert "Heroes" in explicit_dates["2025-08-25"]["name"]

    def test_national_heroes_2026(self, explicit_dates):
        assert "2026-08-31" in explicit_dates

    def test_national_heroes_2027(self, explicit_dates):
        assert "2027-08-30" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXPHSRecurrence:
    def test_fixed_rules_exist(self, xphs):
        rules = xphs["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Araw ng Kagitingan (Day of Valor)" in names
        assert "Labour Day" in names
        assert "Independence Day" in names
        assert "Bonifacio Day" in names
        assert "Christmas Day" in names
        assert "Rizal Day" in names

    def test_maundy_thursday_rule(self, xphs):
        rules = xphs["holidays"].get("recurrence_rules", [])
        maundy = [r for r in rules if r["name"] == "Maundy Thursday"]
        assert len(maundy) == 1
        assert maundy[0]["rule"] == "easter_offset"
        assert maundy[0]["offset_days"] == -3

    def test_national_heroes_rule(self, xphs):
        rules = xphs["holidays"].get("recurrence_rules", [])
        heroes = [r for r in rules if r["name"] == "National Heroes Day"]
        assert len(heroes) == 1
        assert heroes[0]["rule"] == "last_weekday"
        assert heroes[0]["weekday"] == "monday"
        assert heroes[0]["month"] == 8

    def test_no_islamic_rules(self, xphs):
        """Eid holidays are NOT in recurrence rules."""
        rules = xphs["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Eid" not in names
        assert "Chinese New Year" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXPHSStructure:
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
        """PSE has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """Scoped to 2025-2029: 73 (unchanged by 4c12). 2010-2024 backfill:
        249 exchange_calendars closures (4c12)."""
        assert len([d for d in explicit_dates if d >= "2025"]) == 73
        assert len([d for d in explicit_dates if d < "2025"]) == 249

    def test_backfill_2010_2024(self, xphs, explicit_dates):
        """4c12: generation starts 2010; every 2010-2024 entry cites
        exchange_calendars; no one-off is moved to ad_hoc_closures without
        PSE's own word."""
        assert xphs["generation_range"] == ["2010-01-01", "2029-12-31"]
        assert {e["source_url"] for d, e in explicit_dates.items() if d < "2025"} == {
            "github.com/gerrymanoim/exchange_calendars"}
        assert xphs.get("ad_hoc_closures", []) == []
        span = xphs["verification"]["coverage"]["sources"][0]
        assert (span["from"], span["to"], span["source"]) == (
            "2010-01-01", "2024-12-31", "exchange_calendars")


# ──────────────────────────────────────────────────────────────
# Proclaimed holidays that PSE closes for, 2025 and 2026
# ──────────────────────────────────────────────────────────────

class TestXPHSProclaimedDays2025And2026:
    """PSE circulars (CN-2025-0010, -0020, -0038, CN-2026-0010) and the
    proclamations they cite (727, 839, 878, 1006, 1189, 1264): the exchange
    does not trade on the Chinese New Year special non-working days, the Eid'l
    Fitr and Eid'l Adha holidays, the 12 May 2025 elections or 31 October 2025.
    All Souls' Day (2 November 2026) is an additional special non-working day
    under Proclamation 1006."""

    @staticmethod
    def _closed_set(explicit_dates, year):
        return {d for d, e in explicit_dates.items()
                if d.startswith(str(year)) and e["status"] == "closed"}

    def test_2025_closed_set(self, explicit_dates):
        assert self._closed_set(explicit_dates, 2025) == {
            "2025-01-01", "2025-01-29", "2025-04-01", "2025-04-09", "2025-04-17",
            "2025-04-18", "2025-05-01", "2025-05-12", "2025-06-06", "2025-06-12",
            "2025-08-21", "2025-08-25", "2025-10-31", "2025-12-08", "2025-12-24",
            "2025-12-25", "2025-12-30", "2025-12-31"}

    def test_2026_closed_set(self, explicit_dates):
        assert self._closed_set(explicit_dates, 2026) == {
            "2026-01-01", "2026-02-17", "2026-03-20", "2026-04-02", "2026-04-03",
            "2026-04-09", "2026-05-01", "2026-05-27", "2026-06-12", "2026-08-21",
            "2026-08-31", "2026-11-02", "2026-11-30", "2026-12-08", "2026-12-24",
            "2026-12-25", "2026-12-30", "2026-12-31"}

    @pytest.mark.parametrize("day", [
        "2025-01-29", "2025-04-01", "2025-05-12", "2025-06-06", "2025-10-31",
        "2026-02-17", "2026-03-20", "2026-05-27", "2026-11-02"])
    def test_proclaimed_days_are_closed(self, explicit_dates, day):
        assert explicit_dates[day]["status"] == "closed"
