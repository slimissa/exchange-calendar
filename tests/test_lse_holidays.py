#!/usr/bin/env python3
"""
test_lse_holidays.py — Ground truth tests for XLON (London Stock Exchange).

Every test verifies a specific date against independently verified facts.
These are not generated from the registry — they are hardcoded from official
LSE trading calendars and UK Bank Holiday schedules.

Key differences from NYSE:
    - Early closes at 12:30 (not 13:00)
    - Easter Monday (not just Good Friday)
    - Bank Holidays: Early May, Spring, Summer
    - Boxing Day (December 26)
    - Christmas Eve and New Year's Eve early closes
    - No Juneteenth, MLK Day, Presidents Day, Thanksgiving
    - 2028 has NO early closes (both Dec 24 and Dec 31 fall on Sunday)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XLON.json)
    2. The ground truth is outdated (verify against londonstockexchange.com)

Run:
    python3 -m pytest tests/test_lse_holidays.py -v
"""

import json
import sys
import pytest
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load XLON data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xlon():
    """Load XLON.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XLON.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xlon):
    """Return a dict of date -> entry from the explicit array."""
    return {e["date"]: e for e in xlon["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# 2025 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXLON2025:
    def test_new_years_day_closed(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["status"] == "closed"

    def test_easter_monday_closed(self, explicit_dates):
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["status"] == "closed"

    def test_early_may_bank_holiday_closed(self, explicit_dates):
        assert "2025-05-05" in explicit_dates
        assert explicit_dates["2025-05-05"]["status"] == "closed"

    def test_spring_bank_holiday_closed(self, explicit_dates):
        assert "2025-05-26" in explicit_dates
        assert explicit_dates["2025-05-26"]["status"] == "closed"

    def test_summer_bank_holiday_closed(self, explicit_dates):
        assert "2025-08-25" in explicit_dates
        assert explicit_dates["2025-08-25"]["status"] == "closed"

    def test_christmas_eve_early_close(self, explicit_dates):
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "early_close"
        assert explicit_dates["2025-12-24"]["early_close_time"] == "12:30"

    def test_christmas_day_closed(self, explicit_dates):
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["status"] == "closed"

    def test_boxing_day_closed(self, explicit_dates):
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["status"] == "closed"

    def test_new_years_eve_early_close(self, explicit_dates):
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["status"] == "early_close"
        assert explicit_dates["2025-12-31"]["early_close_time"] == "12:30"


# ──────────────────────────────────────────────────────────────
# 2026 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXLON2026:
    def test_new_years_day_closed(self, explicit_dates):
        assert "2026-01-01" in explicit_dates
        assert explicit_dates["2026-01-01"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2026-04-03" in explicit_dates
        assert explicit_dates["2026-04-03"]["status"] == "closed"

    def test_easter_monday_closed(self, explicit_dates):
        assert "2026-04-06" in explicit_dates
        assert explicit_dates["2026-04-06"]["status"] == "closed"

    def test_early_may_bank_holiday_closed(self, explicit_dates):
        assert "2026-05-04" in explicit_dates
        assert explicit_dates["2026-05-04"]["status"] == "closed"

    def test_spring_bank_holiday_closed(self, explicit_dates):
        assert "2026-05-25" in explicit_dates
        assert explicit_dates["2026-05-25"]["status"] == "closed"

    def test_summer_bank_holiday_closed(self, explicit_dates):
        assert "2026-08-31" in explicit_dates
        assert explicit_dates["2026-08-31"]["status"] == "closed"

    def test_christmas_eve_early_close(self, explicit_dates):
        assert "2026-12-24" in explicit_dates
        assert explicit_dates["2026-12-24"]["status"] == "early_close"
        assert explicit_dates["2026-12-24"]["early_close_time"] == "12:30"

    def test_christmas_day_closed(self, explicit_dates):
        assert "2026-12-25" in explicit_dates
        assert explicit_dates["2026-12-25"]["status"] == "closed"

    def test_boxing_day_substitute_closed(self, explicit_dates):
        """December 26, 2026 is Saturday — observed Monday December 28."""
        assert "2026-12-28" in explicit_dates
        assert explicit_dates["2026-12-28"]["status"] == "closed"
        assert "substitute" in explicit_dates["2026-12-28"]["name"].lower()

    def test_new_years_eve_early_close(self, explicit_dates):
        assert "2026-12-31" in explicit_dates
        assert explicit_dates["2026-12-31"]["status"] == "early_close"
        assert explicit_dates["2026-12-31"]["early_close_time"] == "12:30"


# ──────────────────────────────────────────────────────────────
# 2027 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXLON2027:
    def test_new_years_day_closed(self, explicit_dates):
        assert "2027-01-01" in explicit_dates
        assert explicit_dates["2027-01-01"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2027-03-26" in explicit_dates
        assert explicit_dates["2027-03-26"]["status"] == "closed"

    def test_easter_monday_closed(self, explicit_dates):
        assert "2027-03-29" in explicit_dates
        assert explicit_dates["2027-03-29"]["status"] == "closed"

    def test_early_may_bank_holiday_closed(self, explicit_dates):
        assert "2027-05-03" in explicit_dates
        assert explicit_dates["2027-05-03"]["status"] == "closed"

    def test_spring_bank_holiday_closed(self, explicit_dates):
        assert "2027-05-31" in explicit_dates
        assert explicit_dates["2027-05-31"]["status"] == "closed"

    def test_summer_bank_holiday_closed(self, explicit_dates):
        assert "2027-08-30" in explicit_dates
        assert explicit_dates["2027-08-30"]["status"] == "closed"

    def test_christmas_eve_early_close(self, explicit_dates):
        assert "2027-12-24" in explicit_dates
        assert explicit_dates["2027-12-24"]["status"] == "early_close"
        assert explicit_dates["2027-12-24"]["early_close_time"] == "12:30"

    def test_christmas_day_substitute_closed(self, explicit_dates):
        """December 25, 2027 is Saturday — observed Monday December 27."""
        assert "2027-12-27" in explicit_dates
        assert explicit_dates["2027-12-27"]["status"] == "closed"

    def test_boxing_day_substitute_closed(self, explicit_dates):
        """December 26, 2027 is Sunday — observed Tuesday December 28."""
        assert "2027-12-28" in explicit_dates
        assert explicit_dates["2027-12-28"]["status"] == "closed"

    def test_new_years_eve_early_close(self, explicit_dates):
        assert "2027-12-31" in explicit_dates
        assert explicit_dates["2027-12-31"]["status"] == "early_close"
        assert explicit_dates["2027-12-31"]["early_close_time"] == "12:30"


# ──────────────────────────────────────────────────────────────
# 2028 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXLON2028:
    def test_new_years_day_substitute_closed(self, explicit_dates):
        """January 1, 2028 is Saturday — observed Monday January 3."""
        assert "2028-01-03" in explicit_dates
        assert explicit_dates["2028-01-03"]["status"] == "closed"

    def test_no_new_years_day_actual_date(self, explicit_dates):
        """January 1, 2028 is Saturday. No entry for actual date."""
        assert "2028-01-01" not in explicit_dates

    def test_good_friday_closed(self, explicit_dates):
        assert "2028-04-14" in explicit_dates
        assert explicit_dates["2028-04-14"]["status"] == "closed"

    def test_easter_monday_closed(self, explicit_dates):
        assert "2028-04-17" in explicit_dates
        assert explicit_dates["2028-04-17"]["status"] == "closed"

    def test_early_may_bank_holiday_closed(self, explicit_dates):
        assert "2028-05-01" in explicit_dates
        assert explicit_dates["2028-05-01"]["status"] == "closed"

    def test_spring_bank_holiday_closed(self, explicit_dates):
        assert "2028-05-29" in explicit_dates
        assert explicit_dates["2028-05-29"]["status"] == "closed"

    def test_summer_bank_holiday_closed(self, explicit_dates):
        assert "2028-08-28" in explicit_dates
        assert explicit_dates["2028-08-28"]["status"] == "closed"

    def test_no_christmas_eve_early_close(self, explicit_dates):
        """December 24, 2028 is Sunday. No early close."""
        assert "2028-12-24" not in explicit_dates

    def test_christmas_day_closed(self, explicit_dates):
        assert "2028-12-25" in explicit_dates
        assert explicit_dates["2028-12-25"]["status"] == "closed"

    def test_boxing_day_closed(self, explicit_dates):
        assert "2028-12-26" in explicit_dates
        assert explicit_dates["2028-12-26"]["status"] == "closed"

    def test_no_new_years_eve_early_close(self, explicit_dates):
        """December 31, 2028 is Sunday. No early close."""
        assert "2028-12-31" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2029 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXLON2029:
    def test_new_years_day_closed(self, explicit_dates):
        assert "2029-01-01" in explicit_dates
        assert explicit_dates["2029-01-01"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2029-03-30" in explicit_dates
        assert explicit_dates["2029-03-30"]["status"] == "closed"

    def test_easter_monday_closed(self, explicit_dates):
        assert "2029-04-02" in explicit_dates
        assert explicit_dates["2029-04-02"]["status"] == "closed"

    def test_early_may_bank_holiday_closed(self, explicit_dates):
        assert "2029-05-07" in explicit_dates
        assert explicit_dates["2029-05-07"]["status"] == "closed"

    def test_spring_bank_holiday_closed(self, explicit_dates):
        assert "2029-05-28" in explicit_dates
        assert explicit_dates["2029-05-28"]["status"] == "closed"

    def test_summer_bank_holiday_closed(self, explicit_dates):
        assert "2029-08-27" in explicit_dates
        assert explicit_dates["2029-08-27"]["status"] == "closed"

    def test_christmas_eve_early_close(self, explicit_dates):
        assert "2029-12-24" in explicit_dates
        assert explicit_dates["2029-12-24"]["status"] == "early_close"
        assert explicit_dates["2029-12-24"]["early_close_time"] == "12:30"

    def test_christmas_day_closed(self, explicit_dates):
        assert "2029-12-25" in explicit_dates
        assert explicit_dates["2029-12-25"]["status"] == "closed"

    def test_boxing_day_closed(self, explicit_dates):
        assert "2029-12-26" in explicit_dates
        assert explicit_dates["2029-12-26"]["status"] == "closed"

    def test_new_years_eve_early_close(self, explicit_dates):
        assert "2029-12-31" in explicit_dates
        assert explicit_dates["2029-12-31"]["status"] == "early_close"
        assert explicit_dates["2029-12-31"]["early_close_time"] == "12:30"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXLONStructure:
    def test_all_explicit_dates_are_iso_format(self, explicit_dates):
        for date_str in explicit_dates:
            parts = date_str.split("-")
            assert len(parts) == 3, f"Date not ISO format: {date_str}"
            assert len(parts[0]) == 4, f"Year wrong: {date_str}"
            assert len(parts[1]) == 2, f"Month wrong: {date_str}"
            assert len(parts[2]) == 2, f"Day wrong: {date_str}"

    def test_all_entries_have_source_url(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url for {date_str}"

    def test_early_close_entries_have_time(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            if entry["status"] == "early_close":
                assert "early_close_time" in entry, f"Missing time for {date_str}"
                assert entry["early_close_time"] == "12:30", f"Wrong time for {date_str}"

    def test_no_weekend_dates(self, explicit_dates):
        """No explicit entry should fall on a Saturday or Sunday."""
        from datetime import date
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Explicit date falls on weekend: {date_str} ({d.strftime('%A')})"

    def test_regular_hours_correct(self, xlon):
        assert xlon["regular_hours"]["open"] == "08:00"
        assert xlon["regular_hours"]["close"] == "16:30"

    def test_timezone_correct(self, xlon):
        assert xlon["timezone"] == "Europe/London"

    def test_code_correct(self, xlon):
        assert xlon["code"] == "XLON"
        assert xlon["mic"] == "XLON"

    def test_sessions_have_auctions(self, xlon):
        """LSE has opening and closing auction sessions."""
        sessions = xlon.get("sessions", [])
        auction_types = [s["type"] for s in sessions if s["type"] == "auction"]
        assert len(auction_types) == 2, "Expected 2 auction sessions"

    def test_no_juneteenth(self, explicit_dates):
        """LSE does not observe Juneteenth."""
        for date_str in explicit_dates:
            assert "Juneteenth" not in explicit_dates[date_str]["name"]

    def test_no_thanksgiving(self, explicit_dates):
        """LSE does not observe Thanksgiving."""
        for date_str in explicit_dates:
            assert "Thanksgiving" not in explicit_dates[date_str]["name"]

    def test_no_mlk_day(self, explicit_dates):
        """LSE does not observe Martin Luther King Jr. Day."""
        for date_str in explicit_dates:
            assert "Martin Luther King" not in explicit_dates[date_str]["name"]