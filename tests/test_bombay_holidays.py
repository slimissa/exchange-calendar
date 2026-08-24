#!/usr/bin/env python3
"""
test_bombay_holidays.py — Ground truth tests for XBOM (Bombay Stock Exchange).

Key facts verified:
    - BSE and NSE share the identical holiday calendar
    - India does NOT shift holidays from weekends (no substitute days)
    - Lunisolar holidays (Diwali, Holi, Ganesh Chaturthi, Dussehra, Muharram,
      Id-Ul-Fitr, Bakri Id) are explicit-only
    - Fixed holidays (Republic Day, Maharashtra Day, Independence Day,
      Gandhi Jayanti, Dr. Ambedkar Jayanti, Christmas) use fixed_date
    - Good Friday uses Easter offset
    - No lunch break (continuous trading)
    - Pre-market: 09:00-09:15, Post-market: 15:30-16:00

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBOM.json)
    2. Indian holiday announcements changed (verify against bseindia.com)

Run:
    python3 -m pytest tests/test_bombay_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbom():
    """Load XBOM.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBOM.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbom):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbom["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBOMProperties:
    def test_code(self, xbom):
        assert xbom["code"] == "XBOM"

    def test_mic(self, xbom):
        assert xbom["mic"] == "XBOM"

    def test_name(self, xbom):
        assert xbom["name"] == "Bombay Stock Exchange"

    def test_timezone(self, xbom):
        assert xbom["timezone"] == "Asia/Kolkata"

    def test_regular_hours(self, xbom):
        assert xbom["regular_hours"]["open"] == "09:15"
        assert xbom["regular_hours"]["close"] == "15:30"

    def test_no_lunch_break(self, xbom):
        lunch = [s for s in xbom.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xbom):
        assert xbom["extended_hours"]["pre_market"]["open"] == "09:00"
        assert xbom["extended_hours"]["after_hours"]["close"] == "16:00"


# ──────────────────────────────────────────────────────────────
# Fixed national holidays (2025)
# ──────────────────────────────────────────────────────────────

class TestXBOMFixed2025:
    def test_republic_day(self, explicit_dates):
        """January 26, 2025 is Sunday — no explicit entry for weekend."""
        assert "2025-01-26" not in explicit_dates

    def test_maharashtra_day(self, explicit_dates):
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["status"] == "closed"

    def test_independence_day(self, explicit_dates):
        assert "2025-08-15" in explicit_dates
        assert explicit_dates["2025-08-15"]["status"] == "closed"

    def test_gandhi_jayanti(self, explicit_dates):
        assert "2025-10-02" in explicit_dates
        assert explicit_dates["2025-10-02"]["status"] == "closed"

    def test_christmas(self, explicit_dates):
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["status"] == "closed"

    def test_ambedkar_jayanti(self, explicit_dates):
        assert "2025-04-14" in explicit_dates
        assert "Ambedkar" in explicit_dates["2025-04-14"]["name"]

    def test_good_friday(self, explicit_dates):
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# Lunisolar holidays (2025)
# ──────────────────────────────────────────────────────────────

class TestXBOMLunisolar2025:
    def test_holi(self, explicit_dates):
        assert "2025-03-14" in explicit_dates
        assert "Holi" in explicit_dates["2025-03-14"]["name"]

    def test_mahashivratri(self, explicit_dates):
        assert "2025-02-26" in explicit_dates
        assert "Mahashivratri" in explicit_dates["2025-02-26"]["name"]

    def test_id_ul_fitr(self, explicit_dates):
        assert "2025-03-31" in explicit_dates
        assert "Id-Ul-Fitr" in explicit_dates["2025-03-31"]["name"]

    def test_ganesh_chaturthi(self, explicit_dates):
        assert "2025-08-27" in explicit_dates
        assert "Ganesh" in explicit_dates["2025-08-27"]["name"]

    def test_diwali_laxmi_pujan(self, explicit_dates):
        assert "2025-10-21" in explicit_dates
        assert "Diwali" in explicit_dates["2025-10-21"]["name"]

    def test_diwali_balipratipada(self, explicit_dates):
        assert "2025-10-22" in explicit_dates
        assert "Diwali" in explicit_dates["2025-10-22"]["name"]

    def test_guru_nanak_jayanti(self, explicit_dates):
        assert "2025-11-05" in explicit_dates
        assert "Guru Nanak" in explicit_dates["2025-11-05"]["name"]


# ──────────────────────────────────────────────────────────────
# 2026 holidays
# ──────────────────────────────────────────────────────────────

class TestXBOM2026:
    def test_republic_day(self, explicit_dates):
        assert "2026-01-26" in explicit_dates

    def test_holi(self, explicit_dates):
        assert "2026-03-04" in explicit_dates

    def test_id_ul_fitr(self, explicit_dates):
        assert "2026-03-20" in explicit_dates
        assert "Id-Ul-Fitr" in explicit_dates["2026-03-20"]["name"]

    def test_good_friday(self, explicit_dates):
        assert "2026-04-03" in explicit_dates

    def test_bakri_id(self, explicit_dates):
        assert "2026-05-27" in explicit_dates
        assert "Bakri" in explicit_dates["2026-05-27"]["name"]

    def test_muharram(self, explicit_dates):
        assert "2026-06-26" in explicit_dates
        assert "Muharram" in explicit_dates["2026-06-26"]["name"]

    def test_dussehra(self, explicit_dates):
        assert "2026-10-20" in explicit_dates
        assert "Dussehra" in explicit_dates["2026-10-20"]["name"]

    def test_diwali(self, explicit_dates):
        """H3 correction: Nov 8, 2026 (Sunday) is officially gazetted by
        NSE/BSE as the Laxmi Pujan trading holiday, with Muhurat trading
        held on it -- a distinct, sourced event, not just an ordinary
        closed Sunday. It IS explicit, flagged weekend_exception so the
        H1 weekend-date validator doesn't treat it as a data error.
        Nov 9 (Monday, Balipratipada) is unaffected and unrelated."""
        assert "2026-11-08" in explicit_dates
        assert explicit_dates["2026-11-08"]["name"] == "Diwali (Laxmi Pujan)"
        assert explicit_dates["2026-11-08"].get("weekend_exception") is True
        assert "2026-11-09" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2027 holidays
# ──────────────────────────────────────────────────────────────

class TestXBOM2027:
    def test_republic_day(self, explicit_dates):
        assert "2027-01-26" in explicit_dates

    def test_id_ul_fitr(self, explicit_dates):
        assert "2027-03-10" in explicit_dates

    def test_holi(self, explicit_dates):
        assert "2027-03-23" in explicit_dates

    def test_bakri_id(self, explicit_dates):
        assert "2027-05-17" in explicit_dates

    def test_muharram(self, explicit_dates):
        assert "2027-06-16" in explicit_dates

    def test_diwali(self, explicit_dates):
        """Oct 29 is Friday (explicit). Oct 30 is Saturday — no explicit."""
        assert "2027-10-29" in explicit_dates
        assert "2027-10-30" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2028 holidays
# ──────────────────────────────────────────────────────────────

class TestXBOM2028:
    def test_mahashivratri(self, explicit_dates):
        assert "2028-02-24" in explicit_dates

    def test_holi(self, explicit_dates):
        """March 11, 2028 is Saturday — no explicit entry."""
        assert "2028-03-11" not in explicit_dates

    def test_combined_good_friday_ambedkar(self, explicit_dates):
        """April 14, 2028 — both Good Friday and Ambedkar Jayanti."""
        assert "2028-04-14" in explicit_dates
        name = explicit_dates["2028-04-14"]["name"]
        assert "Good Friday" in name
        assert "Ambedkar" in name

    def test_bakri_id(self, explicit_dates):
        assert "2028-05-05" in explicit_dates

    def test_ganesh_chaturthi(self, explicit_dates):
        assert "2028-08-23" in explicit_dates

    def test_dussehra(self, explicit_dates):
        assert "2028-09-28" in explicit_dates

    def test_diwali(self, explicit_dates):
        assert "2028-10-17" in explicit_dates
        assert "2028-10-18" in explicit_dates


# ──────────────────────────────────────────────────────────────
# 2029 holidays
# ──────────────────────────────────────────────────────────────

class TestXBOM2029:
    def test_mahashivratri(self, explicit_dates):
        assert "2029-02-12" in explicit_dates

    def test_id_ul_fitr(self, explicit_dates):
        assert "2029-02-15" in explicit_dates

    def test_holi(self, explicit_dates):
        assert "2029-03-01" in explicit_dates

    def test_bakri_id(self, explicit_dates):
        assert "2029-04-24" in explicit_dates

    def test_muharram(self, explicit_dates):
        assert "2029-05-24" in explicit_dates

    def test_ganesh_chaturthi(self, explicit_dates):
        assert "2029-09-12" in explicit_dates

    def test_dussehra(self, explicit_dates):
        assert "2029-10-17" in explicit_dates

    def test_diwali(self, explicit_dates):
        assert "2029-11-05" in explicit_dates
        assert "2029-11-06" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXBOMRecurrence:
    def test_fixed_rules_exist(self, xbom):
        rules = xbom["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Republic Day" in names
        assert "Maharashtra Day" in names
        assert "Independence Day" in names
        assert "Gandhi Jayanti" in names
        assert "Dr. Ambedkar Jayanti" in names
        assert "Christmas" in names

    def test_good_friday_rule(self, xbom):
        rules = xbom["holidays"].get("recurrence_rules", [])
        good_friday = [r for r in rules if r["name"] == "Good Friday"]
        assert len(good_friday) == 1
        assert good_friday[0]["rule"] == "easter_offset"
        assert good_friday[0]["offset_days"] == -2

    def test_no_lunisolar_rules(self, xbom):
        """Diwali, Holi, Ganesh Chaturthi must NOT be in recurrence rules."""
        rules = xbom["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Diwali" not in names
        assert "Holi" not in names
        assert "Ganesh Chaturthi" not in names
        assert "Dussehra" not in names
        assert "Muharram" not in names
        assert "Id-Ul-Fitr" not in names
        assert "Bakri Id" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBOMStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """No explicit date should fall on the weekend, EXCEPT entries
        explicitly flagged weekend_exception (H3: NSE/BSE's Diwali
        Laxmi Pujan 2026 is a real, sourced, gazetted exception to
        this rule -- see schema.json's weekend_exception field)."""
        for date_str, entry in explicit_dates.items():
            if entry.get("weekend_exception"):
                continue
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source: {date_str}"

    def test_all_statuses_closed(self, explicit_dates):
        """India has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~63 entries: ~13 holidays × 5 years."""
        assert 55 <= len(explicit_dates) <= 75