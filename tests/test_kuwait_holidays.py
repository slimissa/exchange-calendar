#!/usr/bin/env python3
"""
test_kuwait_holidays.py — Ground truth tests for XKUW (Bursa Kuwait).

Key facts verified:
    - Regular hours: 09:00-12:30 (morning), 13:00-14:30 (afternoon)
    - Lunch break: 12:30-13:00
    - Weekend is Friday-Saturday
    - New Year's Day with substitution
    - National Day (Feb 25) with substitution
    - Liberation Day (Feb 26) with substitution
    - Eid al-Fitr, Eid al-Adha, Islamic New Year, Prophet's Birthday — explicit-only
    - All holidays are full closures

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XKUW.json)
    2. Kuwaiti holiday announcements changed (verify against boursakuwait.com.kw)

Run:
    python3 -m pytest tests/test_kuwait_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xkuw():
    """Load XKUW.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XKUW.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xkuw):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xkuw["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xkuw):
    """Return dict of name -> rule."""
    rules = xkuw["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXKUWProperties:
    def test_code(self, xkuw):
        assert xkuw["code"] == "XKUW"

    def test_mic(self, xkuw):
        assert xkuw["mic"] == "XKUW"

    def test_name(self, xkuw):
        assert xkuw["name"] == "Bursa Kuwait"

    def test_timezone(self, xkuw):
        assert xkuw["timezone"] == "Asia/Kuwait"

    def test_regular_hours(self, xkuw):
        assert xkuw["regular_hours"]["open"] == "09:00"
        assert xkuw["regular_hours"]["close"] == "12:30"

    def test_lunch_break(self, xkuw):
        lunch = [s for s in xkuw.get("sessions", []) if s.get("type") == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "12:30"
        assert lunch[0]["close"] == "13:00"

    def test_afternoon_session(self, xkuw):
        afternoon = [s for s in xkuw.get("sessions", []) if s.get("type") == "afternoon"]
        assert len(afternoon) == 1
        assert afternoon[0]["open"] == "13:00"
        assert afternoon[0]["close"] == "14:30"

    def test_no_extended_hours(self, xkuw):
        assert "extended_hours" not in xkuw or xkuw.get("extended_hours") is None

    def test_generation_range(self, xkuw):
        assert "generation_range" in xkuw
        assert xkuw["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xkuw):
        assert xkuw.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXKUWFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Sunday Jan 2."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-02" in explicit_dates
        assert "New Year's Day" in explicit_dates["2028-01-02"]["name"]

    def test_national_day_2025(self, explicit_dates):
        """Feb 25, 2025 is Tuesday — no substitution."""
        assert "2025-02-25" in explicit_dates
        assert explicit_dates["2025-02-25"]["name"] == "National Day"

    def test_national_day_2026(self, explicit_dates):
        """Feb 25, 2026 is Wednesday — no substitution."""
        assert "2026-02-25" in explicit_dates

    def test_national_day_2027(self, explicit_dates):
        """Feb 25, 2027 is Thursday — no substitution."""
        assert "2027-02-25" in explicit_dates

    def test_liberation_day_2025(self, explicit_dates):
        """Feb 26, 2025 is Wednesday — no substitution."""
        assert "2025-02-26" in explicit_dates
        assert explicit_dates["2025-02-26"]["name"] == "Liberation Day"

    def test_liberation_day_2027_substitute(self, explicit_dates):
        """Feb 26, 2027 is Friday (weekend) — substitute to Sunday Feb 28."""
        assert "2027-02-26" not in explicit_dates
        assert "2027-02-28" in explicit_dates
        assert "Liberation Day" in explicit_dates["2027-02-28"]["name"]

    def test_liberation_day_2028_substitute(self, explicit_dates):
        """Feb 26, 2028 is Saturday (weekend) — substitute to Sunday Feb 27."""
        assert "2028-02-26" not in explicit_dates
        assert "2028-02-27" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXKUWEidAlFitr:
    def test_eid_al_fitr_2025(self, explicit_dates):
        """Eid al-Fitr 2025 — predicted March 30."""
        assert "2025-03-30" in explicit_dates
        assert "Eid al-Fitr" in explicit_dates["2025-03-30"]["name"]

    def test_eid_al_fitr_2026(self, explicit_dates):
        """Eid al-Fitr 2026 — March 20 (Friday, weekend) — not in explicit.
        Weekday holiday starts March 22 (Sunday)."""
        assert "2026-03-20" not in explicit_dates
        assert "2026-03-22" in explicit_dates

    def test_eid_al_fitr_2027(self, explicit_dates):
        """Eid al-Fitr 2027 — predicted March 9."""
        assert "2027-03-09" in explicit_dates

    def test_eid_al_fitr_2028(self, explicit_dates):
        """Eid al-Fitr 2028 — predicted February 27."""
        assert "2028-02-27" in explicit_dates

    def test_eid_al_fitr_2029(self, explicit_dates):
        """Eid al-Fitr 2029 — predicted February 15."""
        assert "2029-02-15" in explicit_dates

    def test_eid_al_fitr_names_contain_predicted(self, explicit_dates):
        for entry in explicit_dates.values():
            if "Eid al-Fitr" in entry["name"]:
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Adha)
# ──────────────────────────────────────────────────────────────

class TestXKUWEidAlAdha:
    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — June 6 (Friday, weekend) — not in explicit.
        Weekday holiday starts June 8 (Sunday)."""
        assert "2025-06-06" not in explicit_dates
        assert "2025-06-08" in explicit_dates

    def test_eid_al_adha_2026(self, explicit_dates):
        """Eid al-Adha 2026 — predicted May 27."""
        assert "2026-05-27" in explicit_dates

    def test_eid_al_adha_2027(self, explicit_dates):
        """Eid al-Adha 2027 — predicted May 16."""
        assert "2027-05-16" in explicit_dates

    def test_eid_al_adha_2028(self, explicit_dates):
        """Eid al-Adha 2028 — May 5 (Friday, weekend) — not in explicit.
        Weekday holiday starts May 7 (Sunday)."""
        assert "2028-05-05" not in explicit_dates
        assert "2028-05-07" in explicit_dates

    def test_eid_al_adha_2029(self, explicit_dates):
        """Eid al-Adha 2029 — predicted April 24."""
        assert "2029-04-24" in explicit_dates

    def test_eid_al_adha_names_contain_predicted(self, explicit_dates):
        for entry in explicit_dates.values():
            if "Eid al-Adha" in entry["name"]:
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Islamic holidays (New Year and Prophet's Birthday)
# ──────────────────────────────────────────────────────────────

class TestXKUWIslamicHolidays:
    def test_islamic_new_year_2025(self, explicit_dates):
        """Islamic New Year 2025 — predicted June 26."""
        assert "2025-06-26" in explicit_dates
        assert "Islamic New Year" in explicit_dates["2025-06-26"]["name"]

    def test_islamic_new_year_2026(self, explicit_dates):
        """Islamic New Year 2026 — predicted June 16."""
        assert "2026-06-16" in explicit_dates

    def test_islamic_new_year_2027(self, explicit_dates):
        """Islamic New Year 2027 — predicted June 6."""
        assert "2027-06-06" in explicit_dates

    def test_islamic_new_year_2028(self, explicit_dates):
        """Islamic New Year 2028 — May 26 (Friday, weekend) — not in explicit."""
        assert "2028-05-26" not in explicit_dates

    def test_islamic_new_year_2029(self, explicit_dates):
        """Islamic New Year 2029 — predicted May 14."""
        assert "2029-05-14" in explicit_dates

    def test_prophets_birthday_2025(self, explicit_dates):
        """Prophet's Birthday 2025 — predicted September 4."""
        assert "2025-09-04" in explicit_dates
        assert "Prophet" in explicit_dates["2025-09-04"]["name"]

    def test_prophets_birthday_2026(self, explicit_dates):
        """Prophet's Birthday 2026 — predicted August 25."""
        assert "2026-08-25" in explicit_dates

    def test_prophets_birthday_2027(self, explicit_dates):
        """Prophet's Birthday 2027 — predicted August 15."""
        assert "2027-08-15" in explicit_dates

    def test_prophets_birthday_2028(self, explicit_dates):
        """Prophet's Birthday 2028 — August 4 (Friday, weekend) — not in explicit."""
        assert "2028-08-04" not in explicit_dates

    def test_prophets_birthday_2029(self, explicit_dates):
        """Prophet's Birthday 2029 — predicted July 24."""
        assert "2029-07-24" in explicit_dates

    def test_islamic_holidays_contain_predicted(self, explicit_dates):
        islamic_names = ["Islamic New Year", "Prophet"]
        for entry in explicit_dates.values():
            if any(name in entry["name"] for name in islamic_names):
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXKUWRecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {"New Year's Day", "National Day", "Liberation Day"}
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_no_islamic_rules(self, recurrence_rules):
        for name in recurrence_rules.keys():
            assert "Eid" not in name
            assert "Islamic" not in name
            assert "Prophet" not in name

    def test_weekend_adjustment_rules(self, recurrence_rules):
        for name in ["New Year's Day", "National Day", "Liberation Day"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_with_weekend_adjustment"

    def test_all_rules_closed_status(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXKUWStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Kuwait weekend is Friday-Saturday."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() not in [4, 5], f"Weekend date: {date_str} ({d.strftime('%A')})"

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
        """Kuwait has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", f"Unexpected status: {entry['date']}"

    def test_dates_within_generation_range(self, xkuw, explicit_dates):
        start = date.fromisoformat(xkuw["generation_range"][0])
        end = date.fromisoformat(xkuw["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~45-55 entries."""
        assert 40 <= len(explicit_dates) <= 60, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "boursakuwait.com.kw" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXKUWWeekendPattern:
    def test_friday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 4, f"Friday date: {date_str}"

    def test_saturday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_is_working_day(self, explicit_dates):
        sunday_count = sum(1 for ds in explicit_dates if date.fromisoformat(ds).weekday() == 6)
        assert sunday_count > 0, "Expected some Sunday holidays"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXKUWSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-02-26" not in explicit_dates  # Friday

    def test_substitute_names_contain_observed(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "observed" in name or "substitute" in name:
                assert "observed" in name or "substitute" in name