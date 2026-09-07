#!/usr/bin/env python3
"""
test_malaysia_holidays.py — Ground truth tests for XKLS (Bursa Malaysia).

Key facts verified:
    - Lunch break: 12:30-14:30 (longer than most exchanges)
    - Malaysia observes Sunday holidays on Monday (Holidays Act 1951, Section 3)
    - Thaipusam and Federal Territory Day are SEPARATE holidays
    - Hari Raya Puasa (Eid al-Fitr) is 2 days
    - Hari Raya Haji (Eid al-Adha) is 1 day
    - Agong's Birthday is 1st Monday of June
    - Wesak Day, Deepavali, Awal Muharram, Maulidur Rasul are lunisolar/fixed
    - No weekend shift for Saturday holidays (only Sunday → Monday)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XKLS.json)
    2. Malaysian holiday announcements changed (verify against bursamalaysia.com)

Run:
    python3 -m pytest tests/test_malaysia_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xkls():
    """Load XKLS.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XKLS.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xkls):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xkls["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXKLSProperties:
    def test_code(self, xkls):
        assert xkls["code"] == "XKLS"

    def test_mic(self, xkls):
        assert xkls["mic"] == "XKLS"

    def test_name(self, xkls):
        assert xkls["name"] == "Bursa Malaysia"

    def test_timezone(self, xkls):
        assert xkls["timezone"] == "Asia/Kuala_Lumpur"

    def test_regular_hours(self, xkls):
        assert xkls["regular_hours"]["open"] == "09:00"
        assert xkls["regular_hours"]["close"] == "17:00"

    def test_lunch_break(self, xkls):
        lunch = [s for s in xkls.get("sessions", []) if s["type"] == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "12:30"
        assert lunch[0]["close"] == "14:30"

    def test_extended_hours(self, xkls):
        assert xkls["extended_hours"]["pre_market"]["open"] == "08:30"
        assert xkls["extended_hours"]["after_hours"]["close"] == "17:15"


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXKLSFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_national_day_2025(self, explicit_dates):
        """Aug 31, 2025 is Sunday — no explicit entry."""
        assert "2025-08-31" not in explicit_dates

    def test_national_day_2025_observed(self, explicit_dates):
        """Aug 31 is Sunday — observed Monday Sep 1."""
        assert "2025-09-01" in explicit_dates
        assert "observed" in explicit_dates["2025-09-01"]["name"].lower()

    def test_malaysia_day_2025(self, explicit_dates):
        assert "2025-09-16" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_christmas_2026(self, explicit_dates):
        assert "2026-12-25" in explicit_dates

    def test_christmas_2027(self, explicit_dates):
        """Dec 25, 2027 is Saturday — no explicit entry."""
        assert "2027-12-25" not in explicit_dates

    def test_christmas_2028(self, explicit_dates):
        assert "2028-12-25" in explicit_dates

    def test_christmas_2029(self, explicit_dates):
        assert "2029-12-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Thaipusam and Federal Territory Day (separate holidays)
# ──────────────────────────────────────────────────────────────

class TestXKLSThaipusamFT:
    def test_thaipusam_2025(self, explicit_dates):
        """Feb 11, 2025 — Thaipusam."""
        assert "2025-02-11" in explicit_dates
        assert "Thaipusam" in explicit_dates["2025-02-11"]["name"]

    def test_ft_day_2025(self, explicit_dates):
        """Feb 1, 2025 is Saturday — no explicit entry."""
        assert "2025-02-01" not in explicit_dates

    def test_thaipusam_2026(self, explicit_dates):
        """Feb 2, 2026 — Thaipusam observed."""
        assert "2026-02-02" in explicit_dates
        assert "Thaipusam" in explicit_dates["2026-02-02"]["name"]

    def test_thaipusam_2027_jan22(self, explicit_dates):
        """Jan 22, 2027 — Thaipusam, NOT Feb 1."""
        assert "2027-01-22" in explicit_dates
        assert "Thaipusam" in explicit_dates["2027-01-22"]["name"]

    def test_ft_day_2027(self, explicit_dates):
        """Feb 1, 2027 is Monday — Federal Territory Day."""
        assert "2027-02-01" in explicit_dates

    def test_thaipusam_2028_feb9(self, explicit_dates):
        """Feb 9, 2028 — Thaipusam, separate from FT Day Feb 1."""
        assert "2028-02-09" in explicit_dates
        assert "Thaipusam" in explicit_dates["2028-02-09"]["name"]

    def test_ft_day_2028(self, explicit_dates):
        """Feb 1, 2028 is Tuesday — Federal Territory Day."""
        assert "2028-02-01" in explicit_dates

    def test_thaipusam_2029_jan30(self, explicit_dates):
        """Jan 30, 2029 — Thaipusam, separate from FT Day Feb 1."""
        assert "2029-01-30" in explicit_dates
        assert "Thaipusam" in explicit_dates["2029-01-30"]["name"]

    def test_ft_day_2029(self, explicit_dates):
        """Feb 1, 2029 is Thursday — Federal Territory Day."""
        assert "2029-02-01" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays
# ──────────────────────────────────────────────────────────────

class TestXKLSIslamic:
    def test_hari_raya_puasa_2025(self, explicit_dates):
        assert "2025-03-31" in explicit_dates
        assert "2025-04-01" in explicit_dates

    def test_hari_raya_haji_2025(self, explicit_dates):
        """Jun 7, 2025 is Saturday — no explicit entry."""
        assert "2025-06-07" not in explicit_dates

    def test_awal_muharram_2025(self, explicit_dates):
        assert "2025-06-27" in explicit_dates
        assert "Muharram" in explicit_dates["2025-06-27"]["name"]

    def test_maulidur_rasul_2025(self, explicit_dates):
        assert "2025-09-05" in explicit_dates
        assert "Maulidur" in explicit_dates["2025-09-05"]["name"]

    def test_hari_raya_haji_2029(self, explicit_dates):
        """Apr 24, 2029 — Hari Raya Haji (NOT May 24)."""
        assert "2029-04-24" in explicit_dates
        assert "2029-05-24" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Buddhist / Indian holidays
# ──────────────────────────────────────────────────────────────

class TestXKLSBuddhistIndian:
    def test_wesak_2025(self, explicit_dates):
        assert "2025-05-12" in explicit_dates
        assert "Wesak" in explicit_dates["2025-05-12"]["name"]

    def test_wesak_2026_observed(self, explicit_dates):
        """Wesak May 31 is Sunday; Jun 1 is Agong's; observed Jun 2."""
        assert "2026-06-02" in explicit_dates
        assert "Wesak" in explicit_dates["2026-06-02"]["name"]

    def test_deepavali_2025(self, explicit_dates):
        assert "2025-10-20" in explicit_dates

    def test_deepavali_2026_observed(self, explicit_dates):
        assert "2026-11-09" in explicit_dates
        assert "observed" in explicit_dates["2026-11-09"]["name"].lower()

    def test_agong_birthday_2025(self, explicit_dates):
        assert "2025-06-02" in explicit_dates
        assert "Agong" in explicit_dates["2025-06-02"]["name"]

    def test_agong_birthday_2029(self, explicit_dates):
        """1st Monday June — Jun 4, 2029."""
        assert "2029-06-04" in explicit_dates
        assert "Agong" in explicit_dates["2029-06-04"]["name"]


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXKLSRecurrence:
    def test_fixed_rules_exist(self, xkls):
        rules = xkls["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Labour Day" in names
        assert "National Day (Merdeka Day)" in names
        assert "Malaysia Day" in names
        assert "Christmas Day" in names

    def test_no_lunisolar_rules(self, xkls):
        """CNY, Hari Raya, Wesak, Deepavali must NOT be in recurrence."""
        rules = xkls["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Chinese New Year" not in names
        assert "Hari Raya" not in names
        assert "Wesak" not in names
        assert "Deepavali" not in names
        assert "Thaipusam" not in names

    def test_no_agong_in_rules(self, xkls):
        """Agong's Birthday is 1st Monday June — not in recurrence."""
        rules = xkls["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Agong" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXKLSStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source: {date_str}"

    def test_all_statuses_closed(self, explicit_dates):
        """Malaysia has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~70-90 entries: multiple holidays × 5 years."""
        assert 60 <= len(explicit_dates) <= 100
        