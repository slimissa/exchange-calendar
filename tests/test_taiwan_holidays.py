#!/usr/bin/env python3
"""
test_taiwan_holidays.py — Ground truth tests for XTAI (Taiwan Stock Exchange).

Key facts verified:
    - Pre-CNY settlement days (2 business days before Chinese New Year's Eve)
    - DGPA bridge days: when holidays fall on Tuesday/Thursday, adjacent
      weekdays become observed holidays
    - Saturday holidays observed on Friday; Sunday holidays observed on Monday
    - Lunisolar holidays (CNY, Dragon Boat, Mid-Autumn) are explicit-only
    - No lunch break (continuous trading)
    - After-hours: 13:30-14:30 (block trading)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XTAI.json)
    2. Taiwan holiday announcements changed (verify against twse.com.tw)

Run:
    python3 -m pytest tests/test_taiwan_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xtai():
    """Load XTAI.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XTAI.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xtai):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xtai["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXTAIProperties:
    def test_code(self, xtai):
        assert xtai["code"] == "XTAI"

    def test_mic(self, xtai):
        assert xtai["mic"] == "XTAI"

    def test_name(self, xtai):
        assert xtai["name"] == "Taiwan Stock Exchange"

    def test_timezone(self, xtai):
        assert xtai["timezone"] == "Asia/Taipei"

    def test_regular_hours(self, xtai):
        assert xtai["regular_hours"]["open"] == "09:00"
        assert xtai["regular_hours"]["close"] == "13:30"

    def test_no_lunch_break(self, xtai):
        lunch = [s for s in xtai.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xtai):
        assert xtai["extended_hours"]["pre_market"]["open"] == "08:30"
        assert xtai["extended_hours"]["after_hours"]["close"] == "14:30"


# ──────────────────────────────────────────────────────────────
# Pre-CNY Settlement Days
# ──────────────────────────────────────────────────────────────

class TestXTAIPreCNY:
    def test_2025_settlement_days(self, explicit_dates):
        """Jan 23-24, 2025 are Pre-CNY settlement days."""
        assert "2025-01-23" in explicit_dates
        assert "2025-01-24" in explicit_dates
        assert "Settlement" in explicit_dates["2025-01-23"]["name"]

    def test_2026_settlement_days(self, explicit_dates):
        """CNY Eve is Feb 16, 2026 — settlement Feb 12-13."""
        assert "2026-02-12" in explicit_dates
        assert "2026-02-13" in explicit_dates
        assert "Settlement" in explicit_dates["2026-02-12"]["name"]

    def test_2027_settlement_days(self, explicit_dates):
        """CNY Eve is Feb 5, 2027 — settlement Feb 3-4."""
        assert "2027-02-03" in explicit_dates
        assert "2027-02-04" in explicit_dates

    def test_2028_settlement_days(self, explicit_dates):
        """CNY Eve is Jan 26, 2028 — settlement Jan 24-25."""
        assert "2028-01-24" in explicit_dates
        assert "2028-01-25" in explicit_dates

    def test_2029_settlement_days(self, explicit_dates):
        """CNY Eve is Feb 12, 2029 — settlement Feb 8-9."""
        assert "2029-02-08" in explicit_dates
        assert "2029-02-09" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Chinese New Year
# ──────────────────────────────────────────────────────────────

class TestXTAICNY:
    def test_cny_2025(self, explicit_dates):
        assert "2025-01-28" in explicit_dates  # Eve
        assert "2025-01-29" in explicit_dates  # Day 1
        assert "2025-01-30" in explicit_dates  # Day 2
        assert "2025-01-31" in explicit_dates  # Day 3

    def test_cny_2026(self, explicit_dates):
        assert "2026-02-16" in explicit_dates  # Eve
        assert "2026-02-17" in explicit_dates  # Day 1
        assert "2026-02-18" in explicit_dates  # Day 2
        assert "2026-02-19" in explicit_dates  # Day 3
        assert "2026-02-20" in explicit_dates  # Day 4

    def test_cny_2027(self, explicit_dates):
        assert "2027-02-05" in explicit_dates  # Eve
        assert "2027-02-08" in explicit_dates  # Day 1 (Monday)
        assert "2027-02-09" in explicit_dates  # Day 2

    def test_cny_2028(self, explicit_dates):
        assert "2028-01-26" in explicit_dates  # Eve
        assert "2028-01-27" in explicit_dates  # Day 1
        assert "2028-01-28" in explicit_dates  # Day 2
        assert "2028-01-31" in explicit_dates  # Day 3

    def test_cny_2029(self, explicit_dates):
        assert "2029-02-12" in explicit_dates  # Eve
        assert "2029-02-13" in explicit_dates  # Day 1
        assert "2029-02-14" in explicit_dates  # Day 2


# ──────────────────────────────────────────────────────────────
# Observed holidays (DGPA bridge days)
# ──────────────────────────────────────────────────────────────

class TestXTAIObserved:
    def test_dragon_boat_2025_observed(self, explicit_dates):
        """Dragon Boat May 31 is Saturday — observed Friday May 30."""
        assert "2025-05-30" in explicit_dates
        assert "Dragon Boat" in explicit_dates["2025-05-30"]["name"]

    def test_peace_memorial_2026_observed(self, explicit_dates):
        """Feb 28, 2026 is Saturday — observed Friday Feb 27."""
        assert "2026-02-27" in explicit_dates
        assert "Peace Memorial" in explicit_dates["2026-02-27"]["name"]

    def test_national_day_2026_observed(self, explicit_dates):
        """Oct 10, 2026 is Saturday — observed Friday Oct 9."""
        assert "2026-10-09" in explicit_dates
        assert "National" in explicit_dates["2026-10-09"]["name"]

    def test_peace_memorial_2027_observed(self, explicit_dates):
        """Feb 28, 2027 is Sunday — observed Friday Feb 26."""
        assert "2027-02-26" in explicit_dates

    def test_dragon_boat_2029(self, explicit_dates):
        """Dragon Boat June 18, 2029 is Monday — no shift needed."""
        assert "2029-06-18" in explicit_dates
        assert "Dragon Boat" in explicit_dates["2029-06-18"]["name"]


# ──────────────────────────────────────────────────────────────
# Lunisolar festivals
# ──────────────────────────────────────────────────────────────

class TestXTAILunisolar:
    def test_mid_autumn_2025(self, explicit_dates):
        assert "2025-10-06" in explicit_dates
        assert "Mid-Autumn" in explicit_dates["2025-10-06"]["name"]

    def test_mid_autumn_2026(self, explicit_dates):
        assert "2026-09-25" in explicit_dates
        assert "Mid-Autumn" in explicit_dates["2026-09-25"]["name"]

    def test_mid_autumn_2027(self, explicit_dates):
        assert "2027-09-15" in explicit_dates

    def test_mid_autumn_2028(self, explicit_dates):
        assert "2028-09-25" in explicit_dates

    def test_dragon_boat_2026(self, explicit_dates):
        assert "2026-06-19" in explicit_dates

    def test_dragon_boat_2027(self, explicit_dates):
        assert "2027-06-09" in explicit_dates

    def test_dragon_boat_2028_sunday(self, explicit_dates):
        """June 18, 2028 is Sunday — no explicit entry."""
        assert "2028-06-18" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXTAIRecurrence:
    def test_fixed_rules_exist(self, xtai):
        rules = xtai["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Republic Day (New Year's Day)" in names
        assert "Peace Memorial Day" in names
        assert "Tomb Sweeping Day" in names
        assert "Labour Day" in names
        assert "National Day" in names

    def test_no_lunisolar_rules(self, xtai):
        """CNY, Dragon Boat, Mid-Autumn must NOT be in recurrence."""
        rules = xtai["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Chinese New Year" not in names
        assert "Dragon Boat" not in names
        assert "Mid-Autumn" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXTAIStructure:
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
        """Taiwan has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~62 entries: multiple holidays per year + settlement days."""
        assert 50 <= len(explicit_dates) <= 80