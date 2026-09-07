#!/usr/bin/env python3
"""
test_nyse_holidays.py — Ground truth tests for XNYS (New York Stock Exchange).

Every test verifies a specific date against independently verified facts.
These are not generated from the registry — they are hardcoded from official
NYSE holiday calendars and represent the ground truth the registry must match.

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XNYS.json)
    2. The ground truth is outdated (verify against nyse.com and update)

Run:
    python3 -m pytest tests/test_nyse_holidays.py -v
"""

import json
import sys
import pytest
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load XNYS data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xnys():
    """Load XNYS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xnys):
    """Return a dict of date -> entry from the explicit array."""
    return {e["date"]: e for e in xnys["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# 2025 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNY2025:
    def test_new_years_day_closed(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_national_day_of_mourning_closed(self, explicit_dates):
        assert "2025-01-09" in explicit_dates
        assert explicit_dates["2025-01-09"]["status"] == "closed"
        assert "Carter" in explicit_dates["2025-01-09"]["name"]

    def test_mlk_day_closed(self, explicit_dates):
        assert "2025-01-20" in explicit_dates
        assert explicit_dates["2025-01-20"]["status"] == "closed"

    def test_presidents_day_closed(self, explicit_dates):
        assert "2025-02-17" in explicit_dates
        assert explicit_dates["2025-02-17"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["status"] == "closed"

    def test_memorial_day_closed(self, explicit_dates):
        assert "2025-05-26" in explicit_dates
        assert explicit_dates["2025-05-26"]["status"] == "closed"

    def test_juneteenth_closed(self, explicit_dates):
        assert "2025-06-19" in explicit_dates
        assert explicit_dates["2025-06-19"]["status"] == "closed"

    def test_july_3_early_close(self, explicit_dates):
        assert "2025-07-03" in explicit_dates
        assert explicit_dates["2025-07-03"]["status"] == "early_close"
        assert explicit_dates["2025-07-03"]["early_close_time"] == "13:00"

    def test_independence_day_closed(self, explicit_dates):
        assert "2025-07-04" in explicit_dates
        assert explicit_dates["2025-07-04"]["status"] == "closed"

    def test_labor_day_closed(self, explicit_dates):
        assert "2025-09-01" in explicit_dates
        assert explicit_dates["2025-09-01"]["status"] == "closed"

    def test_thanksgiving_closed(self, explicit_dates):
        assert "2025-11-27" in explicit_dates
        assert explicit_dates["2025-11-27"]["status"] == "closed"

    def test_black_friday_early_close(self, explicit_dates):
        assert "2025-11-28" in explicit_dates
        assert explicit_dates["2025-11-28"]["status"] == "early_close"
        assert explicit_dates["2025-11-28"]["early_close_time"] == "13:00"

    def test_christmas_eve_early_close(self, explicit_dates):
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["status"] == "early_close"
        assert explicit_dates["2025-12-24"]["early_close_time"] == "13:00"

    def test_christmas_day_closed(self, explicit_dates):
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2026 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNY2026:
    def test_new_years_day_closed(self, explicit_dates):
        assert "2026-01-01" in explicit_dates
        assert explicit_dates["2026-01-01"]["status"] == "closed"

    def test_mlk_day_closed(self, explicit_dates):
        assert "2026-01-19" in explicit_dates
        assert explicit_dates["2026-01-19"]["status"] == "closed"

    def test_presidents_day_closed(self, explicit_dates):
        assert "2026-02-16" in explicit_dates
        assert explicit_dates["2026-02-16"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2026-04-03" in explicit_dates
        assert explicit_dates["2026-04-03"]["status"] == "closed"

    def test_memorial_day_closed(self, explicit_dates):
        assert "2026-05-25" in explicit_dates
        assert explicit_dates["2026-05-25"]["status"] == "closed"

    def test_juneteenth_closed(self, explicit_dates):
        assert "2026-06-19" in explicit_dates
        assert explicit_dates["2026-06-19"]["status"] == "closed"

    def test_independence_day_observed_friday_july_3(self, explicit_dates):
        """July 4, 2026 is Saturday — observed Friday July 3."""
        assert "2026-07-03" in explicit_dates
        assert explicit_dates["2026-07-03"]["status"] == "closed"
        assert "observed" in explicit_dates["2026-07-03"]["name"].lower()

    def test_no_independence_day_on_actual_date(self, explicit_dates):
        """July 4, 2026 is Saturday. No separate entry for the actual date."""
        # The entry is on July 3 (observed), not July 4
        assert "2026-07-04" not in explicit_dates

    def test_labor_day_closed(self, explicit_dates):
        assert "2026-09-07" in explicit_dates
        assert explicit_dates["2026-09-07"]["status"] == "closed"

    def test_thanksgiving_closed(self, explicit_dates):
        assert "2026-11-26" in explicit_dates
        assert explicit_dates["2026-11-26"]["status"] == "closed"

    def test_day_after_thanksgiving_early_close(self, explicit_dates):
        assert "2026-11-27" in explicit_dates
        assert explicit_dates["2026-11-27"]["status"] == "early_close"
        assert explicit_dates["2026-11-27"]["early_close_time"] == "13:00"

    def test_christmas_eve_early_close(self, explicit_dates):
        assert "2026-12-24" in explicit_dates
        assert explicit_dates["2026-12-24"]["status"] == "early_close"

    def test_christmas_day_closed(self, explicit_dates):
        assert "2026-12-25" in explicit_dates
        assert explicit_dates["2026-12-25"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2027 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNY2027:
    def test_new_years_day_closed(self, explicit_dates):
        assert "2027-01-01" in explicit_dates
        assert explicit_dates["2027-01-01"]["status"] == "closed"

    def test_mlk_day_closed(self, explicit_dates):
        assert "2027-01-18" in explicit_dates
        assert explicit_dates["2027-01-18"]["status"] == "closed"

    def test_presidents_day_closed(self, explicit_dates):
        assert "2027-02-15" in explicit_dates
        assert explicit_dates["2027-02-15"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2027-03-26" in explicit_dates
        assert explicit_dates["2027-03-26"]["status"] == "closed"

    def test_memorial_day_closed(self, explicit_dates):
        assert "2027-05-31" in explicit_dates
        assert explicit_dates["2027-05-31"]["status"] == "closed"

    def test_juneteenth_observed_friday(self, explicit_dates):
        """June 19, 2027 is Saturday — observed Friday June 18."""
        assert "2027-06-18" in explicit_dates
        assert explicit_dates["2027-06-18"]["status"] == "closed"
        assert "observed" in explicit_dates["2027-06-18"]["name"].lower()

    def test_independence_day_observed_monday(self, explicit_dates):
        """July 4, 2027 is Sunday — observed Monday July 5."""
        assert "2027-07-05" in explicit_dates
        assert explicit_dates["2027-07-05"]["status"] == "closed"

    def test_labor_day_closed(self, explicit_dates):
        assert "2027-09-06" in explicit_dates
        assert explicit_dates["2027-09-06"]["status"] == "closed"

    def test_thanksgiving_closed(self, explicit_dates):
        assert "2027-11-25" in explicit_dates
        assert explicit_dates["2027-11-25"]["status"] == "closed"

    def test_day_after_thanksgiving_early_close(self, explicit_dates):
        assert "2027-11-26" in explicit_dates
        assert explicit_dates["2027-11-26"]["status"] == "early_close"

    def test_christmas_eve_early_close(self, explicit_dates):
        assert "2027-12-24" in explicit_dates
        assert explicit_dates["2027-12-24"]["status"] == "early_close"

    def test_christmas_day_on_saturday_no_entry(self, explicit_dates):
        """December 25, 2027 is Saturday. No explicit entry — market closed on weekends."""
        assert "2027-12-25" not in explicit_dates

    def test_new_years_eve_observed_for_2028(self, explicit_dates):
        """January 1, 2028 is Saturday — observed Friday December 31, 2027."""
        assert "2027-12-31" in explicit_dates
        assert explicit_dates["2027-12-31"]["status"] == "closed"
        # Name may or may not include "observed" — date and status are authoritative


# ──────────────────────────────────────────────────────────────
# 2028 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNY2028:
    def test_no_new_years_day_entry_actual_date(self, explicit_dates):
        """January 1, 2028 is Saturday. No entry for the actual date."""
        assert "2028-01-01" not in explicit_dates

    def test_mlk_day_closed(self, explicit_dates):
        assert "2028-01-17" in explicit_dates
        assert explicit_dates["2028-01-17"]["status"] == "closed"

    def test_presidents_day_closed(self, explicit_dates):
        assert "2028-02-21" in explicit_dates
        assert explicit_dates["2028-02-21"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2028-04-14" in explicit_dates
        assert explicit_dates["2028-04-14"]["status"] == "closed"

    def test_memorial_day_closed(self, explicit_dates):
        assert "2028-05-29" in explicit_dates
        assert explicit_dates["2028-05-29"]["status"] == "closed"

    def test_juneteenth_closed(self, explicit_dates):
        """June 19, 2028 is Monday. No weekend adjustment."""
        assert "2028-06-19" in explicit_dates
        assert explicit_dates["2028-06-19"]["status"] == "closed"

    def test_july_3_early_close(self, explicit_dates):
        """July 3, 2028 is Monday, day before Tuesday July 4 holiday."""
        assert "2028-07-03" in explicit_dates
        assert explicit_dates["2028-07-03"]["status"] == "early_close"
        assert explicit_dates["2028-07-03"]["early_close_time"] == "13:00"

    def test_independence_day_closed(self, explicit_dates):
        assert "2028-07-04" in explicit_dates
        assert explicit_dates["2028-07-04"]["status"] == "closed"

    def test_labor_day_closed(self, explicit_dates):
        assert "2028-09-04" in explicit_dates
        assert explicit_dates["2028-09-04"]["status"] == "closed"

    def test_thanksgiving_closed(self, explicit_dates):
        assert "2028-11-23" in explicit_dates
        assert explicit_dates["2028-11-23"]["status"] == "closed"

    def test_day_after_thanksgiving_early_close(self, explicit_dates):
        assert "2028-11-24" in explicit_dates
        assert explicit_dates["2028-11-24"]["status"] == "early_close"

    def test_no_christmas_eve_entry(self, explicit_dates):
        """December 24, 2028 is Sunday. No early close entry."""
        assert "2028-12-24" not in explicit_dates

    def test_christmas_day_closed(self, explicit_dates):
        assert "2028-12-25" in explicit_dates
        assert explicit_dates["2028-12-25"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2029 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNY2029:
    def test_new_years_day_closed(self, explicit_dates):
        assert "2029-01-01" in explicit_dates
        assert explicit_dates["2029-01-01"]["status"] == "closed"

    def test_mlk_day_closed(self, explicit_dates):
        assert "2029-01-15" in explicit_dates
        assert explicit_dates["2029-01-15"]["status"] == "closed"

    def test_presidents_day_closed(self, explicit_dates):
        assert "2029-02-19" in explicit_dates
        assert explicit_dates["2029-02-19"]["status"] == "closed"

    def test_good_friday_closed(self, explicit_dates):
        assert "2029-03-30" in explicit_dates
        assert explicit_dates["2029-03-30"]["status"] == "closed"

    def test_memorial_day_closed(self, explicit_dates):
        assert "2029-05-28" in explicit_dates
        assert explicit_dates["2029-05-28"]["status"] == "closed"

    def test_juneteenth_closed(self, explicit_dates):
        """June 19, 2029 is Tuesday. No weekend adjustment."""
        assert "2029-06-19" in explicit_dates
        assert explicit_dates["2029-06-19"]["status"] == "closed"

    def test_july_3_early_close(self, explicit_dates):
        """July 3, 2029 is Tuesday, day before Wednesday July 4 holiday."""
        assert "2029-07-03" in explicit_dates
        assert explicit_dates["2029-07-03"]["status"] == "early_close"
        assert explicit_dates["2029-07-03"]["early_close_time"] == "13:00"

    def test_independence_day_closed(self, explicit_dates):
        assert "2029-07-04" in explicit_dates
        assert explicit_dates["2029-07-04"]["status"] == "closed"

    def test_labor_day_closed(self, explicit_dates):
        assert "2029-09-03" in explicit_dates
        assert explicit_dates["2029-09-03"]["status"] == "closed"

    def test_thanksgiving_closed(self, explicit_dates):
        assert "2029-11-22" in explicit_dates
        assert explicit_dates["2029-11-22"]["status"] == "closed"

    def test_day_after_thanksgiving_early_close(self, explicit_dates):
        assert "2029-11-23" in explicit_dates
        assert explicit_dates["2029-11-23"]["status"] == "early_close"

    def test_christmas_eve_early_close(self, explicit_dates):
        assert "2029-12-24" in explicit_dates
        assert explicit_dates["2029-12-24"]["status"] == "early_close"

    def test_christmas_day_closed(self, explicit_dates):
        assert "2029-12-25" in explicit_dates
        assert explicit_dates["2029-12-25"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXNYStructure:
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
                assert entry["early_close_time"] == "13:00", f"Wrong time for {date_str}"

    def test_no_weekend_dates(self, explicit_dates):
        """No explicit entry should fall on a Saturday or Sunday."""
        from datetime import date
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Explicit date falls on weekend: {date_str} ({d.strftime('%A')})"

    def test_regular_hours_correct(self, xnys):
        assert xnys["regular_hours"]["open"] == "09:30"
        assert xnys["regular_hours"]["close"] == "16:00"

    def test_timezone_correct(self, xnys):
        assert xnys["timezone"] == "America/New_York"

    def test_code_correct(self, xnys):
        assert xnys["code"] == "XNYS"
        assert xnys["mic"] == "XNYS"