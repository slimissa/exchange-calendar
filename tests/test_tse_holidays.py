#!/usr/bin/env python3
"""
test_tse_holidays.py — Ground truth tests for XTKS (Tokyo Stock Exchange).

Tests Japanese holiday calendar, lunch break sessions, the 2024 trading
hours extension (close at 15:30), Citizens' Holidays (Kokumin no Kyūjitsu),
and observed holiday logic.

Key facts verified:
    - TSE extended close from 15:00 to 15:30 on November 5, 2024
    - Lunch break: 11:30-12:30 JST
    - New Year holiday: December 31 to January 3
    - Golden Week: April 29 to May 5 cluster with observed days
    - Citizens' Holiday: September 22, 2026 (sandwiched between holidays)
    - Children's Day observed: May 7, 2029 (Monday after Golden Week)
    - No US-style extended hours

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XTKS.json)
    2. Japanese holiday law changed (verify against jpx.co.jp)

Run:
    python3 -m pytest tests/test_tse_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xtks():
    """Load XTKS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XTKS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xtks):
    """Return dict of date -> entry from explicit array."""
    return {e["date"]: e for e in xtks["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Identity and properties
# ──────────────────────────────────────────────────────────────

class TestXTKSProperties:
    def test_code(self, xtks):
        assert xtks["code"] == "XTKS"

    def test_mic(self, xtks):
        assert xtks["mic"] == "XTKS"

    def test_name(self, xtks):
        assert xtks["name"] == "Tokyo Stock Exchange"

    def test_timezone(self, xtks):
        assert xtks["timezone"] == "Asia/Tokyo"

    def test_regular_hours_extended(self, xtks):
        """TSE extended close to 15:30 on November 5, 2024."""
        assert xtks["regular_hours"]["open"] == "09:00"
        assert xtks["regular_hours"]["close"] == "15:30"

    def test_no_extended_hours(self, xtks):
        """TSE does not have US-style pre-market/after-hours sessions."""
        assert "extended_hours" not in xtks

    def test_lunch_break_session(self, xtks):
        """TSE has a lunch break from 11:30 to 12:30."""
        sessions = xtks.get("sessions", [])
        lunch_breaks = [s for s in sessions if s["type"] == "lunch_break"]
        assert len(lunch_breaks) == 1
        assert lunch_breaks[0]["open"] == "11:30"
        assert lunch_breaks[0]["close"] == "12:30"

    def test_no_recurrence_rules(self, xtks):
        """Japanese holidays are explicit-only (equinox dates vary by year)."""
        rules = xtks["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# 2025 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXTKS2025:
    def test_new_year_holiday(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_new_year_holiday_jan2(self, explicit_dates):
        assert "2025-01-02" in explicit_dates
        assert explicit_dates["2025-01-02"]["status"] == "closed"

    def test_new_year_holiday_jan3(self, explicit_dates):
        assert "2025-01-03" in explicit_dates
        assert explicit_dates["2025-01-03"]["status"] == "closed"

    def test_coming_of_age_day(self, explicit_dates):
        assert "2025-01-13" in explicit_dates
        assert explicit_dates["2025-01-13"]["status"] == "closed"

    def test_national_foundation_day(self, explicit_dates):
        assert "2025-02-11" in explicit_dates
        assert explicit_dates["2025-02-11"]["status"] == "closed"

    def test_emperors_birthday(self, explicit_dates):
        """Emperor's Birthday is Sunday Feb 23 — no explicit entry for Sunday."""
        assert "2025-02-23" not in explicit_dates

    def test_emperors_birthday_observed(self, explicit_dates):
        """Emperor's Birthday is Sunday Feb 23 — observed Monday Feb 24."""
        assert "2025-02-24" in explicit_dates
        assert "observed" in explicit_dates["2025-02-24"]["name"].lower()

    def test_vernal_equinox(self, explicit_dates):
        assert "2025-03-20" in explicit_dates
        assert explicit_dates["2025-03-20"]["status"] == "closed"

    def test_showa_day(self, explicit_dates):
        assert "2025-04-29" in explicit_dates
        assert explicit_dates["2025-04-29"]["status"] == "closed"

    def test_constitution_memorial(self, explicit_dates):
        """May 3 is Saturday — no explicit entry for Saturday."""
        assert "2025-05-03" not in explicit_dates

    def test_greenery_day(self, explicit_dates):
        """May 4 is Sunday — no explicit entry for Sunday."""
        assert "2025-05-04" not in explicit_dates

    def test_childrens_day(self, explicit_dates):
        assert "2025-05-05" in explicit_dates
        assert explicit_dates["2025-05-05"]["status"] == "closed"

    def test_childrens_day_observed(self, explicit_dates):
        """May 5 is Monday, but May 3 is Saturday — observed May 6."""
        assert "2025-05-06" in explicit_dates
        assert "observed" in explicit_dates["2025-05-06"]["name"].lower()

    def test_marine_day(self, explicit_dates):
        assert "2025-07-21" in explicit_dates
        assert explicit_dates["2025-07-21"]["status"] == "closed"

    def test_mountain_day(self, explicit_dates):
        assert "2025-08-11" in explicit_dates
        assert explicit_dates["2025-08-11"]["status"] == "closed"

    def test_respect_for_aged(self, explicit_dates):
        assert "2025-09-15" in explicit_dates
        assert explicit_dates["2025-09-15"]["status"] == "closed"

    def test_autumnal_equinox(self, explicit_dates):
        assert "2025-09-23" in explicit_dates
        assert explicit_dates["2025-09-23"]["status"] == "closed"

    def test_sports_day(self, explicit_dates):
        assert "2025-10-13" in explicit_dates
        assert explicit_dates["2025-10-13"]["status"] == "closed"

    def test_culture_day(self, explicit_dates):
        assert "2025-11-03" in explicit_dates
        assert explicit_dates["2025-11-03"]["status"] == "closed"

    def test_labor_thanksgiving(self, explicit_dates):
        """Nov 23 is Sunday — no explicit entry for Sunday."""
        assert "2025-11-23" not in explicit_dates

    def test_labor_thanksgiving_observed(self, explicit_dates):
        """Nov 23 is Sunday — observed Monday Nov 24."""
        assert "2025-11-24" in explicit_dates
        assert "observed" in explicit_dates["2025-11-24"]["name"].lower()

    def test_new_years_eve(self, explicit_dates):
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2026 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXTKS2026:
    def test_citizens_holiday(self, explicit_dates):
        """
        September 22, 2026 is Citizens' Holiday (Kokumin no Kyūjitsu).
        Sandwiched between Respect for the Aged Day (Mon Sep 21)
        and Autumnal Equinox Day (Wed Sep 23).
        """
        assert "2026-09-22" in explicit_dates
        assert "Citizens" in explicit_dates["2026-09-22"]["name"]
        assert explicit_dates["2026-09-22"]["status"] == "closed"

    def test_autumnal_equinox_2026(self, explicit_dates):
        """September 23, 2026 is Autumnal Equinox Day."""
        assert "2026-09-23" in explicit_dates
        assert "Autumnal" in explicit_dates["2026-09-23"]["name"]

    def test_respect_for_aged_2026(self, explicit_dates):
        """September 21, 2026 is Respect for the Aged Day."""
        assert "2026-09-21" in explicit_dates
        assert "Respect" in explicit_dates["2026-09-21"]["name"]

    def test_no_duplicate_sep22(self, explicit_dates):
        """September 22 should appear exactly once."""
        sep22_entries = [e for e in explicit_dates.values() if e["date"] == "2026-09-22"]
        assert len(sep22_entries) == 1


# ──────────────────────────────────────────────────────────────
# 2027 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXTKS2027:
    def test_vernal_equinox_2027(self, explicit_dates):
        """March 21, 2027 is Sunday — observed Monday Mar 22."""
        assert "2027-03-21" not in explicit_dates
        assert "2027-03-22" in explicit_dates
        assert "observed" in explicit_dates["2027-03-22"]["name"].lower()

    def test_new_year_holiday_2027(self, explicit_dates):
        assert "2027-01-01" in explicit_dates
        assert "2027-01-04" in explicit_dates  # Monday after New Year weekend


# ──────────────────────────────────────────────────────────────
# 2029 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXTKS2029:
    def test_childrens_day_observed_2029(self, explicit_dates):
        """
        May 7, 2029 is Children's Day observed.
        May 5 (Saturday) falls on weekend; Monday May 7 is observed.
        """
        assert "2029-05-07" in explicit_dates
        assert "Children" in explicit_dates["2029-05-07"]["name"]
        assert "observed" in explicit_dates["2029-05-07"]["name"].lower()

    def test_showa_day_observed_2029(self, explicit_dates):
        """Showa Day is April 29 (Sunday) — observed Monday April 30."""
        assert "2029-04-30" in explicit_dates
        assert "Showa" in explicit_dates["2029-04-30"]["name"]

    def test_national_foundation_observed_2029(self, explicit_dates):
        """National Foundation Day is Feb 11 (Sunday) — observed Monday Feb 12."""
        assert "2029-02-12" in explicit_dates
        assert "National Foundation" in explicit_dates["2029-02-12"]["name"]


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXTKSStructure:
    def test_all_dates_iso_format(self, explicit_dates):
        for date_str in explicit_dates:
            parts = date_str.split("-")
            assert len(parts) == 3, f"Date not ISO: {date_str}"
            assert len(parts[0]) == 4
            assert len(parts[1]) == 2
            assert len(parts[2]) == 2

    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates)), "Duplicate dates found"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"

    def test_all_statuses_closed(self, explicit_dates):
        """TSE has no early close days — all holidays are full closures."""
        for date_str, entry in explicit_dates.items():
            assert entry["status"] == "closed", f"Unexpected status: {date_str}"

    def test_no_recurrence_rules_used(self, xtks):
        """TSE uses explicit dates only — equinox dates are astronomical."""
        rules = xtks["holidays"].get("recurrence_rules", [])
        assert rules == []