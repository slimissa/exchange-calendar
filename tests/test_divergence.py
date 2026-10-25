#!/usr/bin/env python3
"""
test_divergence.py — Tests for tools/divergence_test.py.

Checks that the comparison engine:
    1. Treats a known fixed holiday (Jan 1, 2026, XNYS) as closed in the
       registry and in both reference libraries, with no disagreement
    2. Treats early_close days as trading days (half days are not closures)
    3. Records an unsupported exchange as "No reference data" instead of
       crashing, and leaves it out of the vote
    4. Reports a disagreement with which source says what
    5. Does not shift dates by timezone (Christmas Day stays closed)

Run:
    python3 -m pytest tests/test_divergence.py -v
"""

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import divergence_test as dv  # noqa: E402

HAS_PMC = importlib.util.find_spec("pandas_market_calendars") is not None
HAS_XC = importlib.util.find_spec("exchange_calendars") is not None
needs_refs = pytest.mark.skipif(
    not (HAS_PMC and HAS_XC),
    reason="reference libraries are dev-only (requirements-dev.txt)",
)

NEW_YEARS = dt.date(2026, 1, 1)
CHRISTMAS = dt.date(2026, 12, 25)
START, END = dv.year_bounds(2026)


# ---------------------------------------------------------------------------
# Pure comparison logic (no reference libraries needed)
# ---------------------------------------------------------------------------

class TestCompareSources:
    def test_agreement_and_disagreement(self):
        a = {dt.date(2026, 1, 5), dt.date(2026, 1, 6)}
        b = {dt.date(2026, 1, 5)}
        res = dv.compare_sources(
            {"registry": a, "pandas_market_calendars": b},
            dt.date(2026, 1, 5), dt.date(2026, 1, 6),
        )
        assert res["all_agree_trading_days"] == ["2026-01-05"]
        assert len(res["disagreements"]) == 1
        row = res["disagreements"][0]
        assert row["date"] == "2026-01-06"
        assert row["says"] == {"registry": "open", "pandas_market_calendars": "closed"}

    def test_unavailable_source_is_recorded_not_voted(self):
        days = {dt.date(2026, 1, 5)}
        res = dv.compare_sources(
            {"registry": days, "exchange_calendars": "No reference data: nope"},
            dt.date(2026, 1, 5), dt.date(2026, 1, 5),
        )
        assert res["sources_compared"] == ["registry"]
        assert res["total_trading_days"]["exchange_calendars"].startswith(
            "No reference data")
        assert res["disagreements"] == []

    def test_weekend_agreement_is_not_listed_as_closed_weekday(self):
        res = dv.compare_sources(
            {"registry": set(), "pandas_market_calendars": set()},
            dt.date(2026, 1, 3), dt.date(2026, 1, 4),  # Sat, Sun
        )
        assert res["all_agree_closed_weekdays"] == []
        assert res["disagreements"] == []


class TestRegistryLoader:
    def test_jan_1_2026_xnys_is_closed_in_registry(self):
        entry = dv.load_registry_entry("XNYS")
        days = dv.registry_trading_days(entry, START, END)
        assert NEW_YEARS not in days

    def test_early_close_is_a_trading_day(self):
        entry = dv.load_registry_entry("XNYS")
        days = dv.registry_trading_days(entry, START, END)
        thanksgiving_friday = dt.date(2026, 11, 27)
        assert thanksgiving_friday in dv.registry_early_closes(entry)
        assert thanksgiving_friday in days

    def test_weekends_excluded_using_exchange_weekend_days(self):
        entry = dv.load_registry_entry("XNYS")
        days = dv.registry_trading_days(entry, START, END)
        assert all(d.weekday() < 5 for d in days)

    def test_unknown_exchange_raises_keyerror(self):
        with pytest.raises(KeyError):
            dv.load_registry_entry("ZZZZ")


# ---------------------------------------------------------------------------
# Integration with the reference libraries
# ---------------------------------------------------------------------------

@needs_refs
class TestKnownFixedHoliday:
    """Jan 1, 2026 (Thursday): XNYS is closed everywhere."""

    def test_all_three_sources_say_closed(self):
        entry = dv.load_registry_entry("XNYS")
        assert NEW_YEARS not in dv.registry_trading_days(entry, START, END)
        assert NEW_YEARS not in dv.pmc_trading_days("XNYS", START, END)
        assert NEW_YEARS not in dv.xc_trading_days("XNYS", START, END)

    def test_run_exchange_reports_it_as_agreed_closed(self):
        res = dv.run_exchange("XNYS", 2026)
        assert "2026-01-01" in res["all_agree_closed_weekdays"]
        assert "2026-01-01" not in res["all_agree_trading_days"]
        assert all(r["date"] != "2026-01-01" for r in res["disagreements"])

    def test_day_after_is_agreed_trading_day(self):
        res = dv.run_exchange("XNYS", 2026)
        assert "2026-01-02" in res["all_agree_trading_days"]

    def test_christmas_not_shifted_by_timezone(self):
        # A UTC/local offset bug would make a library report Dec 24 or 26
        # instead of Dec 25 (or the reverse); Dec 25 is closed for all.
        for code in ("XNYS", "XLON", "XASX"):
            res = dv.run_exchange(code, 2026)
            assert "2026-12-25" in res["all_agree_closed_weekdays"], code

    def test_no_xnys_disagreement_in_2026(self):
        assert dv.run_exchange("XNYS", 2026)["disagreements"] == []


@needs_refs
class TestMissingReferenceData:
    def test_unsupported_exchange_is_recorded_not_raised(self):
        # Present in the registry, unknown to the reference libraries.
        entry = dv.load_registry_entry("DSMD")
        assert entry["code"] == "DSMD"
        res = dv.run_exchange("DSMD", 2026)
        totals = res["total_trading_days"]
        assert isinstance(totals["registry"], int)
        for lib in ("pandas_market_calendars", "exchange_calendars"):
            assert str(totals[lib]).startswith(dv.NO_REFERENCE_DATA)
        assert res["sources_compared"] == ["registry"]


class TestCli:
    def test_writes_json_report(self, tmp_path):
        out = tmp_path / "divergence.json"
        assert dv.main(["--exchanges", "XNYS", "--year", "2026",
                        "--output", str(out)]) == 0
        report = json.loads(out.read_text())
        assert report["year"] == 2026
        assert "XNYS" in report["exchanges"]
        assert "total_trading_days" in report["exchanges"]["XNYS"]

    def test_unknown_exchange_is_reported_not_fatal(self, tmp_path):
        out = tmp_path / "divergence.json"
        assert dv.main(["--exchanges", "ZZZZ", "--output", str(out)]) == 0
        report = json.loads(out.read_text())
        assert "error" in report["exchanges"]["ZZZZ"]
