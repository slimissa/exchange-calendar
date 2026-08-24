#!/usr/bin/env python3
"""
test_recurrence.py — Unit tests for the recurrence rule engine.

Tests every rule type in generate_dates.py:
    fixed_date
    fixed_with_weekend_adjustment
    nth_weekday
    last_weekday
    easter_offset

Also tests error handling, edge cases, and the expand_exchange integration.

Run:
    python3 -m pytest tests/test_recurrence.py -v
"""

import json
import sys
import pytest
from datetime import date
from pathlib import Path

# Add tools/ to path so we can import generate_dates
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from generate_dates import (
    easter_sunday,
    adjust_weekend,
    nth_weekday,
    last_weekday,
    generate_dates_for_rule,
    expand_exchange,
)


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_exchange():
    """Minimal valid exchange dict for expand_exchange tests."""
    return {
        "code": "TEST",
        "name": "Test Exchange",
        "mic": "TEST",
        "timezone": "UTC",
        "regular_hours": {"open": "09:00", "close": "17:00"},
        "holidays": {
            "explicit": [],
            "recurrence_rules": [
                {
                    "rule": "fixed_date",
                    "month": 1,
                    "day": 1,
                    "name": "New Year's Day",
                    "status": "closed",
                },
                {
                    "rule": "nth_weekday",
                    "month": 9,
                    "weekday": "monday",
                    "n": 1,
                    "name": "Labor Day",
                    "status": "closed",
                },
            ],
        },
        "generation_range": ["2025-01-01", "2027-12-31"],
    }


# ──────────────────────────────────────────────────────────────
# Easter Sunday
# ──────────────────────────────────────────────────────────────

class TestEasterSunday:
    """Oudin algorithm correctness against known dates."""

    @pytest.mark.parametrize("year,expected", [
        (2025, date(2025, 4, 20)),
        (2026, date(2026, 4, 5)),
        (2027, date(2027, 3, 28)),
        (2028, date(2028, 4, 16)),
        (2029, date(2029, 4, 1)),
        (2030, date(2030, 4, 21)),
        (2031, date(2031, 4, 13)),
        (2032, date(2032, 3, 28)),
        (2033, date(2033, 4, 17)),
        (2034, date(2034, 4, 9)),
        (2000, date(2000, 4, 23)),
        (1990, date(1990, 4, 15)),
        (1980, date(1980, 4, 6)),
        (1970, date(1970, 3, 29)),
        (1960, date(1960, 4, 17)),
        (1950, date(1950, 4, 9)),
        (1900, date(1900, 4, 15)),
        (1800, date(1800, 4, 13)),
    ])
    def test_easter_known_dates(self, year, expected):
        assert easter_sunday(year) == expected

    def test_easter_pre_gregorian_rejected(self):
        with pytest.raises(ValueError, match="before 1583"):
            easter_sunday(1500)

    def test_easter_boundary_1583(self):
        # Gregorian calendar adopted 1582; 1583 is first valid year
        result = easter_sunday(1583)
        assert result.year == 1583
        assert result.month in [3, 4]


# ──────────────────────────────────────────────────────────────
# Weekend Adjustment
# ──────────────────────────────────────────────────────────────

class TestWeekendAdjustment:
    def test_fixed_date_no_adjustment_weekday(self):
        # Wednesday July 4, 2029 — no adjustment
        d = date(2029, 7, 4)
        assert adjust_weekend(d, "fixed_date") == d

    def test_fixed_with_adjustment_saturday_to_friday(self):
        # Saturday January 1, 2028 -> Friday December 31, 2027
        d = date(2028, 1, 1)
        result = adjust_weekend(d, "fixed_with_weekend_adjustment")
        assert result == date(2027, 12, 31)

    def test_fixed_with_adjustment_sunday_to_monday(self):
        # Sunday July 4, 2032 -> Monday July 5, 2032
        d = date(2032, 7, 4)
        result = adjust_weekend(d, "fixed_with_weekend_adjustment")
        assert result == date(2032, 7, 5)

    def test_fixed_with_adjustment_weekday_unchanged(self):
        # Wednesday July 4, 2029 — no weekend, no adjustment
        d = date(2029, 7, 4)
        result = adjust_weekend(d, "fixed_with_weekend_adjustment")
        assert result == d

    def test_fixed_date_saturday_no_adjustment(self):
        # fixed_date does not move weekends
        d = date(2028, 1, 1)
        assert adjust_weekend(d, "fixed_date") == d


# ──────────────────────────────────────────────────────────────
# nth_weekday
# ──────────────────────────────────────────────────────────────

