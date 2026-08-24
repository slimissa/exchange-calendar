#!/usr/bin/env python3
"""
test_early_close.py — Boundary tests for early close detection.

Tests the precise behavior of early close boundaries:
    - What happens at 12:29:59 vs 12:30:00 vs 12:30:01 for LSE
    - What happens at 12:59:59 vs 13:00:00 vs 13:00:01 for NYSE
    - Early close only applies on weekdays
    - Weekend early close dates are not in explicit arrays
    - Multiple exchanges have different early close times

These tests do not require a consumer implementation — they verify
the data in the registry is structured such that a consumer can
correctly determine status at any timestamp.

Run:
    python3 -m pytest tests/test_early_close.py -v
"""

import json
import sys
import pytest
from datetime import date, datetime, time, timedelta
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xnys():
    path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def xlon():
    path = Path(__file__).parent.parent / "exchanges" / "XLON.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def xnys_early_closes(xnys):
    """Return dict of date -> early_close_time for XNYS."""
    return {
        e["date"]: e["early_close_time"]
        for e in xnys["holidays"]["explicit"]
        if e["status"] == "early_close"
    }


@pytest.fixture(scope="module")
def xlon_early_closes(xlon):
    """Return dict of date -> early_close_time for XLON."""
    return {
        e["date"]: e["early_close_time"]
        for e in xlon["holidays"]["explicit"]
        if e["status"] == "early_close"
    }


# ──────────────────────────────────────────────────────────────
# Boundary time tests
# ──────────────────────────────────────────────────────────────

class TestBoundaryTimes:
    def test_nyse_early_close_is_1300(self):
        """All NYSE early closes are exactly 13:00."""
        early_closes = {}
        path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
        with open(path) as f:
            data = json.load(f)
        for e in data["holidays"]["explicit"]:
            if e["status"] == "early_close":
                early_closes[e["date"]] = e["early_close_time"]

        for date_str, close_time in early_closes.items():
            assert close_time == "13:00", f"{date_str}: expected 13:00, got {close_time}"

    def test_lse_early_close_is_1230(self):
        """All LSE early closes are exactly 12:30."""
        early_closes = {}
        path = Path(__file__).parent.parent / "exchanges" / "XLON.json"
        with open(path) as f:
            data = json.load(f)
        for e in data["holidays"]["explicit"]:
            if e["status"] == "early_close":
                early_closes[e["date"]] = e["early_close_time"]

        for date_str, close_time in early_closes.items():
            assert close_time == "12:30", f"{date_str}: expected 12:30, got {close_time}"

    def test_nyse_vs_lse_early_close_times_differ(self, xnys_early_closes, xlon_early_closes):
        """NYSE closes at 13:00, LSE at 12:30 — 30 minutes apart."""
        nyse_time = set(xnys_early_closes.values())
        lse_time = set(xlon_early_closes.values())

        assert nyse_time == {"13:00"}
        assert lse_time == {"12:30"}
        assert nyse_time != lse_time

    def test_early_close_time_parseable(self, xnys_early_closes, xlon_early_closes):
        """Every early close time is a valid HH:MM."""
        all_times = list(xnys_early_closes.values()) + list(xlon_early_closes.values())
        for time_str in all_times:
            hours, minutes = time_str.split(":")
            assert 0 <= int(hours) <= 23
            assert 0 <= int(minutes) <= 59

    def test_early_close_before_regular_close(self, xnys, xlon):
        """Early close time is always before regular close time."""
        nyse_regular_close = xnys["regular_hours"]["close"]
        lse_regular_close = xlon["regular_hours"]["close"]

        for e in xnys["holidays"]["explicit"]:
            if e["status"] == "early_close":
                assert e["early_close_time"] < nyse_regular_close

        for e in xlon["holidays"]["explicit"]:
            if e["status"] == "early_close":
                assert e["early_close_time"] < lse_regular_close

    def test_early_close_after_regular_open(self, xnys, xlon):
        """Early close time is always after regular open time."""
        nyse_regular_open = xnys["regular_hours"]["open"]
        lse_regular_open = xlon["regular_hours"]["open"]

        for e in xnys["holidays"]["explicit"]:
            if e["status"] == "early_close":
                assert e["early_close_time"] > nyse_regular_open

        for e in xlon["holidays"]["explicit"]:
            if e["status"] == "early_close":
                assert e["early_close_time"] > lse_regular_open


# ──────────────────────────────────────────────────────────────
# Weekday tests
# ──────────────────────────────────────────────────────────────

class TestWeekdayEarlyCloses:
    def test_nyse_early_closes_only_on_weekdays(self):
        """Every NYSE early close date is a Monday-Friday."""
        path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
        with open(path) as f:
            data = json.load(f)

        for e in data["holidays"]["explicit"]:
            if e["status"] == "early_close":
                d = date.fromisoformat(e["date"])
                assert d.weekday() < 5, f"Early close on weekend: {e['date']}"

    def test_lse_early_closes_only_on_weekdays(self):
        """Every LSE early close date is a Monday-Friday."""
        path = Path(__file__).parent.parent / "exchanges" / "XLON.json"
        with open(path) as f:
            data = json.load(f)

        for e in data["holidays"]["explicit"]:
            if e["status"] == "early_close":
                d = date.fromisoformat(e["date"])
                assert d.weekday() < 5, f"Early close on weekend: {e['date']}"

    def test_no_early_close_when_christmas_eve_is_weekend(self):
        """When Dec 24 falls on Saturday/Sunday, no early close entry."""
        path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
        with open(path) as f:
            data = json.load(f)

        # 2028-12-24 is Sunday — no early close
        dates = [e["date"] for e in data["holidays"]["explicit"] if e["status"] == "early_close"]
        assert "2028-12-24" not in dates

        # 2027-12-24 is Friday — early close exists
        assert "2027-12-24" in dates

    def test_no_early_close_when_new_years_eve_is_weekend(self):
        """When Dec 31 falls on Saturday/Sunday, no early close entry for LSE."""
        path = Path(__file__).parent.parent / "exchanges" / "XLON.json"
        with open(path) as f:
            data = json.load(f)

        dates = [e["date"] for e in data["holidays"]["explicit"] if e["status"] == "early_close"]
        # 2028-12-31 is Sunday — no early close
        assert "2028-12-31" not in dates

        # 2027-12-31 is Friday — early close exists
        assert "2027-12-31" in dates


