#!/usr/bin/env python3
"""
test_iceland_holidays.py — Ground truth tests for XICE (Nasdaq Iceland).

Key facts verified:
    - Regular hours: 09:30-15:30
    - Pre-market: 09:00-09:30, After-hours: 15:30-15:45
    - Maundy Thursday (Easter - 3) is an Icelandic market closure
    - Icelandic National Day (June 17) is a statutory holiday
    - Christmas Eve, Christmas Day, Boxing Day, New Year's Eve are closures
    - Iceland does NOT shift holidays from weekends
    - No lunch break (continuous trading)

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XICE.json)
    2. Icelandic holiday announcements changed (verify against nasdaqomxnordic.com)

Run:
    python3 -m pytest tests/test_iceland_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xice():
    """Load XICE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XICE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xice):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xice["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXICEProperties:
    def test_code(self, xice):
        assert xice["code"] == "XICE"

    def test_mic(self, xice):
        assert xice["mic"] == "XICE"

    def test_name(self, xice):
        assert xice["name"] == "Nasdaq Iceland"

    def test_timezone(self, xice):
        assert xice["timezone"] == "Atlantic/Reykjavik"

    def test_regular_hours(self, xice):
        assert xice["regular_hours"]["open"] == "09:30"
        assert xice["regular_hours"]["close"] == "15:30"

    def test_no_lunch_break(self, xice):
        lunch = [s for s in xice.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xice):
        assert xice["extended_hours"]["pre_market"]["open"] == "09:00"
        assert xice["extended_hours"]["after_hours"]["close"] == "15:45"


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXICEFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_labour_day_2025(self, explicit_dates):
        assert "2025-05-01" in explicit_dates

    def test_national_day_2025(self, explicit_dates):
        assert "2025-06-17" in explicit_dates
        assert "National" in explicit_dates["2025-06-17"]["name"]

    def test_christmas_eve_2025(self, explicit_dates):
        assert "2025-12-24" in explicit_dates

    def test_christmas_2025(self, explicit_dates):
        assert "2025-12-25" in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        assert "2025-12-26" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        assert "2025-12-31" in explicit_dates

    def test_national_day_2026(self, explicit_dates):
        assert "2026-06-17" in explicit_dates

    def test_national_day_2029(self, explicit_dates):
        """Jun 17, 2029 is Sunday — no explicit entry."""
        assert "2029-06-17" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Easter offsets
# ──────────────────────────────────────────────────────────────

class TestXICEEaster:
    def test_maundy_thursday_2025(self, explicit_dates):
        assert "2025-04-17" in explicit_dates
        assert "Maundy" in explicit_dates["2025-04-17"]["name"]

    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_easter_monday_2025(self, explicit_dates):
        assert "2025-04-21" in explicit_dates

    def test_ascension_2025(self, explicit_dates):
        assert "2025-05-29" in explicit_dates

    def test_whit_monday_2025(self, explicit_dates):
        assert "2025-06-09" in explicit_dates

    def test_maundy_thursday_2026(self, explicit_dates):
        assert "2026-04-02" in explicit_dates

    def test_whit_monday_2026(self, explicit_dates):
        assert "2026-05-25" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXICERecurrence:
    def test_fixed_rules_exist(self, xice):
        rules = xice["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Labour Day" in names
        assert "Icelandic National Day" in names
        assert "Christmas Eve" in names
        assert "Christmas Day" in names
        assert "Boxing Day" in names
        assert "New Year's Eve" in names

    def test_easter_rules(self, xice):
        rules = xice["holidays"].get("recurrence_rules", [])
        rule_by_name = {r["name"]: r for r in rules}
        assert rule_by_name["Maundy Thursday"]["rule"] == "easter_offset"
        assert rule_by_name["Maundy Thursday"]["offset_days"] == -3
        assert rule_by_name["Good Friday"]["offset_days"] == -2
        assert rule_by_name["Easter Monday"]["offset_days"] == 1
        assert rule_by_name["Ascension Day"]["offset_days"] == 39
        assert rule_by_name["Whit Monday"]["offset_days"] == 50


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXICEStructure:
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
        """Nasdaq Iceland has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~45-55 entries: 12 holidays × 5 years."""
        assert 40 <= len(explicit_dates) <= 60


# ──────────────────────────────────────────────────────────────
# First Day of Summer and Commerce Day (added v2.15.0)
# ──────────────────────────────────────────────────────────────

class TestXICESummerAndCommerceDay:
    """Both are Icelandic public holidays on which Nasdaq Iceland's settlement
    calendars (Nasdaq CSD Iceland, LuxCSD) are closed. First Day of Summer is the
    first Thursday after 18 April; Commerce Day is the first Monday in August."""

    SUMMER = {"2025": "2025-04-24", "2026": "2026-04-23", "2027": "2027-04-22",
              "2028": "2028-04-20", "2029": "2029-04-19"}
    COMMERCE = {"2025": "2025-08-04", "2026": "2026-08-03", "2027": "2027-08-02",
                "2028": "2028-08-07", "2029": "2029-08-06"}

    @pytest.mark.parametrize("year,d", sorted(SUMMER.items()))
    def test_first_day_of_summer(self, explicit_dates, year, d):
        assert explicit_dates[d]["name"] == "First Day of Summer"
        assert date.fromisoformat(d).weekday() == 3          # Thursday
        assert 19 <= date.fromisoformat(d).day <= 25          # first Thursday after Apr 18

    @pytest.mark.parametrize("year,d", sorted(COMMERCE.items()))
    def test_commerce_day(self, explicit_dates, year, d):
        assert explicit_dates[d]["name"] == "Commerce Day"
        assert date.fromisoformat(d).weekday() == 0          # Monday
        assert date.fromisoformat(d).day <= 7                 # first Monday of August

    def test_four_confirmed_2025_2026_dates(self, explicit_dates):
        """The four closures confirmed by both CSD calendars."""
        for d in ("2025-04-24", "2025-08-04", "2026-04-23", "2026-08-03"):
            assert d in explicit_dates, d

    def test_commerce_day_has_a_rule(self, xice):
        rules = {r["name"]: r for r in xice["holidays"]["recurrence_rules"]}
        r = rules["Commerce Day"]
        assert (r["rule"], r["month"], r["weekday"], r["n"]) == ("nth_weekday", 8, "monday", 1)

    def test_rule_matches_the_entries(self, xice):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from generate_dates import generate_dates_for_rule
        rule = next(r for r in xice["holidays"]["recurrence_rules"] if r["name"] == "Commerce Day")
        for year, d in self.COMMERCE.items():
            assert generate_dates_for_rule(rule, int(year)).isoformat() == d

    def test_earlier_year_pattern(self, xice):
        """2024 (outside the range): Commerce Day was Monday 5 Aug, and the
        first Thursday after 18 April was 25 April."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from generate_dates import generate_dates_for_rule
        rule = next(r for r in xice["holidays"]["recurrence_rules"] if r["name"] == "Commerce Day")
        assert generate_dates_for_rule(rule, 2024) == date(2024, 8, 5)

    def test_built_calendar_has_all_four(self):
        root = Path(__file__).parent.parent
        built = json.loads((root / "calendar.json").read_text())["exchanges"]
        e = next(x for x in built if x["code"] == "XICE")
        have = {h["date"] for k in ("explicit", "generated") for h in e["holidays"][k]}
        assert {"2025-04-24", "2025-08-04", "2026-04-23", "2026-08-03"} <= have
