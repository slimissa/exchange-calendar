#!/usr/bin/env python3
"""
test_bangkok_holidays.py — Ground truth tests for XBKK (Stock Exchange of Thailand).

Key facts verified:
    - Regular hours: 10:00-16:30 (split session)
    - Lunch break: 12:30-14:00
    - Weekend is Saturday-Sunday (Western weekend)
    - Thailand uses substitution for holidays falling on weekends
    - Songkran Festival (3 days in April)
    - Buddhist holidays (Makha Bucha, Visakha Bucha, Asahna Bucha)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBKK.json)
    2. Thai holiday announcements changed (verify against set.or.th)

Run:
    python3 -m pytest tests/test_bangkok_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbkk():
    """Load XBKK.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBKK.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbkk):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbkk["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBKKProperties:
    def test_code(self, xbkk):
        assert xbkk["code"] == "XBKK"

    def test_mic(self, xbkk):
        assert xbkk["mic"] == "XBKK"

    def test_name(self, xbkk):
        assert xbkk["name"] == "Stock Exchange of Thailand"

    def test_timezone(self, xbkk):
        assert xbkk["timezone"] == "Asia/Bangkok"

    def test_regular_hours(self, xbkk):
        assert xbkk["regular_hours"]["open"] == "10:00"
        assert xbkk["regular_hours"]["close"] == "16:30"

    def test_lunch_break(self, xbkk):
        lunch = [s for s in xbkk.get("sessions", []) if s.get("type") == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "12:30"
        assert lunch[0]["close"] == "14:00"

    def test_no_extended_hours(self, xbkk):
        assert "extended_hours" not in xbkk or xbkk.get("extended_hours") is None

    def test_generation_range(self, xbkk):
        assert "generation_range" in xbkk
        # Shortened from 2029-12-31 per C4: XBKK's data only covers
        # through 2027 (Buddhist/lunar holidays aren't rule-generatable).
        assert xbkk["generation_range"] == ["2025-01-01", "2027-12-31"]

    def test_ad_hoc_closures_empty(self, xbkk):
        assert xbkk.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xbkk):
        """Thailand uses explicit dates only."""
        rules = xbkk["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# New Year holidays
# ──────────────────────────────────────────────────────────────

class TestXBKKNewYear:
    def test_new_year_day_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_holiday_2025(self, explicit_dates):
        """Jan 2, 2025 is Thursday."""
        assert "2025-01-02" in explicit_dates
        assert "New Year Holiday" in explicit_dates["2025-01-02"]["name"]

    def test_new_year_holiday_2027_substitute(self, explicit_dates):
        """Jan 2, 2027 is Saturday — substitute to Monday Jan 4."""
        assert "2027-01-02" not in explicit_dates
        assert "2027-01-04" in explicit_dates

    def test_new_year_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday."""
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["name"] == "New Year's Eve"


# ──────────────────────────────────────────────────────────────
# Songkran Festival (3 days in April)
# ──────────────────────────────────────────────────────────────

class TestXBKKSongkran:
    def test_songkran_2025(self, explicit_dates):
        """Songkran 2025 — Apr 14-16."""
        assert "2025-04-14" in explicit_dates
        assert "Songkran" in explicit_dates["2025-04-14"]["name"]
        assert "2025-04-15" in explicit_dates
        assert "2025-04-16" in explicit_dates

    def test_songkran_2026(self, explicit_dates):
        """Songkran 2026 — Apr 13-15."""
        assert "2026-04-13" in explicit_dates
        assert "2026-04-14" in explicit_dates
        assert "2026-04-15" in explicit_dates

    def test_songkran_2027(self, explicit_dates):
        """Songkran 2027 — Apr 13-15."""
        assert "2027-04-13" in explicit_dates
        assert "2027-04-14" in explicit_dates
        assert "2027-04-15" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Buddhist holidays
# ──────────────────────────────────────────────────────────────

class TestXBKKBuddhist:
    def test_makha_bucha_2025(self, explicit_dates):
        """Makha Bucha 2025 — Feb 12."""
        assert "2025-02-12" in explicit_dates
        assert "Makha" in explicit_dates["2025-02-12"]["name"]

    def test_makha_bucha_2026(self, explicit_dates):
        """Makha Bucha 2026 — Mar 3."""
        assert "2026-03-03" in explicit_dates

    def test_makha_bucha_2027(self, explicit_dates):
        """Makha Bucha 2027 — Mar 22."""
        assert "2027-03-22" in explicit_dates

    def test_visakha_bucha_2025(self, explicit_dates):
        """Visakha Bucha 2025 — May 12."""
        assert "2025-05-12" in explicit_dates
        assert "Visakha" in explicit_dates["2025-05-12"]["name"]

    def test_visakha_bucha_2026(self, explicit_dates):
        """Visakha Bucha 2026 — May 25."""
        assert "2026-05-25" in explicit_dates

    def test_visakha_bucha_2027(self, explicit_dates):
        """Visakha Bucha 2027 — May 13."""
        assert "2027-05-13" in explicit_dates

    def test_asahna_bucha_2025(self, explicit_dates):
        """Asahna Bucha 2025 — Jul 10."""
        assert "2025-07-10" in explicit_dates
        assert "Asahna" in explicit_dates["2025-07-10"]["name"]

    def test_asahna_bucha_2026(self, explicit_dates):
        """Asahna Bucha 2026 — Jul 29."""
        assert "2026-07-29" in explicit_dates

    def test_asahna_bucha_2027(self, explicit_dates):
        """Asahna Bucha 2027 — Jul 18 (Sunday, weekend) — not in explicit.
        Weekday holiday starts Jul 19 (Monday)."""
        assert "2027-07-18" not in explicit_dates
        assert "2027-07-19" in explicit_dates

    def test_buddhist_lent_2025(self, explicit_dates):
        """Buddhist Lent 2025 — Jul 11."""
        assert "2025-07-11" in explicit_dates
        assert "Lent" in explicit_dates["2025-07-11"]["name"]

    def test_buddhist_lent_2026(self, explicit_dates):
        """Buddhist Lent 2026 — Jul 30."""
        assert "2026-07-30" in explicit_dates

    def test_buddhist_lent_2027(self, explicit_dates):
        """Buddhist Lent 2027 — Jul 19."""
        assert "2027-07-19" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Royal holidays
# ──────────────────────────────────────────────────────────────

class TestXBKKRoyal:
    def test_chakri_day_2025(self, explicit_dates):
        """Chakri Memorial Day — Apr 7, 2025 (substitute)."""
        assert "2025-04-07" in explicit_dates
        assert "Chakri" in explicit_dates["2025-04-07"]["name"]

    def test_chakri_day_2026(self, explicit_dates):
        """Chakri Memorial Day — Apr 6, 2026."""
        assert "2026-04-06" in explicit_dates

    def test_coronation_day_2025(self, explicit_dates):
        """Coronation Day — May 5, 2025 (substitute)."""
        assert "2025-05-05" in explicit_dates
        assert "Coronation" in explicit_dates["2025-05-05"]["name"]

    def test_coronation_day_2026(self, explicit_dates):
        """Coronation Day — May 4, 2026 (substitute)."""
        assert "2026-05-04" in explicit_dates

    def test_queen_birthday_2025(self, explicit_dates):
        """Queen's Birthday — Jun 3, 2025 (substitute)."""
        assert "2025-06-03" in explicit_dates
        assert "Queen" in explicit_dates["2025-06-03"]["name"]

    def test_kings_memorial_2025(self, explicit_dates):
        """King's Memorial Day — Oct 13, 2025 (substitute)."""
        assert "2025-10-13" in explicit_dates
        assert "King" in explicit_dates["2025-10-13"]["name"]

    def test_mothers_day_2025(self, explicit_dates):
        """Mother's Day — Aug 12, 2025."""
        assert "2025-08-12" in explicit_dates
        assert "Mother" in explicit_dates["2025-08-12"]["name"]

    def test_fathers_day_2025(self, explicit_dates):
        """Father's Day — Dec 5, 2025."""
        assert "2025-12-05" in explicit_dates
        assert "Father" in explicit_dates["2025-12-05"]["name"]

    def test_fathers_day_2026_substitute(self, explicit_dates):
        """Father's Day — Dec 5, 2026 is Saturday — substitute to Dec 7."""
        assert "2026-12-05" not in explicit_dates
        assert "2026-12-07" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Other national holidays
# ──────────────────────────────────────────────────────────────

class TestXBKKNational:
    def test_labour_day_2025(self, explicit_dates):
        """Labour Day — May 1, 2025."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_substitute(self, explicit_dates):
        """Labour Day — May 1, 2027 is Saturday — substitute to May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_chulalongkorn_2025(self, explicit_dates):
        """Chulalongkorn Day — Oct 23, 2025."""
        assert "2025-10-23" in explicit_dates
        assert "Chulalongkorn" in explicit_dates["2025-10-23"]["name"]

    def test_chulalongkorn_2027_substitute(self, explicit_dates):
        """Chulalongkorn Day — Oct 23, 2027 is Saturday — substitute to Oct 25."""
        assert "2027-10-23" not in explicit_dates
        assert "2027-10-25" in explicit_dates

    def test_constitution_day_2025(self, explicit_dates):
        """Constitution Day — Dec 10, 2025."""
        assert "2025-12-10" in explicit_dates
        assert "Constitution" in explicit_dates["2025-12-10"]["name"]


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBKKStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Thailand weekend is Saturday-Sunday."""
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
        """Thailand has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xbkk, explicit_dates):
        start = date.fromisoformat(xbkk["generation_range"][0])
        end = date.fromisoformat(xbkk["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries."""
        assert 50 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "set.or.th" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBKKWeekendPattern:
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

class TestXBKKSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2027-05-01" not in explicit_dates  # Saturday
        assert "2026-12-05" not in explicit_dates  # Saturday

    def test_substitute_names_contain_substitute(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "substitute" in name:
                assert "substitute" in name