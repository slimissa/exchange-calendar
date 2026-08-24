#!/usr/bin/env python3
"""
test_korea_holidays.py — Ground truth tests for XKRX (Korea Exchange).

Key facts verified:
    - KRX has NO lunch break (continuous trading 09:00-15:30 KST)
    - Seollal (Lunar New Year) and Chuseok are lunisolar — explicit-only
    - Year-End Holiday: last business day of December
    - Labour Day (May 1) is a mandatory closure on KRX
    - Substitute holidays (Daeche Gonghyuil) when fixed dates fall on weekends
    - Buddha's Birthday: 8th day of 4th lunar month
    - No US-style extended hours

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XKRX.json)
    2. Korean holiday regulations changed (verify against krx.co.kr)

Run:
    python3 -m pytest tests/test_korea_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xkrx():
    """Load XKRX.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XKRX.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xkrx):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xkrx["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXKRXProperties:
    def test_code(self, xkrx):
        assert xkrx["code"] == "XKRX"

    def test_mic(self, xkrx):
        assert xkrx["mic"] == "XKRX"

    def test_name(self, xkrx):
        assert xkrx["name"] == "Korea Exchange"

    def test_timezone(self, xkrx):
        assert xkrx["timezone"] == "Asia/Seoul"

    def test_regular_hours(self, xkrx):
        assert xkrx["regular_hours"]["open"] == "09:00"
        assert xkrx["regular_hours"]["close"] == "15:30"

    def test_no_lunch_break(self, xkrx):
        """KRX is continuous trading — NO lunch break."""
        lunch = [s for s in xkrx.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_auction_sessions(self, xkrx):
        auctions = [s for s in xkrx.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 2
        times = [a["at"] for a in auctions]
        assert "09:00" in times
        assert "15:30" in times

    def test_no_recurrence_rules(self, xkrx):
        """Korean holidays are lunisolar — explicit-only."""
        assert xkrx["holidays"].get("recurrence_rules", []) == []


# ──────────────────────────────────────────────────────────────
# Substitute holidays (Daeche Gonghyuil)
# ──────────────────────────────────────────────────────────────

class TestXKRXSubstitutes:
    def test_independence_observed_2025(self, explicit_dates):
        """March 1, 2025 is Saturday — observed Monday March 3."""
        assert "2025-03-01" not in explicit_dates  # Saturday
        assert "2025-03-03" in explicit_dates
        assert "Independence" in explicit_dates["2025-03-03"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        """May 1 is Labour Day — mandatory KRX closure."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["status"] == "closed"

    def test_independence_observed_2026(self, explicit_dates):
        """March 1, 2026 is Sunday — observed Monday March 2."""
        assert "2026-03-02" in explicit_dates
        assert "Independence" in explicit_dates["2026-03-02"]["name"]

    def test_buddha_birthday_observed_2026(self, explicit_dates):
        """Buddha's Birthday May 24, 2026 is Sunday — observed Monday May 25."""
        assert "2026-05-24" not in explicit_dates
        assert "2026-05-25" in explicit_dates
        assert "Buddha" in explicit_dates["2026-05-25"]["name"]

    def test_liberation_observed_2026(self, explicit_dates):
        """Aug 15, 2026 is Saturday — observed Monday Aug 17."""
        assert "2026-08-17" in explicit_dates
        assert "Liberation" in explicit_dates["2026-08-17"]["name"]

    def test_national_foundation_observed_2026(self, explicit_dates):
        """Oct 3, 2026 is Saturday — observed Monday Oct 5."""
        assert "2026-10-05" in explicit_dates
        assert "National Foundation" in explicit_dates["2026-10-05"]["name"]

    def test_national_foundation_observed_2027(self, explicit_dates):
        """Oct 3, 2027 is Sunday — observed Monday Oct 4."""
        assert "2027-10-04" in explicit_dates
        assert "National Foundation" in explicit_dates["2027-10-04"]["name"]

    def test_christmas_observed_2027(self, explicit_dates):
        """Dec 25, 2027 is Saturday — observed Monday Dec 27."""
        assert "2027-12-27" in explicit_dates
        assert "Christmas" in explicit_dates["2027-12-27"]["name"]


# ──────────────────────────────────────────────────────────────
# Year-End Holiday
# ──────────────────────────────────────────────────────────────

class TestXKRXYearEnd:
    def test_year_end_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — closure."""
        assert "2025-12-31" in explicit_dates
        assert "Year-End" in explicit_dates["2025-12-31"]["name"]

    def test_year_end_2026(self, explicit_dates):
        """Dec 31, 2026 is Thursday — closure."""
        assert "2026-12-31" in explicit_dates

    def test_year_end_2027(self, explicit_dates):
        """Dec 31, 2027 is Friday — closure."""
        assert "2027-12-31" in explicit_dates

    def test_year_end_2028_friday(self, explicit_dates):
        """
        Dec 31, 2028 is Sunday. Last business day is Friday Dec 29.
        """
        assert "2028-12-29" in explicit_dates
        assert "2028-12-31" not in explicit_dates  # Sunday

    def test_year_end_2029(self, explicit_dates):
        """Dec 31, 2029 is Monday — closure."""
        assert "2029-12-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Seollal (Lunar New Year)
# ──────────────────────────────────────────────────────────────

class TestXKRXSeollal:
    def test_seollal_2025(self, explicit_dates):
        assert "2025-01-28" in explicit_dates  # Eve
        assert "2025-01-29" in explicit_dates  # Day 1
        assert "2025-01-30" in explicit_dates  # Day 2

    def test_seollal_2026(self, explicit_dates):
        assert "2026-02-16" in explicit_dates  # Eve
        assert "2026-02-17" in explicit_dates  # Day 1
        assert "2026-02-18" in explicit_dates  # Day 2

    def test_seollal_2027(self, explicit_dates):
        assert "2027-02-05" in explicit_dates  # Eve
        assert "2027-02-08" in explicit_dates  # Day 1 (Monday)
        assert "2027-02-09" in explicit_dates  # Day 2

    def test_seollal_2028(self, explicit_dates):
        assert "2028-01-26" in explicit_dates  # Eve
        assert "2028-01-27" in explicit_dates  # Day 1

    def test_seollal_2029(self, explicit_dates):
        assert "2029-02-12" in explicit_dates  # Eve
        assert "2029-02-13" in explicit_dates  # Day 1
        assert "2029-02-14" in explicit_dates  # Day 2


# ──────────────────────────────────────────────────────────────
# Chuseok (Korean Thanksgiving)
# ──────────────────────────────────────────────────────────────

class TestXKRXChuseok:
    def test_chuseok_2025(self, explicit_dates):
        assert "2025-10-06" in explicit_dates  # Eve
        assert "2025-10-07" in explicit_dates  # Day 1
        assert "2025-10-08" in explicit_dates  # Day 2

    def test_chuseok_2026(self, explicit_dates):
        assert "2026-09-24" in explicit_dates  # Eve
        assert "2026-09-25" in explicit_dates  # Day 1

    def test_chuseok_2027(self, explicit_dates):
        assert "2027-09-14" in explicit_dates  # Eve
        assert "2027-09-15" in explicit_dates  # Day 1

    def test_chuseok_2028(self, explicit_dates):
        assert "2028-10-03" in explicit_dates  # Day 1
        assert "2028-10-04" in explicit_dates  # Day 2

    def test_chuseok_2029(self, explicit_dates):
        assert "2029-09-24" in explicit_dates  # Day 1


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXKRXStructure:
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
        """KRX has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", \
                f"Unexpected status: {entry['date']}: {entry['status']}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~71 entries: 12 holidays × 5 years + substitutes."""
        assert 60 <= len(explicit_dates) <= 85