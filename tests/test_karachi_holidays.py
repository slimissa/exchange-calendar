#!/usr/bin/env python3
"""
test_karachi_holidays.py — Ground truth tests for XKAR (Pakistan Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-15:30 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Kashmir Day (Feb 5)
    - Pakistan Day (Mar 23)
    - Labour Day (May 1)
    - Independence Day (Aug 14)
    - Iqbal Day (Nov 9)
    - Quaid-e-Azam Day (Dec 25)
    - Islamic holidays (Eid al-Fitr, Eid al-Adha, Ashura, Eid Milad-un-Nabi) — explicit-only
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XKAR.json)
    2. Pakistani holiday announcements changed (verify against psx.com.pk)

Run:
    python3 -m pytest tests/test_karachi_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xkar():
    """Load XKAR.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XKAR.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xkar):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xkar["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXKARProperties:
    def test_code(self, xkar):
        assert xkar["code"] == "XKAR"

    def test_mic(self, xkar):
        assert xkar["mic"] == "XKAR"

    def test_name(self, xkar):
        assert xkar["name"] == "Pakistan Stock Exchange"

    def test_timezone(self, xkar):
        assert xkar["timezone"] == "Asia/Karachi"

    def test_regular_hours(self, xkar):
        assert xkar["regular_hours"]["open"] == "09:30"
        assert xkar["regular_hours"]["close"] == "15:30"

    def test_no_lunch_break(self, xkar):
        lunch = [s for s in xkar.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xkar):
        assert "extended_hours" not in xkar or xkar.get("extended_hours") is None

    def test_generation_range(self, xkar):
        assert "generation_range" in xkar
        assert xkar["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xkar):
        assert xkar.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xkar):
        """Pakistan uses explicit dates only."""
        rules = xkar["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXKARFixedHolidays:
    def test_kashmir_day_2025(self, explicit_dates):
        """Feb 5, 2025 is Wednesday."""
        assert "2025-02-05" in explicit_dates
        assert "Kashmir" in explicit_dates["2025-02-05"]["name"]

    def test_kashmir_day_2026(self, explicit_dates):
        """Feb 5, 2026 is Thursday."""
        assert "2026-02-05" in explicit_dates

    def test_pakistan_day_2025(self, explicit_dates):
        """Mar 23, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-03-23" not in explicit_dates

    def test_pakistan_day_2026(self, explicit_dates):
        """Mar 23, 2026 is Monday."""
        assert "2026-03-23" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_independence_2025(self, explicit_dates):
        """Aug 14, 2025 is Thursday."""
        assert "2025-08-14" in explicit_dates
        assert "Independence" in explicit_dates["2025-08-14"]["name"]

    def test_iqbal_day_2025(self, explicit_dates):
        """Nov 9, 2025 is Sunday (weekend) — no explicit entry."""
        assert "2025-11-09" not in explicit_dates

    def test_quaid_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert "Quaid" in explicit_dates["2025-12-25"]["name"]

    def test_quaid_day_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXKAREidAlFitr:
    def test_eid_al_fitr_2025(self, explicit_dates):
        """Eid al-Fitr 2025 — predicted March 31."""
        assert "2025-03-31" in explicit_dates
        assert "Eid al-Fitr" in explicit_dates["2025-03-31"]["name"]

    def test_eid_al_fitr_2026(self, explicit_dates):
        """Eid al-Fitr 2026 — predicted March 20."""
        assert "2026-03-20" in explicit_dates

    def test_eid_al_fitr_2027(self, explicit_dates):
        """Eid al-Fitr 2027 — predicted March 9."""
        assert "2027-03-09" in explicit_dates

    def test_eid_al_fitr_2028(self, explicit_dates):
        """Eid al-Fitr 2028 — Feb 26 (Saturday, weekend) — not in explicit."""
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

class TestXKAREidAlAdha:
    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — June 7 (Saturday, weekend) — not in explicit."""
        assert "2025-06-07" not in explicit_dates

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
# Islamic holidays (Ashura and Eid Milad-un-Nabi)
# ──────────────────────────────────────────────────────────────

class TestXKARIslamicHolidays:
    def test_ashura_2025(self, explicit_dates):
        """Ashura 2025 — July 6 (Sunday, weekend) — not in explicit."""
        assert "2025-07-06" not in explicit_dates

    def test_ashura_2026(self, explicit_dates):
        """Ashura 2026 — predicted June 26."""
        assert "2026-06-26" in explicit_dates

    def test_ashura_2027(self, explicit_dates):
        """Ashura 2027 — predicted June 15."""
        assert "2027-06-15" in explicit_dates

    def test_ashura_2028(self, explicit_dates):
        """Ashura 2028 — June 4 (Sunday, weekend) — not in explicit."""
        assert "2028-06-04" not in explicit_dates

    def test_ashura_2029(self, explicit_dates):
        """Ashura 2029 — predicted May 24."""
        assert "2029-05-24" in explicit_dates

    def test_eid_milad_2025(self, explicit_dates):
        """Eid Milad-un-Nabi 2025 — predicted September 5."""
        assert "2025-09-05" in explicit_dates
        assert "Milad" in explicit_dates["2025-09-05"]["name"]

    def test_eid_milad_2026(self, explicit_dates):
        """Eid Milad-un-Nabi 2026 — predicted August 25."""
        assert "2026-08-25" in explicit_dates

    def test_eid_milad_2027(self, explicit_dates):
        """Eid Milad-un-Nabi 2027 — Aug 15 (Sunday, weekend) — not in explicit."""
        assert "2027-08-15" not in explicit_dates

    def test_eid_milad_2028(self, explicit_dates):
        """Eid Milad-un-Nabi 2028 — predicted August 4."""
        assert "2028-08-04" in explicit_dates

    def test_eid_milad_2029(self, explicit_dates):
        """Eid Milad-un-Nabi 2029 — predicted July 24."""
        assert "2029-07-24" in explicit_dates

    def test_islamic_holidays_contain_predicted(self, explicit_dates):
        islamic_names = ["Ashura", "Milad"]
        for entry in explicit_dates.values():
            if any(name in entry["name"] for name in islamic_names):
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXKARStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Pakistan weekend is Saturday-Sunday."""
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
        """Pakistan has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xkar, explicit_dates):
        start = date.fromisoformat(xkar["generation_range"][0])
        end = date.fromisoformat(xkar["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~55-70 entries."""
        assert 50 <= len(explicit_dates) <= 75, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "psx.com.pk" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXKARWeekendPattern:
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

class TestXKARSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2027-05-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 2, f"Expected some observed holidays, got {observed_count}"