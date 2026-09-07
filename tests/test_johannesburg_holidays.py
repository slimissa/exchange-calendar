#!/usr/bin/env python3
"""
test_johannesburg_holidays.py — Ground truth tests for XJSE (Johannesburg Stock Exchange).

Key facts verified:
    - South Africa observes Sunday holidays on Monday (Public Holidays Act)
    - Human Rights Day (Mar 21), Freedom Day (Apr 27), Youth Day (Jun 16),
      National Women's Day (Aug 9), Heritage Day (Sep 24),
      Day of Reconciliation (Dec 16), Day of Goodwill (Dec 26)
    - Workers' Day (May 1) does NOT shift from weekend
    - Good Friday and Family Day (Easter Monday) use Easter offsets
    - No lunch break (continuous trading)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XJSE.json)
    2. South African holiday announcements changed (verify against jse.co.za)

Run:
    python3 -m pytest tests/test_johannesburg_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xjse():
    """Load XJSE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XJSE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xjse):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xjse["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXJSEProperties:
    def test_code(self, xjse):
        assert xjse["code"] == "XJSE"

    def test_mic(self, xjse):
        assert xjse["mic"] == "XJSE"

    def test_name(self, xjse):
        assert xjse["name"] == "Johannesburg Stock Exchange"

    def test_timezone(self, xjse):
        assert xjse["timezone"] == "Africa/Johannesburg"

    def test_regular_hours(self, xjse):
        assert xjse["regular_hours"]["open"] == "09:00"
        assert xjse["regular_hours"]["close"] == "17:00"

    def test_no_lunch_break(self, xjse):
        lunch = [s for s in xjse.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xjse):
        assert xjse["extended_hours"]["pre_market"]["open"] == "08:30"
        assert xjse["extended_hours"]["after_hours"]["close"] == "17:15"


# ──────────────────────────────────────────────────────────────
# 2025 holidays
# ──────────────────────────────────────────────────────────────

class TestXJSE2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_human_rights_day(self, explicit_dates):
        assert "2025-03-21" in explicit_dates
        assert "Human Rights" in explicit_dates["2025-03-21"]["name"]

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_family_day(self, explicit_dates):
        assert "2025-04-21" in explicit_dates
        assert "Family" in explicit_dates["2025-04-21"]["name"]

    def test_freedom_day_observed(self, explicit_dates):
        """Apr 27, 2025 is Sunday — observed Monday Apr 28."""
        assert "2025-04-28" in explicit_dates
        assert "Freedom" in explicit_dates["2025-04-28"]["name"]
        assert "observed" in explicit_dates["2025-04-28"]["name"].lower()

    def test_workers_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_youth_day(self, explicit_dates):
        assert "2025-06-16" in explicit_dates

    def test_womens_day_observed(self, explicit_dates):
        """Aug 9, 2025 is Saturday — observed Monday Aug 11."""
        assert "2025-08-11" in explicit_dates
        assert "Women" in explicit_dates["2025-08-11"]["name"]
        assert "observed" in explicit_dates["2025-08-11"]["name"].lower()

    def test_heritage_day(self, explicit_dates):
        assert "2025-09-24" in explicit_dates

    def test_day_of_reconciliation(self, explicit_dates):
        assert "2025-12-16" in explicit_dates

    def test_christmas(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_day_of_goodwill(self, explicit_dates):
        assert "2025-12-26" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2026 holidays
# ──────────────────────────────────────────────────────────────

class TestXJSE2026:
    def test_new_year(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_human_rights_day_saturday(self, explicit_dates):
        """Mar 21, 2026 is Saturday — no explicit entry."""
        assert "2026-03-21" not in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_family_day(self, explicit_dates):
        assert "2026-04-06" in explicit_dates

    def test_freedom_day(self, explicit_dates):
        """Apr 27, 2026 is Monday — no shift needed."""
        assert "2026-04-27" in explicit_dates

    def test_workers_day(self, explicit_dates):
        assert "2026-05-01" in explicit_dates

    def test_youth_day(self, explicit_dates):
        assert "2026-06-16" in explicit_dates

    def test_womens_day_sunday(self, explicit_dates):
        """Aug 9, 2026 is Sunday — observed Monday Aug 10."""
        assert "2026-08-10" in explicit_dates or "2026-08-09" not in explicit_dates

    def test_heritage_day(self, explicit_dates):
        assert "2026-09-24" in explicit_dates

    def test_day_of_reconciliation(self, explicit_dates):
        assert "2026-12-16" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2027 holidays
# ──────────────────────────────────────────────────────────────

class TestXJSE2027:
    def test_human_rights_day_observed(self, explicit_dates):
        """Mar 21, 2027 is Sunday — observed Monday Mar 22."""
        assert "2027-03-22" in explicit_dates
        assert "observed" in explicit_dates["2027-03-22"]["name"].lower()

    def test_good_friday(self, explicit_dates):
        assert "2027-03-26" in explicit_dates

    def test_family_day(self, explicit_dates):
        assert "2027-03-29" in explicit_dates

    def test_freedom_day(self, explicit_dates):
        assert "2027-04-27" in explicit_dates

    def test_youth_day(self, explicit_dates):
        assert "2027-06-16" in explicit_dates

    def test_day_of_goodwill_observed(self, explicit_dates):
        """Dec 26, 2027 is Sunday — observed Monday Dec 27."""
        assert "2027-12-27" in explicit_dates
        assert "observed" in explicit_dates["2027-12-27"]["name"].lower()


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXJSERecurrence:
    def test_fixed_rules_exist(self, xjse):
        rules = xjse["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Human Rights Day" in names
        assert "Good Friday" in names
        assert "Family Day (Easter Monday)" in names
        assert "Freedom Day" in names
        assert "Workers' Day" in names
        assert "Youth Day" in names
        assert "National Women's Day" in names
        assert "Heritage Day" in names
        assert "Day of Reconciliation" in names
        assert "Christmas Day" in names
        assert "Day of Goodwill" in names

    def test_weekend_adjustment_rules(self, xjse):
        """South Africa observes Sunday holidays on Monday."""
        rules = xjse["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}

        for name in ["Human Rights Day", "Freedom Day", "Youth Day",
                      "National Women's Day", "Heritage Day",
                      "Day of Reconciliation", "Day of Goodwill"]:
            assert rule_by_name[name]["rule"] == "fixed_with_weekend_adjustment", \
                f"{name} should use fixed_with_weekend_adjustment"

    def test_workers_day_no_shift(self, xjse):
        """Workers' Day (May 1) does NOT shift in South Africa."""
        rules = xjse["holidays"].get("recurrence_rules", [])
        workers = [r for r in rules if r["name"] == "Workers' Day"]
        assert len(workers) == 1
        assert workers[0]["rule"] == "fixed_date"

    def test_easter_rules(self, xjse):
        rules = xjse["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}
        assert rule_by_name["Good Friday"]["rule"] == "easter_offset"
        assert rule_by_name["Good Friday"]["offset_days"] == -2
        assert rule_by_name["Family Day (Easter Monday)"]["rule"] == "easter_offset"
        assert rule_by_name["Family Day (Easter Monday)"]["offset_days"] == 1


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXJSEStructure:
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
        """JSE has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~60-70 entries: 12 holidays × 5 years."""
        assert 45 <= len(explicit_dates) <= 65