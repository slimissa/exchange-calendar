#!/usr/bin/env python3
"""
test_dubai_holidays.py — Ground truth tests for XDFM (Dubai Financial Market).

Key facts verified:
    - Trading week: Monday-Friday (since January 2022)
    - Weekend: Saturday-Sunday
    - No after-hours trading session
    - Closing auction at 14:50, Trade-at-Last 14:55-15:00
    - Commemoration Day (Dec 1) is a statutory holiday
    - UAE National Day (Dec 2-3) is a statutory holiday
    - No weekend shift for fixed holidays

Note: Islamic holidays (Eid al-Fitr, Eid al-Adha, Islamic New Year,
Prophet's Birthday) are included for 2025-2029, sourced from the Saudi
Umm al-Qura calendar. XDFM observes a Saturday/Sunday weekend (since
January 2022), so the weekend-exclusion pattern differs from
Friday/Saturday-weekend exchanges like XSAU/XBAH: Friday dates are
trading days here and ARE included, while Saturday/Sunday dates are
excluded. These are computed dates, not DFM-announced ones — DFM's own
real holiday calendar (see XTAD for comparison) sometimes extends
Islamic holidays by extra government-announced bonus days beyond the
base Umm al-Qura dates, which this data does not attempt to model.

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XDFM.json)
    2. UAE holiday announcements changed (verify against dfm.ae)

Run:
    python3 -m pytest tests/test_dubai_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xdfm():
    """Load XDFM.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XDFM.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xdfm):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xdfm["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXDFMProperties:
    def test_code(self, xdfm):
        assert xdfm["code"] == "XDFM"

    def test_mic(self, xdfm):
        assert xdfm["mic"] == "XDFM"

    def test_name(self, xdfm):
        assert xdfm["name"] == "Dubai Financial Market"

    def test_timezone(self, xdfm):
        assert xdfm["timezone"] == "Asia/Dubai"

    def test_regular_hours(self, xdfm):
        assert xdfm["regular_hours"]["open"] == "10:00"
        assert xdfm["regular_hours"]["close"] == "15:00"

    def test_no_lunch_break(self, xdfm):
        lunch = [s for s in xdfm.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []

    def test_no_after_hours(self, xdfm):
        """DFM has no after-hours session."""
        assert "after_hours" not in xdfm["extended_hours"]

    def test_closing_auction(self, xdfm):
        auctions = [s for s in xdfm.get("sessions", []) if s["type"] == "auction"]
        assert len(auctions) == 1
        assert auctions[0]["at"] == "14:50"


# ──────────────────────────────────────────────────────────────
# Fixed national holidays
# ──────────────────────────────────────────────────────────────

class TestXDFMFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    def test_new_year_2026(self, explicit_dates):
        assert "2026-01-01" in explicit_dates

    def test_new_year_2027(self, explicit_dates):
        assert "2027-01-01" in explicit_dates

    def test_commemoration_day_2025(self, explicit_dates):
        """Dec 1, 2025 is Monday — explicit."""
        assert "2025-12-01" in explicit_dates
        assert "Commemoration" in explicit_dates["2025-12-01"]["name"]

    def test_national_day_2025(self, explicit_dates):
        """Dec 2-3, 2025 — explicit."""
        assert "2025-12-02" in explicit_dates
        assert "National" in explicit_dates["2025-12-02"]["name"]
        assert "2025-12-03" in explicit_dates

    def test_commemoration_day_2026(self, explicit_dates):
        assert "2026-12-01" in explicit_dates

    def test_national_day_2026(self, explicit_dates):
        assert "2026-12-02" in explicit_dates
        assert "2026-12-03" in explicit_dates

    def test_commemoration_day_2027(self, explicit_dates):
        assert "2027-12-01" in explicit_dates

    def test_national_day_2027(self, explicit_dates):
        assert "2027-12-02" in explicit_dates
        assert "2027-12-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Weekend awareness (Saturday-Sunday)
# ──────────────────────────────────────────────────────────────

class TestXDFMWeekend:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_no_national_day_2028_sunday(self, explicit_dates):
        """Dec 2, 2028 is Sunday — no explicit entry."""
        assert "2028-12-02" not in explicit_dates

    def test_no_national_day_2029_sunday(self, explicit_dates):
        """Dec 2, 2029 is Sunday — no explicit entry."""
        assert "2029-12-02" not in explicit_dates

    def test_no_commemoration_2028_saturday(self, explicit_dates):
        """Dec 1, 2028 is Saturday — no explicit entry."""
        assert "2028-12-01" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Recurrence rules
# ──────────────────────────────────────────────────────────────

class TestXDFMRecurrence:
    def test_fixed_rules_exist(self, xdfm):
        rules = xdfm["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "New Year's Day" in names
        assert "Commemoration Day" in names
        assert "UAE National Day" in names
        assert "UAE National Day Holiday" in names

    def test_no_islamic_rules(self, xdfm):
        """Islamic holidays are NOT in recurrence rules (lunisolar)."""
        rules = xdfm["holidays"].get("recurrence_rules", [])
        names = {r["name"] for r in rules}
        assert "Eid" not in names
        assert "Prophet" not in names
        assert "Islamic New Year" not in names


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXDFMStructure:
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
        """DFM has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_holiday_count_reasonable(self, explicit_dates):
        """~43 entries: 4 fixed national holidays x ~3.25 years avg
        (+ observed shifts) plus 4 categories of Islamic holiday x 5
        years, minus entries dropped for landing on the Saturday/Sunday
        weekend."""
        assert 35 <= len(explicit_dates) <= 50


# ──────────────────────────────────────────────────────────────
# Islamic holidays (Umm al-Qura calendar, 2025-2029)
# ──────────────────────────────────────────────────────────────

class TestXDFMIslamicHolidays:
    """Regression coverage for C3: XDFM previously had zero Islamic
    holidays despite being an Islamic-calendar exchange. Unlike XSAU
    (Friday/Saturday weekend), XDFM observes a Saturday/Sunday weekend,
    so Friday dates are trading days here and ARE expected, while
    Saturday/Sunday dates are excluded — the opposite pattern from C2."""

    EID_FITR_DAY1 = {
        2026: "2026-03-20", 2027: "2027-03-09", 2029: "2029-02-14",
    }
    EID_FITR_ANY_YEAR_KEPT = {
        2025: ["2025-03-31", "2025-04-01"],  # day1 (Sun) falls on the weekend
        2026: ["2026-03-20"],  # day1 (Fri) is a trading day here, unlike XSAU
        2027: ["2027-03-09", "2027-03-10", "2027-03-11"],
        2028: ["2028-02-28"],  # day1 (Sat), day2 (Sun) fall on the weekend
        2029: ["2029-02-14", "2029-02-15", "2029-02-16"],
    }
    EID_ADHA_ANY_YEAR_KEPT = {
        2025: ["2025-06-06"],  # day1 (Fri) is a trading day here
        2026: ["2026-05-27", "2026-05-28", "2026-05-29"],
        2027: ["2027-05-17", "2027-05-18"],  # day1 (Sun) falls on the weekend
        2028: ["2028-05-04", "2028-05-05"],  # day3 (Sat) falls on the weekend
        2029: ["2029-04-24", "2029-04-25", "2029-04-26"],
    }
    ISLAMIC_NEW_YEAR = {
        2025: "2025-06-26", 2026: "2026-06-16",
        2028: "2028-05-26", 2029: "2029-05-14",
        # 2027-06-06 is a Sunday — no entry expected for that year.
    }
    MAWLID = {
        2025: "2025-09-04", 2026: "2026-08-25",
        2028: "2028-08-04", 2029: "2029-07-24",
        # 2027-08-15 is a Sunday — no entry expected for that year.
    }

    def test_eid_al_fitr_dates_present(self, explicit_dates):
        for year, dates in self.EID_FITR_ANY_YEAR_KEPT.items():
            for d in dates:
                assert d in explicit_dates, f"Missing Eid al-Fitr date for {year}: {d}"
                assert "Eid al-Fitr" in explicit_dates[d]["name"]

    def test_eid_al_fitr_day1_uses_bare_name(self, explicit_dates):
        for year, d in self.EID_FITR_DAY1.items():
            assert explicit_dates[d]["name"] == "Eid al-Fitr (predicted)", \
                f"{year} Eid al-Fitr day 1 ({d}) should use the bare name"

    def test_eid_al_fitr_friday_included_unlike_xsau(self, explicit_dates):
        """XDFM's Sat/Sun weekend means Friday is a trading day here,
        unlike XSAU's Fri/Sat weekend where the same date is excluded."""
        assert "2026-03-20" in explicit_dates  # Friday, day 1, bare name
        assert "2025-06-06" in explicit_dates  # Friday, Eid al-Adha day 1

    def test_eid_al_fitr_weekend_days_excluded(self, explicit_dates):
        assert "2025-03-30" not in explicit_dates  # Sunday
        assert "2026-03-21" not in explicit_dates  # Saturday
        assert "2026-03-22" not in explicit_dates  # Sunday
        assert "2028-02-26" not in explicit_dates  # Saturday
        assert "2028-02-27" not in explicit_dates  # Sunday

    def test_eid_al_adha_dates_present(self, explicit_dates):
        for year, dates in self.EID_ADHA_ANY_YEAR_KEPT.items():
            for d in dates:
                assert d in explicit_dates, f"Missing Eid al-Adha date for {year}: {d}"
                assert "Eid al-Adha" in explicit_dates[d]["name"]

    def test_eid_al_adha_weekend_days_excluded(self, explicit_dates):
        assert "2025-06-07" not in explicit_dates  # Saturday
        assert "2025-06-08" not in explicit_dates  # Sunday
        assert "2027-05-16" not in explicit_dates  # Sunday
        assert "2028-05-06" not in explicit_dates  # Saturday

    def test_islamic_new_year_present_when_not_weekend(self, explicit_dates):
        for year, d in self.ISLAMIC_NEW_YEAR.items():
            assert d in explicit_dates, f"Missing Islamic New Year for {year}: {d}"
            assert explicit_dates[d]["name"] == "Islamic New Year (predicted)"

    def test_islamic_new_year_2027_correctly_absent(self, explicit_dates):
        """2027-06-06 is a Sunday for XDFM's Sat/Sun weekend."""
        assert "2027-06-06" not in explicit_dates

    def test_mawlid_present_when_not_weekend(self, explicit_dates):
        for year, d in self.MAWLID.items():
            assert d in explicit_dates, f"Missing Prophet's Birthday for {year}: {d}"
            assert explicit_dates[d]["name"] == "Prophet's Birthday (predicted)"

    def test_mawlid_2027_correctly_absent(self, explicit_dates):
        """2027-08-15 is a Sunday — same reasoning as Islamic New Year 2027."""
        assert "2027-08-15" not in explicit_dates

    def test_all_islamic_entries_marked_predicted(self, explicit_dates):
        islamic_keywords = ("Eid al-Fitr", "Eid al-Adha", "Islamic New Year", "Prophet's Birthday")
        for date_str, entry in explicit_dates.items():
            if any(k in entry["name"] for k in islamic_keywords):
                assert "(predicted)" in entry["name"], \
                    f"{date_str} ({entry['name']}) should be marked predicted"

    def test_islamic_dates_differ_from_xsau_set(self, explicit_dates):
        """Sanity check that XDFM's weekend-filtered date set is not
        just a copy of XSAU's (they use different weekend systems, so
        different dates should survive filtering)."""
        with open("exchanges/XSAU.json") as f:
            import json
            xsau = json.load(f)
        xsau_islamic_dates = {
            h["date"] for h in xsau["holidays"]["explicit"]
            if "predicted" in h["name"]
        }
        xdfm_islamic_dates = {
            d for d, e in explicit_dates.items() if "predicted" in e["name"]
        }
        assert xsau_islamic_dates != xdfm_islamic_dates