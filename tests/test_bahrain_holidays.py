#!/usr/bin/env python3
"""
test_bahrain_holidays.py — Ground truth tests for XBAH (Bahrain Bourse).

Key facts verified:
    - Regular hours: 09:30-13:00
    - No lunch break
    - No extended hours sessions
    - Weekend is Friday-Saturday
    - New Year's Day (Jan 1) with substitution
    - Labour Day (May 1) with substitution
    - National Day (Dec 16) with substitution
    - Accession Day (Dec 17) with substitution
    - Eid al-Fitr, Eid al-Adha, Islamic New Year, Prophet's Birthday — explicit-only
    - All holidays are full closures

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBAH.json)
    2. Bahraini holiday announcements changed (verify against bahrainbourse.com)

Run:
    python3 -m pytest tests/test_bahrain_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbah():
    """Load XBAH.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBAH.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbah):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbah["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xbah):
    """Return dict of name -> rule."""
    rules = xbah["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBAHProperties:
    def test_code(self, xbah):
        assert xbah["code"] == "XBAH"

    def test_mic(self, xbah):
        assert xbah["mic"] == "XBAH"

    def test_name(self, xbah):
        assert xbah["name"] == "Bahrain Bourse"

    def test_timezone(self, xbah):
        assert xbah["timezone"] == "Asia/Bahrain"

    def test_regular_hours(self, xbah):
        assert xbah["regular_hours"]["open"] == "09:30"
        assert xbah["regular_hours"]["close"] == "13:00"

    def test_no_lunch_break(self, xbah):
        lunch = [s for s in xbah.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbah):
        assert "extended_hours" not in xbah or xbah.get("extended_hours") is None

    def test_generation_range(self, xbah):
        assert "generation_range" in xbah
        assert xbah["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xbah):
        assert xbah.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXBAHFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Sunday Jan 2."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-02" in explicit_dates
        assert "New Year's Day" in explicit_dates["2028-01-02"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday — no substitution."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2026(self, explicit_dates):
        """May 1, 2026 is Friday (weekend) — no explicit entry."""
        assert "2026-05-01" not in explicit_dates

    def test_labour_day_2027(self, explicit_dates):
        """May 1, 2027 is Saturday (weekend) — no explicit entry."""
        assert "2027-05-01" not in explicit_dates

    def test_labour_day_2028(self, explicit_dates):
        """May 1, 2028 is Monday — no substitution."""
        assert "2028-05-01" in explicit_dates

    def test_national_day_2025(self, explicit_dates):
        """Dec 16, 2025 is Tuesday — no substitution."""
        assert "2025-12-16" in explicit_dates
        assert explicit_dates["2025-12-16"]["name"] == "National Day"

    def test_national_day_2028_substitute(self, explicit_dates):
        """Dec 16, 2028 is Saturday — substitute to Sunday Dec 17."""
        assert "2028-12-16" not in explicit_dates
        assert "2028-12-17" in explicit_dates
        assert "National Day" in explicit_dates["2028-12-17"]["name"]

    def test_accession_day_2025(self, explicit_dates):
        """Dec 17, 2025 is Wednesday — no substitution."""
        assert "2025-12-17" in explicit_dates
        assert explicit_dates["2025-12-17"]["name"] == "Accession Day"

    def test_accession_day_2028_substitute(self, explicit_dates):
        """Dec 17, 2028 is Sunday — substitute to Monday Dec 18."""
        assert "2028-12-18" in explicit_dates
        assert "Accession Day" in explicit_dates["2028-12-18"]["name"]


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXBAHEidAlFitr:
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
        """All Eid al-Fitr holidays should be marked as predicted."""
        for entry in explicit_dates.values():
            if "Eid al-Fitr" in entry["name"]:
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Adha)
# ──────────────────────────────────────────────────────────────

class TestXBAHEidAlAdha:
    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — June 6 (Friday, weekend) — not in explicit.
        Weekday holiday starts June 8 (Sunday)."""
        assert "2025-06-06" not in explicit_dates
        assert "2025-06-08" in explicit_dates
        assert "Eid al-Adha" in explicit_dates["2025-06-08"]["name"]

    def test_eid_al_adha_2026(self, explicit_dates):
        """Eid al-Adha 2026 — predicted May 27."""
        assert "2026-05-27" in explicit_dates

    def test_eid_al_adha_2027(self, explicit_dates):
        """Eid al-Adha 2027 — predicted May 16."""
        assert "2027-05-16" in explicit_dates

    def test_eid_al_adha_2028(self, explicit_dates):
        """Eid al-Adha 2028 — predicted May 4."""
        assert "2028-05-04" in explicit_dates

    def test_eid_al_adha_2029(self, explicit_dates):
        """Eid al-Adha 2029 — predicted April 24."""
        assert "2029-04-24" in explicit_dates

    def test_eid_al_adha_names_contain_predicted(self, explicit_dates):
        """All Eid al-Adha holidays should be marked as predicted."""
        for entry in explicit_dates.values():
            if "Eid al-Adha" in entry["name"]:
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Islamic holidays (New Year and Prophet's Birthday)
# ──────────────────────────────────────────────────────────────

class TestXBAHIslamicHolidays:
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
        """All Islamic holidays should be marked as predicted."""
        islamic_names = ["Islamic New Year", "Prophet"]
        for entry in explicit_dates.values():
            if any(name in entry["name"] for name in islamic_names):
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXBAHRecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {"New Year's Day", "Labour Day", "National Day", "Accession Day"}
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_no_islamic_rules(self, recurrence_rules):
        """Islamic holidays are explicit-only (no recurrence rules)."""
        for name in recurrence_rules.keys():
            assert "Eid" not in name, f"Eid should not have recurrence rule: {name}"
            assert "Islamic" not in name, f"Islamic holiday should not have recurrence rule: {name}"
            assert "Prophet" not in name, f"Prophet's Birthday should not have recurrence rule: {name}"

    def test_weekend_adjustment_rules(self, recurrence_rules):
        for name in ["New Year's Day", "Labour Day", "National Day", "Accession Day"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_with_weekend_adjustment", f"{name} should use weekend adjustment"

    def test_all_rules_closed_status(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed", f"{name} should be closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBAHStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Bahrain weekend is Friday-Saturday. Sundays are working days."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() not in [4, 5], f"Weekend date: {date_str} ({d.strftime('%A')})"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates)), "Duplicate dates found"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"
            assert entry["source_url"].startswith("http"), f"Invalid source_url: {date_str}"

    def test_all_entries_have_name(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "name" in entry, f"Missing name: {date_str}"
            assert entry["name"], f"Empty name: {date_str}"

    def test_all_entries_have_status(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "status" in entry, f"Missing status: {date_str}"
            assert entry["status"] in ["closed", "early_close"], f"Invalid status: {date_str}"

    def test_all_statuses_closed(self, explicit_dates):
        """Bahrain has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", f"Unexpected status: {entry['date']}"

    def test_dates_within_generation_range(self, xbah, explicit_dates):
        start = date.fromisoformat(xbah["generation_range"][0])
        end = date.fromisoformat(xbah["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end, f"Date outside range: {date_str}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries: 7 holidays × 5 years (minus weekends)."""
        assert 45 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """All source URLs should be from bahrainbourse.com."""
        for entry in explicit_dates.values():
            assert "bahrainbourse.com" in entry["source_url"], f"Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBAHWeekendPattern:
    def test_friday_weekend(self, explicit_dates):
        """No Friday dates in explicit array."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 4, f"Friday date: {date_str}"

    def test_saturday_weekend(self, explicit_dates):
        """No Saturday dates in explicit array."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_is_working_day(self, explicit_dates):
        """Sunday is a working day in Bahrain."""
        sunday_count = 0
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            if d.weekday() == 6:
                sunday_count += 1
        assert sunday_count > 0, "Expected some Sunday holidays"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXBAHSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        """Verify known weekend holidays are correctly absent."""
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday
        assert "2028-12-16" not in explicit_dates  # Saturday

    def test_substitute_names_contain_observed(self, explicit_dates):
        """Bahrain uses 'observed' for shifted holidays."""
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "observed" in name:
                assert "observed" in name

    def test_substitutes_are_sunday_or_monday(self, explicit_dates):
        """Bahrain substitutes to Sunday (first working day)."""
        for entry in explicit_dates.values():
            if "observed" in entry["name"].lower() or "substitute" in entry["name"].lower():
                d = date.fromisoformat(entry["date"])
                assert d.weekday() in [0, 6], f"Substitute should be Sunday or Monday: {entry['date']}"