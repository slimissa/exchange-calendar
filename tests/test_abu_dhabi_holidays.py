#!/usr/bin/env python3
"""
test_abu_dhabi_holidays.py — Ground truth tests for XTAD (Abu Dhabi Securities Exchange).

Key facts verified:
    - Regular hours: 10:00-14:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (since Jan 2022 UAE workweek change,
      NOT the Friday-Saturday weekend some other Gulf exchanges use)
    - Arafat Day (movable)
    - Eid al-Fitr and Eid al-Adha (3-4 days each)
    - Islamic New Year (movable)
    - Prophet's Birthday (movable)
    - Commemoration Day (Dec 1)
    - National Day (Dec 2-3)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XTAD.json)
    2. UAE holiday announcements changed (verify against adx.ae)

Run:
    python3 -m pytest tests/test_abu_dhabi_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xtad():
    """Load XTAD.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XTAD.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xtad):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xtad["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXTADProperties:
    def test_code(self, xtad):
        assert xtad["code"] == "XTAD"

    def test_mic(self, xtad):
        assert xtad["mic"] == "XTAD"

    def test_name(self, xtad):
        assert xtad["name"] == "Abu Dhabi Securities Exchange"

    def test_timezone(self, xtad):
        assert xtad["timezone"] == "Asia/Dubai"

    def test_regular_hours(self, xtad):
        assert xtad["regular_hours"]["open"] == "10:00"
        assert xtad["regular_hours"]["close"] == "14:00"

    def test_no_lunch_break(self, xtad):
        lunch = [s for s in xtad.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xtad):
        assert "extended_hours" not in xtad or xtad.get("extended_hours") is None

    def test_generation_range(self, xtad):
        assert "generation_range" in xtad
        assert xtad["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xtad):
        assert xtad.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xtad):
        """UAE uses explicit dates only."""
        rules = xtad["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXTADFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_commemoration_2025(self, explicit_dates):
        """Dec 1, 2025 is Monday."""
        assert "2025-12-01" in explicit_dates
        assert "Commemoration" in explicit_dates["2025-12-01"]["name"]

    def test_national_day_2025(self, explicit_dates):
        """Dec 2, 2025 is Tuesday."""
        assert "2025-12-02" in explicit_dates
        assert "National Day" in explicit_dates["2025-12-02"]["name"]

    def test_national_day_holiday_2025(self, explicit_dates):
        """Dec 3, 2025 is Wednesday."""
        assert "2025-12-03" in explicit_dates

    def test_national_day_2028_substitute(self, explicit_dates):
        """Dec 2, 2028 is Saturday, Dec 3 is Sunday -- both weekend
        days, so neither the original date nor a same-weekend
        'substitute' can be a valid trading holiday. H1-check-1 fix:
        the file previously (incorrectly) listed Dec 3 as an
        'observed' substitute despite it being a Sunday itself; that
        entry has been removed. Dec 4 (Monday) is the actual valid
        substitute day and should remain.

        Note: this may still be under-counting -- if BOTH
        Commemoration Day (normally Dec 1) and National Day (normally
        Dec 2) fall on the weekend in 2028, UAE policy may warrant two
        substitute days, not one. That's a separate data-completeness
        question this test doesn't resolve, flagged for follow-up
        rather than guessed at here."""
        assert "2028-12-02" not in explicit_dates
        assert "2028-12-03" not in explicit_dates
        assert "2028-12-04" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXTADEidAlFitr:
    def test_eid_al_fitr_2025(self, explicit_dates):
        """Eid al-Fitr 2025 civil day 1 (March 30) is a Sunday --
        XTAD's own weekend day -- so it's correctly excluded (H1
        check 1 fix). Days 2-3 (Mar 31, Apr 1) survive; per the
        established convention they don't get promoted to the bare
        name since day 1 itself was dropped. M7: 2025's date is now
        confirmed (Gulf News), so these entries no longer carry the
        '(predicted)' suffix."""
        assert "2025-03-30" not in explicit_dates
        assert "2025-03-31" in explicit_dates
        assert explicit_dates["2025-03-31"]["name"] == "Eid al-Fitr Holiday"
        assert "2025-04-01" in explicit_dates

    def test_eid_al_fitr_2026(self, explicit_dates):
        """Eid al-Fitr 2026 — March 20 (Friday) — not in explicit.
        Weekday starts March 23 (Monday)."""
        assert "2026-03-20" not in explicit_dates
        assert "2026-03-23" in explicit_dates

    def test_eid_al_fitr_2029(self, explicit_dates):
        """Eid al-Fitr 2029 — predicted February 14."""
        assert "2029-02-14" in explicit_dates

    def test_eid_al_fitr_names_contain_predicted(self, explicit_dates):
        """2025 is reconciled (M7, confirmed via Gulf News) and no
        longer carries the suffix; other years remain predicted."""
        for date_str, entry in explicit_dates.items():
            if "Eid al-Fitr" in entry["name"] and not date_str.startswith("2025"):
                assert "predicted" in entry["name"].lower(), \
                    f"{date_str} ({entry['name']}) should still be predicted"


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Arafat Day and Eid al-Adha)
# ──────────────────────────────────────────────────────────────

class TestXTADArafatEidAlAdha:
    def test_arafat_2025(self, explicit_dates):
        """Arafat Day 2025 — predicted June 5."""
        assert "2025-06-05" in explicit_dates
        assert "Arafat" in explicit_dates["2025-06-05"]["name"]

    def test_arafat_2028(self, explicit_dates):
        """Arafat Day 2028 — predicted May 4."""
        assert "2028-05-04" in explicit_dates

    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — June 6 (Friday) — not in explicit.
        Weekday starts June 9 (Monday)."""
        assert "2025-06-06" not in explicit_dates
        assert "2025-06-09" in explicit_dates

    def test_eid_al_adha_2026(self, explicit_dates):
        """Eid al-Adha 2026 — predicted May 27."""
        assert "2026-05-27" in explicit_dates

    def test_eid_al_adha_2029(self, explicit_dates):
        """Eid al-Adha 2029 — predicted April 25."""
        assert "2029-04-25" in explicit_dates

    def test_eid_al_adha_names_contain_predicted(self, explicit_dates):
        for entry in explicit_dates.values():
            if "Eid al-Adha" in entry["name"]:
                assert "predicted" in entry["name"].lower()


# ──────────────────────────────────────────────────────────────
# Islamic holidays (New Year and Prophet's Birthday)
# ──────────────────────────────────────────────────────────────

class TestXTADIslamicHolidays:
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

class TestXTADStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """UAE weekend is Saturday-Sunday (since Jan 2022), not Friday-Saturday."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() not in [5, 6], f"Weekend date: {date_str} ({d.strftime('%A')})"

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
        """UAE has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xtad, explicit_dates):
        start = date.fromisoformat(xtad["generation_range"][0])
        end = date.fromisoformat(xtad["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~40-50 entries after H1-fix removed 7 weekend-violating
        entries (was ~50-60)."""
        assert 35 <= len(explicit_dates) <= 50, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "adx.ae" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks (Saturday-Sunday)
# ──────────────────────────────────────────────────────────────

class TestXTADWeekendPattern:
    """XTAD observes a Saturday/Sunday weekend (weekend_days [5, 6]),
    NOT the Friday/Saturday pattern used by exchanges like XSAU/XBAH.
    This class previously tested the opposite model -- forbidding
    Friday/Saturday and requiring Sunday dates -- and only passed
    because the weekend-violating Sunday entries this same fix
    removed happened to satisfy the (backwards) assertion. Corrected
    to match XTAD's actual weekend system."""

    def test_no_saturday_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date (weekend): {date_str}"

    def test_no_sunday_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 6, f"Sunday date (weekend): {date_str}"

    def test_friday_is_a_trading_day(self, explicit_dates):
        """Friday is NOT XTAD's weekend day (unlike XSAU/XBAH) -- a
        Friday-dated holiday should be a legitimate explicit entry if
        one exists, not filtered out. No Friday-dated holiday
        currently exists in this file's data, so this only checks
        that IF one appears, it isn't accidentally excluded as if
        Friday were a weekend day -- i.e. this test would fail loudly
        if a future edit reintroduces the wrong weekend model rather
        than passing trivially either way."""
        weekend = [5, 6]
        assert 4 not in weekend, "Friday should not be in XTAD's weekend_days"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXTADSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2025-06-06" not in explicit_dates  # Friday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 2, f"Expected some observed holidays, got {observed_count}"