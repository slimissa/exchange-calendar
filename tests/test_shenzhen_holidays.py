#!/usr/bin/env python3
"""
test_shenzhen_holidays.py — Ground truth tests for XSHE (Shenzhen Stock Exchange).

Key facts verified:
    - Regular hours: 09:30-15:00 (09:30-11:30 morning, 13:00-15:00 afternoon)
    - Lunch break: 11:30-13:00 (a lunch_break session inside regular hours)
    - Weekend is Saturday-Sunday (Western weekend)
    - Spring Festival (7 days)
    - Qingming Festival
    - Labour Day (3 days)
    - Dragon Boat Festival
    - Mid-Autumn Festival
    - National Day Golden Week (7 days)
    - No recurrence rules — all dates explicit

If any test fails, either:
    1. The registry data is wrong (fix exchanges/XSHE.json)
    2. Chinese holiday announcements changed (verify against szse.cn)

Run:
    python3 -m pytest tests/test_shenzhen_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def xshe():
    """Load XSHE.json once for all tests."""
    path = Path(__file__).parent.parent / "exchanges" / "XSHE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xshe):
    """Return dict of date -> entry."""
    return {e["date"]: e for e in xshe["holidays"]["explicit"]}


# ──────────────────────────────────────────────────────────────
# Properties
# ──────────────────────────────────────────────────────────────

class TestXSHEProperties:
    def test_code(self, xshe):
        assert xshe["code"] == "XSHE"

    def test_mic(self, xshe):
        assert xshe["mic"] == "XSHE"

    def test_name(self, xshe):
        assert xshe["name"] == "Shenzhen Stock Exchange"

    def test_timezone(self, xshe):
        assert xshe["timezone"] == "Asia/Shanghai"

    def test_regular_hours(self, xshe):
        assert xshe["regular_hours"]["open"] == "09:30"
        # 15:00, not 11:30: the lunch break is a separate session (4c-R1).
        assert xshe["regular_hours"]["close"] == "15:00"
        regular = [s for s in xshe["sessions"] if s["type"] == "regular"]
        assert regular == [{"type": "regular", "open": "09:30", "close": "15:00"}]

    def test_lunch_break(self, xshe):
        lunch = [s for s in xshe.get("sessions", []) if s.get("type") == "lunch_break"]
        assert len(lunch) == 1
        assert lunch[0]["open"] == "11:30"
        assert lunch[0]["close"] == "13:00"

    def test_no_extended_hours(self, xshe):
        assert "extended_hours" not in xshe or xshe.get("extended_hours") is None

    def test_generation_range(self, xshe):
        assert "generation_range" in xshe
        # Shortened from 2029-12-31 per C4: XSHE's data only covers
        # through 2027 (Spring Festival etc. aren't rule-generatable).
        # The start moved to 2010 with the backfill inferred from XSHG
        # (exchange_calendars has no XSHE); the end stays at 2027.
        assert xshe["generation_range"] == ["2010-01-01", "2027-12-31"]

    def test_ad_hoc_closures_empty(self, xshe):
        assert xshe.get("ad_hoc_closures", []) == []

    def test_no_recurrence_rules(self, xshe):
        """China uses explicit dates only."""
        rules = xshe["holidays"].get("recurrence_rules", [])
        assert rules == []


# ──────────────────────────────────────────────────────────────
# New Year's Day
# ──────────────────────────────────────────────────────────────

class TestXSHENewYear:
    def test_new_year_2025(self, explicit_dates):
        """Jan 1, 2025 is Wednesday."""
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["name"] == "New Year's Day"

    def test_new_year_2026(self, explicit_dates):
        """Jan 1, 2026 is Thursday."""
        assert "2026-01-01" in explicit_dates

    def test_new_year_2027(self, explicit_dates):
        """Jan 1, 2027 is Friday."""
        assert "2027-01-01" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Spring Festival (7 days)
# ──────────────────────────────────────────────────────────────

class TestXSHESpringFestival:
    def test_spring_festival_2025(self, explicit_dates):
        """Spring Festival 2025 — Jan 28-Feb 4 (7 weekdays)."""
        dates = ["2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",
                 "2025-02-03", "2025-02-04"]
        for d in dates:
            assert d in explicit_dates, f"Missing Spring Festival: {d}"

    def test_spring_festival_2026(self, explicit_dates):
        """Spring Festival 2026 — Feb 16-23 (6 weekdays)."""
        dates = ["2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19",
                 "2026-02-20", "2026-02-23"]
        for d in dates:
            assert d in explicit_dates, f"Missing Spring Festival: {d}"

    def test_spring_festival_2027(self, explicit_dates):
        """Spring Festival 2027 — Feb 5-12 (6 weekdays)."""
        dates = ["2027-02-05", "2027-02-08", "2027-02-09", "2027-02-10",
                 "2027-02-11", "2027-02-12"]
        for d in dates:
            assert d in explicit_dates, f"Missing Spring Festival: {d}"

    def test_spring_festival_names(self, explicit_dates):
        for entry in explicit_dates.values():
            if "Spring Festival" in entry["name"]:
                assert entry["status"] == "closed"


# ──────────────────────────────────────────────────────────────
# Qingming Festival
# ──────────────────────────────────────────────────────────────

class TestXSHEQingming:
    def test_qingming_2025(self, explicit_dates):
        """Qingming 2025 — April 4."""
        assert "2025-04-04" in explicit_dates
        assert "Qingming" in explicit_dates["2025-04-04"]["name"]

    def test_qingming_2026(self, explicit_dates):
        """Qingming 2026 — April 6."""
        assert "2026-04-06" in explicit_dates

    def test_qingming_2027(self, explicit_dates):
        """Qingming 2027 — April 5."""
        assert "2027-04-05" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Labour Day (3 days)
# ──────────────────────────────────────────────────────────────

class TestXSHELabourDay:
    def test_labour_day_2025(self, explicit_dates):
        """Labour Day 2025 — May 1-5 (3 weekdays)."""
        dates = ["2025-05-01", "2025-05-02", "2025-05-05"]
        for d in dates:
            assert d in explicit_dates, f"Missing Labour Day: {d}"

    def test_labour_day_2026(self, explicit_dates):
        """Labour Day 2026 — May 1-5 (3 weekdays)."""
        dates = ["2026-05-01", "2026-05-04", "2026-05-05"]
        for d in dates:
            assert d in explicit_dates, f"Missing Labour Day: {d}"

    def test_labour_day_2027(self, explicit_dates):
        """Labour Day 2027 — May 3-5."""
        dates = ["2027-05-03", "2027-05-04", "2027-05-05"]
        for d in dates:
            assert d in explicit_dates, f"Missing Labour Day: {d}"


# ──────────────────────────────────────────────────────────────
# Dragon Boat Festival
# ──────────────────────────────────────────────────────────────

class TestXSHEDragonBoat:
    def test_dragon_boat_2025(self, explicit_dates):
        """Dragon Boat 2025 — June 2."""
        assert "2025-06-02" in explicit_dates
        assert "Dragon Boat" in explicit_dates["2025-06-02"]["name"]

    def test_dragon_boat_2026(self, explicit_dates):
        """Dragon Boat 2026 — June 19."""
        assert "2026-06-19" in explicit_dates

    def test_dragon_boat_2027(self, explicit_dates):
        """Dragon Boat 2027 — June 9."""
        assert "2027-06-09" in explicit_dates


# ──────────────────────────────────────────────────────────────
# Mid-Autumn Festival
# ──────────────────────────────────────────────────────────────

class TestXSHEMidAutumn:
    def test_mid_autumn_2026(self, explicit_dates):
        """Mid-Autumn 2026 — September 25."""
        assert "2026-09-25" in explicit_dates
        assert "Mid-Autumn" in explicit_dates["2026-09-25"]["name"]

    def test_mid_autumn_2027(self, explicit_dates):
        """Mid-Autumn 2027 — September 15."""
        assert "2027-09-15" in explicit_dates


# ──────────────────────────────────────────────────────────────
# National Day Golden Week (7 days)
# ──────────────────────────────────────────────────────────────

class TestXSHENationalDay:
    def test_national_day_2025(self, explicit_dates):
        """National Day 2025 — Oct 1-8 (7 weekdays)."""
        dates = ["2025-10-01", "2025-10-02", "2025-10-03", "2025-10-06",
                 "2025-10-07", "2025-10-08"]
        for d in dates:
            assert d in explicit_dates, f"Missing National Day: {d}"

    def test_national_day_2026(self, explicit_dates):
        """National Day 2026 — Oct 1-7 (5 weekdays); SZSE resumes trading Oct 8."""
        dates = ["2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06",
                 "2026-10-07"]
        for d in dates:
            assert d in explicit_dates, f"Missing National Day: {d}"
        assert "2026-10-08" not in explicit_dates

    def test_national_day_2027(self, explicit_dates):
        """National Day 2027 — Oct 1-7 (5 weekdays) per the State Council notice;
        Oct 8 (Fri) trades, Oct 9 (Sat) is a make-up working day."""
        dates = ["2027-10-01", "2027-10-04", "2027-10-05", "2027-10-06",
                 "2027-10-07"]
        for d in dates:
            assert d in explicit_dates, f"Missing National Day: {d}"
        assert "2027-10-08" not in explicit_dates

    def test_new_year_2026_is_two_days(self, explicit_dates):
        """SZSE 2026: closed Jan 1-2, resumes Jan 5."""
        assert "2026-01-01" in explicit_dates
        assert "2026-01-02" in explicit_dates

    def test_matches_xshg_2010_2027(self, explicit_dates):
        """Both mainland exchanges close on the same State Council holidays."""
        import json
        from pathlib import Path
        xshg = json.loads((Path(__file__).parent.parent / "exchanges" / "XSHG.json").read_text())
        g = {h["date"] for h in xshg["holidays"]["explicit"] if h["date"] < "2028-01-01"}
        e = {d for d in explicit_dates if d < "2028-01-01"}
        assert g == e


# ──────────────────────────────────────────────────────────────
# Structural checks
# ──────────────────────────────────────────────────────────────

class TestXSHEStructure:
    def test_no_weekend_dates(self, explicit_dates):
        """China weekend is Saturday-Sunday."""
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str} ({d.strftime('%A')})"

    def test_no_duplicate_dates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates)), "Duplicate dates found"

    def test_all_entries_have_source(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "source_url" in entry, f"Missing source_url: {date_str}"
            if date_str >= "2025-01-01":
                assert entry["source_url"].startswith("http")
            else:
                # 2010-2024 is inferred from XSHG, not read from an exchange page.
                assert entry["source_url"] == "inferred from XSHG"

    def test_all_entries_have_name(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "name" in entry, f"Missing name: {date_str}"
            assert entry["name"], f"Empty name: {date_str}"

    def test_all_entries_have_status(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            assert "status" in entry, f"Missing status: {date_str}"
            assert entry["status"] in ["closed", "early_close"]

    def test_all_statuses_closed(self, explicit_dates):
        """China has no early closes — all holidays are full closures."""
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"

    def test_dates_within_generation_range(self, xshe, explicit_dates):
        start = date.fromisoformat(xshe["generation_range"][0])
        end = date.fromisoformat(xshe["generation_range"][1])
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert start <= d <= end

    def test_holiday_count_reasonable(self, explicit_dates):
        """~50-60 entries in 2025-2027 (2010-2024 is the inferred backfill)."""
        window = [d for d in explicit_dates if d >= "2025-01-01"]
        assert 50 <= len(window) <= 65, f"Unexpected count: {len(window)}"

    def test_source_url_consistency(self, explicit_dates):
        for date_str, entry in explicit_dates.items():
            if "2025-01-01" <= date_str < "2027-01-01":
                assert "szse.cn" in entry["source_url"], date_str
            elif date_str >= "2027-01-01":  # State Council 2027 notice
                assert "xinhuanet.com" in entry["source_url"], date_str

    def test_backfill_is_labelled_as_inferred(self, explicit_dates):
        """2010-2024 is copied from XSHG's closures, and says so."""
        backfill = [e for d, e in explicit_dates.items() if d < "2025-01-01"]
        assert backfill, "no backfilled entries"
        assert all(e["name"] == "Historical Holiday" for e in backfill)
        assert all(e["source_url"] == "inferred from XSHG" for e in backfill)


# ──────────────────────────────────────────────────────────────
# Weekend pattern checks
# ──────────────────────────────────────────────────────────────

class TestXSHEWeekendPattern:
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

class TestXSHESubstitution:
    def test_weekend_holidays_absent(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5, f"Weekend date: {date_str}"

    def test_multi_day_holidays(self, explicit_dates):
        """China has multiple multi-day holidays."""
        spring_festival = sum(1 for e in explicit_dates.values() if "Spring Festival" in e["name"])
        national_day = sum(1 for e in explicit_dates.values() if "National Day" in e["name"])
        assert spring_festival >= 18, f"Expected many Spring Festival days, got {spring_festival}"
        # 2025: 6 weekdays (Oct 1-8); 2026 and 2027: 5 each (Oct 1-7).
        assert national_day >= 16, f"Expected many National Day days, got {national_day}"