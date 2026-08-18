#!/usr/bin/env python3
"""
test_dhaka_holidays.py — Ground truth tests for XDHA (Dhaka Stock Exchange).

Key facts verified:
    - Regular hours: 10:00-14:30 (single session)
    - No lunch break
    - Weekend is Friday-Saturday (Islamic weekend)
    - Language Movement Day (Feb 21)
    - Independence Day (Mar 26)
    - Bengali New Year (Apr 14)
    - Labour Day (May 1)
    - Victory Day (Dec 16)
    - Christmas Day (Dec 25)
    - Islamic holidays (Eid al-Fitr, Eid al-Adha) — explicit-only
    - Durga Puja (Hindu, movable) — explicit-only
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XDHA.json)
    2. Bangladeshi holiday announcements changed (verify against dsebd.org)

Run:
    python3 -m pytest tests/test_dhaka_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xdha():
    """Load XDHA.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XDHA.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xdha):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xdha["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXDHAProperties:
    def test_code(self, xdha):
        assert xdha["code"] == "XDHA"

    def test_mic(self, xdha):
        assert xdha["mic"] == "XDHA"

    def test_name(self, xdha):
        assert xdha["name"] == "Dhaka Stock Exchange"

    def test_timezone(self, xdha):
        assert xdha["timezone"] == "Asia/Dhaka"

    def test_regular_hours(self, xdha):
        assert xdha["regular_hours"]["open"] == "10:00"
        assert xdha["regular_hours"]["close"] == "14:30"

    def test_no_lunch_break(self, xdha):
        lunch = [s for s in xdha.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xdha):
        assert "extended_hours" not in xdha or xdha.get("extended_hours") is None

    def test_generation_range(self, xdha):
        assert "generation_range" in xdha
        assert xdha["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xdha):
        assert xdha.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xdha):
        """Bangladesh uses explicit dates only."""
        rules = xdha["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXDHAFixedHolidays:
    def test_language_day_2025(self, explicit_dates):
        """Feb 21, 2025 is Friday — no explicit entry (weekend)."""
        assert "2025-02-21" not in explicit_dates

    def test_language_day_2026(self, explicit_dates):
        """Feb 21, 2026 is Saturday — no explicit entry (weekend)."""
        assert "2026-02-21" not in explicit_dates

    def test_independence_2025(self, explicit_dates):
        """Mar 26, 2025 is Wednesday."""
        assert "2025-03-26" in explicit_dates
        assert "Independence" in explicit_dates["2025-03-26"]["name"]

    def test_independence_2026(self, explicit_dates):
        """Mar 26, 2026 is Thursday."""
        assert "2026-03-26" in explicit_dates

    def test_bengali_new_year_2025(self, explicit_dates):
        """Apr 14, 2025 is Monday."""
        assert "2025-04-14" in explicit_dates
        assert "Bengali" in explicit_dates["2025-04-14"]["name"]

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_victory_day_2025(self, explicit_dates):
        """Dec 16, 2025 is Tuesday."""
        assert "2025-12-16" in explicit_dates
        assert "Victory" in explicit_dates["2025-12-16"]["name"]

    def test_christmas_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert "Christmas" in explicit_dates["2025-12-25"]["name"]

    def test_christmas_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXDHAEidAlFitr:
    def test_eid_al_fitr_2025(self, explicit_dates):
        """Eid al-Fitr 2025 — predicted March 31."""
        assert "2025-03-31" in explicit_dates
        assert "Eid al-Fitr" in explicit_dates["2025-03-31"]["name"]

    def test_eid_al_fitr_2026(self, explicit_dates):
        """Eid al-Fitr 2026 — March 20 (Friday) — not in explicit."""
        assert "2026-03-20" not in explicit_dates

    def test_eid_al_fitr_2027(self, explicit_dates):
        """Eid al-Fitr 2027 — predicted March 9."""
        assert "2027-03-09" in explicit_dates

    def test_eid_al_fitr_2028(self, explicit_dates):
        """Eid al-Fitr 2028 — Feb 26 (Saturday) — not in explicit."""
        assert "2028-02-26" not in explicit_dates

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

class TestXDHAEidAlAdha:
    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — June 7 (Saturday) — not in explicit.
        Weekday holiday starts June 9 (Monday)."""
        assert "2025-06-07" not in explicit_dates
        assert "2025-06-09" in explicit_dates

    def test_eid_al_adha_2026(self, explicit_dates):
        """Eid al-Adha 2026 — predicted May 27."""
        assert "2026-05-27" in explicit_dates

    def test_eid_al_adha_2027(self, explicit_dates):
        """Eid al-Adha 2027 — May 16 (Sunday, working day) — explicit entry."""
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
# Durga Puja (Hindu movable holiday)
# ──────────────────────────────────────────────────────────────

class TestXDHADurgaPuja:
    def test_durga_puja_2025(self, explicit_dates):
        """Durga Puja 2025 — predicted October 2."""
        assert "2025-10-02" in explicit_dates
        assert "Durga" in explicit_dates["2025-10-02"]["name"]

    def test_durga_puja_2026(self, explicit_dates):
        """Durga Puja 2026 — predicted October 20."""
        assert "2026-10-20" in explicit_dates

    def test_durga_puja_2027(self, explicit_dates):
        """Durga Puja 2027 — Oct 9 (Saturday, weekend) — not in explicit."""
        assert "2027-10-09" not in explicit_dates

    def test_durga_puja_2028(self, explicit_dates):
        """Durga Puja 2028 — predicted September 28."""
        assert "2028-09-28" in explicit_dates

    def test_durga_puja_2029(self, explicit_dates):
        """Durga Puja 2029 — predicted October 17."""
        assert "2029-10-17" in explicit_dates

    def test_durga_puja_names_contain_predicted(self, explicit_dates):
        for entry in explicit_dates.values():
            if "Durga" in entry["name"]:
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXDHAStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Bangladesh weekend is Friday-Saturday."""
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
        """Bangladesh has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xdha, explicit_dates):
        start = date.fromisoformat(xdha["generation_range"][0])
        end = date.fromisoformat(xdha["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~45-60 entries."""
        assert 40 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "dsebd.org" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXDHAWeekendPattern:
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

class TestXDHASubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2025-02-21" not in explicit_dates  # Friday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 2, f"Expected some observed holidays, got {observed_count}"