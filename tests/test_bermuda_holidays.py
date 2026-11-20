#!/usr/bin/env python3
"""
test_bermuda_holidays.py — Ground truth tests for XBDA (Bermuda Stock Exchange).

Key facts verified:
    - Regular hours: 10:00-16:00 (single session)
    - No lunch break
    - Weekend is Saturday-Sunday (Western weekend)
    - Bermuda Day (last Friday in May)
    - National Heroes' Day (third Monday in June)
    - Cup Match (Thursday-Friday before first Monday in August)
    - Labour Day (first Monday in September)
    - Remembrance Day (Nov 11) with substitution
    - Christmas Eve (Dec 24) — early close at 14:00 (BSX festive notices
      2024 and 2025; corrected in 4c11, was 13:00)
    - New Year's Eve (Dec 31) — a normal day (same notices; the 13:00 early
      closes were removed in 4c11)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XBDA.json)
    2. Bermudian holiday announcements changed (verify against bsx.com)

Run:
    python3 -m pytest tests/test_bermuda_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xbda():
    """Load XBDA.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XBDA.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xbda):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xbda["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXBDAProperties:
    def test_code(self, xbda):
        assert xbda["code"] == "XBDA"

    def test_mic(self, xbda):
        assert xbda["mic"] == "XBDA"

    def test_name(self, xbda):
        assert xbda["name"] == "Bermuda Stock Exchange"

    def test_timezone(self, xbda):
        assert xbda["timezone"] == "Atlantic/Bermuda"

    def test_regular_hours(self, xbda):
        """4c11: BSX's trading page, 'Trading Hours are Monday through Friday
        9:00 a.m. - 4:30 p.m.' (was 10:00-16:00); continuous trading, no
        closing auction, so ADR 0013 gives 16:30. One dated entry,
        2010-01-01 unconfirmed."""
        assert xbda["regular_hours"] == [
            {"close": "16:30", "effective_from": "2010-01-01", "open": "09:00"}]
        assert xbda["sessions"] == [{"close": "16:30", "open": "09:00", "type": "regular"}]
        assert "2010-01-01" in xbda["verification"]["coverage"]["sources"][0]["unconfirmed"]

    def test_no_lunch_break(self, xbda):
        lunch = [s for s in xbda.get("sessions", []) if s.get("type") == "lunch_break"]
        assert lunch == []

    def test_no_extended_hours(self, xbda):
        assert "extended_hours" not in xbda or xbda.get("extended_hours") is None

    def test_generation_range(self, xbda):
        assert "generation_range" in xbda
        assert xbda["generation_range"] == ["2010-01-01", "2029-12-31"]  # 4c11 backfill

    def test_ad_hoc_closures(self, xbda):
        """4c11: four exchange_calendars one-offs (unconfirmed) and two BSX
        notices: Hurricane Fiona (closed) and Hurricane Imelda (early close)."""
        assert [(c["date"], c["status"], c.get("early_close_time")) for c in xbda["ad_hoc_closures"]] == [
            ("2019-11-04", "closed", None), ("2021-10-18", "closed", None),
            ("2022-09-19", "closed", None), ("2022-09-23", "closed", None),
            ("2023-05-08", "closed", None), ("2025-10-01", "early_close", "13:00")]
        by_date = {c["date"]: c["source_url"] for c in xbda["ad_hoc_closures"]}
        assert by_date["2022-09-23"] == "https://www.bsx.com/article/1100801631"
        assert by_date["2025-10-01"] == "https://www.bsx.com/article/1100805973"

    def test_no_recurrence_rules(self, xbda):
        """Bermuda uses explicit dates only."""
        rules = xbda["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# Fixed holidays
# ──────────────────────────────────────────────────────────────

class TestXBDAFixedHolidays:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2028_substitute(self, explicit_dates):
        """Jan 1, 2028 is Saturday — substitute to Monday Jan 3."""
        assert "2028-01-01" not in explicit_dates
        assert "2028-01-03" in explicit_dates

    def test_remembrance_day_2025(self, explicit_dates):
        """Nov 11, 2025 is Tuesday."""
        assert "2025-11-11" in explicit_dates
        assert "Remembrance" in explicit_dates["2025-11-11"]["name"]

    def test_remembrance_day_2028_substitute(self, explicit_dates):
        """Nov 11, 2028 is Saturday — substitute to Monday Nov 13."""
        assert "2028-11-11" not in explicit_dates
        assert "2028-11-13" in explicit_dates

    def test_remembrance_day_2029_substitute(self, explicit_dates):
        """Nov 11, 2029 is Sunday — substitute to Monday Nov 12."""
        assert "2029-11-12" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Bermuda Day (last Friday in May)
# ──────────────────────────────────────────────────────────────

class TestXBDABermudaDay:
    def test_bermuda_day_2025(self, explicit_dates):
        """Last Friday in May — May 23, 2025."""
        assert "2025-05-23" in explicit_dates
        assert explicit_dates["2025-05-23"]["name"] == "Bermuda Day"

    def test_bermuda_day_2026(self, explicit_dates):
        """Last Friday in May — May 22, 2026."""
        assert "2026-05-22" in explicit_dates

    def test_bermuda_day_2027(self, explicit_dates):
        """Last Friday in May — May 28, 2027."""
        assert "2027-05-28" in explicit_dates

    def test_bermuda_day_2028(self, explicit_dates):
        """Last Friday in May — May 26, 2028."""
        assert "2028-05-26" in explicit_dates

    def test_bermuda_day_2029(self, explicit_dates):
        """Last Friday in May — May 25, 2029."""
        assert "2029-05-25" in explicit_dates

    def test_bermuda_day_always_friday(self, explicit_dates):
        """Bermuda Day is a Friday from 2018 (the 2010-2024 backfill, 4c11,
        holds the earlier 24 May rule; see the next test)."""
        for entry in explicit_dates.values():
            if entry["name"] == "Bermuda Day" and entry["date"] >= "2018":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 4, f"Bermuda Day should be Friday: {entry['date']}"

    def test_bermuda_day_2010_2017_is_24_may_or_the_next_monday(self, explicit_dates):
        """4c11 backfill (exchange_calendars): before 2018, 24 May, moved to
        the Monday after when it fell on a weekend."""
        days = sorted(d for d, e in explicit_dates.items()
                      if e["name"] == "Bermuda Day" and d < "2018")
        assert days == ["2010-05-24", "2011-05-24", "2012-05-24", "2013-05-24",
                        "2014-05-26", "2015-05-25", "2016-05-24", "2017-05-24"]


# ──────────────────────────────────────────────────────────────
# National Heroes' Day (third Monday in June)
# ──────────────────────────────────────────────────────────────

class TestXBDANationalHeroes:
    def test_heroes_day_2025(self, explicit_dates):
        """Third Monday in June — June 16, 2025."""
        assert "2025-06-16" in explicit_dates
        assert "Heroes" in explicit_dates["2025-06-16"]["name"]

    def test_heroes_day_2026(self, explicit_dates):
        """Third Monday in June — June 15, 2026."""
        assert "2026-06-15" in explicit_dates

    def test_heroes_day_2027(self, explicit_dates):
        """Third Monday in June — June 21, 2027."""
        assert "2027-06-21" in explicit_dates

    def test_heroes_day_2028(self, explicit_dates):
        """Third Monday in June — June 19, 2028."""
        assert "2028-06-19" in explicit_dates

    def test_heroes_day_2029(self, explicit_dates):
        """Third Monday in June — June 18, 2029."""
        assert "2029-06-18" in explicit_dates

    def test_heroes_day_always_monday(self, explicit_dates):
        """National Heroes' Day must always be Monday."""
        for entry in explicit_dates.values():
            if "Heroes" in entry["name"]:
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"Heroes' Day should be Monday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Cup Match (Thursday-Friday before first Monday in August)
# ──────────────────────────────────────────────────────────────

class TestXBDACupMatch:
    def test_cup_match_2025(self, explicit_dates):
        """Cup Match 2025 — Jul 31-Aug 1."""
        assert "2025-07-31" in explicit_dates
        assert "Cup Match" in explicit_dates["2025-07-31"]["name"]
        assert "2025-08-01" in explicit_dates

    def test_cup_match_2026(self, explicit_dates):
        """Cup Match 2026 — Jul 30-31."""
        assert "2026-07-30" in explicit_dates
        assert "2026-07-31" in explicit_dates

    def test_cup_match_2027(self, explicit_dates):
        """Cup Match 2027 — Jul 29-30."""
        assert "2027-07-29" in explicit_dates
        assert "2027-07-30" in explicit_dates

    def test_cup_match_2028(self, explicit_dates):
        """Cup Match 2028 — Aug 3-4: the Thursday and Friday before the first
        Monday in August (7 August 2028; 1 August is a Tuesday)."""
        assert "2028-08-03" in explicit_dates
        assert "2028-08-04" in explicit_dates
        assert "2028-07-27" not in explicit_dates
        assert "2028-07-28" not in explicit_dates

    def test_cup_match_2029(self, explicit_dates):
        """Cup Match 2029 — Aug 2-3."""
        assert "2029-08-02" in explicit_dates
        assert "2029-08-03" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Labour Day (first Monday in September)
# ──────────────────────────────────────────────────────────────

class TestXBDALabourDay:
    def test_labour_day_2025(self, explicit_dates):
        """First Monday in September — Sep 1, 2025."""
        assert "2025-09-01" in explicit_dates
        assert explicit_dates["2025-09-01"]["name"] == "Labour Day"

    def test_labour_day_2026(self, explicit_dates):
        """First Monday in September — Sep 7, 2026."""
        assert "2026-09-07" in explicit_dates

    def test_labour_day_2027(self, explicit_dates):
        """First Monday in September — Sep 6, 2027."""
        assert "2027-09-06" in explicit_dates

    def test_labour_day_2028(self, explicit_dates):
        """First Monday in September — Sep 4, 2028."""
        assert "2028-09-04" in explicit_dates

    def test_labour_day_2029(self, explicit_dates):
        """First Monday in September — Sep 3, 2029."""
        assert "2029-09-03" in explicit_dates

    def test_labour_day_always_monday(self, explicit_dates):
        """Labour Day must always be Monday."""
        for entry in explicit_dates.values():
            if entry["name"] == "Labour Day":
                d = date.fromisoformat(entry["date"])
                assert d.weekday() == 0, f"Labour Day should be Monday: {entry['date']}"


# ──────────────────────────────────────────────────────────────
# Good Friday (movable)
# ──────────────────────────────────────────────────────────────

class TestXBDAGoodFriday:
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


# ──────────────────────────────────────────────────────────────
# Christmas holidays
# ──────────────────────────────────────────────────────────────

class TestXBDAChristmas:
    def test_christmas_eve_2025(self, explicit_dates):
        """4c11: BSX's 2025/2026 festive notice, 'Christmas Eve - Early
        Closure, 9:00am - 2:00pm' (the registry had 13:00)."""
        entry = explicit_dates.get("2025-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "14:00"
        assert entry["source_url"] == (
            "https://www.bsx.com/bermuda-stock-exchange-20252026-festive-holiday-closure-notice")

    def test_christmas_eve_2026(self, explicit_dates, xbda):
        """Dec 24, 2026 is Thursday: predicted early close at 14:00 (the 2024
        and 2025 pattern), unconfirmed until the 2026 festive notice."""
        entry = explicit_dates.get("2026-12-24")
        assert entry is not None
        assert entry["status"] == "early_close"
        assert entry["early_close_time"] == "14:00"
        assert entry["predicted"] is True
        span = xbda["verification"]["coverage"]["sources"][1]
        assert "2026-12-24" in span["unconfirmed"] and span["recheck_date"] == "2026-12-22"

    def test_christmas_day_2025(self, explicit_dates):
        """Dec 25, 2025 is Thursday."""
        assert "2025-12-25" in explicit_dates
        assert explicit_dates["2025-12-25"]["name"] == "Christmas Day"

    def test_christmas_day_2027_substitute(self, explicit_dates):
        """Dec 25, 2027 is Saturday — substitute to Monday Dec 27."""
        assert "2027-12-25" not in explicit_dates
        assert "2027-12-27" in explicit_dates

    def test_boxing_day_2025(self, explicit_dates):
        """Dec 26, 2025 is Friday."""
        assert "2025-12-26" in explicit_dates
        assert explicit_dates["2025-12-26"]["name"] == "Boxing Day"

    def test_boxing_day_2026_substitute(self, explicit_dates):
        """Dec 26, 2026 is Saturday — substitute to Monday Dec 28."""
        assert "2026-12-26" not in explicit_dates
        assert "2026-12-28" in explicit_dates

    def test_new_years_eve_2025(self, explicit_dates):
        """4c11: BSX's 2025/2026 festive notice gives Wednesday 31 December
        2025 normal operating hours, so it is a full trading day (the
        registry had an early close at 13:00)."""
        assert "2025-12-31" not in explicit_dates

    def test_new_years_eve_2029(self, explicit_dates):
        """Dec 31, 2029 is Monday: a normal day on the 2024 and 2025 pattern."""
        assert "2029-12-31" not in explicit_dates


# ──────────────────────────────────────────────────────────────
# Early close days
# ──────────────────────────────────────────────────────────────

class TestXBDAEarlyCloses:
    def test_no_other_early_closes(self, explicit_dates):
        """Scoped to 2025-2029: only Christmas Eve is an early close (4c11)."""
        early = sorted(d for d, e in explicit_dates.items()
                       if e.get("status") == "early_close" and d >= "2025")
        assert early == ["2025-12-24", "2026-12-24", "2027-12-24", "2029-12-24"]
        assert {explicit_dates[d]["name"] for d in early} == {
            "Christmas Eve", "Christmas Eve (predicted)"}

    def test_all_early_closes_have_early_close_time(self, explicit_dates):
        """All early closes are at 14:00: BSX's festive notices for 2025-2029,
        exchange_calendars' Christmas Eve early close for the backfill."""
        early = {d: e for d, e in explicit_dates.items() if e.get("status") == "early_close"}
        assert len([d for d in early if d < "2025"]) == 15
        assert {e["early_close_time"] for e in early.values()} == {"14:00"}

    def test_delayed_opens_on_bsx_notices(self, explicit_dates, xbda):
        """4c11: two one-off delayed opens, in explicit (ad_hoc_closures has no
        delayed-open status): 9 January 2025 (Carter, from 09:30) and
        2 October 2025 (Hurricane Imelda, from 12:15, unconfirmed)."""
        delayed = {d: e["delayed_open_time"] for d, e in explicit_dates.items()
                   if e["status"] == "delayed_open"}
        assert delayed == {"2025-01-09": "09:30", "2025-10-02": "12:15"}
        assert {"2025-10-01", "2025-10-02"} <= set(xbda["verification"]["coverage"]["sources"][1]["unconfirmed"])

    def test_closed_entries_no_early_close_time(self, explicit_dates):
        for entry in explicit_dates.values():
            if entry.get("status") == "closed":
                assert "early_close_time" not in entry


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXBDAStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """Bermuda weekend is Saturday-Sunday."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str} ({d.strftime('%A')})"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates)), "Duplicate dates found"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"
            if date_str < "2025":  # 4c11 backfill cites exchange_calendars
                assert entry["source_url"] == "github.com/gerrymanoim/exchange_calendars"
                continue
            assert entry["source_url"].startswith("http")

    def test_all_entries_have_name(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "name" in entry, f"Missing name: {date_str}"
            assert entry["name"], f"Empty name: {date_str}"

    def test_all_entries_have_status(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "status" in entry, f"Missing status: {date_str}"
            assert entry["status"] in ["closed", "early_close", "delayed_open"]

    def test_dates_within_generation_range(self, xbda, explicit_dates):
        start = date.fromisoformat(xbda["generation_range"][0])
        end = date.fromisoformat(xbda["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """Scoped to 2025-2029: 58 before 4c11, less the four 31 December
        early closes (2025, 2026, 2027, 2029), plus the two 2025 delayed opens
        = 56. 2010-2024 backfill: 142 closures + 15 early closes = 157."""
        assert len([d for d in explicit_dates if d >= "2025"]) == 56
        assert len([d for d in explicit_dates if d < "2025"]) == 157

    def test_source_url_consistency(self, explicit_dates):
        for d, entry in explicit_dates.items():
            if d < "2025":
                continue  # 4c11 backfill cites exchange_calendars
            assert "bsx.com" in entry["source_url"]


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXBDAWeekendPattern:
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

class TestXBDASubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        assert "2028-01-01" not in explicit_dates  # Saturday
        assert "2027-12-25" not in explicit_dates  # Saturday

    def test_substitute_names_contain_substitute(self, explicit_dates):
        for entry in explicit_dates.values():
            name = entry["name"].lower()
            if "substitute" in name:
                assert "substitute" in name