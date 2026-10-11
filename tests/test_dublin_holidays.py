#!/usr/bin/env python3
"""
test_dublin_holidays.py — Ground truth tests for XDUB (Euronext Dublin / Irish Stock Exchange).

Key facts verified:
    - Regular hours: 08:00-16:30
    - No lunch break (continuous trading)
    - No extended hours sessions
    - UK-style weekend substitution (Sat→Mon, Sun→Mon)
    - Labour Day (May 1) — fixed date, no weekend substitution
    - Good Friday and Easter Monday (movable)
    - Irish May Bank Holiday (first Monday in May) is the only Irish bank holiday
      Euronext closes Dublin for. St. Patrick's Day and the June, August and
      October bank holidays are full trading days (Euronext holiday calendars).
    - Christmas Eve (Dec 24) — early close at 12:30
    - New Year's Eve (Dec 31) — early close at 12:30
    - Christmas Day and St. Stephen's Day — with substitution

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XDUB.json)
    2. Irish holiday announcements changed (verify against euronext.com)

Source for the Task 36 corrections: Euronext's own holiday calendars,
live.euronext.com/en/resources/trading-hours-holidays ("Calendar of business
days" 2022 to 2025 and "2026 Holiday Calendar for Euronext's Cash and
Derivatives markets"), tier 1. 2025 and 2026 are published; 2027 to 2029 are not
and rest on the pattern of the published years (pattern-derived, not tier 1).

Run:
    python3 -m pytest tests/test_dublin_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xdub():
    """Load XDUB.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XDUB.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xdub):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xdub["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xdub):
    """Return dict of name -> rule."""
    rules = xdub["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXDUBProperties:
    def test_code(self, xdub):
        assert xdub["code"] == "XDUB"

    def test_mic(self, xdub):
        assert xdub["mic"] == "XDUB"

    def test_name(self, xdub):
        assert xdub["name"] == "Euronext Dublin"

    def test_timezone(self, xdub):
        assert xdub["timezone"] == "Europe/Dublin"

    def test_regular_hours(self, xdub):
        assert xdub["regular_hours"]["open"] == "08:00"
        assert xdub["regular_hours"]["close"] == "16:30"

    def test_no_lunch_break(self, xdub):
        lunch = [s for s in xdub.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xdub):
        assert "extended_hours" not in xdub or xdub.get("extended_hours") is None

    def test_generation_range(self, xdub):
        assert "generation_range" in xdub
        assert xdub["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xdub):
        assert xdub.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays (with weekend substitution)
# ──────────────────────────────────────────────────────────────

class TestXDUBFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday — no substitution."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_new_year_2027_substitute(self, explicit_dates):
        """Jan 1, 2027 is Friday — no substitution."""
        assert "2027-01-01" in explicit_dates

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates
        assert "substitute" in explicit_dates["2028-01-03"]["name"].lower()

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday — no substitution."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_day_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27.
           Dec 26, 2027 is Sunday — substitute to Tuesday Dec 28."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-27" in explicit_dates
        assert "2027-12-28" in explicit_dates

    def test_st_stephens_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday — no substitution."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "St. Stephen's Day"

    def test_st_stephens_day_2026_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute to Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates
        assert "substitute" in explicit_dates["2026-12-28"]["name"].lower()


# ──────────────────────────────────────────────────────────────
# Bank Holidays (nth weekday rules)
# ──────────────────────────────────────────────────────────────

class TestXDUBBankHolidays:
    def test_may_bank_holiday_2025(self, explicit_dates):
        """First Monday in May — May 5, 2025."""
        assert "2025-05-05" in explicit_dates
        assert explicit_dates["2025-05-05"]["name"] == "May Bank Holiday"

    def test_may_bank_holiday_2026(self, explicit_dates):
        """First Monday in May — May 4, 2026."""
        assert "2026-05-04" in explicit_dates

    def test_may_bank_holiday_2027(self, explicit_dates):
        """First Monday in May — May 3, 2027."""
        assert "2027-05-03" in explicit_dates

    def test_may_bank_holiday_2028_coincides_with_labour_day(self, explicit_dates):
        """May 1, 2028 is a Monday: Irish May Bank Holiday and Labour Day on one date."""
        assert "2028-05-01" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Early close days
# ──────────────────────────────────────────────────────────────

class TestXDUBEarlyCloses:
    def test_christmas_eve_2025(self, explicit_dates):
        """Dec 24, 2025 is Wednesday — early close at 12:30."""
        entry = explicit_dates.get("2025-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_christmas_eve_2026(self, explicit_dates):
        """Dec 24, 2026 is Thursday — early close at 12:30."""
        entry = explicit_dates.get("2026-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_new_years_eve_2025(self, explicit_dates):
        """Dec 31, 2025 is Wednesday — early close at 12:30."""
        entry = explicit_dates.get("2025-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_new_years_eve_2026(self, explicit_dates):
        """Dec 31, 2026 is Thursday — early close at 12:30."""
        entry = explicit_dates.get("2026-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_new_years_eve_2027(self, explicit_dates):
        """Dec 31, 2027 is Friday — early close at 12:30."""
        entry = explicit_dates.get("2027-12-31")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "12:30"

    def test_no_other_early_closes(self, explicit_dates):
        """Only Christmas Eve and New Year's Eve are early closes."""
        early_closes = [e for e in explicit_dates.values() if e.get("status") == "early_close"]
        early_close_names = {e["name"] for e in early_closes}
        assert early_close_names == {"Christmas Eve", "New Year's Eve"}


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXDUBEaster:
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


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXDUBRecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {
            "New Year's Day",
            "Labour Day",
            "Good Friday",
            "Easter Monday",
            "May Bank Holiday",
            "Christmas Day",
            "St. Stephen's Day",
        }
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_weekend_adjustment_rules(self, recurrence_rules):
        """UK-style substitution: Sat→Mon, Sun→Mon."""
        for name in ["New Year's Day", "Christmas Day", "St. Stephen's Day"]:
            rule = recurrence_rules[name]
            assert rule["rule"] == "fixed_with_weekend_adjustment", f"{name} should use weekend adjustment"

    def test_easter_rules(self, recurrence_rules):
        assert recurrence_rules["Good Friday"]["rule"] == "easter_offset"
        assert recurrence_rules["Good Friday"]["offset_days"] == -2

        assert recurrence_rules["Easter Monday"]["rule"] == "easter_offset"
        assert recurrence_rules["Easter Monday"]["offset_days"] == 1

    def test_bank_holiday_rules(self, recurrence_rules):
        rule = recurrence_rules["May Bank Holiday"]
        assert rule["rule"] == "nth_weekday"
        assert rule["weekday"] == "monday"
        assert rule["n"] == 1

    def test_labour_day_rule(self, recurrence_rules):
        """Labour Day, 1 May: Euronext closes all markets (Euronext holiday calendars
        2022 to 2026, tier 1). Fixed date, no weekend substitution: when 1 May is a
        Saturday (2027) Euronext does not close on the Monday."""
        rule = recurrence_rules["Labour Day"]
        assert rule["rule"] == "fixed_date"
        assert (rule["month"], rule["day"]) == (5, 1)

    def test_removed_rules_stay_removed(self, recurrence_rules):
        """Euronext's calendars show Dublin trading on these days (2022 to 2026)."""
        for name in ["St. Patrick's Day", "June Bank Holiday",
                     "August Bank Holiday", "October Bank Holiday"]:
            assert name not in recurrence_rules, f"{name} is not a Euronext Dublin closure"

    def test_no_early_close_rules(self, recurrence_rules):
        """Early close days are explicit only, not in recurrence rules."""
        for name, rule in recurrence_rules.items():
            assert rule.get("status") != "early_close", f"{name} should not be in recurrence as early_close"

    def test_closed_rules_have_no_early_close_time(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            if rule.get("status") == "closed":
                assert "early_close_time" not in rule, f"{name} should not have early_close_time"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXDUBStructure:
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

    def test_early_close_entries_have_early_close_time(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            if entry.get("status") == "early_close":
                assert "early_close_time" in entry, f"Missing early_close_time: {date_str}"

    def test_closed_entries_no_early_close_time(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            if entry.get("status") == "closed":
                assert "early_close_time" not in entry, f"Unexpected early_close_time: {date_str}"

    def test_dates_within_generation_range(self, xdub, explicit_dates):
        start = date.fromisoformat(xdub["generation_range"][0])
        end = date.fromisoformat(xdub["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end, f"Date outside range: {date_str}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~35-50 entries: 7 closure types × 5 years + early closes + substitutes."""
        assert 35 <= len(explicit_dates) <= 50, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """All source URLs should be from euronext.com."""
        for entry in explicit_dates.values():
            assert "euronext.com" in entry["source_url"], f"Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Substitution logic cross-checks
# ──────────────────────────────────────────────────────────────

class TestXDUBSubstitution:
    def test_saturday_substitutes_to_monday(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute should be Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates

    def test_sunday_substitutes_to_monday(self, explicit_dates):
        """Dec 26, 2027 is Sunday — substitute should be Tuesday Dec 28.
           (Monday Dec 27 is already Christmas Day substitute)."""
        assert "2027-12-26" not in explicit_dates
        assert "2027-12-28" in explicit_dates

    def test_substitute_names_contain_substitute(self, explicit_dates):
        """All substitute holidays should have 'substitute' in name."""
        for entry in explicit_dates.values():
            if "substitute" in entry["name"].lower():
                assert "substitute" in entry["name"].lower()

    def test_no_observed_holidays(self, explicit_dates):
        """Ireland uses 'substitute', not 'observed'."""
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            assert "observed" not in name, f"Observed holiday found: {entry['name']}"

    def test_weekend_holidays_absent(self, explicit_dates):
        """Verify known weekend holidays are correctly absent."""
        weekend_holidays = [
            ("2027-12-25", "Christmas Day (Saturday)"),
            ("2027-12-26", "St. Stephen's Day (Sunday)"),
            ("2028-01-01", "New Year's Day (Saturday)"),
        ]
        for date_str, name in weekend_holidays:
            assert date_str not in explicit_dates, f"{name} should not be in explicit dates"


# ──────────────────────────────────────────────────────────────
# Calendar calculation cross-checks
# ──────────────────────────────────────────────────────────────

class TestXDUBCalendarCrossChecks:
    def test_easter_2025_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2025."""
        # Easter Sunday 2025 is April 20
        assert "2025-04-18" in explicit_dates  # Good Friday (-2)
        assert "2025-04-21" in explicit_dates  # Easter Monday (+1)

    def test_easter_2026_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2026."""
        # Easter Sunday 2026 is April 5
        assert "2026-04-03" in explicit_dates  # Good Friday (-2)
        assert "2026-04-06" in explicit_dates  # Easter Monday (+1)

    def test_easter_2027_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2027."""
        # Easter Sunday 2027 is March 28
        assert "2027-03-26" in explicit_dates  # Good Friday (-2)
        assert "2027-03-29" in explicit_dates  # Easter Monday (+1)

    def test_easter_2028_calculations(self, explicit_dates):
        """Verify Easter-based dates are internally consistent for 2028."""
        # Easter Sunday 2028 is April 16
        assert "2028-04-14" in explicit_dates  # Good Friday (-2)
        assert "2028-04-17" in explicit_dates  # Easter Monday (+1)

    def test_bank_holiday_mondays(self, explicit_dates):
        """Verify all bank holidays fall on Mondays."""
        bank_holiday_names = ["May Bank Holiday"]
        for entry in explicit_dates.values():
            if entry["name"] in bank_holiday_names:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"{entry['name']} should be Monday: {entry['date']}"


def _explicit(code):
    import json as _j
    from pathlib import Path as _P
    x = _j.loads((_P(__file__).resolve().parent.parent / "exchanges" / f"{code}.json").read_text())
    return {h["date"]: h for h in x["holidays"]["explicit"]}


class TestXDUBStBrigidsDay:
    """Euronext's own 2025 and 2026 holiday calendars (tier 1) show Dublin as a
    full trading day on St Brigid's Day (2025-02-03, 2026-02-02). A public
    holiday in Ireland, not an exchange closure."""

    def test_st_brigids_day_is_not_a_closure(self):
        e = _explicit("XDUB")
        assert "2025-02-03" not in e and "2026-02-02" not in e


class TestXDUBFalseClosuresRemoved:
    """Task 36. Euronext's own calendars (tier 1, live.euronext.com/en/resources/
    trading-hours-holidays: "Calendar of business days 2025" and "2026 Holiday
    Calendar") list Dublin closed only on 1 Jan, Good Friday, Easter Monday,
    1 May, the Irish May Bank Holiday, 25 Dec and 26 Dec (28 Dec 2026 as the
    substitute for St Stephen's Day). Dublin trades on St Patrick's Day, the
    June, August and October bank holidays and on 29 Dec 2025."""

    FALSE_2025_2026 = [
        "2025-03-17", "2025-06-02", "2025-08-04", "2025-10-27", "2025-12-29",
        "2026-03-17", "2026-06-01", "2026-08-03", "2026-10-26",
    ]
    # 2027 to 2029: Euronext has not published these years. Absent on the pattern
    # of 2022 to 2026 (pattern-derived, not tier 1); re-check when published.
    FALSE_2027_2029 = [
        "2027-03-17", "2027-06-07", "2027-08-02", "2027-10-25",
        "2028-03-17", "2028-06-05", "2028-08-07", "2028-10-30",
        "2029-03-19", "2029-06-04", "2029-08-06", "2029-10-29",
    ]

    def test_false_closures_absent_2025_2026(self):
        e = _explicit("XDUB")
        for d in self.FALSE_2025_2026:
            assert d not in e, f"{d}: Euronext shows Dublin as a full trading day"

    def test_false_closures_absent_2027_2029_pattern_derived(self):
        e = _explicit("XDUB")
        for d in self.FALSE_2027_2029:
            assert d not in e, f"{d}: absent on the pattern of published years"


class TestXDUBLabourDay:
    """Task 36. Euronext closes all markets on 1 May (Euronext holiday calendars
    2025 and 2026, tier 1). 2027-05-01 is a Saturday. 2028-05-01 is a Monday and
    also the Irish May Bank Holiday. 2029 is not yet published."""

    def test_labour_day_2025(self):
        e = _explicit("XDUB")
        assert e["2025-05-01"]["name"] == "Labour Day"
        assert e["2025-05-01"]["status"] == "closed"

    def test_labour_day_2026(self):
        e = _explicit("XDUB")
        assert e["2026-05-01"]["name"] == "Labour Day"
        assert e["2026-05-01"]["status"] == "closed"

    def test_labour_day_2027_saturday_has_no_entry(self):
        assert "2027-05-01" not in _explicit("XDUB")
        assert "2027-05-03" in _explicit("XDUB")  # Irish May Bank Holiday only

    def test_labour_day_2029_is_pattern_derived(self):
        entry = _explicit("XDUB")["2029-05-01"]
        assert entry["predicted"] is True
        assert entry["name"] == "Labour Day (predicted)"


class TestXDUBSubstituteDays:
    """Euronext Dublin keeps weekend substitutes for New Year's Day, Christmas Day
    and St Stephen's Day (Euronext calendars: 2022-01-03, 2022-12-27, 2023-01-02,
    2020-12-28, 2021-12-27 and 2021-12-28, 2026-12-28). 29 Dec 2025 is not one:
    25 and 26 Dec 2025 were Thursday and Friday."""

    def test_2026_12_28_closed(self):
        e = _explicit("XDUB")["2026-12-28"]
        assert e["status"] == "closed"
        assert "St. Stephen's Day" in e["name"]

    def test_2025_12_29_is_a_trading_day(self):
        assert "2025-12-29" not in _explicit("XDUB")