class TestNthWeekday:
    def test_first_monday_september_2029(self):
        # Labor Day 2029: Monday September 3
        result = nth_weekday(2029, 9, "monday", 1)
        assert result == date(2029, 9, 3)

    def test_third_monday_january_2027(self):
        # MLK Day 2027: Monday January 18
        result = nth_weekday(2027, 1, "monday", 3)
        assert result == date(2027, 1, 18)

    def test_fourth_thursday_november_2032(self):
        # Thanksgiving 2032: Thursday November 25
        result = nth_weekday(2032, 11, "thursday", 4)
        assert result == date(2032, 11, 25)

    def test_fifth_monday_may_2025(self):
        # May 2025 has 5 Mondays: 5, 12, 19, 26, (no 5th?)
        # May 2025: Mondays are 5, 12, 19, 26 — only 4
        with pytest.raises(ValueError, match="No 5th monday"):
            nth_weekday(2025, 5, "monday", 5)

    def test_invalid_n_zero(self):
        with pytest.raises(ValueError, match="n must be between 1 and 5"):
            nth_weekday(2025, 1, "monday", 0)

    def test_invalid_n_six(self):
        with pytest.raises(ValueError, match="n must be between 1 and 5"):
            nth_weekday(2025, 1, "monday", 6)

    def test_invalid_month_zero(self):
        with pytest.raises(ValueError, match="month must be between 1 and 12"):
            nth_weekday(2025, 0, "monday", 1)

    def test_invalid_month_thirteen(self):
        with pytest.raises(ValueError, match="month must be between 1 and 12"):
            nth_weekday(2025, 13, "monday", 1)

    def test_invalid_weekday(self):
        with pytest.raises(ValueError, match="Invalid weekday"):
            nth_weekday(2025, 1, "funday", 1)

    def test_first_friday_november_2035(self):
        # November 2035: Fridays are 2, 9, 16, 23, 30
        result = nth_weekday(2035, 11, "friday", 1)
        assert result == date(2035, 11, 2)


# ──────────────────────────────────────────────────────────────
# last_weekday
# ──────────────────────────────────────────────────────────────

class TestLastWeekday:
    def test_last_monday_may_2025(self):
        # Memorial Day 2025: Monday May 26
        result = last_weekday(2025, 5, "monday")
        assert result == date(2025, 5, 26)

    def test_last_monday_august_2029(self):
        # Summer Bank Holiday 2029: Monday August 27
        result = last_weekday(2029, 8, "monday")
        assert result == date(2029, 8, 27)

    def test_last_friday_december_2028(self):
        # December 2028: Fridays are 1, 8, 15, 22, 29
        result = last_weekday(2028, 12, "friday")
        assert result == date(2028, 12, 29)

    def test_last_sunday_february_2028_leap(self):
        # February 2028 (leap year): Sundays are 6, 13, 20, 27
        result = last_weekday(2028, 2, "sunday")
        assert result == date(2028, 2, 27)

    def test_last_sunday_february_2027_non_leap(self):
        # February 2027 (non-leap): Sundays are 7, 14, 21, 28
        result = last_weekday(2027, 2, "sunday")
        assert result == date(2027, 2, 28)

    def test_invalid_month(self):
        with pytest.raises(ValueError):
            last_weekday(2025, 13, "monday")

    def test_invalid_weekday(self):
        with pytest.raises(ValueError):
            last_weekday(2025, 1, "notaday")


# ──────────────────────────────────────────────────────────────
# generate_dates_for_rule
# ──────────────────────────────────────────────────────────────

class TestGenerateDatesForRule:
    def test_fixed_date(self):
        rule = {"rule": "fixed_date", "month": 12, "day": 25}
        result = generate_dates_for_rule(rule, 2025)
        assert result == date(2025, 12, 25)

    def test_fixed_with_weekend_adjustment_sunday(self):
        rule = {"rule": "fixed_with_weekend_adjustment", "month": 7, "day": 4}
        result = generate_dates_for_rule(rule, 2032)
        assert result == date(2032, 7, 5)

    def test_nth_weekday(self):
        rule = {"rule": "nth_weekday", "month": 11, "weekday": "thursday", "n": 4}
        result = generate_dates_for_rule(rule, 2026)
        assert result == date(2026, 11, 26)

    def test_last_weekday(self):
        rule = {"rule": "last_weekday", "month": 5, "weekday": "monday"}
        result = generate_dates_for_rule(rule, 2025)
        assert result == date(2025, 5, 26)

    def test_easter_offset_good_friday(self):
        rule = {"rule": "easter_offset", "offset_days": -2}
        result = generate_dates_for_rule(rule, 2025)
        assert result == date(2025, 4, 18)

    def test_easter_offset_easter_monday(self):
        rule = {"rule": "easter_offset", "offset_days": 1}
        result = generate_dates_for_rule(rule, 2025)
        assert result == date(2025, 4, 21)

    def test_missing_rule_type(self):
        rule = {"month": 1, "day": 1}
        with pytest.raises(ValueError, match="missing 'rule'"):
            generate_dates_for_rule(rule, 2025)

    def test_unknown_rule_type(self):
        rule = {"rule": "not_a_rule"}
        with pytest.raises(ValueError, match="Unknown rule type"):
            generate_dates_for_rule(rule, 2025)

    def test_fixed_date_missing_fields(self):
        rule = {"rule": "fixed_date", "month": 1}
        with pytest.raises(ValueError, match="missing month or day"):
            generate_dates_for_rule(rule, 2025)

    def test_nth_weekday_missing_fields(self):
        rule = {"rule": "nth_weekday", "month": 1, "weekday": "monday"}
        with pytest.raises(ValueError, match="missing month, weekday, or n"):
            generate_dates_for_rule(rule, 2025)

    def test_easter_offset_missing_offset(self):
        rule = {"rule": "easter_offset"}
        with pytest.raises(ValueError, match="missing offset_days"):
            generate_dates_for_rule(rule, 2025)


