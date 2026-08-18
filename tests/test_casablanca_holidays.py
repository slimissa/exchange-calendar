#!/usr/bin/env python3
"""
test_casablanca_holidays.py — Ground truth tests for XCAS (Casablanca Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-15:30 (single session)
    - No lunch break
    - No extended hours sessions
    - Weekend is Saturday-Sunday (Western weekend)
    - Morocco does NOT shift holidays from weekends
    - New Year's Day (Jan 1)
    - Independence Manifesto Day (Jan 11)
    - Labour Day (May 1)
    - Throne Day (Jul 30)
    - Oued Ed-Dahab Day (Aug 14)
    - Revolution Day (Aug 20)
    - Youth Day (Aug 21)
    - Green March Day (Nov 6)
    - Independence Day (Nov 18)
    - Eid al-Fitr, Eid al-Adha, Islamic New Year, Prophet's Birthday — explicit-only
    - All holidays are full closures

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XCAS.json)
    2. Moroccan holiday announcements changed (verify against casablanca-bourse.com)

Run:
    python3 -m pytest tests/test_casablanca_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xcas():
    """Load XCAS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XCAS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xcas):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xcas["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xcas):
    """Return dict of name -> rule."""
    rules = xcas["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXCASProperties:
    def test_code(self, xcas):
        assert xcas["code"] == "XCAS"

    def test_mic(self, xcas):
        assert xcas["mic"] == "XCAS"

    def test_name(self, xcas):
        assert xcas["name"] == "Casablanca Stock Exchange"

    def test_timezone(self, xcas):
        assert xcas["timezone"] == "Africa/Casablanca"

    def test_regular_hours(self, xcas):
        assert xcas["regular_hours"]["open"] == "09:30"
        assert xcas["regular_hours"]["close"] == "15:30"

    def test_no_lunch_break(self, xcas):
        lunch = [s for s in xcas.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xcas):
        assert "extended_hours" not in xcas or xcas.get("extended_hours") is None

    def test_generation_range(self, xcas):
        assert "generation_range" in xcas
        assert xcas["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xcas):
        assert xcas.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (no weekend substitution)
# ──────────────────────────────────────────────────────────────

class TestXCASFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution needed."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_weekend(self, explicit_dates):
        """Jan 1, 2028 is Saturday — no explicit entry (no substitution)."""
        assert "2028-01-01" not in explicit_dates

    def test_independence_manifesto_2025(self, explicit_dates):
        """Jan 11, 2025 is Saturday — no explicit entry (no substitution)."""
        assert "2025-01-11" not in explicit_dates

    def test_independence_manifesto_2026(self, explicit_dates):
        """Jan 11, 2026 is Sunday — no explicit entry (no substitution)."""
        assert "2026-01-11" not in explicit_dates

    def test_independence_manifesto_2027(self, explicit_dates):
        """Jan 11, 2027 is Monday — explicit entry."""
        assert "2027-01-11" in explicit_dates
        assert explicit_dates["2027-01-11"]["name"] == "Independence Manifesto Day"

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday — explicit entry."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_weekend(self, explicit_dates):
        """May 1, 2027 is Saturday — no explicit entry (no substitution)."""
        assert "2027-05-01" not in explicit_dates

    def test_throne_day_2025(self, explicit_dates):
        """Jul 30, 2025 is Wednesday — explicit entry."""
        assert "2025-07-30" in explicit_dates
        assert explicit_dates["2025-07-30"]["name"] == "Throne Day"

    def test_oued_ed_dahab_2025(self, explicit_dates):
        """Aug 14, 2025 is Thursday — explicit entry."""
        assert "2025-08-14" in explicit_dates
        assert explicit_dates["2025-08-14"]["name"] == "Oued Ed-Dahab Day"

    def test_revolution_day_2025(self, explicit_dates):
        """Aug 20, 2025 is Wednesday — explicit entry."""
        assert "2025-08-20" in explicit_dates
        assert explicit_dates["2025-08-20"]["name"] == "Revolution Day"

    def test_youth_day_2025(self, explicit_dates):
        """Aug 21, 2025 is Thursday — explicit entry."""
        assert "2025-08-21" in explicit_dates
        assert explicit_dates["2025-08-21"]["name"] == "Youth Day"

    def test_green_march_2025(self, explicit_dates):
        """Nov 6, 2025 is Thursday — explicit entry."""
        assert "2025-11-06" in explicit_dates
        assert explicit_dates["2025-11-06"]["name"] == "Green March Day"

    def test_independence_day_2025(self, explicit_dates):
        """Nov 18, 2025 is Tuesday — explicit entry."""
        assert "2025-11-18" in explicit_dates
        assert explicit_dates["2025-11-18"]["name"] == "Independence Day"

    def test_independence_day_2028_weekend(self, explicit_dates):
        """Nov 18, 2028 is Saturday — no explicit entry (no substitution)."""
        assert "2028-11-18" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXCASEidAlFitr:
    def test_eid_al_fitr_2025(self, explicit_dates):
        """Eid al-Fitr 2025 — March 30 (Sunday, weekend) — not in explicit."""
        assert "2025-03-30" not in explicit_dates

    def test_eid_al_fitr_2026(self, explicit_dates):
        """Eid al-Fitr 2026 — March 20 (Friday, working day) — explicit entry."""
        assert "2026-03-20" in explicit_dates
        assert "2026-03-23" in explicit_dates

    def test_eid_al_fitr_2027(self, explicit_dates):
        """Eid al-Fitr 2027 — predicted March 9."""
        assert "2027-03-09" in explicit_dates

    def test_eid_al_fitr_2028(self, explicit_dates):
        """Eid al-Fitr 2028 — Feb 26 (Saturday) — not in explicit.
        Weekday holiday starts Feb 28 (Monday)."""
        assert "2028-02-26" not in explicit_dates
        assert "2028-02-28" in explicit_dates

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

class TestXCASEidAlAdha:
    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — June 6 (Friday) — explicit entry.
        June 9 (Monday) is the holiday."""
        assert "2025-06-06" in explicit_dates
        assert "2025-06-09" in explicit_dates

    def test_eid_al_adha_2026(self, explicit_dates):
        """Eid al-Adha 2026 — predicted May 27."""
        assert "2026-05-27" in explicit_dates

    def test_eid_al_adha_2027(self, explicit_dates):
        """Eid al-Adha 2027 — May 16 (Sunday, weekend) — not in explicit."""
        assert "2027-05-16" not in explicit_dates

    def test_eid_al_adha_2028(self, explicit_dates):
        """Eid al-Adha 2028 — predicted May 4."""
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

class TestXCASIslamicHolidays:
    def test_islamic_new_year_2025(self, explicit_dates):
        """Islamic New Year 2025 — predicted June 26."""
        assert "2025-06-26" in explicit_dates
        assert "Islamic New Year" in explicit_dates["2025-06-26"]["name"]

    def test_islamic_new_year_2026(self, explicit_dates):
        """Islamic New Year 2026 — predicted June 16."""
        assert "2026-06-16" in explicit_dates

    def test_islamic_new_year_2027(self, explicit_dates):
        """Islamic New Year 2027 — June 6 (Sunday, weekend) — not in explicit."""
        assert "2027-06-06" not in explicit_dates

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
        """Prophet's Birthday 2027 — August 15 (Sunday, weekend) — not in explicit."""
        assert "2027-08-15" not in explicit_dates

    def test_prophets_birthday_2028(self, explicit_dates):
        """Prophet's Birthday 2028 — August 4 (Friday, working day) — explicit entry."""
        assert "2028-08-04" in explicit_dates

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

class TestXCASRecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "New Year's Day",
            "Independence Manifesto Day",
            "Labour Day",
            "Throne Day",
            "Oued Ed-Dahab Day",
            "Revolution Day",
            "Youth Day",
            "Green March Day",
            "Independence Day",
        }
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_no_islamic_rules(self, recurrence_rules):
        for name in recurrence_rules.keys():
            assert "Eid" not in name
            assert "Islamic" not in name
            assert "Prophet" not in name

    def test_no_substitution_rules(self, recurrence_rules):
        """Morocco does NOT shift holidays from weekends."""
        for name, rule in recurrence_rules.items():
            assert rule["rule"] == "fixed_date", f"{name} should use fixed_date (no substitution)"

    def test_all_rules_closed_status(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXCASStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Morocco weekend is Saturday-Sunday."""
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
        """Morocco has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xcas, explicit_dates):
        start = date.fromisoformat(xcas["generation_range"][0])
        end = date.fromisoformat(xcas["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~55-75 entries: 9 fixed + 4 Islamic holidays across 5 years."""
        assert 55 <= len(explicit_dates) <= 80, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "casablanca-bourse.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXCASWeekendPattern:
    def test_saturday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_weekend(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 6, f"Sunday date: {date_str}"

    def test_friday_is_working_day(self, explicit_dates):
        friday_count = sum(1 for ds in explicit_dates if date.fromisoformat(ds).weekday() == 4)
        assert friday_count > 0, "Expected some Friday holidays"


# ──────────────────────────────────────────────────────────────
# No substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXCASNoSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        """Weekend holidays should be absent (no substitution)."""
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2025-01-11" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_no_observed_holidays(self, explicit_dates):
        """Morocco does not use 'observed' or 'substitute' names."""
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            assert "observed" not in name, f"Observed holiday found: {entry['name']}"
            assert "substitute" not in name, f"Substitute holiday found: {entry['name']}"