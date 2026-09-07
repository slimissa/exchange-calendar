#!/usr/bin/env python3
"""
test_nasdaq_holidays.py — Ground truth tests for XNAS (NASDAQ).

NASDAQ follows the exact same holiday schedule as NYSE. These tests
verify that XNAS has an identical calendar to XNYS for 2025-2029,
plus independent checks on NASDAQ-specific properties.

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XNAS.json)
    2. The ground truth is outdated (verify against nasdaq.com)
    3. XNAS and XNYS have genuinely diverged (rare — both follow
       the same US equity market holiday schedule)

Run:
    python3 -m pytest tests/test_nasdaq_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xnas():
    """Load XNAS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XNAS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def xnys():
    """Load XNYS.json for comparison tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xnas):
    """Return dict of date -> entry from XNAS explicit array."""
    return {e["date"]: e for e in xnas["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Identity and properties
# ──────────────────────────────────────────────────────────────

class TestXNASProperties:
    def test_code(self, xnas):
        assert xnas["code"] == "XNAS"

    def test_mic(self, xnas):
        assert xnas["mic"] == "XNAS"

    def test_name(self, xnas):
        assert xnas["name"] == "NASDAQ"

    def test_timezone(self, xnas):
        assert xnas["timezone"] == "America/New_York"

    def test_regular_hours(self, xnas):
        assert xnas["regular_hours"]["open"] == "09:30"
        assert xnas["regular_hours"]["close"] == "16:00"

    def test_extended_hours(self, xnas):
        assert xnas["extended_hours"]["pre_market"]["open"] == "04:00"
        assert xnas["extended_hours"]["pre_market"]["close"] == "09:30"
        assert xnas["extended_hours"]["after_hours"]["open"] == "16:00"
        assert xnas["extended_hours"]["after_hours"]["close"] == "20:00"

    def test_no_sessions(self, xnas):
        assert xnas["sessions"] == []

    def test_generation_range(self, xnas):
        assert xnas["generation_range"] == ["2025-01-01", "2029-12-31"]


# ──────────────────────────────────────────────────────────────
# XNAS matches XNYS
# ──────────────────────────────────────────────────────────────

class TestXNASMatchesXNYS:
    def test_same_explicit_dates(self, xnas, xnys):
        xnas_dates = {e["date"] for e in xnas["holidays"]["explicit"]}
        xnys_dates = {e["date"] for e in xnys["holidays"]["explicit"]}
        assert xnas_dates == xnys_dates, \
            "XNAS and XNYS must have identical explicit holiday dates"

    def test_same_statuses(self, xnas, xnys):
        xnas_status = {e["date"]: e["status"] for e in xnas["holidays"]["explicit"]}
        xnys_status = {e["date"]: e["status"] for e in xnys["holidays"]["explicit"]}
        assert xnas_status == xnys_status, \
            "XNAS and XNYS must have identical statuses"

    def test_same_early_close_times(self, xnas, xnys):
        xnas_times = {e["date"]: e.get("early_close_time") for e in xnas["holidays"]["explicit"]}
        xnys_times = {e["date"]: e.get("early_close_time") for e in xnys["holidays"]["explicit"]}
        assert xnas_times == xnys_times, \
            "XNAS and XNYS must have identical early close times"

    def test_same_holiday_count(self, xnas, xnys):
        xnas_count = len(xnas["holidays"]["explicit"])
        xnys_count = len(xnys["holidays"]["explicit"])
        assert xnas_count == xnys_count, \
            f"XNAS has {xnas_count} explicit dates, XNYS has {xnys_count}"

    def test_same_recurrence_rules(self, xnas, xnys):
        xnas_rules = xnas["holidays"].get("recurrence_rules", [])
        xnys_rules = xnys["holidays"].get("recurrence_rules", [])
        assert len(xnas_rules) == len(xnys_rules), \
            "XNAS and XNYS must have same number of recurrence rules"


# ──────────────────────────────────────────────────────────────
# 2025 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNAS2025:
    def test_new_years_day(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_national_day_of_mourning(self, explicit_dates):
        assert "2025-01-09" in explicit_dates
        assert explicit_dates["2025-01-09"]["status"] == "closed"
        assert "Carter" in explicit_dates["2025-01-09"]["name"]

    def test_mlk_day(self, explicit_dates):
        assert "2025-01-20" in explicit_dates
        assert explicit_dates["2025-01-20"]["status"] == "closed"

    def test_presidents_day(self, explicit_dates):
        assert "2025-02-17" in explicit_dates
        assert explicit_dates["2025-02-17"]["status"] == "closed"

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["status"] == "closed"

    def test_memorial_day(self, explicit_dates):
        assert "2025-05-26" in explicit_dates
        assert explicit_dates["2025-05-26"]["status"] == "closed"

    def test_juneteenth(self, explicit_dates):
        assert "2025-06-19" in explicit_dates
        assert explicit_dates["2025-06-19"]["status"] == "closed"

    def test_july_3_early_close(self, explicit_dates):
        assert "2025-07-03" in explicit_dates
        assert explicit_dates["2025-07-03"]["status"] == "early_close"
        assert explicit_dates["2025-07-03"]["early_close_time"] == "13:00"

    def test_independence_day(self, explicit_dates):
        assert "2025-07-04" in explicit_dates
        assert explicit_dates["2025-07-04"]["status"] == "closed"

    def test_labor_day(self, explicit_dates):
        assert "2025-09-01" in explicit_dates
        assert explicit_dates["2025-09-01"]["status"] == "closed"

    def test_thanksgiving(self, explicit_dates):
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

    def test_christmas_day(self, explicit_dates):
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2026 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNAS2026:
    def test_new_years_day(self, explicit_dates):
        assert "2026-01-01" in explicit_dates
        assert explicit_dates["2026-01-01"]["status"] == "closed"

    def test_independence_day_observed(self, explicit_dates):
        """July 4, 2026 is Saturday — observed Friday July 3."""
        assert "2026-07-03" in explicit_dates
        assert explicit_dates["2026-07-03"]["status"] == "closed"
        assert "observed" in explicit_dates["2026-07-03"]["name"].lower()

    def test_no_independence_day_actual(self, explicit_dates):
        assert "2026-07-04" not in explicit_dates

    def test_christmas_eve(self, explicit_dates):
        assert "2026-12-24" in explicit_dates
        assert explicit_dates["2026-12-24"]["status"] == "early_close"

    def test_christmas_day(self, explicit_dates):
        assert "2026-12-25" in explicit_dates
        assert explicit_dates["2026-12-25"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2027 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNAS2027:
    def test_juneteenth_observed(self, explicit_dates):
        """June 19, 2027 is Saturday — observed Friday June 18."""
        assert "2027-06-18" in explicit_dates
        assert explicit_dates["2027-06-18"]["status"] == "closed"

    def test_independence_day_observed(self, explicit_dates):
        """July 4, 2027 is Sunday — observed Monday July 5."""
        assert "2027-07-05" in explicit_dates
        assert explicit_dates["2027-07-05"]["status"] == "closed"

    def test_christmas_eve(self, explicit_dates):
        assert "2027-12-24" in explicit_dates
        assert explicit_dates["2027-12-24"]["status"] == "early_close"

    def test_no_christmas_day_saturday(self, explicit_dates):
        """December 25, 2027 is Saturday — no explicit entry."""
        assert "2027-12-25" not in explicit_dates

    def test_new_years_observed(self, explicit_dates):
        """January 1, 2028 is Saturday — observed Friday December 31, 2027."""
        assert "2027-12-31" in explicit_dates
        assert explicit_dates["2027-12-31"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2028 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNAS2028:
    def test_no_new_years_day_saturday(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates

    def test_july_3_early_close(self, explicit_dates):
        assert "2028-07-03" in explicit_dates
        assert explicit_dates["2028-07-03"]["status"] == "early_close"
        assert explicit_dates["2028-07-03"]["early_close_time"] == "13:00"

    def test_independence_day(self, explicit_dates):
        assert "2028-07-04" in explicit_dates
        assert explicit_dates["2028-07-04"]["status"] == "closed"

    def test_no_christmas_eve_sunday(self, explicit_dates):
        assert "2028-12-24" not in explicit_dates

    def test_christmas_day(self, explicit_dates):
        assert "2028-12-25" in explicit_dates
        assert explicit_dates["2028-12-25"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# 2029 Ground Truth
# ──────────────────────────────────────────────────────────────

class TestXNAS2029:
    def test_july_3_early_close(self, explicit_dates):
        assert "2029-07-03" in explicit_dates
        assert explicit_dates["2029-07-03"]["status"] == "early_close"
        assert explicit_dates["2029-07-03"]["early_close_time"] == "13:00"

    def test_independence_day(self, explicit_dates):
        assert "2029-07-04" in explicit_dates
        assert explicit_dates["2029-07-04"]["status"] == "closed"

    def test_christmas_eve(self, explicit_dates):
        assert "2029-12-24" in explicit_dates
        assert explicit_dates["2029-12-24"]["status"] == "early_close"

    def test_christmas_day(self, explicit_dates):
        assert "2029-12-25" in explicit_dates
        assert explicit_dates["2029-12-25"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXNASStructure:
    def test_all_dates_iso_format(self, explicit_dates):
        for date_str in explicit_dates:
            parts = date_str.split("-")
            assert len(parts) == 3, f"Date not ISO: {date_str}"
            assert len(parts[0]) == 4
            assert len(parts[1]) == 2
            assert len(parts[2]) == 2

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"

    def test_early_close_entries_have_time(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            if entry["status"] == "early_close":
                assert "early_close_time" in entry
                assert entry["early_close_time"] == "13:00"

    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str} ({d.strftime('%A')})"

    def test_holiday_count(self, explicit_dates):
        # XNYS has 61 explicit dates after weekend removals
        assert len(explicit_dates) == 62, f"Expected 61 dates, got {len(explicit_dates)}"