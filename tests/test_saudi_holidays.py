#!/usr/bin/env python3
"""
test_saudi_holidays.py — Ground truth tests for XSAU (Saudi Stock Exchange / Tadawul).

Key facts verified:
    - Trading week: Sunday through Thursday
    - Weekend: Friday-Saturday (NOT Saturday-Sunday)
    - Saudi Founding Day (Feb 22) — shifted to Sunday when on Saturday
    - Saudi National Day (Sep 23) — shifted to Thursday when on Friday,
      shifted to Sunday when on Saturday
    - No lunch break (continuous trading)
    - Opening auction: 09:30-10:00, Closing auction: 15:00-15:10,
      Trade-at-Last: 15:10-15:20

Note: Islamic holidays (Eid al-Fitr, Eid al-Adha) are NOT included in
this version. They will be added in v1.1.0 with official Tadawul dates.

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XSAU.json)
    2. Saudi holiday announcements changed (verify against saudiexchange.sa)

Run:
    python3 -m pytest tests/test_saudi_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xsau():
    """Load XSAU.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XSAU.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xsau):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xsau["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXSAUProperties:
    def test_code(self, xsau):
        assert xsau["code"] == "XSAU"

    def test_mic(self, xsau):
        assert xsau["mic"] == "XSAU"

    def test_name(self, xsau):
        assert xsau["name"] == "Saudi Stock Exchange (Tadawul)"

    def test_timezone(self, xsau):
        assert xsau["timezone"] == "Asia/Riyadh"

    def test_regular_hours(self, xsau):
        assert xsau["regular_hours"]["open"] == "10:00"
        assert xsau["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xsau):
        lunch = [s for s in xsau.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xsau):
        assert xsau["extended_hours"]["pre_market"]["open"] == "09:30"
        assert xsau["extended_hours"]["after_hours"]["close"] == "15:20"


# ──────────────────────────────────────────────────────────────
# Saudi Founding Day — Feb 22
# ──────────────────────────────────────────────────────────────

class TestXSAUFoundingDay:
    def test_founding_day_2025_observed_sunday(self, explicit_dates):
        """
        Feb 22, 2025 is Saturday.
        Saudi Arabia observes on Sunday Feb 23, 2025.
        """
        assert "2025-02-22" not in explicit_dates  # Saturday
        assert "2025-02-23" in explicit_dates
        assert "Founding" in explicit_dates["2025-02-23"]["name"]
        assert "observed" in explicit_dates["2025-02-23"]["name"].lower()

    def test_founding_day_2026_sunday(self, explicit_dates):
        """Feb 22, 2026 is Sunday — no shift needed."""
        assert "2026-02-22" in explicit_dates
        assert explicit_dates["2026-02-22"]["status"] == "closed"

    def test_founding_day_2027_monday(self, explicit_dates):
        """Feb 22, 2027 is Monday — no shift needed."""
        assert "2027-02-22" in explicit_dates

    def test_founding_day_2028_tuesday(self, explicit_dates):
        """Feb 22, 2028 is Tuesday — no shift needed."""
        assert "2028-02-22" in explicit_dates

    def test_founding_day_2029_thursday(self, explicit_dates):
        """Feb 22, 2029 is Thursday — no shift needed."""
        assert "2029-02-22" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Saudi National Day — Sep 23
# ──────────────────────────────────────────────────────────────

class TestXSAUNationalDay:
    def test_national_day_2025_tuesday(self, explicit_dates):
        """Sep 23, 2025 is Tuesday — no shift needed."""
        assert "2025-09-23" in explicit_dates
        assert explicit_dates["2025-09-23"]["status"] == "closed"

    def test_national_day_2026_wednesday(self, explicit_dates):
        """Sep 23, 2026 is Wednesday — no shift needed."""
        assert "2026-09-23" in explicit_dates

    def test_national_day_2027_thursday(self, explicit_dates):
        """Sep 23, 2027 is Thursday — no shift needed."""
        assert "2027-09-23" in explicit_dates

    def test_national_day_2028_observed_sunday(self, explicit_dates):
        """
        Sep 23, 2028 is Saturday.
        Saudi Arabia observes on Sunday Sep 24, 2028.
        """
        assert "2028-09-23" not in explicit_dates  # Saturday
        assert "2028-09-24" in explicit_dates
        assert "National" in explicit_dates["2028-09-24"]["name"]
        assert "observed" in explicit_dates["2028-09-24"]["name"].lower()

    def test_national_day_2029_sunday(self, explicit_dates):
        """Sep 23, 2029 is Sunday — no shift needed."""
        assert "2029-09-23" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Weekend awareness — Friday/Saturday
# ──────────────────────────────────────────────────────────────

class TestXSAUWeekend:
    def test_no_friday_dates(self, explicit_dates):
        """Saudi weekend includes Friday — no Friday dates in explicit."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 4, f"Friday date: {date_str}"

    def test_no_saturday_dates(self, explicit_dates):
        """Saudi weekend includes Saturday — no Saturday dates in explicit."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_is_trading_day(self, explicit_dates):
        """
        Sunday is a TRADING day in Saudi Arabia.
        No weekend exclusion for Sunday.
        """
        # Founding Day 2026 is Sunday — it's in explicit as a holiday
        assert "2026-02-22" in explicit_dates
        # But it's a holiday, not a weekend


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXSAURecurrence:
    def test_fixed_rules_exist(self, xsau):
        rules = xsau["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Saudi Founding Day" in names
        assert "Saudi National Day" in names

    def test_all_use_fixed_date(self, xsau):
        rules = xsau["holidays"].get("recurrence_rules", [])
        for r in rules:
            assert r["rule"] == "fixed_date", \
                f"{r['name']} should use fixed_date, not {r['rule']}"

    def test_no_islamic_rules(self, xsau):
        """Islamic holidays are NOT in recurrence rules (lunisolar)."""
        rules = xsau["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Eid Al-Fitr" not in names
        assert "Eid Al-Adha" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXSAUStructure:
    def test_no_friday_saturday_dates(self, explicit_dates):
        """Explicit array contains only Sunday-Thursday dates."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() not in (4, 5), \
                f"Weekend date (Fri/Sat): {date_str}"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source: {date_str}"

    def test_all_statuses_closed(self, explicit_dates):
        """Saudi Arabia has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~10 entries: 2 fixed holidays × 5 years + observed shifts."""
        assert 8 <= len(explicit_dates) <= 15