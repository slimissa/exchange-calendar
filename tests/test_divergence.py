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
    6. Accepts a single year or an inclusive range, and every exchange ("all")
    7. Records a year outside the registry's generation_range as
       "No registry data" and compares the two libraries alone
    8. Flags exchanges whose PMC calendar is a mirror of exchange_calendars

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


class TestWeekendSkipping:
    SAT = dt.date(2026, 1, 3)
    SUN = dt.date(2026, 1, 4)

    def test_default_skips_saturday_and_sunday_disagreements(self):
        """A library-only weekend session is not a disagreement."""
        res = dv.compare_sources(
            {"registry": set(), "pandas_market_calendars": {self.SAT},
             "exchange_calendars": {self.SAT, self.SUN}},
            self.SAT, self.SUN,
        )
        assert res["disagreements"] == []
        assert res["all_agree_trading_days"] == []

    def test_weekday_disagreement_still_reported(self):
        mon = dt.date(2026, 1, 5)
        res = dv.compare_sources(
            {"registry": {mon}, "pandas_market_calendars": set()}, mon, mon)
        assert len(res["disagreements"]) == 1

    def test_friday_saturday_weekend_compares_sunday_and_skips_friday(self):
        fri, sun = dt.date(2026, 1, 2), dt.date(2026, 1, 4)
        res = dv.compare_sources(
            {"registry": set(), "pandas_market_calendars": {fri, sun}},
            fri, sun, weekend=[4, 5],
        )
        assert [r["date"] for r in res["disagreements"]] == ["2026-01-04"]

    def test_xbom_budget_saturday_is_not_compared(self):
        res = dv.run_exchange("XBOM", 2025)
        assert "2025-02-01" not in [r["date"] for r in res["disagreements"]]

    def test_gulf_sunday_still_compared(self):
        """XSAU trades Sunday-Thursday: Sunday must not be skipped."""
        res = dv.run_exchange("XSAU", 2025)
        assert res["all_agree_trading_days"]
        assert any(d for d in res["all_agree_trading_days"]
                   if dt.date.fromisoformat(d).weekday() == 6)


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


class TestYears:
    def test_single_year(self):
        assert dv.parse_years("2026") == [2026]

    def test_inclusive_range(self):
        assert dv.parse_years("2024-2026") == [2024, 2025, 2026]

    @pytest.mark.parametrize("bad", ["", "abc", "2026-2024", "2024-", "2024-20x6"])
    def test_rejects_bad_input(self, bad):
        with pytest.raises(ValueError):
            dv.parse_years(bad)

    def test_default_covers_2024_to_2026(self):
        assert dv.parse_years(dv.DEFAULT_YEARS) == [2024, 2025, 2026]


class TestRegistryCoverage:
    def test_year_outside_generation_range_has_no_registry_data(self):
        res = dv.run_exchange("XNYS", 2024)
        assert res["total_trading_days"]["registry"].startswith(dv.NO_REGISTRY_DATA)
        assert "registry" in res["sources_unavailable"]
        assert "registry" not in res["sources_compared"]

    def test_year_inside_generation_range_has_registry_data(self):
        res = dv.run_exchange("XNYS", 2025)
        assert isinstance(res["total_trading_days"]["registry"], int)

    def test_registry_covers_uses_generation_range(self):
        entry = {"generation_range": ["2025-01-01", "2029-12-31"]}
        assert dv.registry_covers(entry, dt.date(2025, 1, 1), dt.date(2025, 12, 31))
        assert not dv.registry_covers(entry, dt.date(2024, 1, 1), dt.date(2024, 12, 31))
        assert not dv.registry_covers({}, dt.date(2025, 1, 1), dt.date(2025, 12, 31))

    @needs_refs
    def test_2024_compares_libraries_only(self):
        res = dv.run_exchange("XNYS", 2024)
        assert res["sources_compared"] == ["exchange_calendars",
                                           "pandas_market_calendars"]
        assert res["disagreements"] == []


@needs_refs
class TestMirror:
    def test_mirrored_exchange_is_flagged(self):
        assert dv.pmc_is_mirror("XNYS") is True
        assert dv.run_exchange("XNYS", 2026)["pmc_mirrors_exchange_calendars"] is True

    def test_unknown_exchange_is_none(self):
        assert dv.pmc_is_mirror("DSMD") is None


class TestCli:
    def test_writes_json_report(self, tmp_path):
        out = tmp_path / "divergence.json"
        assert dv.main(["--exchanges", "XNYS", "--year", "2026",
                        "--output", str(out)]) == 0
        report = json.loads(out.read_text())
        assert report["years"] == [2026]
        year = report["exchanges"]["XNYS"]["years"]["2026"]
        assert "total_trading_days" in year

    def test_range_writes_every_year(self, tmp_path):
        out = tmp_path / "divergence.json"
        assert dv.main(["--exchanges", "XNYS,XASX", "--year", "2024-2026",
                        "--output", str(out)]) == 0
        report = json.loads(out.read_text())
        assert report["years"] == [2024, 2025, 2026]
        for code in ("XNYS", "XASX"):
            assert sorted(report["exchanges"][code]["years"]) == ["2024", "2025", "2026"]

    def test_all_means_every_registry_exchange(self, tmp_path, monkeypatch):
        # Stub the per-exchange work: only the code selection is under test.
        monkeypatch.setattr(dv, "run_exchange", lambda code, year, path=None: {
            "sources_unavailable": {}, "summary": {"disagreements": 0}})
        out = tmp_path / "divergence.json"
        assert dv.main(["--exchanges", "all", "--year", "2026",
                        "--output", str(out)]) == 0
        report = json.loads(out.read_text())
        assert sorted(report["exchanges"]) == dv.registry_codes()
        assert len(report["exchanges"]) == 74

    def test_bad_year_exits_nonzero(self, tmp_path, capsys):
        with pytest.raises(SystemExit) as exc:
            dv.main(["--year", "2026-2024", "--output", str(tmp_path / "x.json")])
        assert exc.value.code == 2

    def test_unknown_exchange_is_reported_not_fatal(self, tmp_path):
        out = tmp_path / "divergence.json"
        assert dv.main(["--exchanges", "ZZZZ", "--year", "2026",
                        "--output", str(out)]) == 0
        report = json.loads(out.read_text())
        assert "error" in report["exchanges"]["ZZZZ"]