# ──────────────────────────────────────────────────────────────
# expand_exchange
# ──────────────────────────────────────────────────────────────

class TestExpandExchange:
    def test_expands_rules_within_range(self, sample_exchange):
        result = expand_exchange(sample_exchange)
        assert len(result) == 6  # 2 rules × 3 years

    def test_expands_no_duplicates_with_explicit(self, sample_exchange):
        # Add explicit entry that matches a recurrence rule
        sample_exchange["holidays"]["explicit"].append({
            "date": "2025-01-01",
            "name": "New Year's Day",
            "status": "closed",
        })
        result = expand_exchange(sample_exchange)
        # Should skip 2025-01-01 because it's explicit
        dates = [entry["date"] for entry in result]
        assert "2025-01-01" not in dates
        assert len(result) == 5

    def test_respects_year_override(self, sample_exchange):
        result = expand_exchange(sample_exchange, start_year=2026, end_year=2026)
        assert len(result) == 2  # 2 rules × 1 year

    def test_invalid_range_rejected(self, sample_exchange):
        with pytest.raises(ValueError, match="start_year"):
            expand_exchange(sample_exchange, start_year=2030, end_year=2025)

    def test_missing_generation_range(self, sample_exchange):
        del sample_exchange["generation_range"]
        with pytest.raises(ValueError, match="generation_range"):
            expand_exchange(sample_exchange)

    def test_sorted_output(self, sample_exchange):
        result = expand_exchange(sample_exchange)
        dates = [entry["date"] for entry in result]
        assert dates == sorted(dates)

    def test_early_close_time_preserved(self):
        exchange = {
            "code": "TEST",
            "name": "Test Exchange",
            "mic": "TEST",
            "timezone": "UTC",
            "regular_hours": {"open": "09:00", "close": "17:00"},
            "holidays": {
                "explicit": [],
                "recurrence_rules": [
                    {
                        "rule": "fixed_date",
                        "month": 12,
                        "day": 24,
                        "name": "Christmas Eve",
                        "status": "early_close",
                        "early_close_time": "13:00",
                    },
                ],
            },
            "generation_range": ["2025-01-01", "2025-12-31"],
        }
        result = expand_exchange(exchange)
        assert len(result) == 1
        assert result[0]["status"] == "early_close"
        assert result[0]["early_close_time"] == "13:00"

    def test_source_url_propagated(self):
        exchange = {
            "code": "TEST",
            "name": "Test Exchange",
            "mic": "TEST",
            "timezone": "UTC",
            "regular_hours": {"open": "09:00", "close": "17:00"},
            "holidays": {
                "explicit": [],
                "recurrence_rules": [
                    {
                        "rule": "fixed_date",
                        "month": 1,
                        "day": 1,
                        "name": "New Year's Day",
                        "status": "closed",
                        "source_url": "https://example.com/holidays",
                    },
                ],
            },
            "generation_range": ["2025-01-01", "2025-12-31"],
        }
        result = expand_exchange(exchange)
        assert result[0]["source_url"] == "https://example.com/holidays"


# ──────────────────────────────────────────────────────────────
# Edge cases
# ──────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_easter_never_before_march_22(self):
        # Earliest possible Easter is March 22
        for year in range(1583, 2050):
            d = easter_sunday(year)
            assert d >= date(year, 3, 22)

    def test_easter_never_after_april_25(self):
        # Latest possible Easter is April 25
        for year in range(1583, 2050):
            d = easter_sunday(year)
            assert d <= date(year, 4, 25)

    def test_leap_year_february_29(self):
        # February 29, 2028 is a Tuesday
        result = nth_weekday(2028, 2, "tuesday", 5)
        assert result == date(2028, 2, 29)

    def test_non_leap_year_february_max_28(self):
        # February 2027 has 28 days, last Tuesday is Feb 23
        result = last_weekday(2027, 2, "tuesday")
        assert result == date(2027, 2, 23)

    def test_nth_weekday_spanning_month_boundary(self):
        # First Monday of March 2025 is March 3 (not Feb 24)
        result = nth_weekday(2025, 3, "monday", 1)
        assert result == date(2025, 3, 3)