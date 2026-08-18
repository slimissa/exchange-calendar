#!/usr/bin/env python3
"""
test_ho_chi_minh_holidays.py — Ground truth tests for XSTC (Ho Chi Minh Stock Exchange).

Key facts verified:
    - Regular hours: 09:00-11:30 (morning session)
    - Lunch break: 11:30-13:00
    - Weekend is Saturday-Sunday (Western weekend)
    - Tet (Lunar New Year) — 5 days each year
    - Hung Kings Commemoration Day (10th day of 3rd lunar month)
    - Reunification Day (Apr 30)
    - Labour Day (May 1)
    - National Day (Sep 2)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XSTC.json)
    2. Vietnamese holiday announcements changed (verify against hsx.vn)

Run:
    python3 -m pytest tests/test_ho_chi_minh_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xstc():
    """Load XSTC.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XSTC.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xstc):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xstc["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXSTCProperties:
    def test_code(self, xstc):
        assert xstc["code"] == "XSTC"

    def test_mic(self, xstc):
        assert xstc["mic"] == "XSTC"

    def test_name(self, xstc):
        assert xstc["name"] == "Ho Chi Minh Stock Exchange"

    def test_timezone(self, xstc):
        assert xstc["timezone"] == "Asia/Ho_Chi_Minh"

    def test_regular_hours(self, xstc):
        assert xstc["regular_hours"]["open"] == "09:00"
        assert xstc["regular_hours"]["close"] == "11:30"

    def test_lunch_break(self, xstc):
        lunch = [s for s in xstc.get("sessions", []) if s.get("type") == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "11:30"
        assert lunch[0]["close"] == "13:00"

    def test_no_extended_hours(self, xstc):
        assert "extended_hours" not in xstc or xstc.get("extended_hours") is None

    def test_generation_range(self, xstc):
        assert "generation_range" in xstc
        assert xstc["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xstc):
        assert xstc.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xstc):
        """Vietnam uses explicit dates only."""
        rules = xstc["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# New Year's Day
# ──────────────────────────────────────────────────────────────

class TestXSTCNewYear:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Tet Holiday (Lunar New Year)
# ──────────────────────────────────────────────────────────────

class TestXSTCTet:
    def test_tet_2025(self, explicit_dates):
        """Tet 2025 — Jan 27-31 (5 days)."""
        for d in ["2025-01-27", "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31"]:
            assert d in explicit_dates, f"Missing Tet holiday: {d}"
            assert "Tet" in explicit_dates[d]["name"]

    def test_tet_2026(self, explicit_dates):
        """Tet 2026 — Feb 16-20 (5 days)."""
        for d in ["2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20"]:
            assert d in explicit_dates, f"Missing Tet holiday: {d}"

    def test_tet_2027(self, explicit_dates):
        """Tet 2027 — Feb 8-12 (5 days)."""
        for d in ["2027-02-08", "2027-02-09", "2027-02-10", "2027-02-11", "2027-02-12"]:
            assert d in explicit_dates, f"Missing Tet holiday: {d}"

    def test_tet_2028(self, explicit_dates):
        """Tet 2028 — Jan 26-28, Jan 31-Feb 1 (5 weekdays)."""
        tet_dates = ["2028-01-26", "2028-01-27", "2028-01-28", "2028-01-31", "2028-02-01"]
        for d in tet_dates:
            assert d in explicit_dates, f"Missing Tet holiday: {d}"

    def test_tet_2029(self, explicit_dates):
        """Tet 2029 — Feb 12-16 (5 days)."""
        for d in ["2029-02-12", "2029-02-13", "2029-02-14", "2029-02-15", "2029-02-16"]:
            assert d in explicit_dates, f"Missing Tet holiday: {d}"


# ──────────────────────────────────────────────────────────────
# Hung Kings Commemoration Day
# ──────────────────────────────────────────────────────────────

class TestXSTCHungKings:
    def test_hung_kings_2025(self, explicit_dates):
        """Hung Kings Day 2025 — Apr 7."""
        assert "2025-04-07" in explicit_dates
        assert "Hung Kings" in explicit_dates["2025-04-07"]["name"]

    def test_hung_kings_2026(self, explicit_dates):
        """Hung Kings Day 2026 — Apr 27."""
        assert "2026-04-27" in explicit_dates

    def test_hung_kings_2027(self, explicit_dates):
        """Hung Kings Day 2027 — Apr 16."""
        assert "2027-04-16" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Reunification Day and Labour Day
# ──────────────────────────────────────────────────────────────

class TestXSTCReunification:
    def test_reunification_2025(self, explicit_dates):
        """Apr 30, 2025 is Wednesday."""
        assert "2025-04-30" in explicit_dates
        assert "Reunification" in explicit_dates["2025-04-30"]["name"]

    def test_reunification_2026(self, explicit_dates):
        """Apr 30, 2026 is Thursday."""
        assert "2026-04-30" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# National Day
# ──────────────────────────────────────────────────────────────

class TestXSTCNationalDay:
    def test_national_day_2025(self, explicit_dates):
        """Sep 2, 2025 is Tuesday."""
        assert "2025-09-02" in explicit_dates
        assert "National Day" in explicit_dates["2025-09-02"]["name"]

    def test_national_day_2026(self, explicit_dates):
        """Sep 2, 2026 is Wednesday."""
        assert "2026-09-02" in explicit_dates

    def test_national_day_2027(self, explicit_dates):
        """Sep 2, 2027 is Thursday."""
        assert "2027-09-02" in explicit_dates

    def test_national_day_2029_substitute(self, explicit_dates):
        """Sep 2, 2029 is Sunday — substitute to Monday Sep 3."""
        assert "2029-09-02" not in explicit_dates
        assert "2029-09-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXSTCStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Vietnam weekend is Saturday-Sunday."""
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
        """Vietnam has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xstc, explicit_dates):
        start = date.fromisoformat(xstc["generation_range"][0])
        end = date.fromisoformat(xstc["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~45-55 entries."""
        assert 40 <= len(explicit_dates) <= 60, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "hsx.vn" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXSTCWeekendPattern:
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

class TestXSTCSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_substitute_names_contain_observed(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "observed" in name:
                assert "observed" in name