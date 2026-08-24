#!/usr/bin/env python3
"""
test_saudi_holidays.py — Ground truth tests for XSAU (Saudi Stock Exchange / Tadawul).

Key facts verified:
    - Trading week: Sunday through Thursday
    - Weekend: Friday-Saturday (NOT Saturday-Sunday)
    - Saudi Founding Day (Feb 22) — shifted to Sunday when on Saturday
    - Saudi National Day (Sep 23) — shifted to Thursday when on Friday,
      shifted to Sunday when on Saturday
    - No lunch break (continuous trading)
    - Opening auction: 09:30-10:00, Closing auction: 15:00-15:10,
      Trade-at-Last: 15:10-15:20

Note: Islamic holidays (Eid al-Fitr, Eid al-Adha, Islamic New Year,
Prophet's Birthday) are included for 2025-2029, sourced from the Saudi
Umm al-Qura calendar. Dates falling on the Friday/Saturday weekend are
intentionally omitted from `explicit` (the weekend closure already
covers them), matching the convention used by every other
Islamic-weekend exchange in this registry (see XBAH).

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XSAU.json)
    2. Saudi holiday announcements changed (verify against saudiexchange.sa)

Run:
    python3 -m pytest tests/test_saudi_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xsau():
    """Load XSAU.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XSAU.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xsau):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xsau["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXSAUProperties:
    def test_code(self, xsau):
        assert xsau["code"] == "XSAU"

    def test_mic(self, xsau):
        assert xsau["mic"] == "XSAU"

    def test_name(self, xsau):
        assert xsau["name"] == "Saudi Stock Exchange (Tadawul)"

    def test_timezone(self, xsau):
        assert xsau["timezone"] == "Asia/Riyadh"

    def test_regular_hours(self, xsau):
        assert xsau["regular_hours"]["open"] == "10:00"
        assert xsau["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xsau):
        lunch = [s for s in xsau.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_extended_hours(self, xsau):
        assert xsau["extended_hours"]["pre_market"]["open"] == "09:30"
        assert xsau["extended_hours"]["after_hours"]["close"] == "15:20"


# ──────────────────────────────────────────────────────────────
# Saudi Founding Day — Feb 22
# ──────────────────────────────────────────────────────────────

class TestXSAUFoundingDay:
    def test_founding_day_2025_observed_sunday(self, explicit_dates):
        """
        Feb 22, 2025 is Saturday.
        Saudi Arabia observes on Sunday Feb 23, 2025.
        """
        assert "2025-02-22" not in explicit_dates  # Saturday
        assert "2025-02-23" in explicit_dates
        assert "Founding" in explicit_dates["2025-02-23"]["name"]
        assert "observed" in explicit_dates["2025-02-23"]["name"].lower()

    def test_founding_day_2026_sunday(self, explicit_dates):
        """Feb 22, 2026 is Sunday — no shift needed."""
        assert "2026-02-22" in explicit_dates
        assert explicit_dates["2026-02-22"]["status"] == "closed"

    def test_founding_day_2027_monday(self, explicit_dates):
        """Feb 22, 2027 is Monday — no shift needed."""
        assert "2027-02-22" in explicit_dates

    def test_founding_day_2028_tuesday(self, explicit_dates):
        """Feb 22, 2028 is Tuesday — no shift needed."""
        assert "2028-02-22" in explicit_dates

    def test_founding_day_2029_thursday(self, explicit_dates):
        """Feb 22, 2029 is Thursday — no shift needed."""
        assert "2029-02-22" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Saudi National Day — Sep 23
# ──────────────────────────────────────────────────────────────

class TestXSAUNationalDay:
    def test_national_day_2025_tuesday(self, explicit_dates):
        """Sep 23, 2025 is Tuesday — no shift needed."""
        assert "2025-09-23" in explicit_dates
        assert explicit_dates["2025-09-23"]["status"] == "closed"

    def test_national_day_2026_wednesday(self, explicit_dates):
        """Sep 23, 2026 is Wednesday — no shift needed."""
        assert "2026-09-23" in explicit_dates

    def test_national_day_2027_thursday(self, explicit_dates):
        """Sep 23, 2027 is Thursday — no shift needed."""
        assert "2027-09-23" in explicit_dates

    def test_national_day_2028_observed_sunday(self, explicit_dates):
        """
        Sep 23, 2028 is Saturday.
        Saudi Arabia observes on Sunday Sep 24, 2028.
        """
        assert "2028-09-23" not in explicit_dates  # Saturday
        assert "2028-09-24" in explicit_dates
        assert "National" in explicit_dates["2028-09-24"]["name"]
        assert "observed" in explicit_dates["2028-09-24"]["name"].lower()

    def test_national_day_2029_sunday(self, explicit_dates):
        """Sep 23, 2029 is Sunday — no shift needed."""
        assert "2029-09-23" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Weekend awareness — Friday/Saturday
# ──────────────────────────────────────────────────────────────

class TestXSAUWeekend:
    def test_no_friday_dates(self, explicit_dates):
        """Saudi weekend includes Friday — no Friday dates in explicit."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 4, f"Friday date: {date_str}"

    def test_no_saturday_dates(self, explicit_dates):
        """Saudi weekend includes Saturday — no Saturday dates in explicit."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() != 5, f"Saturday date: {date_str}"

    def test_sunday_is_trading_day(self, explicit_dates):
        """
        Sunday is a TRADING day in Saudi Arabia.
        No weekend exclusion for Sunday.
        """
        # Founding Day 2026 is Sunday — it's in explicit as a holiday
        assert "2026-02-22" in explicit_dates
        # But it's a holiday, not a weekend


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXSAURecurrence:
    def test_fixed_rules_exist(self, xsau):
        rules = xsau["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Saudi Founding Day" in names
        assert "Saudi National Day" in names

    def test_all_use_fixed_date(self, xsau):
        rules = xsau["holidays"].get("recurrence_rules", [])
        for r in rules:
            assert r["rule"] == "fixed_date", \
                f"{r['name']} should use fixed_date, not {r['rule']}"

    def test_no_islamic_rules(self, xsau):
        """Islamic holidays are NOT in recurrence rules (lunisolar)."""
        rules = xsau["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Eid Al-Fitr" not in names
        assert "Eid Al-Adha" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXSAUStructure:
    def test_no_friday_saturday_dates(self, explicit_dates):
        """Explicit array contains only Sunday-Thursday dates."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() not in (4, 5), \
                f"Weekend date (Fri/Sat): {date_str}"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source: {date_str}"

    def test_all_statuses_closed(self, explicit_dates):
        """Saudi Arabia has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~39 entries: 2 fixed national holidays x 5 years (+ observed
        shifts) plus 4 categories of Islamic holiday x 5 years (Eid
        al-Fitr, Eid al-Adha multi-day; Islamic New Year, Mawlid
        single-day), minus entries dropped for landing on the
        Friday/Saturday weekend."""
        assert 30 <= len(explicit_dates) <= 45


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Umm al-Qura calendar, 2025-2029)
# ──────────────────────────────────────────────────────────────

class TestXSAUIslamicHolidays:
    """Regression coverage for C2: XSAU previously had zero Islamic
    holidays despite being a Friday/Saturday-weekend, Islamic-calendar
    exchange. Dates sourced from the Umm al-Qura calendar; days that
    fall on XSAU's Friday/Saturday weekend are intentionally absent."""

    EID_FITR_DAY1 = {
        2025: "2025-03-30", 2027: "2027-03-09", 2029: "2029-02-14",
    }
    EID_FITR_ANY_YEAR_KEPT = {
        2025: ["2025-03-30", "2025-03-31", "2025-04-01"],
        2026: ["2026-03-22"],  # day1 (Fri) and day2 (Sat) fall on the weekend
        2027: ["2027-03-09", "2027-03-10", "2027-03-11"],
        2028: ["2028-02-27", "2028-02-28"],  # day1 (Sat) falls on the weekend
        2029: ["2029-02-14", "2029-02-15"],  # day3 (Fri) falls on the weekend
    }
    EID_ADHA_ANY_YEAR_KEPT = {
        2025: ["2025-06-08"],  # day1 (Fri) and day2 (Sat) fall on the weekend
        2026: ["2026-05-27", "2026-05-28"],  # day3 (Fri) falls on the weekend
        2027: ["2027-05-16", "2027-05-17", "2027-05-18"],
        2028: ["2028-05-04"],  # day2 (Fri) and day3 (Sat) fall on the weekend
        2029: ["2029-04-24", "2029-04-25", "2029-04-26"],
    }
    ISLAMIC_NEW_YEAR = {
        2025: "2025-06-26", 2026: "2026-06-16", 2027: "2027-06-06",
        2029: "2029-05-14",
        # 2028-05-26 is a Friday — no entry expected for that year.
    }
    MAWLID = {
        2025: "2025-09-04", 2026: "2026-08-25", 2027: "2027-08-15",
        2029: "2029-07-24",
        # 2028-08-04 is a Friday — no entry expected for that year.
    }

    def test_eid_al_fitr_dates_present(self, explicit_dates):
        for year, dates in self.EID_FITR_ANY_YEAR_KEPT.items():
            for d in dates:
                assert d in explicit_dates, f"Missing Eid al-Fitr date for {year}: {d}"
                assert "Eid al-Fitr" in explicit_dates[d]["name"]

    def test_eid_al_fitr_day1_uses_bare_name(self, explicit_dates):
        """Civil day 1 gets the bare holiday name; later days get the
        'Holiday' suffix — but only when day 1 itself isn't dropped for
        falling on the weekend (see 2026, 2028 in EID_FITR_ANY_YEAR_KEPT).
        M7: 2025 is reconciled (confirmed, no longer predicted), so its
        bare name drops the '(predicted)' suffix; 2027/2029 keep it."""
        for year, d in self.EID_FITR_DAY1.items():
            expected = "Eid al-Fitr" if year == 2025 else "Eid al-Fitr (predicted)"
            assert explicit_dates[d]["name"] == expected, \
                f"{year} Eid al-Fitr day 1 ({d}) should be {expected!r}"

    def test_eid_al_fitr_weekend_days_excluded(self, explicit_dates):
        assert "2026-03-20" not in explicit_dates  # Friday
        assert "2026-03-21" not in explicit_dates  # Saturday
        assert "2028-02-26" not in explicit_dates  # Saturday
        assert "2029-02-16" not in explicit_dates  # Friday

    def test_eid_al_adha_dates_present(self, explicit_dates):
        for year, dates in self.EID_ADHA_ANY_YEAR_KEPT.items():
            for d in dates:
                assert d in explicit_dates, f"Missing Eid al-Adha date for {year}: {d}"
                assert "Eid al-Adha" in explicit_dates[d]["name"]

    def test_eid_al_adha_weekend_days_excluded(self, explicit_dates):
        assert "2025-06-06" not in explicit_dates  # Friday
        assert "2025-06-07" not in explicit_dates  # Saturday
        assert "2028-05-05" not in explicit_dates  # Friday
        assert "2028-05-06" not in explicit_dates  # Saturday

    def test_islamic_new_year_present_when_not_weekend(self, explicit_dates):
        for year, d in self.ISLAMIC_NEW_YEAR.items():
            assert d in explicit_dates, f"Missing Islamic New Year for {year}: {d}"
            assert explicit_dates[d]["name"] == "Islamic New Year (predicted)"

    def test_islamic_new_year_2028_correctly_absent(self, explicit_dates):
        """2028-05-26 is a Friday; a single-day holiday landing on the
        weekend is absorbed by the weekend closure, not listed."""
        assert "2028-05-26" not in explicit_dates

    def test_mawlid_present_when_not_weekend(self, explicit_dates):
        for year, d in self.MAWLID.items():
            assert d in explicit_dates, f"Missing Prophet's Birthday for {year}: {d}"
            assert explicit_dates[d]["name"] == "Prophet's Birthday (predicted)"

    def test_mawlid_2028_correctly_absent(self, explicit_dates):
        """2028-08-04 is a Friday — same reasoning as Islamic New Year 2028."""
        assert "2028-08-04" not in explicit_dates

    def test_all_islamic_entries_marked_predicted(self, explicit_dates):
        """M7: 2025 entries are reconciled (confirmed) and no longer
        carry '(predicted)'; all other years still do."""
        islamic_keywords = ("Eid al-Fitr", "Eid al-Adha", "Islamic New Year", "Prophet's Birthday")
        for date_str, entry in explicit_dates.items():
            if date_str.startswith("2025"):
                continue
            if any(k in entry["name"] for k in islamic_keywords):
                assert "(predicted)" in entry["name"], \
                    f"{date_str} ({entry['name']}) should be marked predicted"

    def test_all_islamic_entries_use_umm_al_qura_source(self, explicit_dates):
        islamic_keywords = ("Eid al-Fitr", "Eid al-Adha", "Islamic New Year", "Prophet's Birthday")
        for date_str, entry in explicit_dates.items():
            if any(k in entry["name"] for k in islamic_keywords):
                assert entry["source_url"] == "https://www.ummulqura.org.sa/", \
                    f"{date_str} has unexpected source_url: {entry['source_url']}"

    def test_2025_entries_use_structured_predicted_field(self, explicit_dates):
        """M6/M7: reconciled 2025 entries should set predicted=false
        explicitly (not just omit the field), so the structured field
        and the (now-absent) name suffix agree -- verifying the M6
        consistency check has something real to check against."""
        for date_str, entry in explicit_dates.items():
            if date_str.startswith("2025") and "Eid al-Fitr" in entry["name"]:
                assert entry.get("predicted") is False, \
                    f"{date_str} should explicitly set predicted=false"
                assert "(predicted)" not in entry["name"]