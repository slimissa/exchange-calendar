#!/usr/bin/env python3
"""
test_sse_holidays.py — Ground truth tests for XSHG (Shanghai Stock Exchange).

Key facts verified:
    - Chinese holidays are lunisolar — explicit-only, no recurrence rules
    - Spring Festival: 7-8 day Golden Week (varies by year)
    - National Day: 7-day Golden Week (Oct 1-7, may extend to Oct 8)
    - Mid-Autumn may merge into National Day Golden Week
    - Dragon Boat Festival (Duanwu): 5th day of 5th lunar month
    - Qingming Festival: early April
    - Weekends always closed, even if designated as make-up workdays
    - Lunch break: 11:30-13:00
    - Opening auction at 09:25

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XSHG.json)
    2. Chinese holiday arrangements changed (verify against sse.com.cn)

Run:
    python3 -m pytest tests/test_sse_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xshg():
    """Load XSHG.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XSHG.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xshg):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xshg["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXSHGProperties:
    def test_code(self, xshg):
        assert xshg["code"] == "XSHG"

    def test_mic(self, xshg):
        assert xshg["mic"] == "XSHG"

    def test_name(self, xshg):
        assert xshg["name"] == "Shanghai Stock Exchange"

    def test_timezone(self, xshg):
        assert xshg["timezone"] == "Asia/Shanghai"

    def test_regular_hours(self, xshg):
        assert xshg["regular_hours"]["open"] == "09:30"
        assert xshg["regular_hours"]["close"] == "15:00"

    def test_lunch_break(self, xshg):
        lunch = [s for s in xshg.get("sessions", []) if s["type"] == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "11:30"
        assert lunch[0]["close"] == "13:00"

    def test_opening_auction(self, xshg):
        auctions = [s for s in xshg.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 1
        assert auctions[0]["at"] == "09:25"

    def test_no_recurrence_rules(self, xshg):
        """Chinese holidays are lunisolar — explicit-only."""
        assert xshg["holidays"].get("recurrence_rules", []) == []


# ──────────────────────────────────────────────────────────────
# 2025
# ──────────────────────────────────────────────────────────────

class TestXSHG2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates

    def test_spring_festival_full_span(self, explicit_dates):
        """Jan 28 - Feb 4: 8-day Spring Festival Golden Week."""
        assert "2025-01-28" in explicit_dates  # Eve
        assert "2025-01-29" in explicit_dates  # Day 1
        assert "2025-01-30" in explicit_dates  # Day 2
        assert "2025-01-31" in explicit_dates  # Day 3
        assert "2025-02-03" in explicit_dates  # Observed Monday
        assert "2025-02-04" in explicit_dates  # Observed Tuesday

    def test_qingming(self, explicit_dates):
        assert "2025-04-04" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates
        assert "2025-05-02" in explicit_dates
        assert "2025-05-05" in explicit_dates

    def test_dragon_boat(self, explicit_dates):
        assert "2025-06-02" in explicit_dates

    def test_national_day_golden_week_full(self, explicit_dates):
        """Oct 1-8: 8-day National Day Golden Week (includes Mid-Autumn)."""
        assert "2025-10-01" in explicit_dates
        assert "2025-10-02" in explicit_dates
        assert "2025-10-03" in explicit_dates
        assert "2025-10-06" in explicit_dates  # Monday after weekend
        assert "2025-10-07" in explicit_dates
        assert "2025-10-08" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2026
# ──────────────────────────────────────────────────────────────

class TestXSHG2026:
    def test_spring_festival(self, explicit_dates):
        assert "2026-02-16" in explicit_dates  # Eve
        assert "2026-02-17" in explicit_dates  # Day 1
        assert "2026-02-18" in explicit_dates  # Day 2
        assert "2026-02-19" in explicit_dates  # Day 3
        assert "2026-02-20" in explicit_dates  # Observed
        assert "2026-02-23" in explicit_dates  # Observed Monday

    def test_qingming_observed(self, explicit_dates):
        """Qingming is Saturday Apr 4 — observed Monday Apr 6."""
        assert "2026-04-06" in explicit_dates

    def test_mid_autumn(self, explicit_dates):
        """Mid-Autumn 2026: Friday September 25."""
        assert "2026-09-25" in explicit_dates

    def test_national_day(self, explicit_dates):
        assert "2026-10-01" in explicit_dates
        assert "2026-10-02" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2028
# ──────────────────────────────────────────────────────────────

class TestXSHG2028:
    def test_dragon_boat_2028(self, explicit_dates):
        """Dragon Boat Festival 2028: Monday June 19."""
        assert "2028-06-19" in explicit_dates
        assert "Dragon Boat" in explicit_dates["2028-06-19"]["name"]

    def test_mid_autumn_merged_with_national_day(self, explicit_dates):
        """Mid-Autumn 2028: Tuesday October 3, merged into National Day."""
        assert "2028-10-03" in explicit_dates
        assert "Mid-Autumn" in explicit_dates["2028-10-03"]["name"]

    def test_no_wrong_mid_autumn(self, explicit_dates):
        """September 25, 2028 is NOT Mid-Autumn — wrong date removed."""
        assert "2028-09-25" not in explicit_dates

    def test_national_day_golden_week(self, explicit_dates):
        """Oct 1 is Sunday — observed Oct 2-6."""
        assert "2028-10-02" in explicit_dates
        assert "2028-10-03" in explicit_dates
        assert "2028-10-04" in explicit_dates
        assert "2028-10-05" in explicit_dates
        assert "2028-10-06" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2029
# ──────────────────────────────────────────────────────────────

class TestXSHG2029:
    def test_new_year(self, explicit_dates):
        assert "2029-01-01" in explicit_dates

    def test_no_dragon_boat_saturday(self, explicit_dates):
        """Dragon Boat 2029 is Saturday June 16 — no explicit entry."""
        assert "2029-06-16" not in explicit_dates

    def test_national_day(self, explicit_dates):
        assert "2029-10-01" in explicit_dates
        assert "2029-10-02" in explicit_dates
        assert "2029-10-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXSHGStructure:
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
        """SSE has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", \
                f"Unexpected status: {entry['date']}: {entry['status']}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~80 entries: Chinese holidays across 5 years."""
        assert 75 <= len(explicit_dates) <= 90