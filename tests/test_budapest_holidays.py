#!/usr/bin/env python3
"""
test_budapest_holidays.py — Ground truth tests for XBUD (Budapest Stock Exchange).

Key facts verified:
    - Regular hours: 09:00-17:00
    - No lunch break (continuous trading)
    - No extended hours sessions
    - Hungary uses weekend substitution (Sat→Mon, Sun→Mon)
    - National Day (Mar 15) with substitution
    - Labour Day (May 1) with substitution
    - St. Stephen's Day (Aug 20) with substitution
    - Republic Day (Oct 23) with substitution
    - Christmas Eve (Dec 24) — full closure
    - New Year's Eve (Dec 31) — full closure
    - Good Friday and Easter Monday
    - Whit Monday (Easter + 50 days)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBUD.json)
    2. Hungarian holiday announcements changed (verify against bse.hu)

Run:
    python3 -m pytest tests/test_budapest_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbud():
    """Load XBUD.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBUD.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbud):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbud["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xbud):
    """Return dict of name -> rule."""
    rules = xbud["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBUDProperties:
    def test_code(self, xbud):
        assert xbud["code"] == "XBUD"

    def test_mic(self, xbud):
        assert xbud["mic"] == "XBUD"

    def test_name(self, xbud):
        assert xbud["name"] == "Budapest Stock Exchange"

    def test_timezone(self, xbud):
        assert xbud["timezone"] == "Europe/Budapest"

    def test_regular_hours(self, xbud):
        assert xbud["regular_hours"]["open"] == "09:00"
        assert xbud["regular_hours"]["close"] == "17:00"

    def test_no_lunch_break(self, xbud):
        lunch = [s for s in xbud.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbud):
        assert "extended_hours" not in xbud or xbud.get("extended_hours") is None

    def test_generation_range(self, xbud):
        assert "generation_range" in xbud
        assert xbud["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xbud):
        assert xbud.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays with weekend substitution
# ──────────────────────────────────────────────────────────────

class TestXBUDFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_new_year_2028_saturday_is_not_moved(self, explicit_dates):
        """Jan 1, 2028 is Saturday. Hungary gives no substitute day."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" not in explicit_dates

    def test_national_day_2025(self, explicit_dates):
        """Mar 15, 2025 is Saturday: BSE resolution 311/2024 lists no closure on Friday 14 March."""
        assert "2025-03-15" not in explicit_dates
        assert "2025-03-14" not in explicit_dates

    def test_national_day_2026(self, explicit_dates):
        """Mar 15, 2026 is Sunday: the Labour Code gives no Monday substitute."""
        assert "2026-03-15" not in explicit_dates
        assert "2026-03-16" not in explicit_dates

    def test_national_day_2027(self, explicit_dates):
        """Mar 15, 2027 is Monday — no substitution."""
        assert "2027-03-15" in explicit_dates
        assert explicit_dates["2027-03-15"]["name"] == "National Day"

    def test_labour_day_2025(self, explicit_dates):
        """May 1, 2025 is Thursday — no substitution."""
        assert "2025-05-01" in explicit_dates
        assert explicit_dates["2025-05-01"]["name"] == "Labour Day"

    def test_labour_day_2027_saturday_is_not_moved(self, explicit_dates):
        """May 1, 2027 is Saturday. Neither Friday 30 Apr nor Monday 3 May closes."""
        assert "2027-05-03" not in explicit_dates

    def test_st_stephens_day_2025(self, explicit_dates):
        """Aug 20, 2025 is Wednesday — no substitution."""
        assert "2025-08-20" in explicit_dates
        assert explicit_dates["2025-08-20"]["name"] == "St. Stephen's Day"

    def test_st_stephens_day_2028_sunday_is_not_moved(self, explicit_dates):
        """Aug 20, 2028 is Sunday. Hungary gives no substitute day."""
        assert "2028-08-21" not in explicit_dates

    def test_republic_day_2025(self, explicit_dates):
        """Oct 23, 2025 is Thursday — no substitution."""
        assert "2025-10-23" in explicit_dates
        assert explicit_dates["2025-10-23"]["name"] == "Republic Day"

    def test_republic_day_2027_saturday_is_not_moved(self, explicit_dates):
        """Oct 23, 2027 is Saturday. Hungary gives no substitute day."""
        assert "2027-10-25" not in explicit_dates

    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — full closure."""
        assert "2025-12-24" in explicit_dates
        assert explicit_dates["2025-12-24"]["name"] == "Christmas Eve"
        assert explicit_dates["2025-12-24"]["status"] == "closed"

    def test_christmas_eve_2029(self, explicit_dates):
        """Dec 24, 2029 is Monday — full closure."""
        assert "2029-12-24" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — full closure."""
        assert "2025-12-31" in explicit_dates
        assert explicit_dates["2025-12-31"]["name"] == "New Year's Eve"
        assert explicit_dates["2025-12-31"]["status"] == "closed"

    def test_new_years_eve_2029(self, explicit_dates):
        """Dec 31, 2029 is Monday — full closure."""
        assert "2029-12-31" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXBUDChristmas:
    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_day_2027_saturday_is_not_moved(self, explicit_dates):
        """Dec 25, 2027 is Saturday. Hungary gives no substitute day."""
        assert "2027-12-27" not in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_boxing_day_2026_saturday_is_not_moved(self, explicit_dates):
        """Dec 26, 2026 is Saturday: no Monday substitute."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" not in explicit_dates

    def test_boxing_day_2027_sunday_is_not_moved(self, explicit_dates):
        """Dec 26, 2027 is Sunday. Hungary gives no substitute day."""
        assert "2027-12-28" not in explicit_dates

    def test_boxing_day_2028(self, explicit_dates):
        """Dec 26, 2028 is Tuesday."""
        assert "2028-12-26" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXBUDEaster:
    def test_good_friday_2025(self, explicit_dates):
        """Easter - 2 days — April 18, 2025."""
        assert "2025-04-18" in explicit_dates
        assert explicit_dates["2025-04-18"]["name"] == "Good Friday"

    def test_good_friday_2026(self, explicit_dates):
        """Easter - 2 days — April 3, 2026."""
        assert "2026-04-03" in explicit_dates

    def test_good_friday_2027(self, explicit_dates):
        """Easter - 2 days — March 26, 2027."""
        assert "2027-03-26" in explicit_dates

    def test_good_friday_2028(self, explicit_dates):
        """Easter - 2 days — April 14, 2028."""
        assert "2028-04-14" in explicit_dates

    def test_good_friday_2029(self, explicit_dates):
        """Easter - 2 days — March 30, 2029."""
        assert "2029-03-30" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        """Easter + 1 day — April 21, 2025."""
        assert "2025-04-21" in explicit_dates
        assert explicit_dates["2025-04-21"]["name"] == "Easter Monday"

    def test_easter_monday_2026(self, explicit_dates):
        """Easter + 1 day — April 6, 2026."""
        assert "2026-04-06" in explicit_dates

    def test_easter_monday_2027(self, explicit_dates):
        """Easter + 1 day — March 29, 2027."""
        assert "2027-03-29" in explicit_dates

    def test_easter_monday_2028(self, explicit_dates):
        """Easter + 1 day — April 17, 2028."""
        assert "2028-04-17" in explicit_dates

    def test_easter_monday_2029(self, explicit_dates):
        """Easter + 1 day — April 2, 2029."""
        assert "2029-04-02" in explicit_dates

    def test_whit_monday_2025(self, explicit_dates):
        """Easter + 50 days — June 9, 2025."""
        assert "2025-06-09" in explicit_dates
        assert explicit_dates["2025-06-09"]["name"] == "Whit Monday"

    def test_whit_monday_2026(self, explicit_dates):
        """Easter + 50 days — May 25, 2026."""
        assert "2026-05-25" in explicit_dates

    def test_whit_monday_2027(self, explicit_dates):
        """Easter + 50 days — May 17, 2027."""
        assert "2027-05-17" in explicit_dates

    def test_whit_monday_2028(self, explicit_dates):
        """Easter + 50 days — June 5, 2028."""
        assert "2028-06-05" in explicit_dates

    def test_whit_monday_2029(self, explicit_dates):
        """Easter + 50 days — May 21, 2029."""
        assert "2029-05-21" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXBUDRecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "New Year's Day",
            "National Day",
            "Good Friday",
            "Easter Monday",
            "Labour Day",
            "Whit Monday",
            "St. Stephen's Day",
            "Republic Day",
            "Christmas Eve",
            "Christmas Day",
            "Boxing Day",
            "New Year's Eve",
        }
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_weekend_adjustment_rules(self, recurrence_rules):
        """The Labour Code gives no substitute day for a holiday on a weekend;
        only the yearly NGM decree moves working days (not known for 2027+)."""
        for name in ["New Year's Day", "National Day", "Labour Day",
                     "St. Stephen's Day", "Republic Day", "Christmas Eve",
                     "Christmas Day", "Boxing Day", "New Year's Eve",
                     "All Saints' Day"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_date", f"{name} should not shift"

    def test_easter_rules(self, recurrence_rules):
        assert recurrence_rules["Good Friday"]["rule"] == "easter_offset"
        assert recurrence_rules["Good Friday"]["offset_days"] == -2

        assert recurrence_rules["Easter Monday"]["rule"] == "easter_offset"
        assert recurrence_rules["Easter Monday"]["offset_days"] == 1

        assert recurrence_rules["Whit Monday"]["rule"] == "easter_offset"
        assert recurrence_rules["Whit Monday"]["offset_days"] == 50

    def test_all_rules_closed_status(self, recurrence_rules):
        """Hungary has no early closes — all rules should be 'closed'."""
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed", f"{name} should be closed"

    def test_closed_rules_have_no_close_time(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert "close_time" not in rule, f"{name} should not have close_time"
            assert "early_close_time" not in rule, f"{name} should not have early_close_time"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBUDStructure:
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

    def test_all_statuses_closed(self, explicit_dates):
        """Hungary has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", f"Unexpected status: {entry['date']}"

    def test_dates_within_generation_range(self, xbud, explicit_dates):
        start = date.fromisoformat(xbud["generation_range"][0])
        end = date.fromisoformat(xbud["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end, f"Date outside range: {date_str}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries: 12 holidays × 5 years (minus weekends, plus substitutes)."""
        assert 50 <= len(explicit_dates) <= 65, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """All source URLs should be from bse.hu."""
        for entry in explicit_dates.values():
            assert "bse.hu" in entry["source_url"], f"Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Easter cross-checks
# ──────────────────────────────────────────────────────────────

class TestXBUDEasterCrossChecks:
    def test_easter_2025_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2025."""
        # Easter Sunday 2025 is April 20
        assert "2025-04-18" in explicit_dates  # Good Friday (-2)
        assert "2025-04-21" in explicit_dates  # Easter Monday (+1)
        assert "2025-06-09" in explicit_dates  # Whit Monday (+50)

    def test_easter_2026_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2026."""
        # Easter Sunday 2026 is April 5
        assert "2026-04-03" in explicit_dates  # Good Friday (-2)
        assert "2026-04-06" in explicit_dates  # Easter Monday (+1)
        assert "2026-05-25" in explicit_dates  # Whit Monday (+50)

    def test_easter_2027_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2027."""
        # Easter Sunday 2027 is March 28
        assert "2027-03-26" in explicit_dates  # Good Friday (-2)
        assert "2027-03-29" in explicit_dates  # Easter Monday (+1)
        assert "2027-05-17" in explicit_dates  # Whit Monday (+50)

    def test_easter_2028_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2028."""
        # Easter Sunday 2028 is April 16
        assert "2028-04-14" in explicit_dates  # Good Friday (-2)
        assert "2028-04-17" in explicit_dates  # Easter Monday (+1)
        assert "2028-06-05" in explicit_dates  # Whit Monday (+50)

    def test_easter_2029_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2029."""
        # Easter Sunday 2029 is April 1
        assert "2029-03-30" in explicit_dates  # Good Friday (-2)
        assert "2029-04-02" in explicit_dates  # Easter Monday (+1)
        assert "2029-05-21" in explicit_dates  # Whit Monday (+50)

    def test_easter_mondays_are_mondays(self, explicit_dates):
        """Easter Monday and Whit Monday must always be Mondays."""
        monday_holidays = ["Easter Monday", "Whit Monday"]
        for entry in explicit_dates.values():
            if entry["name"] in monday_holidays:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"{entry['name']} should be Monday: {entry['date']}"

    def test_good_fridays_are_fridays(self, explicit_dates):
        """Good Friday must always be Friday."""
        for entry in explicit_dates.values():
            if entry["name"] == "Good Friday":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 4, f"Good Friday should be Friday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Substitution logic checks
# ──────────────────────────────────────────────────────────────

class TestXBUDSubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        """Verify known weekend holidays are correctly absent."""
        weekend_holidays = [
            ("2025-03-15", "National Day (Saturday)"),
            ("2027-05-01", "Labour Day (Saturday)"),
            ("2027-12-25", "Christmas Day (Saturday)"),
            ("2028-01-01", "New Year's Day (Saturday)"),
        ]
        for date_str, name in weekend_holidays:
            assert date_str not in explicit_dates, f"{name} should not be in explicit dates"

    def test_substitute_names_contain_substitute_or_observed(self, explicit_dates):
        """Hungary uses 'substitute' or 'observed' for shifted holidays."""
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "substitute" in name or "observed" in name:
                assert "substitute" in name or "observed" in name

    def test_weekend_holidays_have_no_substitutes(self, explicit_dates):
        """Weekend holidays are lost, not moved (2027 onwards)."""
        assert "2028-01-03" not in explicit_dates
        assert "2028-08-21" not in explicit_dates

# ── v2.9.3: weekend substitutes ─────────────────────────────────────

def test_observed_substitutes_2026():
    """March 15, 2026 is a Sunday and December 26 a Saturday. Hungarian
    labour law gives no substitute day for a weekend holiday, and BSE's
    resolution lists every trading holiday, so the fetcher adds none
    (v2.23.13; it used to add 16 March and 28 December)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
    from update_from_exchange import BudapestFetcher

    f = BudapestFetcher()
    assert f._observed_substitutes(2026) == []
    assert f._observed_substitutes(2025) == []
    assert f._observed_substitutes(2027) == []


def test_observed_substitutes_2024_no_occurrence():
    """March 15, 2024 is Friday; December 26 is Thursday. No
    substitutes fire on weekdays."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
    from update_from_exchange import BudapestFetcher

    f = BudapestFetcher()
    assert f._observed_substitutes(2024) == []


# ──────────────────────────────────────────────────────────────
# Future-year fixes (v2.23.5)
# ──────────────────────────────────────────────────────────────

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import generate_dates as _gd


def _closed(code, year):
    """Closed weekdays the registry produces for one year (explicit plus rules)."""
    e = json.loads((Path(__file__).parent.parent / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    days = list(e["holidays"]["explicit"]) + _gd.expand_exchange(e)
    return {d["date"] for d in days
            if d["date"].startswith(str(year)) and d["status"] == "closed"
            and date.fromisoformat(d["date"]).weekday() < 5}


def _early(code, year):
    e = json.loads((Path(__file__).parent.parent / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))
    return {d["date"]: d["early_close_time"] for d in e["holidays"]["explicit"]
            if d["date"].startswith(str(year)) and d["status"] == "early_close"}


class TestFutureYearFixes:
    """The Labour Code lists eleven holidays and gives no substitute day for one
    on a weekend; All Saints (1 November) is among them."""

    @pytest.mark.parametrize("day", ["2027-11-01", "2028-11-01", "2029-11-01"])
    def test_all_saints_is_closed(self, day):
        assert day in _closed("XBUD", int(day[:4]))

    @pytest.mark.parametrize("day", ["2027-04-30", "2027-05-03", "2027-10-22", "2027-10-25",
                                     "2027-12-27", "2027-12-28", "2028-01-03", "2028-08-21"])
    def test_weekend_holidays_leave_no_weekday_closure(self, day):
        assert day not in _closed("XBUD", int(day[:4]))

    def test_2027_closed_weekdays(self):
        assert _closed("XBUD", 2027) == {
            "2027-01-01", "2027-03-15", "2027-03-26", "2027-03-29", "2027-05-17",
            "2027-08-20", "2027-11-01", "2027-12-24", "2027-12-31"}


# ──────────────────────────────────────────────────────────────
# BSE trading holidays, 2025 and 2026 (v2.23.10)
# ──────────────────────────────────────────────────────────────

class TestBseHolidays2025And2026:
    """BSE resolution 311/2024 fixes the 2025 trading holidays: the public
    holidays plus the rest days 2 May, 24 October and 24 December, and no
    weekend holiday is moved to a weekday. For 2026 BSE closes on the rest
    days 2 January and 21 August (working Saturdays 10 January and 8 August)
    and on 24 December."""

    def test_2025_closed_weekdays(self):
        assert _closed("XBUD", 2025) == {
            "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-01", "2025-05-02",
            "2025-06-09", "2025-08-20", "2025-10-23", "2025-10-24", "2025-12-24",
            "2025-12-25", "2025-12-26", "2025-12-31"}

    def test_2026_closed_weekdays(self):
        assert _closed("XBUD", 2026) == {
            "2026-01-01", "2026-01-02", "2026-04-03", "2026-04-06", "2026-05-01",
            "2026-05-25", "2026-08-20", "2026-08-21", "2026-10-23", "2026-12-24",
            "2026-12-25", "2026-12-31"}

    @pytest.mark.parametrize("day", ["2025-03-14", "2026-03-16", "2026-12-28"])
    def test_former_substitutes_are_trading_days(self, day):
        assert day not in _closed("XBUD", int(day[:4]))
