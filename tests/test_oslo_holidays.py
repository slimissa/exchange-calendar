#!/usr/bin/env python3
"""
test_oslo_holidays.py — Ground truth tests for XOSL (Oslo Børs).

Key facts verified:
    - Maundy Thursday (Easter - 3) is a Norwegian market closure
    - Constitution Day (May 17) is Norwegian National Day
    - 2027: Constitution Day and Whit Monday both fall on May 17 (merged)
    - Christmas Eve, Christmas Day, Boxing Day, New Year's Eve are closures
    - Norway does NOT shift holidays from weekends
    - No lunch break (continuous trading)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XOSL.json)
    2. Norwegian holiday announcements changed (verify against euronext.com)

Run:
    python3 -m pytest tests/test_oslo_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xosl():
    """Load XOSL.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XOSL.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xosl):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xosl["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXOSLProperties:
    def test_code(self, xosl):
        assert xosl["code"] == "XOSL"

    def test_mic(self, xosl):
        assert xosl["mic"] == "XOSL"

    def test_name(self, xosl):
        assert xosl["name"] == "Oslo Børs"

    def test_timezone(self, xosl):
        assert xosl["timezone"] == "Europe/Oslo"

    def test_regular_hours(self, xosl):
        """Dated history: close 17:30 until 2012-08-03; from 2012-08-06 the
        close is the 16:25 closing uncross (ADR 0013, 4c8: Euronext Appendix,
        continuous to 16:20, uncross '16:25 Random', TAL 16:25-16:30; was
        16:30). 2026-08-03 is the Appendix's effective date; 2012-08-06 is
        marked unconfirmed."""
        hours = sorted(xosl["regular_hours"], key=lambda e: e["effective_from"])
        assert [(h["effective_from"], h["open"], h["close"]) for h in hours] == [
            ("2010-01-01", "09:00", "17:30"),
            ("2012-08-06", "09:00", "16:25"),
            ("2026-08-03", "09:00", "16:25"),
        ]
        regular = [s for s in xosl["sessions"] if s["type"] == "regular"]
        assert [(s["open"], s["close"]) for s in regular] == [("09:00", "16:25")]
        assert xosl["extended_hours"]["after_hours"] == {"open": "16:25", "close": "16:45"}
        span = xosl["verification"]["coverage"]["sources"][0]
        assert "2012-08-06" in span["unconfirmed"]

    def test_no_lunch_break(self, xosl):
        lunch = [s for s in xosl.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xosl):
        assert xosl["extended_hours"]["pre_market"]["open"] == "08:15"
        assert xosl["extended_hours"]["after_hours"]["close"] == "16:45"


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXOSLFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_constitution_day_2025(self, explicit_dates):
        """May 17, 2025 is Saturday — no explicit entry."""
        assert "2025-05-17" not in explicit_dates

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        assert "2025-12-26" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates

    def test_constitution_day_2026(self, explicit_dates):
        """May 17, 2026 is Sunday — no explicit entry."""
        assert "2026-05-17" not in explicit_dates

    def test_constitution_day_2028(self, explicit_dates):
        """May 17, 2028 is Wednesday — explicit."""
        assert "2028-05-17" in explicit_dates

    def test_constitution_day_2029(self, explicit_dates):
        """May 17, 2029 is Thursday — explicit."""
        assert "2029-05-17" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2027 merged Constitution Day / Whit Monday
# ──────────────────────────────────────────────────────────────

class TestXOSL2027Merged:
    def test_merged_date(self, explicit_dates):
        """May 17, 2027 — both Constitution Day and Whit Monday."""
        assert "2027-05-17" in explicit_dates
        name = explicit_dates["2027-05-17"]["name"]
        assert "Constitution" in name
        assert "Whit Monday" in name

    def test_no_duplicate(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert dates.count("2027-05-17") == 1


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXOSLEaster:
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


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXOSLRecurrence:
    def test_fixed_rules_exist(self, xosl):
        rules = xosl["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Labour Day" in names
        assert "Constitution Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names
        assert "New Year's Eve" in names

    def test_easter_rules(self, xosl):
        rules = xosl["holidays"].get("recurrence_rules", [])
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

class TestXOSLStructure:
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
        """In 2025-2029 every holiday is a full closure except the Wednesday
        before Easter, which Euronext lists as an Oslo half trading day
        (2025-04-16, 2026-04-01, 2027-03-24; 4c-R2). The old version of this
        test asserted there were none."""
        # 4c-R5 (ADR 0013): 2026 closes at the 13:05 uncross per Euronext's
        # schedule; 2025 and 2027 schedules are unreadable images -> 13:00.
        half_days = {"2025-04-16": "13:05", "2026-04-01": "13:05", "2027-03-24": "13:05"}
        for date_, entry in explicit_dates.items():
            if date_ in half_days:
                assert entry["status"] == "early_close", date_
                assert entry["early_close_time"] == half_days[date_], date_
            elif date_ >= "2025-01-01":
                assert entry["status"] == "closed", date_

    def test_half_days_follow_euronext_schedules(self, xosl, explicit_dates):
        """ADR 0013: Euronext's Oslo half-day schedules (2023, 2024, 2026 in
        4c-R5; 2025, 2027 in 4c8) give call 13:00-13:05 and the uncross at
        13:05, so those days close at 13:05 and cite the schedule. 2011-2022
        keep 13:00 and are listed as unconfirmed; no recheck date remains."""
        schedules = {"2023-04-05": "7620", "2024-03-27": "10309", "2025-04-16": "12510",
                     "2026-04-01": "14571", "2027-03-24": "16430"}
        halves = {d: e for d, e in explicit_dates.items() if e["status"] == "early_close"}
        for d, e in halves.items():
            if d in schedules:
                assert e["early_close_time"] == "13:05", d
                assert e["source_url"] == f"https://www.euronext.com/en/media/{schedules[d]}/download"
            else:
                assert e["early_close_time"] == "13:00", d
        spans = xosl["verification"]["coverage"]["sources"]
        unconfirmed = [u for s in spans for u in s.get("unconfirmed", [])]
        expected = sorted([d for d in halves if d not in schedules] + ["2012-08-06"])
        assert sorted(unconfirmed) == expected
        assert all(d < "2023" for d in expected)
        assert not any("recheck_date" in s for s in spans)

    def test_wednesday_before_easter_rule(self, xosl):
        """2028-2029 come from an early_close rule, Easter - 4 days, at the
        13:05 uncross of the 2023-2027 schedules (predicted; 4c8, was 13:00)."""
        rules = [r for r in xosl["holidays"]["recurrence_rules"]
                 if r.get("status") == "early_close"]
        assert rules == [{
            "early_close_time": "13:05", "effective_from": "2025-01-01",
            "name": "Wednesday before Easter (half trading day)",
            "offset_days": -4, "rule": "easter_offset",
            "status": "early_close",
        }]

    def test_holiday_count_reasonable(self, explicit_dates):
        """~49 entries in 2025-2029: 12 holidays × 5 years, minus weekend overlaps.

        Scoped to the original window: 2010-2024 is a backfill from
        exchange_calendars and has its own entries.
        """
        window = [d for d in explicit_dates if d >= "2025-01-01"]
        assert 40 <= len(window) <= 60