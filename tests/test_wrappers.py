#!/usr/bin/env python3
"""
test_wrappers.py — Tests for the Python wrapper.

Verifies that the Python wrapper correctly:
    1. Loads the registry from calendar.json
    2. Looks up exchanges by MIC code (case-insensitive)
    3. Reports correct session status for known dates/times
    4. Identifies holidays and early closes correctly
    5. Performs date navigation (next/previous trading day)
    6. Handles errors gracefully
    7. Provides Pythonic iteration and membership

Run:
    python3 -m pytest tests/test_wrappers.py -v
"""

import json
import sys
import pytest
from pathlib import Path

# Add wrappers/python to path
WRAPPER_DIR = Path(__file__).parent.parent / "wrappers" / "python"
sys.path.insert(0, str(WRAPPER_DIR))

from exchange_calendar import CalendarRegistry, Exchange, SessionStatus


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def registry():
    """Load the real calendar.json registry."""
    registry_path = Path(__file__).parent.parent / "calendar.json"
    return CalendarRegistry(registry_path)


@pytest.fixture(scope="module")
def xnys(registry):
    """Return the XNYS exchange."""
    return registry.get("XNYS")


@pytest.fixture(scope="module")
def xsau(registry):
    """Return the XSAU exchange (Friday/Saturday weekend)."""
    return registry.get("XSAU")


@pytest.fixture(scope="module")
def xlon(registry):
    """Return the XLON exchange."""
    return registry.get("XLON")


@pytest.fixture(scope="module")
def temp_registry(tmp_path_factory):
    """Create a minimal registry for testing."""
    def _make_registry():
        tmp_dir = tmp_path_factory.mktemp("registry")
        data = {
            "meta": {"version": "1.0.0", "exchange_count": 1},
            "exchanges": [
                {
                    "code": "TEST",
                    "name": "Test Exchange",
                    "mic": "TEST",
                    "timezone": "Europe/London",
                    "regular_hours": {"open": "09:00", "close": "17:00"},
                    "extended_hours": {},
                    "sessions": [],
                    "holidays": {
                        "explicit": [
                            {
                                "date": "2025-01-01",
                                "name": "New Year's Day",
                                "status": "closed",
                            },
                            {
                                "date": "2025-07-03",
                                "name": "Early Close Day",
                                "status": "early_close",
                                "early_close_time": "13:00",
                            },
                        ],
                        "generated": [],
                    },
                    "ad_hoc_closures": [],
                    "generation_range": ["2025-01-01", "2025-12-31"],
                }
            ],
        }
        registry_file = tmp_dir / "calendar.json"
        with open(registry_file, "w") as f:
            json.dump(data, f)
        return CalendarRegistry(registry_file)

    return _make_registry


# ──────────────────────────────────────────────────────────────
# Registry loading
# ──────────────────────────────────────────────────────────────

class TestRegistryLoading:
    def test_load_real_registry(self, registry):
        assert registry.version == "1.0.0"
        assert registry.exchange_count == 74
        assert len(registry) == 74

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            CalendarRegistry("nonexistent.json")

    def test_load_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json")
        with pytest.raises(json.JSONDecodeError):
            CalendarRegistry(bad_file)

    def test_load_invalid_structure(self, tmp_path):
        bad_file = tmp_path / "bad_structure.json"
        bad_file.write_text('{"not_meta": {}}')
        with pytest.raises(ValueError, match="meta"):
            CalendarRegistry(bad_file)

    def test_load_duplicate_codes_rejected(self, tmp_path):
        bad_file = tmp_path / "duplicates.json"
        data = {
            "meta": {"version": "1.0.0", "exchange_count": 2},
            "exchanges": [
                {"code": "DUPE", "name": "First", "mic": "DUPE",
                 "timezone": "Europe/London",
                 "regular_hours": {"open": "09:00", "close": "17:00"},
                 "holidays": {"explicit": [], "generated": []}},
                {"code": "DUPE", "name": "Second", "mic": "DUPE",
                 "timezone": "Europe/London",
                 "regular_hours": {"open": "09:00", "close": "17:00"},
                 "holidays": {"explicit": [], "generated": []}},
            ],
        }
        with open(bad_file, "w") as f:
            json.dump(data, f)
        with pytest.raises(ValueError, match="Duplicate"):
            CalendarRegistry(bad_file)

    def test_registry_string_representation(self, registry):
        s = str(registry)
        assert "Exchange Calendar Registry" in s
        assert "1.0.0" in s
        assert "74" in s

    def test_registry_repr(self, registry):
        r = repr(registry)
        assert "CalendarRegistry" in r
        assert "1.0.0" in r


