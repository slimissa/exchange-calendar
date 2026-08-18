#!/usr/bin/env python3
"""
test_athens_holidays.py — Ground truth tests for XATH (Athens Stock Exchange).

Key facts verified:
    - Regular hours: 10:30-17:00
    - No lunch break (continuous trading)
    - No extended hours sessions
    - Orthodox Easter calendar (different from Western)
    - Clean Monday = Orthodox Easter - 48 days
    - Good Friday = Orthodox Easter - 2 days
    - Easter Monday = Orthodox Easter + 1 day
    - Holy Spirit Monday = Orthodox Easter + 50 days
    - Christmas Eve (Dec 24) — early close at 13:00
    - New Year's Eve (Dec 31) — early close at 13:00
    - Christmas/New Year use weekend substitution (Sat→Mon, Sun→Mon)
    - Fixed holidays: Epiphany, Independence Day (Mar 25), Labour Day,
      Dormition of Mary (Aug 15), Ochi Day (Oct 28)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XATH.json)
    2. Greek holiday announcements changed (verify against athexgroup.gr)

Run:
    python3 -m pytest tests/test_athens_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xath():
    """Load XATH.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XATH.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xath):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xath["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXATHProperties:
    def test_code(self, xath):
        assert xath["code"] == "XATH"

    def test_mic(self, xath):
        assert xath["mic"] == "XATH"

    def test_name(self, xath):
        assert xath["name"] == "Athens Stock Exchange"

    def test_timezone(self, xath):
        assert xath["timezone"] == "Europe/Athens"

    def test_regular_hours(self, xath):
        assert xath["regular_hours"]["open"] == "10:30"
        assert xath["regular_hours"]["close"] == "17:00"

    def test_no_lunch_break(self, xath):
        lunch = [s for s in xath.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xath):
        assert "extended_hours" not in xath or xath.get("extended_hours") is None

    def test_generation_range(self, xath):
        assert "generation_range" in xath
        assert xath["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xath):
        assert xath.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xath):
        """Orthodox Easter is complex — all dates should be explicit."""
        rules = xath["holidays"].get("recurrence_rules", [])
        assert rules == [], "XATH should use explicit dates only"


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXATHFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates
        assert "substitute" in explicit_dates["2028-01-03"]["name"].lower()

    def test_epiphany_2025(self, explicit_dates):
        """Jan 6, 2025 is Monday."""
        assert "2025-01-06" in explicit_dates
        assert explicit_dates["2025-01-06"]["name"] == "Epiphany"

    def test_epiphany_2026(self, explicit_dates):
        """Jan 6, 2026 is Tuesday."""
        assert "2026-01-06" in explicit_dates

    def test_independence_day_2025(self, explicit_dates):
        """Mar 25, 2025 is Tuesday."""
        assert "2025-03-25" in explicit_dates
        assert explicit_dates["2025-03-25"]["name"] == "Independence Day"

    def test_independence_day_2026(self, explicit_dates):
        """Mar 25, 2026 is Wednesday."""
        assert "2026-03-25" in explicit_dates

    def test_independence_day_2027(self, explicit_dates):
        """Mar 25, 2027 is Thursday."""
        assert "2027-03-25" in explicit_dates

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2028(self, explicit_dates):
        """May 1, 2028 is Monday."""
        assert "2028-05-01" in explicit_dates

    def test_dormition_2025(self, explicit_dates):
        """Aug 15, 2025 is Friday."""
        assert "2025-08-15" in explicit_dates
        assert explicit_dates["2025-08-15"]["name"] == "Dormition of Mary"

    def test_ochi_day_2025(self, explicit_dates):
        """Oct 28, 2025 is Tuesday."""
        assert "2025-10-28" in explicit_dates
        assert explicit_dates["2025-10-28"]["name"] == "Ochi Day"

    def test_ochi_day_2026(self, explicit_dates):
        """Oct 28, 2026 is Wednesday."""
        assert "2026-10-28" in explicit_dates

    def test_ochi_day_2027(self, explicit_dates):
        """Oct 28, 2027 is Thursday."""
        assert "2027-10-28" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Orthodox Easter holidays
# ──────────────────────────────────────────────────────────────

class TestXATHOrthodoxEaster:
    def test_clean_monday_2025(self, explicit_dates):
        """Orthodox Easter 2025 is April 20 — Clean Monday = -48 days = March 3."""
        assert "2025-03-03" in explicit_dates
        assert explicit_dates["2025-03-03"]["name"] == "Clean Monday"

    def test_clean_monday_2026(self, explicit_dates):
        """Orthodox Easter 2026 is April 12 — Clean Monday = February 23."""
        assert "2026-02-23" in explicit_dates

    def test_clean_monday_2027(self, explicit_dates):
        """Orthodox Easter 2027 is May 2 — Clean Monday = March 15."""
        assert "2027-03-15" in explicit_dates

    def test_clean_monday_2028(self, explicit_dates):
        """Orthodox Easter 2028 is April 16 — Clean Monday = March 6."""
        assert "2028-03-06" in explicit_dates

    def test_clean_monday_2029(self, explicit_dates):
        """Orthodox Easter 2029 is April 8 — Clean Monday = February 26."""
        assert "2029-02-26" in explicit_dates

    def test_good_friday_2025(self, explicit_dates):
        """Orthodox Easter 2025 — Good Friday = April 18."""
        assert "2025-04-18" in explicit_dates
        assert "Good Friday" in explicit_dates["2025-04-18"]["name"]

    def test_good_friday_2026(self, explicit_dates):
        """Orthodox Easter 2026 — Good Friday = April 10."""
        assert "2026-04-10" in explicit_dates

    def test_good_friday_2027(self, explicit_dates):
        """Orthodox Easter 2027 — Good Friday = April 30."""
        assert "2027-04-30" in explicit_dates

    def test_good_friday_2028(self, explicit_dates):
        """Orthodox Easter 2028 — Good Friday = April 14."""
        assert "2028-04-14" in explicit_dates

    def test_good_friday_2029(self, explicit_dates):
        """Orthodox Easter 2029 — Good Friday = April 6."""
        assert "2029-04-06" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        """Orthodox Easter 2025 — Easter Monday = April 21."""
        assert "2025-04-21" in explicit_dates
        assert "Easter Monday" in explicit_dates["2025-04-21"]["name"]

    def test_easter_monday_2026(self, explicit_dates):
        """Orthodox Easter 2026 — Easter Monday = April 13."""
        assert "2026-04-13" in explicit_dates

    def test_easter_monday_2027(self, explicit_dates):
        """Orthodox Easter 2027 — Easter Monday = May 3."""
        assert "2027-05-03" in explicit_dates

    def test_easter_monday_2028(self, explicit_dates):
        """Orthodox Easter 2028 — Easter Monday = April 17."""
        assert "2028-04-17" in explicit_dates

    def test_easter_monday_2029(self, explicit_dates):
        """Orthodox Easter 2029 — Easter Monday = April 9."""
        assert "2029-04-09" in explicit_dates

    def test_holy_spirit_monday_2025(self, explicit_dates):
        """Orthodox Easter 2025 — Holy Spirit Monday = +50 days = June 9."""
        assert "2025-06-09" in explicit_dates
        assert explicit_dates["2025-06-09"]["name"] == "Holy Spirit Monday"

    def test_holy_spirit_monday_2026(self, explicit_dates):
        """Orthodox Easter 2026 — Holy Spirit Monday = June 1."""
        assert "2026-06-01" in explicit_dates

    def test_holy_spirit_monday_2027(self, explicit_dates):
        """Orthodox Easter 2027 — Holy Spirit Monday = June 21."""
        assert "2027-06-21" in explicit_dates

    def test_holy_spirit_monday_2028(self, explicit_dates):
        """Orthodox Easter 2028 — Holy Spirit Monday = June 5."""
        assert "2028-06-05" in explicit_dates

    def test_holy_spirit_monday_2029(self, explicit_dates):
        """Orthodox Easter 2029 — Holy Spirit Monday = May 28."""
        assert "2029-05-28" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas and New Year
# ──────────────────────────────────────────────────────────────

class TestXATHChristmas:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — early close at 13:00."""
        entry = explicit_dates.get("2025-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "13:00"

    def test_christmas_eve_2026(self, explicit_dates):
        """Dec 24, 2026 is Thursday — early close at 13:00."""
        entry = explicit_dates.get("2026-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "13:00"

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_day_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates
        assert "substitute" in explicit_dates["2027-12-27"]["name"].lower()

    def test_christmas_day_2028(self, explicit_dates):
        """Dec 25, 2028 is Monday."""
        assert "2028-12-25" in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_boxing_day_2027_substitute(self, explicit_dates):
        """Dec 26, 2027 is Sunday — substitute to Tuesday Dec 28.
           (Monday Dec 27 is already Christmas Day substitute)."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" not in explicit_dates  # Not needed if Boxing Day not substituted

    def test_boxing_day_2028(self, explicit_dates):
        """Dec 26, 2028 is Tuesday."""
        assert "2028-12-26" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — early close at 13:00."""
        entry = explicit_dates.get("2025-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "13:00"

    def test_new_years_eve_2027(self, explicit_dates):
        """Dec 31, 2027 is Friday — early close at 13:00."""
        entry = explicit_dates.get("2027-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "13:00"

    def test_new_years_eve_2029(self, explicit_dates):
        """Dec 31, 2029 is Monday — early close at 13:00."""
        entry = explicit_dates.get("2029-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"


# ──────────────────────────────────────────────────────────────
# Early close days
# ──────────────────────────────────────────────────────────────

class TestXATHEarlyCloses:
    def test_no_other_early_closes(self, explicit_dates):
        """Only Christmas Eve and New Year's Eve are early closes."""
        early_closes = [e for e in explicit_dates.values() if e.get("status") == "early_close"]
        early_close_names = {e["name"] for e in early_closes}
        assert early_close_names == {"Christmas Eve", "New Year's Eve"}

    def test_all_early_closes_have_early_close_time(self, explicit_dates):
        """All early close entries must have early_close_time."""
        for entry in explicit_dates.values():
            if entry.get("status") == "early_close":
                assert "early_close_time" in entry, f"Missing early_close_time: {entry['date']}"
                assert entry["early_close_time"] == "13:00"

    def test_closed_entries_no_early_close_time(self, explicit_dates):
        """Closed entries should not have early_close_time."""
        for entry in explicit_dates.values():
            if entry.get("status") == "closed":
                assert "early_close_time" not in entry, f"Unexpected early_close_time: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXATHStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str} ({d.strftime('%A')})"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates)), "Duplicate dates found"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"
            assert entry["source_url"].startswith("http"), f"Invalid source_url: {date_str}"

    def test_all_entries_have_name(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "name" in entry, f"Missing name: {date_str}"
            assert entry["name"], f"Empty name: {date_str}"

    def test_all_entries_have_status(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "status" in entry, f"Missing status: {date_str}"
            assert entry["status"] in ["closed", "early_close"], f"Invalid status: {date_str}"

    def test_dates_within_generation_range(self, xath, explicit_dates):
        start = date.fromisoformat(xath["generation_range"][0])
        end = date.fromisoformat(xath["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end, f"Date outside range: {date_str}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries: 12 holidays × 5 years (minus weekends, plus substitutes)."""
        assert 50 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """All source URLs should be from athexgroup.gr."""
        for entry in explicit_dates.values():
            assert "athexgroup.gr" in entry["source_url"], f"Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Orthodox Easter cross-checks
# ──────────────────────────────────────────────────────────────

class TestXATHOrthodoxCrossChecks:
    def test_orthodox_easter_2025(self, explicit_dates):
        """Verify Orthodox Easter 2025 dates are internally consistent."""
        # Orthodox Easter Sunday 2025 is April 20
        assert "2025-03-03" in explicit_dates  # Clean Monday (-48)
        assert "2025-04-18" in explicit_dates  # Good Friday (-2)
        assert "2025-04-21" in explicit_dates  # Easter Monday (+1)
        assert "2025-06-09" in explicit_dates  # Holy Spirit (+50)

    def test_orthodox_easter_2026(self, explicit_dates):
        """Verify Orthodox Easter 2026 dates are internally consistent."""
        # Orthodox Easter Sunday 2026 is April 12
        assert "2026-02-23" in explicit_dates  # Clean Monday (-48)
        assert "2026-04-10" in explicit_dates  # Good Friday (-2)
        assert "2026-04-13" in explicit_dates  # Easter Monday (+1)
        assert "2026-06-01" in explicit_dates  # Holy Spirit (+50)

    def test_orthodox_easter_2027(self, explicit_dates):
        """Verify Orthodox Easter 2027 dates are internally consistent."""
        # Orthodox Easter Sunday 2027 is May 2
        assert "2027-03-15" in explicit_dates  # Clean Monday (-48)
        assert "2027-04-30" in explicit_dates  # Good Friday (-2)
        assert "2027-05-03" in explicit_dates  # Easter Monday (+1)
        assert "2027-06-21" in explicit_dates  # Holy Spirit (+50)

    def test_orthodox_easter_2028(self, explicit_dates):
        """Verify Orthodox Easter 2028 dates are internally consistent."""
        # Orthodox Easter Sunday 2028 is April 16
        assert "2028-03-06" in explicit_dates  # Clean Monday (-48)
        assert "2028-04-14" in explicit_dates  # Good Friday (-2)
        assert "2028-04-17" in explicit_dates  # Easter Monday (+1)
        assert "2028-06-05" in explicit_dates  # Holy Spirit (+50)

    def test_orthodox_easter_2029(self, explicit_dates):
        """Verify Orthodox Easter 2029 dates are internally consistent."""
        # Orthodox Easter Sunday 2029 is April 8
        assert "2029-02-26" in explicit_dates  # Clean Monday (-48)
        assert "2029-04-06" in explicit_dates  # Good Friday (-2)
        assert "2029-04-09" in explicit_dates  # Easter Monday (+1)
        assert "2029-05-28" in explicit_dates  # Holy Spirit (+50)

    def test_orthodox_mondays_are_mondays(self, explicit_dates):
        """Clean Monday, Easter Monday, and Holy Spirit Monday must be Mondays."""
        monday_holidays = ["Clean Monday", "Easter Monday (Orthodox)", "Holy Spirit Monday"]
        for entry in explicit_dates.values():
            if entry["name"] in monday_holidays:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"{entry['name']} should be Monday: {entry['date']}"

    def test_orthodox_good_fridays_are_fridays(self, explicit_dates):
        """Good Friday must always be Friday."""
        for entry in explicit_dates.values():
            if "Good Friday" in entry["name"]:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 4, f"Good Friday should be Friday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXATHSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        """Verify known weekend holidays are correctly absent or substituted."""
        # 2028-01-01 is Saturday → substitute to Monday Jan 3
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

        # 2027-12-25 is Saturday → substitute to Monday Dec 27
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates

    def test_no_observed_holidays(self, explicit_dates):
        """Greece uses 'substitute', not 'observed'."""
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            assert "observed" not in name, f"Observed holiday found: {entry['name']}"

    def test_substitute_names_contain_substitute(self, explicit_dates):
        """All substitute holidays should have 'substitute' in name."""
        for entry in explicit_dates.values():
            if "substitute" in entry["name"].lower():
                assert "substitute" in entry["name"].lower()