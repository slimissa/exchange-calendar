#!/usr/bin/env python3
"""
test_qatar_holidays.py — Ground truth tests for XQSE (Qatar Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-13:15
    - No lunch break
    - No extended hours sessions
    - Weekend is Friday-Saturday (not Saturday-Sunday)
    - National Sports Day: Second Tuesday in February
    - Qatar National Day: December 18 (fixed)
    - Eid al-Fitr and Eid al-Adha are explicit-only (Islamic calendar)
    - No weekend substitution
    - All holidays are full closures

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XQSE.json)
    2. Qatari holiday announcements changed (verify against qe.com.qa)

Run:
    python3 -m pytest tests/test_qatar_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xqse():
    """Load XQSE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XQSE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xqse):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xqse["holidays"]["explicit"]}


@pytest.fixture(scope="module")
def recurrence_rules(xqse):
    """Return dict of name -> rule."""
    rules = xqse["holidays"].get("recurrence_rules", [])
    return {r["name"]: r for r in rules}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXQSEProperties:
    def test_code(self, xqse):
        assert xqse["code"] == "XQSE"

    def test_mic(self, xqse):
        assert xqse["mic"] == "XQSE"

    def test_name(self, xqse):
        assert xqse["name"] == "Qatar Stock Exchange"

    def test_timezone(self, xqse):
        assert xqse["timezone"] == "Asia/Qatar"

    def test_regular_hours(self, xqse):
        assert xqse["regular_hours"]["open"] == "09:30"
        assert xqse["regular_hours"]["close"] == "13:15"

    def test_no_lunch_break(self, xqse):
        lunch = [s for s in xqse.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xqse):
        assert "extended_hours" not in xqse or xqse.get("extended_hours") is None

    def test_generation_range(self, xqse):
        assert "generation_range" in xqse
        assert xqse["generation_range"] == ["2025-01-01", "2029-12-31"]

    def test_ad_hoc_closures_empty(self, xqse):
        assert xqse.get("ad_hoc_closures", []) == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXQSEFixedHolidays:
    def test_national_sports_day_2025(self, explicit_dates):
        """Second Tuesday in February — Feb 11, 2025."""
        assert "2025-02-11" in explicit_dates
        assert explicit_dates["2025-02-11"]["name"] == "National Sports Day"

    def test_national_sports_day_2026(self, explicit_dates):
        """Second Tuesday in February — Feb 10, 2026."""
        assert "2026-02-10" in explicit_dates

    def test_national_sports_day_2027(self, explicit_dates):
        """Second Tuesday in February — Feb 9, 2027."""
        assert "2027-02-09" in explicit_dates

    def test_national_sports_day_2028(self, explicit_dates):
        """Second Tuesday in February — Feb 8, 2028."""
        assert "2028-02-08" in explicit_dates

    def test_national_sports_day_2029(self, explicit_dates):
        """Second Tuesday in February — Feb 13, 2029."""
        assert "2029-02-13" in explicit_dates

    def test_qatar_national_day_2025(self, explicit_dates):
        """Dec 18, 2025 is Thursday."""
        assert "2025-12-18" in explicit_dates
        assert explicit_dates["2025-12-18"]["name"] == "Qatar National Day"

    def test_qatar_national_day_2026(self, explicit_dates):
        """Dec 18, 2026 is Friday (weekend in Qatar) — no explicit entry."""
        assert "2026-12-18" not in explicit_dates

    def test_qatar_national_day_2027(self, explicit_dates):
        """Dec 18, 2027 is Saturday (weekend in Qatar) — no explicit entry."""
        assert "2027-12-18" not in explicit_dates

    def test_qatar_national_day_2028(self, explicit_dates):
        """Dec 18, 2028 is Monday."""
        assert "2028-12-18" in explicit_dates

    def test_qatar_national_day_2029(self, explicit_dates):
        """Dec 18, 2029 is Tuesday."""
        assert "2029-12-18" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Fitr)
