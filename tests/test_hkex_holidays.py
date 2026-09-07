#!/usr/bin/env python3
"""
test_hkex_holidays.py — Ground truth tests for XHKG (Hong Kong Exchange).

Tests Hong Kong holiday calendar, lunch break, auction sessions,
half-day Christmas Eve/New Year's Eve early closes, and observed
holiday logic for lunisolar festivals.

Key facts verified:
    - Regular hours: 09:30-16:00 HKT
    - Lunch break: 12:00-13:00
    - Auctions: Pre-opening at 09:20, Closing Auction at 16:10
    - Christmas Eve / New Year's Eve: half-day (early close 12:00)
    - Lunar New Year: 3-4 days depending on weekend overflow
    - Buddha's Birthday: observed Monday when falls on Sunday
    - No US-style extended hours

Run:
    python3 -m pytest tests/test_hkex_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


@pytest.fixture(scope="module")
def xhkg():
    path = Path(__file__).parent.parent / "exchanges" / "XHKG.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xhkg):
    return {e["date"]: e for e in xhkg["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXHKGProperties:
    def test_code(self, xhkg):
        assert xhkg["code"] == "XHKG"

    def test_mic(self, xhkg):
        assert xhkg["mic"] == "XHKG"

    def test_name(self, xhkg):
        assert xhkg["name"] == "Hong Kong Exchange"

    def test_timezone(self, xhkg):
        assert xhkg["timezone"] == "Asia/Hong_Kong"

    def test_regular_hours(self, xhkg):
        assert xhkg["regular_hours"]["open"] == "09:30"
        assert xhkg["regular_hours"]["close"] == "16:00"

    def test_no_extended_hours(self, xhkg):
        assert "extended_hours" not in xhkg

    def test_lunch_break(self, xhkg):
        lunch = [s for s in xhkg["sessions"] if s["type"] == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "12:00"
        assert lunch[0]["close"] == "13:00"

    def test_auction_sessions(self, xhkg):
        auctions = [s for s in xhkg["sessions"] if s["type"] == "auction"]
        assert len(auctions) == 2
        times = [a["at"] for a in auctions]
        assert "09:20" in times
        assert "16:10" in times

    def test_no_recurrence_rules(self, xhkg):
        assert xhkg["holidays"].get("recurrence_rules", []) == []


# ──────────────────────────────────────────────────────────────
# 2025
# ──────────────────────────────────────────────────────────────

class TestXHKG2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates

    def test_lunar_new_year(self, explicit_dates):
        assert "2025-01-29" in explicit_dates
        assert "2025-01-30" in explicit_dates
        assert "2025-01-31" in explicit_dates

    def test_ching_ming(self, explicit_dates):
        assert "2025-04-04" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_easter_monday(self, explicit_dates):
        assert "2025-04-21" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_buddha_birthday(self, explicit_dates):
        assert "2025-05-05" in explicit_dates

    def test_tuen_ng(self, explicit_dates):
        """May 31 is Saturday — no explicit entry."""
        assert "2025-05-31" not in explicit_dates

    def test_hksar_day(self, explicit_dates):
        assert "2025-07-01" in explicit_dates

    def test_national_day(self, explicit_dates):
        assert "2025-10-01" in explicit_dates

    def test_mid_autumn(self, explicit_dates):
        assert "2025-10-07" in explicit_dates

    def test_chung_yeung(self, explicit_dates):
        assert "2025-10-29" in explicit_dates

    def test_christmas_eve_half_day(self, explicit_dates):
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "early_close"
        assert explicit_dates["2025-12-24"]["early_close_time"] == "12:00"

    def test_christmas_day(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day(self, explicit_dates):
        assert "2025-12-26" in explicit_dates

    def test_new_years_eve_half_day(self, explicit_dates):
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "early_close"
        assert explicit_dates["2025-12-31"]["early_close_time"] == "12:00"


# ──────────────────────────────────────────────────────────────
# 2026
# ──────────────────────────────────────────────────────────────

class TestXHKG2026:
    def test_lunar_new_year(self, explicit_dates):
        assert "2026-02-17" in explicit_dates
        assert "2026-02-18" in explicit_dates
        assert "2026-02-19" in explicit_dates

    def test_buddha_birthday_observed(self, explicit_dates):
        """Buddha's Birthday is Sunday May 24 — observed Monday May 25."""
        assert "2026-05-24" not in explicit_dates
        assert "2026-05-25" in explicit_dates
        assert "observed" in explicit_dates["2026-05-25"]["name"].lower()

    def test_christmas_eve_half_day(self, explicit_dates):
        assert "2026-12-24" in explicit_dates
        assert explicit_dates["2026-12-24"]["status"] == "early_close"

    def test_new_years_eve_half_day(self, explicit_dates):
        assert "2026-12-31" in explicit_dates
        assert explicit_dates["2026-12-31"]["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# 2027
# ──────────────────────────────────────────────────────────────

class TestXHKG2027:
    def test_lunar_new_year(self, explicit_dates):
        """Feb 6 is Saturday, Feb 7 is Sunday — observed Feb 8 and Feb 9."""
        assert "2027-02-06" not in explicit_dates
        assert "2027-02-08" in explicit_dates
        assert "2027-02-09" in explicit_dates

    def test_christmas_eve_half_day(self, explicit_dates):
        assert "2027-12-24" in explicit_dates
        assert explicit_dates["2027-12-24"]["status"] == "early_close"

    def test_new_years_eve_half_day(self, explicit_dates):
        assert "2027-12-31" in explicit_dates
        assert explicit_dates["2027-12-31"]["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# 2028
# ──────────────────────────────────────────────────────────────

class TestXHKG2028:
    def test_lunar_new_year_observed(self, explicit_dates):
        """Jan 28 is Friday — 3rd day of LNY, no weekend overflow."""
        assert "2028-01-26" in explicit_dates
        assert "2028-01-27" in explicit_dates
        assert "2028-01-28" in explicit_dates

    def test_no_christmas_eve_sunday(self, explicit_dates):
        assert "2028-12-24" not in explicit_dates

    def test_no_new_years_eve_sunday(self, explicit_dates):
        assert "2028-12-31" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2029
# ──────────────────────────────────────────────────────────────

class TestXHKG2029:
    def test_lunar_new_year(self, explicit_dates):
        assert "2029-02-13" in explicit_dates
        assert "2029-02-14" in explicit_dates
        assert "2029-02-15" in explicit_dates

    def test_buddha_birthday_observed(self, explicit_dates):
        """Buddha's Birthday is Sunday May 20 — observed Monday May 21."""
        assert "2029-05-20" not in explicit_dates
        assert "2029-05-21" in explicit_dates
        assert "observed" in explicit_dates["2029-05-21"]["name"].lower()

    def test_mid_autumn_observed(self, explicit_dates):
        """Day after Mid-Autumn is Sunday Sep 23 — observed Monday Sep 24."""
        assert "2029-09-24" in explicit_dates
        assert "observed" in explicit_dates["2029-09-24"]["name"].lower()

    def test_christmas_eve_half_day(self, explicit_dates):
        assert "2029-12-24" in explicit_dates
        assert explicit_dates["2029-12-24"]["status"] == "early_close"

    def test_new_years_eve_half_day(self, explicit_dates):
        assert "2029-12-31" in explicit_dates
        assert explicit_dates["2029-12-31"]["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# Structure
# ──────────────────────────────────────────────────────────────

class TestXHKGStructure:
    def test_all_dates_iso(self, explicit_dates):
        for date_str in explicit_dates:
            parts = date_str.split("-")
            assert len(parts) == 3

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

    def test_early_close_time_1200(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry["status"] == "early_close":
                assert entry["early_close_time"] == "12:00"

    def test_lunar_holidays_explicit_only(self, xhkg):
        assert xhkg["holidays"].get("recurrence_rules", []) == []