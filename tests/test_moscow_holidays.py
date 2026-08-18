#!/usr/bin/env python3
"""
test_moscow_holidays.py — Ground truth tests for XMOS (Moscow Exchange).

Key facts verified:
    - Regular hours: 10:00-18:45 (long session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - New Year holidays (Jan 1-8)
    - Orthodox Christmas (Jan 7)
    - Defender of Fatherland Day (Feb 23)
    - Women's Day (Mar 8)
    - Labour Day (May 1)
    - Victory Day (May 9)
    - Russia Day (Jun 12)
    - National Unity Day (Nov 4)
    - No recurrence rules — all dates explicit

Note: Moscow Exchange is under international sanctions.
Data included for completeness and academic purposes.

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XMOS.json)
    2. Russian holiday announcements changed (verify against moex.com)

Run:
    python3 -m pytest tests/test_moscow_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xmos():
    """Load XMOS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XMOS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xmos):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xmos["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXMOSProperties:
    def test_code(self, xmos):
        assert xmos["code"] == "XMOS"

    def test_mic(self, xmos):
        assert xmos["mic"] == "XMOS"

    def test_name(self, xmos):
        assert xmos["name"] == "Moscow Exchange"

    def test_timezone(self, xmos):
        assert xmos["timezone"] == "Europe/Moscow"

    def test_regular_hours(self, xmos):
        assert xmos["regular_hours"]["open"] == "10:00"
        assert xmos["regular_hours"]["close"] == "18:45"

    def test_no_lunch_break(self, xmos):
        lunch = [s for s in xmos.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xmos):
        assert "extended_hours" not in xmos or xmos.get("extended_hours") is None

    def test_generation_range(self, xmos):
        assert "generation_range" in xmos
        assert xmos["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xmos):
        assert xmos.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xmos):
        """Russia uses explicit dates only."""
        rules = xmos["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# New Year holidays (Jan 1-8)
# ──────────────────────────────────────────────────────────────

class TestXMOSNewYear:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_holidays_2025(self, explicit_dates):
        """New Year holidays 2025 — Jan 1-8."""
        dates = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-06",
                 "2025-01-07", "2025-01-08"]
        for d in dates:
            assert d in explicit_dates, f"Missing New Year holiday: {d}"

    def test_orthodox_christmas_2025(self, explicit_dates):
        """Orthodox Christmas — Jan 7, 2025."""
        assert "2025-01-07" in explicit_dates
        assert "Orthodox" in explicit_dates["2025-01-07"]["name"]

    def test_new_year_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday."""
        assert "2025-12-31" in explicit_dates
        assert "New Year's Eve" in explicit_dates["2025-12-31"]["name"]


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXMOSFixedHolidays:
    def test_defender_day_2025(self, explicit_dates):
        """Feb 23, 2025 is Sunday — observed Monday Feb 24."""
        assert "2025-02-23" not in explicit_dates
        assert "2025-02-24" in explicit_dates

    def test_defender_day_2026(self, explicit_dates):
        """Feb 23, 2026 is Monday."""
        assert "2026-02-23" in explicit_dates
        assert "Defender" in explicit_dates["2026-02-23"]["name"]

    def test_womens_day_2025(self, explicit_dates):
        """Mar 8, 2025 is Saturday — observed Monday Mar 10."""
        assert "2025-03-08" not in explicit_dates
        assert "2025-03-10" in explicit_dates

    def test_womens_day_2026(self, explicit_dates):
        """Mar 8, 2026 is Sunday — observed Monday Mar 9."""
        assert "2026-03-08" not in explicit_dates
        assert "2026-03-09" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_victory_day_2025(self, explicit_dates):
        """May 9, 2025 is Friday."""
        assert "2025-05-09" in explicit_dates
        assert "Victory" in explicit_dates["2025-05-09"]["name"]

    def test_victory_day_2026_substitute(self, explicit_dates):
        """May 9, 2026 is Saturday — observed Monday May 11."""
        assert "2026-05-09" not in explicit_dates
        assert "2026-05-11" in explicit_dates

    def test_russia_day_2025(self, explicit_dates):
        """Jun 12, 2025 is Thursday."""
        assert "2025-06-12" in explicit_dates
        assert "Russia" in explicit_dates["2025-06-12"]["name"]

    def test_national_unity_2025(self, explicit_dates):
        """Nov 4, 2025 is Tuesday."""
        assert "2025-11-04" in explicit_dates
        assert "Unity" in explicit_dates["2025-11-04"]["name"]


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXMOSStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Russia weekend is Saturday-Sunday."""
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
        """Russia has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xmos, explicit_dates):
        start = date.fromisoformat(xmos["generation_range"][0])
        end = date.fromisoformat(xmos["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~30-40 entries (Russia has long New Year break)."""
        assert 25 <= len(explicit_dates) <= 45, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "moex.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXMOSWeekendPattern:
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

class TestXMOSSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2025-02-23" not in explicit_dates  # Sunday
        assert "2025-03-08" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 3, f"Expected some observed holidays, got {observed_count}"


# ──────────────────────────────────────────────────────────────
# Sanctions note (documentation only)
# ──────────────────────────────────────────────────────────────

class TestXMOSSanctionsNote:
    def test_exchange_included_despite_sanctions(self, xmos):
        """Moscow Exchange is included for completeness despite sanctions."""
        assert xmos["code"] == "XMOS"
        assert xmos["name"] == "Moscow Exchange"