# ──────────────────────────────────────────────────────────────
# Exchange lookup
# ──────────────────────────────────────────────────────────────

class TestExchangeLookup:
    def test_exchange_by_code(self, registry):
        xnys = registry.exchange("XNYS")
        assert xnys is not None
        assert xnys.code == "XNYS"
        assert xnys.name == "New York Stock Exchange"

    def test_exchange_case_insensitive(self, registry):
        xnys = registry.exchange("xnys")
        assert xnys is not None
        assert xnys.code == "XNYS"

    def test_exchange_not_found_returns_none(self, registry):
        assert registry.exchange("XXXX") is None

    def test_get_raises_keyerror(self, registry):
        with pytest.raises(KeyError, match="XXXX"):
            registry.get("XXXX")

    def test_is_exchange(self, registry):
        assert registry.is_exchange("XNYS") is True
        assert registry.is_exchange("XXXX") is False

    def test_contains(self, registry):
        assert "XNYS" in registry
        assert "XLON" in registry
        assert "XXXX" not in registry

    def test_codes_sorted(self, registry):
        codes = registry.codes()
        assert len(codes) == 74
        assert codes[0] == "XAMS"
        assert codes[-1] == "XZAG"

    def test_names_sorted(self, registry):
        names = registry.names()
        assert len(names) == 74
        assert "London Stock Exchange" in names
        assert "New York Stock Exchange" in names

    def test_list_exchanges_sorted(self, registry):
        exchanges = registry.list_exchanges()
        codes = [e.code for e in exchanges]
        assert len(codes) == 74
        assert codes == sorted(codes)

    def test_iteration(self, registry):
        codes = [e.code for e in registry]
        assert len(codes) == 74
        assert codes[0] == "XAMS"
        assert codes[-1] == "XZAG"

    def test_to_dict(self, registry):
        d = registry.to_dict()
        assert d["version"] == "1.0.0"
        assert d["exchange_count"] == 74
        assert len(d["codes"]) == 74
        assert d["codes"] == sorted(d["codes"])


# ──────────────────────────────────────────────────────────────
# Exchange properties
# ──────────────────────────────────────────────────────────────

class TestExchangeProperties:
    def test_xnys_properties(self, xnys):
        assert xnys.code == "XNYS"
        assert xnys.mic == "XNYS"
        assert xnys.name == "New York Stock Exchange"
        assert xnys.timezone == "America/New_York"
        assert xnys.regular_hours == {"open": "09:30", "close": "16:00"}

    def test_xlon_properties(self, xlon):
        assert xlon.code == "XLON"
        assert xlon.mic == "XLON"
        assert xlon.name == "London Stock Exchange"
        assert xlon.timezone == "Europe/London"
        assert xlon.regular_hours == {"open": "08:00", "close": "16:30"}

    def test_exchange_string_representation(self, xnys):
        s = str(xnys)
        assert "New York Stock Exchange" in s
        assert "XNYS" in s

    def test_exchange_repr(self, xnys):
        r = repr(xnys)
        assert "Exchange" in r
        assert "XNYS" in r

    def test_exchange_has_sessions(self, xlon):
        # XLON has auction sessions
        assert len(xlon.sessions) >= 2


