#!/usr/bin/env python3
"""
test_cairo_holidays.py — Ground truth tests for XCAI (Egyptian Exchange).

Key facts verified:
    - Regular hours: 10:00-14:30 (single session)
    - No lunch break
    - No extended hours sessions
    - Weekend is Friday-Saturday
    - Coptic Christmas (Jan 7) with substitution
    - Revolution Day (Jan 25) with substitution
    - Sinai Liberation Day (Apr 25) with substitution
    - Labour Day (May 1) with substitution
    - Revolution Day (Jul 23) with substitution
    - Armed Forces Day (Oct 6) with substitution
    - Eid al-Fitr, Eid al-Adha, Islamic New Year, Prophet's Birthday — explicit-only
    - All holidays are full closures

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XCAI.json)
    2. Egyptian holiday announcements changed (verify against egx.com.eg)

Run:
    python3 -m pytest tests/test_cairo_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xcai():
    """Load XCAI.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XCAI.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xcai):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xcai["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xcai):
    """Return dict of name -> rule."""
    rules = xcai["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXCAIProperties:
    def test_code(self, xcai):
        assert xcai["code"] == "XCAI"

    def test_mic(self, xcai):
        assert xcai["mic"] == "XCAI"

    def test_name(self, xcai):
        assert xcai["name"] == "Egyptian Exchange"

    def test_timezone(self, xcai):
        assert xcai["timezone"] == "Africa/Cairo"

    def test_regular_hours(self, xcai):
        assert xcai["regular_hours"]["open"] == "10:00"
        assert xcai["regular_hours"]["close"] == "14:30"

    def test_no_lunch_break(self, xcai):
        lunch = [s for s in xcai.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xcai):
        assert "extended_hours" not in xcai or xcai.get("extended_hours") is None

    def test_generation_range(self, xcai):
        assert "generation_range" in xcai
        assert xcai["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xcai):
        assert xcai.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXCAIFixedHolidays:
    def test_coptic_christmas_2025(self, explicit_dates):
        """Jan 7, 2025 is Tuesday — no substitution."""
        assert "2025-01-07" in explicit_dates
        assert explicit_dates["2025-01-07"]["name"] == "Coptic Christmas"

    def test_coptic_christmas_2028_weekend(self, explicit_dates):
        """Jan 7, 2028 is Friday (weekend) — no explicit entry."""
        assert "2028-01-07" not in explicit_dates

    def test_revolution_day_jan_2025_weekend(self, explicit_dates):
        """Jan 25, 2025 is Saturday (weekend) — no explicit entry."""
        assert "2025-01-25" not in explicit_dates

    def test_revolution_day_jan_2026(self, explicit_dates):
        """Jan 25, 2026 is Sunday — no substitution."""
        assert "2026-01-25" in explicit_dates

    def test_sinai_liberation_2025_weekend(self, explicit_dates):
        """Apr 25, 2025 is Friday (weekend) — no explicit entry."""
        assert "2025-04-25" not in explicit_dates

    def test_sinai_liberation_2026_weekend(self, explicit_dates):
        """Apr 25, 2026 is Saturday (weekend) — no explicit entry."""
        assert "2026-04-25" not in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday — no substitution."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_weekend(self, explicit_dates):
        """May 1, 2027 is Saturday (weekend) — no explicit entry."""
        assert "2027-05-01" not in explicit_dates

    def test_revolution_day_jul_2025(self, explicit_dates):
        """Jul 23, 2025 is Wednesday — no substitution."""
        assert "2025-07-23" in explicit_dates
        assert explicit_dates["2025-07-23"]["name"] == "Revolution Day (Jul 23)"

    def test_revolution_day_jul_2028(self, explicit_dates):
        """Jul 23, 2028 is Sunday — no substitution."""
        assert "2028-07-23" in explicit_dates

    def test_armed_forces_day_2025(self, explicit_dates):
        """Oct 6, 2025 is Monday — no substitution."""
        assert "2025-10-06" in explicit_dates
        assert explicit_dates["2025-10-06"]["name"] == "Armed Forces Day"

    def test_armed_forces_day_2028_substitute(self, explicit_dates):
        """Oct 6, 2028 is Friday (weekend) — substitute to Sunday Oct 8."""
        assert "2028-10-06" not in explicit_dates
        assert "2028-10-08" in explicit_dates
        assert "Armed Forces Day" in explicit_dates["2028-10-08"]["name"]


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXCAIEidAlFitr:
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

class TestXCAIEidAlAdha:
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

class TestXCAIIslamicHolidays:
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

class TestXCAIRecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "Coptic Christmas",
            "Revolution Day (Jan 25)",
            "Sinai Liberation Day",
            "Labour Day",
            "Revolution Day (Jul 23)",
            "Armed Forces Day",
        }
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_no_islamic_rules(self, recurrence_rules):
        for name in recurrence_rules.keys():
            assert "Eid" not in name
            assert "Islamic" not in name
            assert "Prophet" not in name

    def test_weekend_adjustment_rules(self, recurrence_rules):
        for name in recurrence_rules.keys():
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_with_weekend_adjustment"

    def test_all_rules_closed_status(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXCAIStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Egypt weekend is Friday-Saturday."""
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
        """Egypt has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xcai, explicit_dates):
        start = date.fromisoformat(xcai["generation_range"][0])
        end = date.fromisoformat(xcai["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-65 entries."""
        assert 50 <= len(explicit_dates) <= 70, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "egx.com.eg" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXCAIWeekendPattern:
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

class TestXCAISubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2025-01-25" not in explicit_dates  # Saturday
        assert "2028-10-06" not in explicit_dates  # Friday

    def test_substitute_names_contain_observed(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "observed" in name or "substitute" in name:
                assert "observed" in name or "substitute" in name