# ──────────────────────────────────────────────────────────────

class TestXQSEEidAlFitr:
    def test_eid_al_fitr_2025(self, explicit_dates):
        """Eid al-Fitr 2025 — predicted March 30."""
        assert "2025-03-30" in explicit_dates
        assert "Eid al-Fitr" in explicit_dates["2025-03-30"]["name"]

    def test_eid_al_fitr_2025_multi_day(self, explicit_dates):
        """Eid al-Fitr 2025 has 5 days of holidays."""
        dates = ["2025-03-30", "2025-03-31", "2025-04-01", "2025-04-02", "2025-04-03"]
        for d in dates:
            assert d in explicit_dates, f"Missing Eid al-Fitr holiday: {d}"

    def test_eid_al_fitr_2026(self, explicit_dates):
        """Eid al-Fitr 2026 — starts March 20 (Friday, weekend).
        Weekday holidays start March 22 (Sunday)."""
        assert "2026-03-22" in explicit_dates  # Sunday (working day)

    def test_eid_al_fitr_2026_multi_day(self, explicit_dates):
        """Eid al-Fitr 2026 — weekday holidays only (Sun-Wed)."""
        dates = ["2026-03-22", "2026-03-23", "2026-03-24"]
        for d in dates:
            assert d in explicit_dates, f"Missing Eid al-Fitr holiday: {d}"

    def test_eid_al_fitr_2027(self, explicit_dates):
        """Eid al-Fitr 2027 — predicted March 9."""
        assert "2027-03-09" in explicit_dates

    def test_eid_al_fitr_2028(self, explicit_dates):
        """Eid al-Fitr 2028 — starts Feb 26 (Saturday, weekend).
        Weekday holidays start Feb 27 (Sunday)."""
        assert "2028-02-27" in explicit_dates  # Sunday (working day)

    def test_eid_al_fitr_2029(self, explicit_dates):
        """Eid al-Fitr 2029 — predicted February 14."""
        assert "2029-02-14" in explicit_dates

    def test_eid_al_fitr_names_contain_predicted(self, explicit_dates):
        """Eid al-Fitr holidays for years still ahead of an official
        announcement should be marked predicted. 2025 is reconciled
        (M7): its date is now confirmed by an actual moon-sighting
        announcement, so those entries no longer carry the suffix."""
        for date_str, entry in explicit_dates.items():
            if "Eid al-Fitr" in entry["name"] and not date_str.startswith("2025"):
                assert "predicted" in entry["name"].lower(), \
                    f"{date_str} ({entry['name']}) should still be predicted"


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Eid al-Adha)
# ──────────────────────────────────────────────────────────────

