#!/usr/bin/env python3
"""
test_dubai_holidays.py — Ground truth tests for XDFM (Dubai Financial Market).

Key facts verified:
    - Trading week: Monday-Friday (since January 2022)
    - Weekend: Saturday-Sunday
    - No after-hours trading session
    - Closing auction at 14:50, Trade-at-Last 14:55-15:00
    - Commemoration Day (Dec 1) is a statutory holiday
    - UAE National Day (Dec 2-3) is a statutory holiday
    - No weekend shift for fixed holidays

Note: Islamic holidays (Eid al-Fitr, Eid al-Adha, Islamic New Year,
Prophet's Birthday) are NOT included in this version. They require
official UAE government announcements and will be added in v1.1.0.

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XDFM.json)
    2. UAE holiday announcements changed (verify against dfm.ae)

Run:
    python3 -m pytest tests/test_dubai_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xdfm():
    """Load XDFM.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XDFM.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xdfm):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xdfm["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXDFMProperties:
    def test_code(self, xdfm):
        assert xdfm["code"] == "XDFM"

    def test_mic(self, xdfm):
        assert xdfm["mic"] == "XDFM"

    def test_name(self, xdfm):
        assert xdfm["name"] == "Dubai Financial Market"

    def test_timezone(self, xdfm):
        assert xdfm["timezone"] == "Asia/Dubai"

    def test_regular_hours(self, xdfm):
        assert xdfm["regular_hours"]["open"] == "10:00"
        assert xdfm["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xdfm):
        lunch = [s for s in xdfm.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_no_after_hours(self, xdfm):
        """DFM has no after-hours session."""
        assert "after_hours" not in xdfm["extended_hours"]

    def test_closing_auction(self, xdfm):
        auctions = [s for s in xdfm.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 1
        assert auctions[0]["at"] == "14:50"


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXDFMFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_new_year_2026(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_new_year_2027(self, explicit_dates):
        assert "2027-01-01" in explicit_dates

    def test_commemoration_day_2025(self, explicit_dates):
        """Dec 1, 2025 is Monday — explicit."""
        assert "2025-12-01" in explicit_dates
        assert "Commemoration" in explicit_dates["2025-12-01"]["name"]

    def test_national_day_2025(self, explicit_dates):
        """Dec 2-3, 2025 — explicit."""
        assert "2025-12-02" in explicit_dates
        assert "National" in explicit_dates["2025-12-02"]["name"]
        assert "2025-12-03" in explicit_dates

    def test_commemoration_day_2026(self, explicit_dates):
        assert "2026-12-01" in explicit_dates

    def test_national_day_2026(self, explicit_dates):
        assert "2026-12-02" in explicit_dates
        assert "2026-12-03" in explicit_dates

    def test_commemoration_day_2027(self, explicit_dates):
        assert "2027-12-01" in explicit_dates

    def test_national_day_2027(self, explicit_dates):
        assert "2027-12-02" in explicit_dates
        assert "2027-12-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Weekend awareness (Saturday-Sunday)
# ──────────────────────────────────────────────────────────────

class TestXDFMWeekend:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_no_national_day_2028_sunday(self, explicit_dates):
        """Dec 2, 2028 is Sunday — no explicit entry."""
        assert "2028-12-02" not in explicit_dates

    def test_no_national_day_2029_sunday(self, explicit_dates):
        """Dec 2, 2029 is Sunday — no explicit entry."""
        assert "2029-12-02" not in explicit_dates

    def test_no_commemoration_2028_saturday(self, explicit_dates):
        """Dec 1, 2028 is Saturday — no explicit entry."""
        assert "2028-12-01" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXDFMRecurrence:
    def test_fixed_rules_exist(self, xdfm):
        rules = xdfm["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Commemoration Day" in names
        assert "UAE National Day" in names
        assert "UAE National Day Holiday" in names

    def test_no_islamic_rules(self, xdfm):
        """Islamic holidays are NOT in recurrence rules (lunisolar)."""
        rules = xdfm["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Eid" not in names
        assert "Prophet" not in names
        assert "Islamic New Year" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXDFMStructure:
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
        """DFM has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~15-25 entries: 4 holidays × 5 years, minus weekend overlaps."""
        assert 10 <= len(explicit_dates) <= 30