# ──────────────────────────────────────────────────────────────
# Holiday detection
# ──────────────────────────────────────────────────────────────

class TestHolidayDetection:
    def test_xnys_new_years_day_is_holiday(self, xnys):
        assert xnys.is_holiday("2025-01-01") is True

    def test_xnys_weekend_is_holiday(self, xnys):
        assert xnys.is_holiday("2025-03-15") is True  # Saturday
        assert xnys.is_holiday("2025-03-16") is True  # Sunday

    def test_xsau_islamic_weekend(self, xsau):
        """XSAU (Saudi) observes a Friday/Saturday weekend, not Sat/Sun.

        Regression test for the wrapper hardcoding Sat/Sun for every
        exchange regardless of its actual weekend system.
        """
        assert xsau.is_holiday("2025-08-22") is True   # Friday — weekend
        assert xsau.is_holiday("2025-08-23") is True   # Saturday — weekend
        assert xsau.is_holiday("2025-08-24") is False  # Sunday — trading day

    def test_xnys_weekday_not_holiday(self, xnys):
        assert xnys.is_holiday("2025-03-14") is False  # Friday

    def test_xnys_early_close_not_full_holiday(self, xnys):
        assert xnys.is_holiday("2025-07-03") is False  # Early close, not full close

    def test_xlon_boxing_day_is_holiday(self, xlon):
        assert xlon.is_holiday("2025-12-26") is True

    def test_xlon_easter_monday_is_holiday(self, xlon):
        assert xlon.is_holiday("2025-04-21") is True

    def test_holiday_count_xnys(self, xnys):
        count = xnys.holiday_count()
        assert count == 62

    def test_holiday_count_xnys_2025(self, xnys):
        count = xnys.holiday_count(year=2025)
        assert count == 14

    def test_holiday_count_xlon(self, xlon):
        count = xlon.holiday_count()
        assert count > 0

    def test_list_holidays_sorted(self, xnys):
        holidays = xnys.list_holidays()
        dates = [h["date"] for h in holidays]
        assert dates == sorted(dates)

    def test_list_holidays_year_filter(self, xnys):
        holidays = xnys.list_holidays(year=2025)
        assert all(h["date"].startswith("2025-") for h in holidays)


# ──────────────────────────────────────────────────────────────
# Early close detection
# ──────────────────────────────────────────────────────────────

class TestEarlyClose:
    def test_xnys_july_3_is_early_close(self, xnys):
        assert xnys.is_early_close("2025-07-03") is True

    def test_xnys_july_3_time(self, xnys):
        assert xnys.early_close_time("2025-07-03") == "13:00"

    def test_xnys_non_early_close_returns_none(self, xnys):
        assert xnys.early_close_time("2025-07-04") is None

    def test_xlon_christmas_eve_is_early_close(self, xlon):
        assert xlon.is_early_close("2025-12-24") is True

    def test_xlon_christmas_eve_time(self, xlon):
        assert xlon.early_close_time("2025-12-24") == "12:30"

    def test_xlon_new_years_eve_is_early_close(self, xlon):
        assert xlon.is_early_close("2025-12-31") is True

    def test_early_close_times_differ_between_exchanges(self, xnys, xlon):
        assert xnys.early_close_time("2025-07-03") == "13:00"
        assert xlon.early_close_time("2025-12-24") == "12:30"
        assert xnys.early_close_time("2025-07-03") != xlon.early_close_time("2025-12-24")


# ──────────────────────────────────────────────────────────────
# Status at specific date/time
# ──────────────────────────────────────────────────────────────