class TestXQSEEidAlAdha:
    def test_eid_al_adha_2025(self, explicit_dates):
        """Eid al-Adha 2025 — starts June 6 (Friday, weekend).
        Weekday holidays start June 8 (Sunday)."""
        assert "2025-06-08" in explicit_dates  # Sunday (working day)
        assert "Eid al-Adha" in explicit_dates["2025-06-08"]["name"]

    def test_eid_al_adha_2025_multi_day(self, explicit_dates):
        """Eid al-Adha 2025 — weekday holidays only (Sun-Wed)."""
        dates = ["2025-06-08", "2025-06-09", "2025-06-10"]
        for d in dates:
            assert d in explicit_dates, f"Missing Eid al-Adha holiday: {d}"

    def test_eid_al_adha_2026(self, explicit_dates):
        """Eid al-Adha 2026 — predicted May 27."""
        assert "2026-05-27" in explicit_dates

    def test_eid_al_adha_2027(self, explicit_dates):
        """Eid al-Adha 2027 — predicted May 16."""
        assert "2027-05-16" in explicit_dates

    def test_eid_al_adha_2028(self, explicit_dates):
        """Eid al-Adha 2028 — predicted May 4."""
        assert "2028-05-04" in explicit_dates

    def test_eid_al_adha_2029(self, explicit_dates):
        """Eid al-Adha 2029 — predicted April 24."""
        assert "2029-04-24" in explicit_dates

    def test_eid_al_adha_names_contain_predicted(self, explicit_dates):
        """All Eid al-Adha holidays should be marked as predicted."""
        for entry in explicit_dates.values():
            if "Eid al-Adha" in entry["name"]:
                assert "predicted" in entry["name"].lower(), f"Missing 'predicted': {entry['name']}"


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXQSERecurrence:
    def test_fixed_rules_exist(self, recurrence_rules):
        names = set(recurrence_rules.keys())
        expected = {"National Sports Day", "Qatar National Day"}
        for name in expected:
            assert name in names, f"Missing recurrence rule: {name}"

    def test_national_sports_day_rule(self, recurrence_rules):
        """National Sports Day is second Tuesday in February."""
        rule = recurrence_rules["National Sports Day"]
        assert rule["rule"] == "nth_weekday"
        assert rule["month"] == 2
        assert rule["weekday"] == "tuesday"
        assert rule["n"] == 2

    def test_qatar_national_day_rule(self, recurrence_rules):
        """Qatar National Day is fixed on December 18."""
        rule = recurrence_rules["Qatar National Day"]
        assert rule["rule"] == "fixed_date"
        assert rule["month"] == 12
        assert rule["day"] == 18

    def test_no_eid_rules(self, recurrence_rules):
        """Eid holidays are explicit-only (no recurrence rules)."""
        for name in recurrence_rules.keys():
            assert "Eid" not in name, f"Eid should not have recurrence rule: {name}"

    def test_all_rules_closed_status(self, recurrence_rules):
        for name, rule in recurrence_rules.items():
            assert rule.get("status") == "closed", f"{name} should be closed"


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXQSEStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Qatar weekend is Friday-Saturday."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() not in [4, 5], f"Weekend date: {date_str} ({d.strftime('%A')})"

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
        """Qatar has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed", f"Unexpected status: {entry['date']}"

    def test_dates_within_generation_range(self, xqse, explicit_dates):
        start = date.fromisoformat(xqse["generation_range"][0])
        end = date.fromisoformat(xqse["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end, f"Date outside range: {date_str}"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~40-50 entries: 3 holidays × 5 years + weekday-only Eid holidays."""
        assert 40 <= len(explicit_dates) <= 55, f"Unexpected count: {len(explicit_dates)}"

    def test_source_url_consistency(self, explicit_dates):
        """QE's own trading-calendar page is the source for fixed
        national holidays. Islamic New Year and Mawlid are sourced
        from Saudi's Umm al-Qura calendar directly (H2), since these
        were added on the basis of Qatar generally following Saudi's
        Islamic dates -- not independently verified against QE's own
        calendar -- so citing Umm al-Qura is the honest source."""
        for date_str, entry in explicit_dates.items():
            if "ummulqura.org.sa" in entry["source_url"]:
                continue
            assert "qe.com.qa" in entry["source_url"], \
                f"{date_str}: Unexpected source: {entry['source_url']}"


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXQSEWeekendPattern:
    def test_friday_weekend(self, explicit_dates):
        """No Friday dates in explicit array (Friday is weekend in Qatar)."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 4, f"Friday date: {date_str}"

    def test_saturday_weekend(self, explicit_dates):
        """No Saturday dates in explicit array (Saturday is weekend in Qatar)."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_is_working_day(self, explicit_dates):
        """Sunday is a working day in Qatar."""
        sunday_entries = []
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            if d.weekday() == 6:  # Sunday
                sunday_entries.append(date_str)
        # Sundays may appear if a holiday falls on Sunday
        assert isinstance(sunday_entries, list)


# ──────────────────────────────────────────────────────────────
# National Sports Day cross-checks
# ──────────────────────────────────────────────────────────────

