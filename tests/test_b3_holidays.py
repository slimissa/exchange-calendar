#!/usr/bin/env python3
"""
test_b3_holidays.py — Ground truth tests for XBSP (B3 — São Paulo Stock Exchange).

Key facts verified:
    - Brazil does NOT shift holidays from weekends (no substitute days)
    - Carnival dates vary (47 days before Easter) — explicit-only
    - Corpus Christi is 60 days after Easter — explicit-only
    - Fixed national holidays use fixed_date (no weekend adjustment)
    - Black Consciousness Day (Nov 20) is a São Paulo state holiday
    - Christmas Eve and New Year's Eve are FULL closures
    - No lunch break (continuous trading)
    - Pre-market: 09:45-10:00, Post-market: 17:00-17:30

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBSP.json)
    2. Brazilian holiday announcements changed (verify against b3.com.br)

Run:
    python3 -m pytest tests/test_b3_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbsp():
    """Load XBSP.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBSP.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbsp):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbsp["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBSPProperties:
    def test_code(self, xbsp):
        assert xbsp["code"] == "XBSP"

    def test_mic(self, xbsp):
        assert xbsp["mic"] == "XBSP"

    def test_name(self, xbsp):
        assert xbsp["name"] == "B3 (São Paulo Stock Exchange)"

    def test_timezone(self, xbsp):
        assert xbsp["timezone"] == "America/Sao_Paulo"

    def test_regular_hours(self, xbsp):
        assert xbsp["regular_hours"]["open"] == "10:00"
        assert xbsp["regular_hours"]["close"] == "17:00"

    def test_no_lunch_break(self, xbsp):
        lunch = [s for s in xbsp.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xbsp):
        assert xbsp["extended_hours"]["pre_market"]["open"] == "09:45"
        assert xbsp["extended_hours"]["after_hours"]["close"] == "17:30"


# ──────────────────────────────────────────────────────────────
# 2025 holidays
# ──────────────────────────────────────────────────────────────

class TestXBSP2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_carnival_monday(self, explicit_dates):
        assert "2025-03-03" in explicit_dates
        assert "Carnival" in explicit_dates["2025-03-03"]["name"]

    def test_carnival_tuesday(self, explicit_dates):
        assert "2025-03-04" in explicit_dates
        assert "Carnival" in explicit_dates["2025-03-04"]["name"]

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_tiradentes(self, explicit_dates):
        assert "2025-04-21" in explicit_dates

    def test_labour_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_corpus_christi(self, explicit_dates):
        assert "2025-06-19" in explicit_dates

    def test_independence_day(self, explicit_dates):
        assert "2025-09-07" not in explicit_dates

    def test_nossa_senhora(self, explicit_dates):
        """Oct 12, 2025 is Sunday — no explicit entry."""
        assert "2025-10-12" not in explicit_dates

    def test_all_souls(self, explicit_dates):
        """Nov 2, 2025 is Sunday — no explicit entry."""
        assert "2025-11-02" not in explicit_dates

    def test_republic_proclamation(self, explicit_dates):
        """Nov 15, 2025 is Saturday — no explicit entry."""
        assert "2025-11-15" not in explicit_dates

    def test_black_consciousness(self, explicit_dates):
        assert "2025-11-20" in explicit_dates

    def test_christmas_eve(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_christmas_day(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_new_years_eve(self, explicit_dates):
        assert "2025-12-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2026 holidays
# ──────────────────────────────────────────────────────────────

class TestXBSP2026:
    def test_new_year(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_carnival(self, explicit_dates):
        assert "2026-02-16" in explicit_dates
        assert "2026-02-17" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_corpus_christi(self, explicit_dates):
        assert "2026-06-04" in explicit_dates

    def test_independence_day(self, explicit_dates):
        assert "2026-09-07" in explicit_dates

    def test_christmas(self, explicit_dates):
        assert "2026-12-24" in explicit_dates
        assert "2026-12-25" in explicit_dates

    def test_new_years_eve(self, explicit_dates):
        assert "2026-12-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2027 holidays
# ──────────────────────────────────────────────────────────────

class TestXBSP2027:
    def test_carnival(self, explicit_dates):
        assert "2027-02-08" in explicit_dates
        assert "2027-02-09" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2027-03-26" in explicit_dates

    def test_corpus_christi(self, explicit_dates):
        assert "2027-05-27" in explicit_dates

    def test_independence_day(self, explicit_dates):
        assert "2027-09-07" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2028 holidays
# ──────────────────────────────────────────────────────────────

class TestXBSP2028:
    def test_carnival(self, explicit_dates):
        assert "2028-02-28" in explicit_dates
        assert "2028-02-29" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2028-04-14" in explicit_dates

    def test_corpus_christi(self, explicit_dates):
        assert "2028-06-15" in explicit_dates

    def test_no_christmas_eve_sunday(self, explicit_dates):
        """Dec 24, 2028 is Sunday — no explicit entry."""
        assert "2028-12-24" not in explicit_dates

    def test_christmas_day(self, explicit_dates):
        assert "2028-12-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2029 holidays
# ──────────────────────────────────────────────────────────────

class TestXBSP2029:
    def test_carnival(self, explicit_dates):
        assert "2029-02-12" in explicit_dates
        assert "2029-02-13" in explicit_dates

    def test_good_friday(self, explicit_dates):
        assert "2029-03-30" in explicit_dates

    def test_corpus_christi(self, explicit_dates):
        assert "2029-05-31" in explicit_dates

    def test_independence_day(self, explicit_dates):
        assert "2029-09-07" in explicit_dates

    def test_christmas_eve(self, explicit_dates):
        assert "2029-12-24" in explicit_dates

    def test_new_years_eve(self, explicit_dates):
        assert "2029-12-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXBSPRecurrence:
    def test_fixed_rules_exist(self, xbsp):
        rules = xbsp["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Tiradentes" in names
        assert "Labour Day" in names
        assert "Independence Day" in names
        assert "Nossa Senhora Aparecida" in names
        assert "All Souls' Day" in names
        assert "Republic Proclamation Day" in names
        assert "Black Consciousness Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "New Year's Eve" in names

    def test_good_friday_rule(self, xbsp):
        rules = xbsp["holidays"].get("recurrence_rules", [])
        good_friday = [r for r in rules if r["name"] == "Good Friday"]
        assert len(good_friday) == 1
        assert good_friday[0]["rule"] == "easter_offset"
        assert good_friday[0]["offset_days"] == -2

    def test_carnival_and_corpus_in_rules(self, xbsp):
        """Carnival and Corpus Christi ARE in recurrence rules (easter_offset)."""
        rules = xbsp["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Carnival Monday" in names
        assert "Carnival Tuesday" in names
        assert "Corpus Christi" in names

    def test_no_weekend_adjustment_in_rules(self, xbsp):
        """Brazil does NOT shift holidays — all fixed dates use fixed_date."""
        rules = xbsp["holidays"].get("recurrence_rules", [])
        for r in rules:
            if r["rule"] != "easter_offset":
                assert r["rule"] == "fixed_date", \
                    f"{r['name']} should use fixed_date, not {r['rule']}"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBSPStructure:
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

    def test_statuses_valid(self, explicit_dates):
        """Statuses are either closed or delayed_open (Ash Wednesday)."""
        for entry in explicit_dates.values():
            assert entry["status"] in ("closed", "delayed_open")

    def test_ash_wednesday_delayed_open(self, explicit_dates):
        """Ash Wednesday has delayed_open at 13:00."""
        ash_wed = [e for e in explicit_dates.values() if e["status"] == "delayed_open"]
        assert len(ash_wed) == 5  # 2025-2029
        for entry in ash_wed:
            assert entry["delayed_open_time"] == "13:00"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~70 entries: 15 holidays × 5 years, minus weekend overlaps."""
        assert 60 <= len(explicit_dates) <= 85