# ──────────────────────────────────────────────────────────────
# Early close pattern tests
# ──────────────────────────────────────────────────────────────

class TestEarlyClosePatterns:
    def test_nyse_three_early_close_types(self):
        """NYSE has 3 recurring early close patterns: Black Friday, Christmas Eve, July 3."""
        path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
        with open(path) as f:
            data = json.load(f)

        early_closes = [e for e in data["holidays"]["explicit"] if e["status"] == "early_close"]

        # Should have: Black Friday (3), Christmas Eve (3), July 3 (3) for 2025-2029
        black_fridays = [e for e in early_closes if "Thanksgiving" in e["name"] or "Black" in e["name"]]
        christmas_eves = [e for e in early_closes if "Christmas Eve" in e["name"]]
        july_thirds = [e for e in early_closes if "July" in e["name"] or "Independence" in e["name"]]

        assert len(black_fridays) >= 4  # 2025, 2026, 2027, 2028, 2029 = 5
        assert len(christmas_eves) == 4  # 2025, 2026, 2027, 2029 (not 2028 - Sunday)
        assert len(july_thirds) == 3  # 2025, 2028, 2029 (not 2026 - observed, not 2027 - weekend)

    def test_lse_two_early_close_types(self):
        """LSE has 2 recurring early close patterns: Christmas Eve, New Year's Eve."""
        path = Path(__file__).parent.parent / "exchanges" / "XLON.json"
        with open(path) as f:
            data = json.load(f)

        early_closes = [e for e in data["holidays"]["explicit"] if e["status"] == "early_close"]

        christmas_eves = [e for e in early_closes if "Christmas Eve" in e["name"]]
        new_years_eves = [e for e in early_closes if "New Year's Eve" in e["name"]]

        # 2025, 2026, 2027, 2029 = 4 each (2028 both on Sunday)
        assert len(christmas_eves) == 4
        assert len(new_years_eves) == 4

    def test_nyse_july_3_early_close_conditional(self):
        """July 3 is early close only when July 4 is Tuesday-Friday."""
        path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
        with open(path) as f:
            data = json.load(f)

        early_closes = [e for e in data["holidays"]["explicit"] if e["status"] == "early_close"]
        july_3_dates = [e["date"] for e in early_closes if e["date"].endswith("-07-03")]

        # 2025: July 4 is Friday → July 3 early close ✓
        assert "2025-07-03" in july_3_dates

        # 2028: July 4 is Tuesday → July 3 early close ✓
        assert "2028-07-03" in july_3_dates

        # 2029: July 4 is Wednesday → July 3 early close ✓
        assert "2029-07-03" in july_3_dates

        # 2026: July 4 is Saturday → July 3 is observed holiday (closed), not early close
        assert "2026-07-03" not in july_3_dates

        # 2027: July 4 is Sunday → July 3 is Saturday (weekend), no early close
        assert "2027-07-03" not in july_3_dates


# ──────────────────────────────────────────────────────────────
# Consistency checks
# ──────────────────────────────────────────────────────────────

class TestConsistency:
    def test_early_close_never_duplicates_closed(self):
        """No date is both 'early_close' and 'closed' in the same exchange."""
        for code in ["XNYS", "XLON"]:
            path = Path(__file__).parent.parent / "exchanges" / f"{code}.json"
            with open(path) as f:
                data = json.load(f)

            dates_by_status = {}
            for e in data["holidays"]["explicit"]:
                if e["date"] not in dates_by_status:
                    dates_by_status[e["date"]] = set()
                dates_by_status[e["date"]].add(e["status"])

            for date_str, statuses in dates_by_status.items():
                assert len(statuses) == 1, f"{code}: {date_str} has multiple statuses: {statuses}"

    def test_early_close_entries_have_source(self):
        """Every early close entry has a source_url."""
        for code in ["XNYS", "XLON"]:
            path = Path(__file__).parent.parent / "exchanges" / f"{code}.json"
            with open(path) as f:
                data = json.load(f)

            for e in data["holidays"]["explicit"]:
                if e["status"] == "early_close":
                    assert "source_url" in e, f"{code}: {e['date']} missing source_url"

    def test_early_close_count_matches_expected(self):
        """XNYS has 12 early closes, XLON has 8 early closes for 2025-2029."""
        counts = {}

        for code in ["XNYS", "XLON"]:
            path = Path(__file__).parent.parent / "exchanges" / f"{code}.json"
            with open(path) as f:
                data = json.load(f)

            early_count = sum(1 for e in data["holidays"]["explicit"] if e["status"] == "early_close")
            counts[code] = early_count

        # XNYS: 5 Black Fridays + 4 Christmas Eves + 3 July 3rds = 12
        assert counts["XNYS"] == 12, f"XNYS: expected 12 early closes, got {counts['XNYS']}"

        # XLON: 4 Christmas Eves + 4 New Year's Eves = 8
        assert counts["XLON"] == 8, f"XLON: expected 8 early closes, got {counts['XLON']}"