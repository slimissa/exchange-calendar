#!/usr/bin/env python3
"""
test_nairobi_holidays.py — Ground truth tests for XNBO (Nairobi Securities Exchange).

Key facts verified:
    - Regular hours: 09:30-15:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Madaraka Day (Jun 1)
    - Mashujaa Day (Oct 20)
    - Jamhuri Day (Dec 12)
    - Eid al-Fitr and Eid al-Adha (Islamic, movable)
    - Christmas Day and Boxing Day
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XNBO.json)
    2. Kenyan holiday announcements changed (verify against nse.co.ke)

Run:
    python3 -m pytest tests/test_nairobi_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xnbo():
    """Load XNBO.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XNBO.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xnbo):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xnbo["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXNBOProperties:
    def test_code(self, xnbo):
        assert xnbo["code"] == "XNBO"

    def test_mic(self, xnbo):
        assert xnbo["mic"] == "XNBO"

    def test_name(self, xnbo):
        assert xnbo["name"] == "Nairobi Securities Exchange"

    def test_timezone(self, xnbo):
        assert xnbo["timezone"] == "Africa/Nairobi"

    def test_regular_hours(self, xnbo):
        assert xnbo["regular_hours"]["open"] == "09:30"
        assert xnbo["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xnbo):
        lunch = [s for s in xnbo.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xnbo):
        assert "extended_hours" not in xnbo or xnbo.get("extended_hours") is None

    def test_generation_range(self, xnbo):
        assert "generation_range" in xnbo
        assert xnbo["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xnbo):
        assert xnbo.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xnbo):
        """Kenya uses explicit dates only."""
        rules = xnbo["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXNBOFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_madaraka_2025(self, explicit_dates):
        """Jun 1, 2025 is Sunday — substitute to Monday Jun 2."""
        assert "2025-06-01" not in explicit_dates
        assert "2025-06-02" in explicit_dates

    def test_madaraka_2026(self, explicit_dates):
        """Jun 1, 2026 is Monday."""
        assert "2026-06-01" in explicit_dates
        assert "Madaraka" in explicit_dates["2026-06-01"]["name"]

    def test_mashujaa_2025(self, explicit_dates):
        """Oct 20, 2025 is Monday."""
        assert "2025-10-20" in explicit_dates
        assert "Mashujaa" in explicit_dates["2025-10-20"]["name"]

    def test_jamhuri_2025(self, explicit_dates):
        """Dec 12, 2025 is Friday."""
        assert "2025-12-12" in explicit_dates
        assert "Jamhuri" in explicit_dates["2025-12-12"]["name"]


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXNBOChristmas:
    def test_christmas_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_christmas_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates

    def test_boxing_day_2026_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute to Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXNBOEaster:
    def test_good_friday_2025(self, explicit_dates):
        """Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["name"] == "Good Friday"

    def test_good_friday_2026(self, explicit_dates):
        """Easter - 2 days — April 3, 2026."""
        assert "2026-04-03" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        """Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["name"] == "Easter Monday"

    def test_easter_monday_2027(self, explicit_dates):
        """Easter + 1 day — March 29, 2027."""
        assert "2027-03-29" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays (movable)
# ──────────────────────────────────────────────────────────────

class TestXNBOIslamicHolidays:
    def test_eid_al_fitr_2025(self, explicit_dates):
        """Eid al-Fitr 2025 — predicted March 31."""
        assert "2025-03-31" in explicit_dates
        assert "Eid al-Fitr" in explicit_dates["2025-03-31"]["name"]

    def test_eid_al_fitr_2028(self, explicit_dates):
        """Eid al-Fitr 2028 — Feb 26 (Saturday, weekend) — not in explicit."""
        assert "2028-02-26" not in explicit_dates

    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — June 7 (Saturday, weekend) — not in explicit."""
        assert "2025-06-07" not in explicit_dates

    def test_eid_al_adha_2029(self, explicit_dates):
        """Eid al-Adha 2029 — predicted April 24."""
        assert "2029-04-24" in explicit_dates

    def test_islamic_holidays_contain_predicted(self, explicit_dates):
        islamic_names = ["Eid al-Fitr", "Eid al-Adha"]
        for entry in explicit_dates.values():
            if any(name in entry["name"] for name in islamic_names):
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXNBOStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Kenya weekend is Saturday-Sunday."""
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
        """Kenya has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xnbo, explicit_dates):
        start = date.fromisoformat(xnbo["generation_range"][0])
        end = date.fromisoformat(xnbo["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries."""
        assert 45 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "nse.co.ke" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXNBOWeekendPattern:
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

class TestXNBOSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 4, f"Expected some observed holidays, got {observed_count}"