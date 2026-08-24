#!/usr/bin/env python3
"""
test_nigeria_holidays.py — Ground truth tests for XNSA (Nigerian Stock Exchange).

Key facts verified:
    - Regular hours: 10:00-14:30 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Democracy Day (Jun 12)
    - Independence Day (Oct 1)
    - Eid al-Adha and Eid al-Maulud (Islamic, movable)
    - Christmas Day and Boxing Day
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XNSA.json)
    2. Nigerian holiday announcements changed (verify against ngxgroup.com)

Run:
    python3 -m pytest tests/test_nigeria_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xnsa():
    """Load XNSA.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XNSA.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xnsa):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xnsa["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXNSAProperties:
    def test_code(self, xnsa):
        assert xnsa["code"] == "XNSA"

    def test_mic(self, xnsa):
        assert xnsa["mic"] == "XNSA"

    def test_name(self, xnsa):
        assert xnsa["name"] == "Nigerian Stock Exchange"

    def test_timezone(self, xnsa):
        assert xnsa["timezone"] == "Africa/Lagos"

    def test_regular_hours(self, xnsa):
        assert xnsa["regular_hours"]["open"] == "10:00"
        assert xnsa["regular_hours"]["close"] == "14:30"

    def test_no_lunch_break(self, xnsa):
        lunch = [s for s in xnsa.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xnsa):
        assert "extended_hours" not in xnsa or xnsa.get("extended_hours") is None

    def test_generation_range(self, xnsa):
        assert "generation_range" in xnsa
        assert xnsa["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xnsa):
        assert xnsa.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xnsa):
        """Nigeria uses explicit dates only."""
        rules = xnsa["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXNSAFixedHolidays:
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

    def test_democracy_day_2025(self, explicit_dates):
        """Jun 12, 2025 is Thursday."""
        assert "2025-06-12" in explicit_dates
        assert "Democracy" in explicit_dates["2025-06-12"]["name"]

    def test_democracy_day_2027_substitute(self, explicit_dates):
        """Jun 12, 2027 is Saturday — substitute to Monday Jun 14."""
        assert "2027-06-12" not in explicit_dates
        assert "2027-06-14" in explicit_dates

    def test_independence_2025(self, explicit_dates):
        """Oct 1, 2025 is Wednesday."""
        assert "2025-10-01" in explicit_dates
        assert "Independence" in explicit_dates["2025-10-01"]["name"]

    def test_independence_2028_substitute(self, explicit_dates):
        """Oct 1, 2028 is Sunday — substitute to Monday Oct 2."""
        assert "2028-10-01" not in explicit_dates
        assert "2028-10-02" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXNSAChristmas:
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

class TestXNSAEaster:
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

class TestXNSAIslamicHolidays:
    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — predicted June 30."""
        assert "2025-06-30" in explicit_dates
        assert "Eid al-Adha" in explicit_dates["2025-06-30"]["name"]

    def test_eid_al_adha_2026(self, explicit_dates):
        """Eid al-Adha 2026 — predicted May 27."""
        assert "2026-05-27" in explicit_dates

    def test_eid_al_maulud_2025(self, explicit_dates):
        """Eid al-Maulud 2025 — predicted September 5."""
        assert "2025-09-05" in explicit_dates
        assert "Maulud" in explicit_dates["2025-09-05"]["name"]

    def test_eid_al_maulud_2029(self, explicit_dates):
        """Eid al-Maulud 2029 — predicted July 24."""
        assert "2029-07-24" in explicit_dates

    def test_islamic_holidays_contain_predicted(self, explicit_dates):
        islamic_names = ["Eid al-Adha", "Eid al-Maulud"]
        for entry in explicit_dates.values():
            if any(name in entry["name"] for name in islamic_names):
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXNSAStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Nigeria weekend is Saturday-Sunday."""
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
        """Nigeria has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xnsa, explicit_dates):
        start = date.fromisoformat(xnsa["generation_range"][0])
        end = date.fromisoformat(xnsa["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries."""
        assert 45 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "ngxgroup.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXNSAWeekendPattern:
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

class TestXNSASubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-05-01" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 4, f"Expected some observed holidays, got {observed_count}"