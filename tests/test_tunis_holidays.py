#!/usr/bin/env python3
"""
test_tunis_holidays.py — Ground truth tests for XTUN (Tunis Stock Exchange).

Key facts verified:
    - Regular hours: 09:00-14:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Independence Day (Mar 20)
    - Martyrs' Day (Apr 9)
    - Republic Day (Jul 25)
    - Women's Day (Aug 13)
    - Evacuation Day (Oct 15)
    - Revolution Day (Dec 17)
    - Islamic holidays (Eid al-Fitr, Eid al-Adha, Islamic New Year, Prophet's Birthday)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XTUN.json)
    2. Tunisian holiday announcements changed (verify against bvmt.com.tn)

Run:
    python3 -m pytest tests/test_tunis_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xtun():
    """Load XTUN.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XTUN.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xtun):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xtun["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXTUNProperties:
    def test_code(self, xtun):
        assert xtun["code"] == "XTUN"

    def test_mic(self, xtun):
        assert xtun["mic"] == "XTUN"

    def test_name(self, xtun):
        assert xtun["name"] == "Tunis Stock Exchange"

    def test_timezone(self, xtun):
        assert xtun["timezone"] == "Africa/Tunis"

    def test_regular_hours(self, xtun):
        assert xtun["regular_hours"]["open"] == "09:00"
        assert xtun["regular_hours"]["close"] == "14:00"

    def test_no_lunch_break(self, xtun):
        lunch = [s for s in xtun.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xtun):
        assert "extended_hours" not in xtun or xtun.get("extended_hours") is None

    def test_generation_range(self, xtun):
        assert "generation_range" in xtun
        assert xtun["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xtun):
        assert xtun.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xtun):
        """Tunisia uses explicit dates only."""
        rules = xtun["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXTUNFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_independence_2025(self, explicit_dates):
        """Mar 20, 2025 is Thursday."""
        assert "2025-03-20" in explicit_dates
        assert "Independence" in explicit_dates["2025-03-20"]["name"]

    def test_martyrs_2025(self, explicit_dates):
        """Apr 9, 2025 is Wednesday."""
        assert "2025-04-09" in explicit_dates
        assert "Martyrs" in explicit_dates["2025-04-09"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_republic_day_2025(self, explicit_dates):
        """Jul 25, 2025 is Friday."""
        assert "2025-07-25" in explicit_dates
        assert "Republic" in explicit_dates["2025-07-25"]["name"]

    def test_womens_day_2025(self, explicit_dates):
        """Aug 13, 2025 is Wednesday."""
        assert "2025-08-13" in explicit_dates
        assert "Women" in explicit_dates["2025-08-13"]["name"]

    def test_evacuation_2025(self, explicit_dates):
        """Oct 15, 2025 is Wednesday."""
        assert "2025-10-15" in explicit_dates
        assert "Evacuation" in explicit_dates["2025-10-15"]["name"]

    def test_revolution_2025(self, explicit_dates):
        """Dec 17, 2025 is Wednesday."""
        assert "2025-12-17" in explicit_dates
        assert "Revolution" in explicit_dates["2025-12-17"]["name"]


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXTUNEidAlFitr:
    def test_eid_al_fitr_2025(self, explicit_dates):
        """Eid al-Fitr 2025 — predicted March 31."""
        assert "2025-03-31" in explicit_dates
        assert "Eid al-Fitr" in explicit_dates["2025-03-31"]["name"]

    def test_eid_al_fitr_2027(self, explicit_dates):
        """Eid al-Fitr 2027 — predicted March 9."""
        assert "2027-03-09" in explicit_dates

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

class TestXTUNEidAlAdha:
    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — predicted June 7."""
        assert "2025-06-07" in explicit_dates
        assert "Eid al-Adha" in explicit_dates["2025-06-07"]["name"]

    def test_eid_al_adha_2026(self, explicit_dates):
        """Eid al-Adha 2026 — predicted May 27."""
        assert "2026-05-27" in explicit_dates

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

class TestXTUNIslamicHolidays:
    def test_islamic_new_year_2025(self, explicit_dates):
        """Islamic New Year 2025 — predicted June 26."""
        assert "2025-06-26" in explicit_dates
        assert "Islamic New Year" in explicit_dates["2025-06-26"]["name"]

    def test_islamic_new_year_2028(self, explicit_dates):
        """Islamic New Year 2028 — predicted May 25."""
        assert "2028-05-25" in explicit_dates

    def test_prophets_birthday_2025(self, explicit_dates):
        """Prophet's Birthday 2025 — predicted September 4."""
        assert "2025-09-04" in explicit_dates
        assert "Prophet" in explicit_dates["2025-09-04"]["name"]

    def test_prophets_birthday_2029(self, explicit_dates):
        """Prophet's Birthday 2029 — predicted July 24."""
        assert "2029-07-24" in explicit_dates

    def test_islamic_holidays_contain_predicted(self, explicit_dates):
        islamic_names = ["Islamic New Year", "Prophet"]
        for entry in explicit_dates.values():
            if any(name in entry["name"] for name in islamic_names):
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXTUNStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Tunisia weekend is Saturday-Sunday."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str} ({d.strftime('%A')})"

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
        """Tunisia has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xtun, explicit_dates):
        start = date.fromisoformat(xtun["generation_range"][0])
        end = date.fromisoformat(xtun["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~60-70 entries."""
        assert 55 <= len(explicit_dates) <= 75, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "bvmt.com.tn" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXTUNWeekendPattern:
    def test_saturday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 6, f"Sunday date: {date_str}"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXTUNSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 2, f"Expected some observed holidays, got {observed_count}"