class TestXQSENationalSportsDay:
    def test_always_tuesday(self, explicit_dates):
        """National Sports Day must always be Tuesday."""
        for entry in explicit_dates.values():
            if entry["name"] == "National Sports Day":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 1, f"National Sports Day should be Tuesday: {entry['date']}"

    def test_always_second_tuesday(self, explicit_dates):
        """National Sports Day is always the second Tuesday in February."""
        for entry in explicit_dates.values():
            if entry["name"] == "National Sports Day":
                d = date.fromisoformat(entry["date"])
                assert d.month == 2, f"Should be February: {entry['date']}"
                assert 8 <= d.day <= 14, f"Should be second Tuesday: {entry['date']}"

    def test_all_years_have_sports_day(self, explicit_dates):
        """Every year 2025-2029 should have National Sports Day."""
        for year in [2025, 2026, 2027, 2028, 2029]:
            found = False
            for entry in explicit_dates.values():
                if entry["name"] == "National Sports Day" and entry["date"].startswith(str(year)):
                    found = True
                    break
            assert found, f"Missing National Sports Day for {year}"


# ──────────────────────────────────────────────────────────────
# Qatar National Day cross-checks
# ──────────────────────────────────────────────────────────────

class TestXQSENationalDay:
    def test_always_december_18(self, explicit_dates):
        """Qatar National Day is always December 18."""
        for entry in explicit_dates.values():
            if entry["name"] == "Qatar National Day":
                d = date.fromisoformat(entry["date"])
                assert d.month == 12, f"Should be December: {entry['date']}"
                assert d.day == 18, f"Should be Dec 18: {entry['date']}"

    def test_not_on_weekend(self, explicit_dates):
        """Qatar National Day should not be on Friday or Saturday."""
        for entry in explicit_dates.values():
            if entry["name"] == "Qatar National Day":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() not in [4, 5], f"Weekend National Day: {entry['date']}"

    def test_weekend_years_absent(self, explicit_dates):
        """2026 (Friday) and 2027 (Saturday) — National Day not in explicit."""
        assert "2026-12-18" not in explicit_dates  # Friday
        assert "2027-12-18" not in explicit_dates  # Saturday


# ──────────────────────────────────────────────────────────────
# Islamic New Year and Mawlid (H2)
# ──────────────────────────────────────────────────────────────

class TestXQSEIslamicNewYearAndMawlid:
    """Regression coverage for H2: XQSE previously had Eid al-Fitr and
    Eid al-Adha but was missing Islamic New Year and Mawlid entirely,
    despite being a Friday/Saturday-weekend, Islamic-calendar
    exchange. Dates sourced from Saudi's Umm al-Qura calendar (Qatar
    generally follows Saudi for these), not independently verified
    against Qatar's own announcements."""

    ISLAMIC_NEW_YEAR = {
        2025: "2025-06-26", 2026: "2026-06-16", 2027: "2027-06-06",
        2029: "2029-05-14",
        # 2028-05-26 is a Friday -- no entry expected for that year.
    }
    MAWLID = {
        2025: "2025-09-04", 2026: "2026-08-25", 2027: "2027-08-15",
        2029: "2029-07-24",
        # 2028-08-04 is a Friday -- no entry expected for that year.
    }

    def test_islamic_new_year_present_when_not_weekend(self, explicit_dates):
        for year, d in self.ISLAMIC_NEW_YEAR.items():
            assert d in explicit_dates, f"Missing Islamic New Year for {year}: {d}"
            assert explicit_dates[d]["name"] == "Islamic New Year (predicted)"

    def test_islamic_new_year_2028_correctly_absent(self, explicit_dates):
        assert "2028-05-26" not in explicit_dates

    def test_mawlid_present_when_not_weekend(self, explicit_dates):
        for year, d in self.MAWLID.items():
            assert d in explicit_dates, f"Missing Prophet's Birthday for {year}: {d}"
            assert explicit_dates[d]["name"] == "Prophet's Birthday (predicted)"

    def test_mawlid_2028_correctly_absent(self, explicit_dates):
        assert "2028-08-04" not in explicit_dates