class TestStatusAt:
    def test_open_during_regular_hours(self, xnys):
        assert xnys.status_at("2025-07-07", "10:00") == SessionStatus.OPEN
        assert xnys.status_at("2025-07-07", "15:00") == SessionStatus.OPEN

    def test_closed_on_weekend(self, xnys):
        assert xnys.status_at("2025-07-05", "10:00") == SessionStatus.CLOSED  # Saturday
        assert xnys.status_at("2025-07-06", "10:00") == SessionStatus.CLOSED  # Sunday

    def test_closed_on_holiday(self, xnys):
        assert xnys.status_at("2025-07-04", "10:00") == SessionStatus.CLOSED

    def test_pre_market(self, xnys):
        assert xnys.status_at("2025-07-07", "08:00") == SessionStatus.PRE_MARKET

    def test_after_hours(self, xnys):
        assert xnys.status_at("2025-07-07", "17:00") == SessionStatus.AFTER_HOURS

    def test_early_close_before_close_time(self, xnys):
        assert xnys.status_at("2025-07-03", "10:00") == SessionStatus.EARLY_CLOSE

    def test_early_close_after_close_time(self, xnys):
        assert xnys.status_at("2025-07-03", "13:30") == SessionStatus.CLOSED

    def test_early_close_exact_close_time(self, xnys):
        assert xnys.status_at("2025-07-03", "13:00") == SessionStatus.CLOSED

    def test_is_open_during_regular_hours(self, xnys):
        assert xnys.is_open("2025-07-07", "10:00") is True

    def test_is_open_during_early_close(self, xnys):
        assert xnys.is_open("2025-07-03", "10:00") is True

    def test_is_open_after_early_close(self, xnys):
        assert xnys.is_open("2025-07-03", "13:30") is False

    def test_is_open_on_holiday(self, xnys):
        assert xnys.is_open("2025-07-04", "10:00") is False

    def test_is_open_on_weekend(self, xnys):
        assert xnys.is_open("2025-07-05", "10:00") is False

    def test_is_open_default_time(self, xnys):
        assert xnys.is_open("2025-07-07") is True  # defaults to 10:00

    def test_xlon_hours(self, xlon):
        assert xlon.status_at("2025-07-07", "08:30") == SessionStatus.OPEN
        assert xlon.status_at("2025-07-07", "07:00") == SessionStatus.PRE_MARKET
        assert xlon.status_at("2025-07-07", "17:00") == SessionStatus.AFTER_HOURS


# ──────────────────────────────────────────────────────────────
# Date navigation
# ──────────────────────────────────────────────────────────────

class TestDateNavigation:
    def test_next_trading_day_after_regular_day(self, xnys):
        assert xnys.next_trading_day("2025-07-07") == "2025-07-08"

    def test_next_trading_day_skips_weekend(self, xnys):
        assert xnys.next_trading_day("2025-07-03") == "2025-07-07"  # Thursday -> Monday

    def test_next_trading_day_skips_holiday(self, xnys):
        assert xnys.next_trading_day("2025-07-03") == "2025-07-07"  # July 4 is Friday

    def test_next_trading_day_early_close_is_trading_day(self, xnys):
        # July 3 is early close but still a trading day
        assert xnys.next_trading_day("2025-07-02") == "2025-07-03"

    def test_previous_trading_day_after_weekend(self, xnys):
        assert xnys.previous_trading_day("2025-07-07") == "2025-07-03"  # Monday -> Thursday

    def test_previous_trading_day_skips_holiday(self, xnys):
        assert xnys.previous_trading_day("2025-07-07") == "2025-07-03"  # July 4 is Friday

    def test_next_trading_day_xlon(self, xlon):
        # LSE Easter: Friday April 18 and Monday April 21 are holidays
        assert xlon.next_trading_day("2025-04-17") == "2025-04-22"

    def test_previous_trading_day_xlon(self, xlon):
        assert xlon.previous_trading_day("2025-04-22") == "2025-04-17"


