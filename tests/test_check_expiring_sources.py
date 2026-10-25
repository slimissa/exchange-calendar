#!/usr/bin/env python3
"""
test_check_expiring_sources.py — Unit tests for check_expiring_sources.py.

Tests that the expiring-sources gate:
    1. Passes when every stated expiry is in the future, and on the expiry
       day itself (the expiry date is still covered)
    2. Fails (exit 1) the day after an expiry, naming the exchange
    3. Treats YYYY-MM as end of month and YYYY as 31 December
    4. Reads "YYYY to YYYY" as coverage through the end of the second year
    5. Ignores dates that are not stated as an expiry (release dates), and
       rows with no date at all ("current year")
    6. Uses the earliest expiry when a cell has several
    7. Exits 2 for: missing file, missing section, missing table, missing
       "Expiry / trigger" column, malformed or invalid dates, a bad --today,
       a short row, and a table in which no row states an expiry
    8. The real docs/FETCHERS.md passes today, fails once the 2027 sources
       expire, and fails for XNYS from 2029-01-01

All tests but the last use a temp FETCHERS.md built with tmp_path.

Run:
    python3 -m pytest tests/test_check_expiring_sources.py -v
"""

import sys
from datetime import date
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_expiring_sources as checker

REAL = Path(__file__).parent.parent / "docs" / "FETCHERS.md"
HEADER = "| Exchange | Source | Expiry / trigger | Action needed |\n|---|---|---|---|\n"


def doc(rows, header=HEADER, heading="## Expiring sources", tail="\n## Next section\n"):
    body = "".join(f"| {r[0]} | src | {r[1]} | do it |\n" for r in rows)
    return f"# Title\n\n{heading}\n\nIntro.\n\n{header}{body}{tail}"


def run(tmp_path, text, today, capsys):
    f = tmp_path / "FETCHERS.md"
    f.write_text(text, encoding="utf-8")
    code = checker.main(["--file", str(f), "--today", today])
    out = capsys.readouterr()
    return code, out.out, out.err


class TestPassAndFail:
    def test_future_date_passes(self, tmp_path, capsys):
        code, out, _ = run(tmp_path, doc([("XAAA", "allowlisted until 2027-06-01")]), "2026-10-25", capsys)
        assert code == 0 and "OK" in out

    def test_expiry_day_still_passes(self, tmp_path, capsys):
        code, _, _ = run(tmp_path, doc([("XAAA", "until 2027-06-01")]), "2027-06-01", capsys)
        assert code == 0

    def test_day_after_fails_and_names_exchange(self, tmp_path, capsys):
        code, out, _ = run(tmp_path, doc([("XAAA", "until 2027-06-01")]), "2027-06-02", capsys)
        assert code == 1
        assert "XAAA" in out and "2027-06-01" in out and "do it" in out

    def test_only_expired_rows_are_reported(self, tmp_path, capsys):
        text = doc([("XOLD", "until 2026-01-01"), ("XNEW", "until 2030-01-01")])
        code, out, _ = run(tmp_path, text, "2026-10-25", capsys)
        assert code == 1 and "XOLD" in out and "XNEW" not in out


class TestDateForms:
    def test_month_is_end_of_month(self, tmp_path, capsys):
        text = doc([("XAAA", "expires 2027-02")])
        assert run(tmp_path, text, "2027-02-28", capsys)[0] == 0
        assert run(tmp_path, text, "2027-03-01", capsys)[0] == 1

    def test_year_is_end_of_year(self, tmp_path, capsys):
        text = doc([("XAAA", "expiry 2028")])
        assert run(tmp_path, text, "2028-12-31", capsys)[0] == 0
        assert run(tmp_path, text, "2029-01-01", capsys)[0] == 1

    def test_range_expires_at_end_of_second_year(self, tmp_path, capsys):
        text = doc([("XAAA", "release covering 2026 to 2028")])
        assert run(tmp_path, text, "2028-12-31", capsys)[0] == 0
        assert run(tmp_path, text, "2029-01-01", capsys)[0] == 1

    def test_earliest_of_several_wins(self, tmp_path, capsys):
        text = doc([("XAAA", "until 2030-01-01 or until 2027-01-01")])
        code, out, _ = run(tmp_path, text, "2027-01-02", capsys)
        assert code == 1 and "2027-01-01" in out

    def test_leap_day(self, tmp_path, capsys):
        text = doc([("XAAA", "until 2028-02")])
        assert run(tmp_path, text, "2028-02-29", capsys)[0] == 0


