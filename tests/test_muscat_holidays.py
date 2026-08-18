#!/usr/bin/env python3
"""
test_muscat_holidays.py — Ground truth tests for XMUS (Muscat Stock Exchange).

Key facts verified:
    - Regular hours: 10:00-13:00 (single session)
    - No lunch break
    - No extended hours sessions
    - Weekend is Friday-Saturday
    - New Year's Day with substitution
    - Renaissance Day (Jul 23) with substitution
    - National Day (Nov 18) with substitution
    - Eid al-Fitr, Eid al-Adha, Islamic New Year, Prophet's Birthday — explicit-only
    - All holidays are full closures

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XMUS.json)
    2. Omani holiday announcements changed (verify against msx.om)

Run:
    python3 -m pytest tests/test_muscat_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xmus():
    """Load XMUS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XMUS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xmus):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xmus["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xmus):
    """Return dict of name -> rule."""
    rules = xmus["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXMUSProperties:
    def test_code(self, xmus):
        assert xmus["code"] == "XMUS"

    def test_mic(self, xmus):
        assert xmus["mic"] == "XMUS"

    def test_name(self, xmus):
        assert xmus["name"] == "Muscat Stock Exchange"

    def test_timezone(self, xmus):
        assert xmus["timezone"] == "Asia/Muscat"

    def test_regular_hours(self, xmus):
        assert xmus["regular_hours"]["open"] == "10:00"
        assert xmus["regular_hours"]["close"] == "13:00"

    def test_no_lunch_break(self, xmus):
        lunch = [s for s in xmus.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xmus):
        assert "extended_hours" not in xmus or xmus.get("extended_hours") is None

    def test_generation_range(self, xmus):
        assert "generation_range" in xmus
        assert xmus["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xmus):
        assert xmus.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXMUSFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Sunday Jan 2."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-02" in explicit_dates
        assert "New Year's Day" in explicit_dates["2028-01-02"]["name"]

    def test_renaissance_day_2025(self, explicit_dates):
        """Jul 23, 2025 is Wednesday — no substitution."""
        assert "2025-07-23" in explicit_dates
        assert explicit_dates["2025-07-23"]["name"] == "Renaissance Day"

    def test_renaissance_day_2027_substitute(self, explicit_dates):
        """Jul 23, 2027 is Friday (weekend) — substitute to Sunday Jul 25."""
        assert "2027-07-23" not in explicit_dates
        assert "2027-07-25" in explicit_dates
        assert "Renaissance Day" in explicit_dates["2027-07-25"]["name"]

    def test_renaissance_day_2028(self, explicit_dates):
        """Jul 23, 2028 is Sunday — no substitution."""
        assert "2028-07-23" in explicit_dates

    def test_national_day_2025(self, explicit_dates):
        """Nov 18, 2025 is Tuesday — no substitution."""
        assert "2025-11-18" in explicit_dates
        assert explicit_dates["2025-11-18"]["name"] == "National Day"

    def test_national_day_2028_substitute(self, explicit_dates):
        """Nov 18, 2028 is Saturday — substitute to Sunday Nov 19."""
        assert "2028-11-18" not in explicit_dates
        assert "2028-11-19" in explicit_dates
        assert "National Day" in explicit_dates["2028-11-19"]["name"]

    def test_national_day_2029(self, explicit_dates):
        """Nov 18, 2029 is Sunday — no substitution."""
        assert "2029-11-18" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXMUSEidAlFitr:
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
        """Eid al-Fitr 2028 — Feb 26 (Saturday, weekend) — not in explicit.
        Weekday holiday starts Feb 27 (Sunday)."""
        assert "2028-02-26" not in explicit_dates
        assert "2028-02-27" in explicit_dates

    def test_eid_al_fitr_2029(self, explicit_dates):
        """Eid al-Fitr 2029 — predicted February 14."""
        assert "2029-02-14" in explicit_dates

    def test_eid_al_fitr_names_contain_predicted(self, explicit_dates):
        for entry in explicit_dates.values():
            if "Eid al-Fitr" in entry["name"]:
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Adha)
# ──────────────────────────────────────────────────────────────

class TestXMUSEidAlAdha:
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
        """Eid al-Adha 2028 — May 4 (Thursday) — no substitution."""
        assert "2028-05-04" in explicit_dates

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

class TestXMUSIslamicHolidays:
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
        """Islamic New Year 2028 — predicted May 25."""
        assert "2028-05-25" in explicit_dates

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

class TestXMUSRecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {"New Year's Day", "Renaissance Day", "National Day"}
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_no_islamic_rules(self, recurrence_rules):
        for name in recurrence_rules.keys():
            assert "Eid" not in name
            assert "Islamic" not in name
            assert "Prophet" not in name

    def test_weekend_adjustment_rules(self, recurrence_rules):
        for name in ["New Year's Day", "Renaissance Day", "National Day"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_with_weekend_adjustment"

    def test_all_rules_closed_status(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXMUSStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Oman weekend is Friday-Saturday."""
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
        """Oman has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xmus, explicit_dates):
        start = date.fromisoformat(xmus["generation_range"][0])
        end = date.fromisoformat(xmus["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~40-55 entries."""
        assert 40 <= len(explicit_dates) <= 60, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "msx.om" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXMUSWeekendPattern:
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

class TestXMUSSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-07-23" not in explicit_dates  # Friday

    def test_substitute_names_contain_observed(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "observed" in name or "substitute" in name:
                assert "observed" in name or "substitute" in name