# ──────────────────────────────────────────────────────────────
# Error handling
# ──────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_invalid_date_format(self, xnys):
        with pytest.raises(ValueError, match="date"):
            xnys.is_holiday("2025/01/01")

    def test_invalid_time_format(self, xnys):
        with pytest.raises(ValueError, match="time"):
            xnys.status_at("2025-07-07", "10am")

    def test_invalid_time_hours(self, xnys):
        with pytest.raises(ValueError, match="time"):
            xnys.status_at("2025-07-07", "25:00")

    def test_invalid_time_minutes(self, xnys):
        with pytest.raises(ValueError, match="time"):
            xnys.status_at("2025-07-07", "10:60")

    def test_unknown_status_string(self):
        with pytest.raises(ValueError, match="Unknown session status"):
            SessionStatus.from_string("not_a_status")

    def test_status_from_string_case_insensitive(self):
        assert SessionStatus.from_string("OPEN") == SessionStatus.OPEN
        assert SessionStatus.from_string("open") == SessionStatus.OPEN
        assert SessionStatus.from_string("Open") == SessionStatus.OPEN
        assert SessionStatus.from_string(" early_close ") == SessionStatus.EARLY_CLOSE

    def test_status_from_string_non_string(self):
        with pytest.raises(TypeError):
            SessionStatus.from_string(123)


# ──────────────────────────────────────────────────────────────
# SessionStatus enum
# ──────────────────────────────────────────────────────────────

class TestSessionStatus:
    def test_all_statuses_exist(self):
        assert SessionStatus.CLOSED.value == "closed"
        assert SessionStatus.PRE_MARKET.value == "pre_market"
        assert SessionStatus.OPEN.value == "open"
        assert SessionStatus.EARLY_CLOSE.value == "early_close"
        assert SessionStatus.AFTER_HOURS.value == "after_hours"
        assert SessionStatus.LUNCH_BREAK.value == "lunch_break"

    def test_is_trading_status(self):
        assert SessionStatus.is_trading_status(SessionStatus.OPEN) is True
        assert SessionStatus.is_trading_status(SessionStatus.EARLY_CLOSE) is True
        assert SessionStatus.is_trading_status(SessionStatus.CLOSED) is False
        assert SessionStatus.is_trading_status(SessionStatus.PRE_MARKET) is False
        assert SessionStatus.is_trading_status(SessionStatus.AFTER_HOURS) is False
        assert SessionStatus.is_trading_status(SessionStatus.LUNCH_BREAK) is False

    def test_str_method(self):
        assert str(SessionStatus.OPEN) == "open"
        assert str(SessionStatus.EARLY_CLOSE) == "early_close"
        assert str(SessionStatus.CLOSED) == "closed"

    def test_repr_method(self):
        assert repr(SessionStatus.OPEN) == "SessionStatus.OPEN"
        assert repr(SessionStatus.CLOSED) == "SessionStatus.CLOSED"


# ──────────────────────────────────────────────────────────────
# Minimal custom registry
# ──────────────────────────────────────────────────────────────

class TestMinimalRegistry:
    def test_minimal_registry_loads(self, temp_registry):
        registry = temp_registry()
        assert registry.exchange_count == 1
        assert len(registry) == 1

    def test_minimal_registry_exchange(self, temp_registry):
        registry = temp_registry()
        test = registry.get("TEST")
        assert test.code == "TEST"
        assert test.name == "Test Exchange"

    def test_minimal_registry_holiday(self, temp_registry):
        registry = temp_registry()
        test = registry.get("TEST")
        assert test.is_holiday("2025-01-01") is True
        assert test.is_holiday("2025-01-02") is False

    def test_minimal_registry_early_close(self, temp_registry):
        registry = temp_registry()
        test = registry.get("TEST")
        assert test.is_early_close("2025-07-03") is True
        assert test.early_close_time("2025-07-03") == "13:00"
        assert test.status_at("2025-07-03", "10:00") == SessionStatus.EARLY_CLOSE
        assert test.status_at("2025-07-03", "13:30") == SessionStatus.CLOSED