class TestIgnored:
    def test_release_dates_are_not_expiries(self, tmp_path, capsys):
        text = doc([("XAAA", "releases 2024-11-08 and 2025-12-23, until 2030-01-01")])
        assert run(tmp_path, text, "2026-10-25", capsys)[0] == 0

    def test_undated_row_is_ignored(self, tmp_path, capsys):
        text = doc([("XAAA", "current year"), ("XBBB", "until 2030-01-01")])
        code, out, _ = run(tmp_path, text, "2026-10-25", capsys)
        assert code == 0 and "1 dated row" in out

    def test_keyword_without_date_is_ignored(self, tmp_path, capsys):
        text = doc([("XAAA", "until the next release"), ("XBBB", "until 2030-01-01")])
        assert run(tmp_path, text, "2026-10-25", capsys)[0] == 0

    def test_date_in_other_columns_is_ignored(self, tmp_path, capsys):
        text = doc([("XAAA", "until 2030-01-01")]).replace("| src |", "| until 2020-01-01 |")
        assert run(tmp_path, text, "2026-10-25", capsys)[0] == 0

    def test_section_ends_at_next_heading(self, tmp_path, capsys):
        text = doc([("XAAA", "until 2030-01-01")], tail="\n## Other\n\n| a | b |\n|---|---|\n| until 2020-01-01 | x |\n")
        assert run(tmp_path, text, "2026-10-25", capsys)[0] == 0


class TestExitTwo:
    def test_missing_file(self, tmp_path, capsys):
        code = checker.main(["--file", str(tmp_path / "nope.md"), "--today", "2026-10-25"])
        assert code == 2 and "cannot read" in capsys.readouterr().err

    def test_missing_section(self, tmp_path, capsys):
        code, _, err = run(tmp_path, "# Title\n\nNothing here.\n", "2026-10-25", capsys)
        assert code == 2 and "Expiring sources" in err

    def test_heading_without_table(self, tmp_path, capsys):
        code, _, err = run(tmp_path, "## Expiring sources\n\nJust prose.\n", "2026-10-25", capsys)
        assert code == 2 and "no table" in err

    def test_missing_column(self, tmp_path, capsys):
        header = "| Exchange | Source | Trigger | Action needed |\n|---|---|---|---|\n"
        code, _, err = run(tmp_path, doc([("XAAA", "until 2030-01-01")], header=header), "2026-10-25", capsys)
        assert code == 2 and "expiry / trigger" in err

    @pytest.mark.parametrize("bad", ["until 2027-13-01", "until 2027-02-30", "until 2027/06/01",
                                     "until 2027-6-1", "until 2027-06-01-05", "expires 2027-00"])
    def test_bad_date_format(self, tmp_path, capsys, bad):
        code, _, err = run(tmp_path, doc([("XAAA", bad)]), "2026-10-25", capsys)
        assert code == 2 and "XAAA" in err

    def test_bad_today(self, tmp_path, capsys):
        f = tmp_path / "FETCHERS.md"
        f.write_text(doc([("XAAA", "until 2030-01-01")]), encoding="utf-8")
        assert checker.main(["--file", str(f), "--today", "tomorrow"]) == 2

    def test_short_row(self, tmp_path, capsys):
        text = doc([("XAAA", "until 2030-01-01")]).replace("| do it |\n", "\n")
        text = text.replace("| src | until 2030-01-01 ", "| src ")
        code, _, err = run(tmp_path, text, "2026-10-25", capsys)
        assert code == 2 and "cells" in err

    def test_no_row_states_an_expiry(self, tmp_path, capsys):
        code, _, err = run(tmp_path, doc([("XAAA", "current year")]), "2026-10-25", capsys)
        assert code == 2 and "check nothing" in err


class TestRealFile:
    def test_passes_today(self):
        assert checker.main(["--file", str(REAL), "--today", "2026-10-25"]) == 0

    def test_2027_sources_expire(self, capsys):
        assert checker.main(["--file", str(REAL), "--today", "2027-06-02"]) == 1
        out = capsys.readouterr().out
        for ex in ("XDFM", "XWBO", "XBUD", "XZAG"):
            assert ex in out

    def test_xnys_expires_in_2029(self, capsys):
        assert checker.main(["--file", str(REAL), "--today", "2028-12-31"]) == 1  # others already expired
        out_2028 = capsys.readouterr().out
        assert "XNYS" not in out_2028
        checker.main(["--file", str(REAL), "--today", "2029-01-01"])
        assert "XNYS" in capsys.readouterr().out

    def test_real_table_has_dated_rows(self):
        expired, dated = checker.check(REAL.read_text(encoding="utf-8"), date(2026, 10, 25))
        assert expired == [] and dated >= 8
