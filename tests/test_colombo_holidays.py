#!/usr/bin/env python3
"""
test_colombo_holidays.py — Ground truth tests for XCOL (Colombo Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-14:30 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - 12 Full Moon Poya Days each year
    - Sinhala and Tamil New Year (Apr 14-15)
    - May Day (May 1)
    - Vesak Poya (2 days)
    - Deepavali (movable)
    - Christmas Day (Dec 25)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XCOL.json)
    2. Sri Lankan holiday announcements changed (verify against cse.lk)

Run:
    python3 -m pytest tests/test_colombo_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xcol():
    """Load XCOL.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XCOL.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xcol):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xcol["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXCOLProperties:
    def test_code(self, xcol):
        assert xcol["code"] == "XCOL"

    def test_mic(self, xcol):
        assert xcol["mic"] == "XCOL"

    def test_name(self, xcol):
        assert xcol["name"] == "Colombo Stock Exchange"

    def test_timezone(self, xcol):
        assert xcol["timezone"] == "Asia/Colombo"

    def test_regular_hours(self, xcol):
        assert xcol["regular_hours"]["open"] == "09:30"
        assert xcol["regular_hours"]["close"] == "14:30"

    def test_no_lunch_break(self, xcol):
        lunch = [s for s in xcol.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xcol):
        assert "extended_hours" not in xcol or xcol.get("extended_hours") is None

    def test_generation_range(self, xcol):
        assert "generation_range" in xcol
        # Shortened from 2029-12-31 per C4: XCOL's data only covers
        # through 2027 (Poya days/Deepavali aren't rule-generatable).
        assert xcol["generation_range"] == ["2025-01-01", "2027-12-31"]

    def test_ad_hoc_closures_empty(self, xcol):
        assert xcol.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xcol):
        """Sri Lanka uses explicit dates only."""
        rules = xcol["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXCOLFixedHolidays:
    def test_sinhala_new_year_2025(self, explicit_dates):
        """Apr 14, 2025 is Monday."""
        assert "2025-04-14" in explicit_dates
        assert "Sinhala" in explicit_dates["2025-04-14"]["name"]

    def test_sinhala_new_year_holiday_2025(self, explicit_dates):
        """Apr 15, 2025 is Tuesday."""
        assert "2025-04-15" in explicit_dates

    def test_may_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "May Day"

    def test_may_day_2027_substitute(self, explicit_dates):
        """May 1, 2027 is Saturday — substitute to Monday May 3."""
        assert "2027-05-01" not in explicit_dates
        assert "2027-05-03" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert "Christmas" in explicit_dates["2025-12-25"]["name"]

    def test_christmas_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Full Moon Poya Days (January-March)
# ──────────────────────────────────────────────────────────────

class TestXCOLPoyaJanMar:
    def test_duruthu_2025(self, explicit_dates):
        """Duruthu Poya — Jan 14, 2025."""
        assert "2025-01-14" in explicit_dates
        assert "Duruthu" in explicit_dates["2025-01-14"]["name"]

    def test_navam_2025(self, explicit_dates):
        """Navam Poya — Feb 12, 2025."""
        assert "2025-02-12" in explicit_dates
        assert "Navam" in explicit_dates["2025-02-12"]["name"]

    def test_medin_2025(self, explicit_dates):
        """Medin Poya — Mar 13, 2025."""
        assert "2025-03-13" in explicit_dates
        assert "Medin" in explicit_dates["2025-03-13"]["name"]

    def test_bak_2025(self, explicit_dates):
        """Bak Poya — Apr 11, 2025."""
        assert "2025-04-11" in explicit_dates
        assert "Bak" in explicit_dates["2025-04-11"]["name"]


# ──────────────────────────────────────────────────────────────
# Full Moon Poya Days (May-August)
# ──────────────────────────────────────────────────────────────

class TestXCOLPoyaMayAug:
    def test_vesak_2025(self, explicit_dates):
        """Vesak Poya — May 12, 2025 (2 days)."""
        assert "2025-05-12" in explicit_dates
        assert "Vesak" in explicit_dates["2025-05-12"]["name"]
        assert "2025-05-13" in explicit_dates

    def test_poson_2025(self, explicit_dates):
        """Poson Poya — Jun 10, 2025."""
        assert "2025-06-10" in explicit_dates
        assert "Poson" in explicit_dates["2025-06-10"]["name"]

    def test_esala_2025(self, explicit_dates):
        """Esala Poya — Jul 10, 2025."""
        assert "2025-07-10" in explicit_dates
        assert "Esala" in explicit_dates["2025-07-10"]["name"]

    def test_nikini_2025(self, explicit_dates):
        """Nikini Poya — Aug 8, 2025."""
        assert "2025-08-08" in explicit_dates
        assert "Nikini" in explicit_dates["2025-08-08"]["name"]


# ──────────────────────────────────────────────────────────────
# Full Moon Poya Days (September-December)
# ──────────────────────────────────────────────────────────────

class TestXCOLPoyaSepDec:
    def test_binara_2025(self, explicit_dates):
        """Binara Poya 2025 — Sep 7 (Sunday, weekend) — not in explicit."""
        assert "2025-09-07" not in explicit_dates

    def test_vap_2025(self, explicit_dates):
        """Vap Poya — Oct 6, 2025."""
        assert "2025-10-06" in explicit_dates
        assert "Vap" in explicit_dates["2025-10-06"]["name"]

    def test_il_2025(self, explicit_dates):
        """Il Poya — Nov 5, 2025."""
        assert "2025-11-05" in explicit_dates
        assert "Il" in explicit_dates["2025-11-05"]["name"]

    def test_unduvap_2025(self, explicit_dates):
        """Unduvap Poya — Dec 4, 2025."""
        assert "2025-12-04" in explicit_dates
        assert "Unduvap" in explicit_dates["2025-12-04"]["name"]


# ──────────────────────────────────────────────────────────────
# Deepavali (movable)
# ──────────────────────────────────────────────────────────────

class TestXCOLDeepavali:
    def test_deepavali_2025(self, explicit_dates):
        """Deepavali 2025 — Oct 20."""
        assert "2025-10-20" in explicit_dates
        assert "Deepavali" in explicit_dates["2025-10-20"]["name"]

    def test_deepavali_2026_not_a_cse_holiday(self, explicit_dates):
        """Deepavali 2026 is Sunday Nov 8, a weekend day for CSE. CSE Circular
        07-10-2025 lists no substitute day, so Monday Nov 9 is a trading day.
        An earlier version of this file pinned "2026-11-09 Deepavali (observed)"
        to match XKLS and XSES; it had no CSE source and the circular
        contradicts it."""
        assert "2026-11-08" not in explicit_dates
        assert "2026-11-09" not in explicit_dates

    def test_deepavali_2027(self, explicit_dates):
        """Deepavali 2027 — Oct 28."""
        assert "2027-10-28" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXCOLStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Sri Lanka weekend is Saturday-Sunday."""
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
        """Sri Lanka has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xcol, explicit_dates):
        start = date.fromisoformat(xcol["generation_range"][0])
        end = date.fromisoformat(xcol["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries."""
        assert 45 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "cse.lk" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXCOLWeekendPattern:
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

class TestXCOLSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2027-05-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_observed_names(self, explicit_dates):
        observed_count = sum(1 for e in explicit_dates.values() if "observed" in e["name"].lower())
        assert observed_count >= 2, f"Expected some observed holidays, got {observed_count}"


# ──────────────────────────────────────────────────────────────
# 2026: CSE Circular No. 07-10-2025 (22 October 2025), tier 1
# ──────────────────────────────────────────────────────────────

CSE_2026_CIRCULAR = {
    "2026-01-01": "CSE Customary Holiday",
    "2026-01-15": "Tamil Thai Pongal Day",
    "2026-02-04": "Independence Day",
    "2026-03-02": "Medin Full Moon Poya Day",
    "2026-04-01": "Bak Full Moon Poya Day",
    "2026-04-03": "Good Friday",
    "2026-04-13": "Day Prior to Sinhala and Tamil New Year Day",
    "2026-04-14": "Sinhala and Tamil New Year",
    "2026-05-01": "May Day",
    "2026-05-28": "Id-Ul-Allah (Hadji Festival Day)",
    "2026-06-29": "Poson Full Moon Poya Day",
    "2026-07-29": "Esala Full Moon Poya Day",
    "2026-08-26": "Milad-Un-Nabi (Holy Prophet's Birthday)",
    "2026-08-27": "Nikini Full Moon Poya Day",
    "2026-11-24": "Il Full Moon Poya Day",
    "2026-12-23": "Unduwap Full Moon Poya Day",
    "2026-12-25": "Christmas Day",
}

# 2025's Poya dates had been repeated for 2026 (same month and day); the
# circular does not list any of these.
REMOVED_2026 = ["2026-01-14", "2026-02-12", "2026-03-13", "2026-04-15",
                "2026-05-12", "2026-05-13", "2026-06-10", "2026-07-10",
                "2026-09-07", "2026-10-06", "2026-11-05", "2026-11-09",
                "2026-12-04"]


class TestXCOL2026Circular:
    """Every 2026 entry is on CSE's own circular, and the circular's closures
    are all present. The Vesak-week half holiday (2026-04-30) and the amended
    Circular 03-04-2026 are an open item (BLOCKED.md, XCOL)."""

    def test_2026_entries_match_the_circular_exactly(self, explicit_dates):
        have = {d: h["name"] for d, h in explicit_dates.items() if d.startswith("2026")}
        assert have == CSE_2026_CIRCULAR

    def test_2026_entries_cite_the_circular(self, explicit_dates):
        for d, h in explicit_dates.items():
            if d.startswith("2026"):
                assert h["source_url"].startswith("https://cdn.cse.lk/"), d

    @pytest.mark.parametrize("d", REMOVED_2026)
    def test_repeated_2025_dates_are_gone(self, explicit_dates, d):
        assert d not in explicit_dates

    def test_the_fourteen_previously_missing_closures(self, explicit_dates):
        missing = [d for d in CSE_2026_CIRCULAR
                   if d not in ("2026-04-14", "2026-05-01", "2026-12-25")]
        assert len(missing) == 14
        assert all(d in explicit_dates for d in missing)

    def test_no_2026_entry_on_a_weekend(self, explicit_dates):
        for d in explicit_dates:
            if d.startswith("2026"):
                assert date.fromisoformat(d).weekday() < 5, d
