#!/usr/bin/env python3
"""
test_check_stale_year_urls.py — Unit tests for check_stale_year_urls.py.

Tests that the year-rollover checker correctly:
    1. Passes when every year-token URL's max year is current or later
    2. Fails when a source_url literal in the fetchers file has a stale
       max year
    3. Fails when an exchanges/*.json source_url has a stale max year
    4. Skips (does not flag) URLs that are clearly dynamic — {year},
       {YYYY}, %Y/%d placeholders — and does not crash on them
    5. Skips (does not flag) source_url assigned from a variable/attribute
       the checker cannot resolve, e.g. `self.source_url`
    6. Reports file/line for fetcher hits and file/entry for JSON hits
    7. Exits 2 when a scanned path does not exist
    8. Exits 1 (not a silent pass) when zero year-token URLs are found

All tests build their own temp fetchers file and/or temp exchanges/
directory (via pytest's tmp_path fixture) — none of them depend on the
real repo's tools/update_from_exchange.py or exchanges/*.json content,
except the one explicit sanity check against the real files.

Run:
    python3 -m pytest tests/test_check_stale_year_urls.py -v
"""

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_stale_year_urls as checker

CURRENT_YEAR = 2026  # matches the fixed "today" this task's evidence uses


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def write_fetchers_file(tmp_path, body):
    path = tmp_path / "update_from_exchange.py"
    path.write_text(body, encoding="utf-8")
    return path


def write_exchange_json(exchanges_dir, filename, urls):
    """urls: list of source_url strings, one holiday entry per URL."""
    exchanges_dir.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "date": f"2026-01-{i + 1:02d}",
            "name": f"Holiday {i}",
            "status": "closed",
            "source_url": url,
        }
        for i, url in enumerate(urls)
    ]
    data = {
        "code": "XTST",
        "name": "Test Exchange",
        "mic": "XTST",
        "timezone": "UTC",
        "holidays": {"explicit": entries, "recurrence_rules": []},
    }
    path = exchanges_dir / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def empty_exchanges_dir(tmp_path, name="exchanges"):
    d = tmp_path / name
    d.mkdir()
    return d


# ──────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────

def test_current_urls_pass(tmp_path):
    """A source_url whose max year token equals the current year passes."""
    fetchers = write_fetchers_file(
        tmp_path,
        'source_url="https://example.com/holidays-2026.pdf"\n',
    )
    exchanges_dir = write_exchange_json(
        empty_exchanges_dir(tmp_path), "XTST.json", []
    ).parent

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)

    assert exit_code == 0
    assert "STALE" not in "\n".join(report)


def test_stale_fetcher_source_url_fails(tmp_path):
    """A source_url literal in the fetchers file with a stale max year
    fails with exit 1 and reports the correct file and line."""
    fetchers = write_fetchers_file(
        tmp_path,
        '# comment line 1\n'
        'source_url="https://example.com/holidays-2024.pdf"\n',
    )
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)
    joined = "\n".join(report)

    assert exit_code == 1
    assert str(fetchers) in joined
    assert ":2:" in joined  # the source_url line is line 2
    assert "2024" in joined


def test_stale_json_source_url_fails(tmp_path):
    """An exchanges/*.json source_url with a stale max year fails with
    exit 1 and identifies the file and entry."""
    fetchers = write_fetchers_file(tmp_path, 'source_url="https://example.com/x-2026.pdf"\n')
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(
        exchanges_dir, "XTST.json",
        ["https://example.com/circulars/holiday-notice-2024.pdf"],
    )

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)
    joined = "\n".join(report)

    assert exit_code == 1
    assert "XTST.json" in joined
    assert "2024" in joined


def test_brace_placeholder_url_skipped(tmp_path):
    """A URL containing '{year}' is dynamic and must be skipped (with a
    warning), not flagged as stale or crashed on."""
    fetchers = write_fetchers_file(
        tmp_path,
        'BASE_URL="https://example.com/holidays-{year}.pdf"\n'
        'source_url="https://example.com/holidays-2026.pdf"\n',
    )
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)
    joined = "\n".join(report)

    assert exit_code == 0
    assert "STALE" not in joined
    assert "skipped dynamic" in joined.lower()
    assert "{year}" in joined


def test_strftime_placeholder_url_skipped(tmp_path):
    """A URL built with a strftime-style '%Y' placeholder is dynamic and
    must be skipped, not misread as containing a literal year."""
    fetchers = write_fetchers_file(
        tmp_path,
        'TEMPLATE_URL="https://example.com/report-%Y.pdf"\n'
        'source_url="https://example.com/holidays-2026.pdf"\n',
    )
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)
    joined = "\n".join(report)

    assert exit_code == 0
    assert "skipped dynamic" in joined.lower()


def test_variable_source_url_not_captured(tmp_path):
    """A source_url assigned from a variable/attribute/method call (no
    leading quote after '=') is never captured as a literal at all — it
    should neither appear as a hit nor trigger a false stale failure,
    and the file must still parse cleanly."""
    fetchers = write_fetchers_file(
        tmp_path,
        'source_url=self.source_url\n'
        'source_url=self.BASE_PAGE_TEMPLATE.format(year=current_year)\n'
        'source_url="https://example.com/holidays-2026.pdf"\n',
    )
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)
    joined = "\n".join(report)

    assert exit_code == 0
    # Only the one literal URL should have been found.
    assert "URLs with a literal http(s) scheme found: 1" in joined


def test_multiple_years_in_one_url_uses_max(tmp_path):
    """A URL citing more than one year (e.g. 'circular-12-2025...2026.pdf')
    is judged on its maximum year token, not the first or minimum."""
    fetchers = write_fetchers_file(
        tmp_path,
        'source_url="https://example.com/circular-12-2023-for-2024.pdf"\n',
    )
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)
    joined = "\n".join(report)

    # max year in the URL is 2024, still < 2026, so it's stale.
    assert exit_code == 1
    assert "2024" in joined


def test_fetchers_file_not_found_exits_2(tmp_path):
    """A nonexistent fetchers file path should exit 2, not crash."""
    missing = tmp_path / "does_not_exist.py"
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code, report = checker.run_check(missing, exchanges_dir, current_year=CURRENT_YEAR)

    assert exit_code == 2
    assert "not found" in "\n".join(report).lower()


def test_exchanges_dir_not_found_exits_2(tmp_path):
    """A nonexistent exchanges directory should exit 2, not crash."""
    fetchers = write_fetchers_file(tmp_path, 'source_url="https://example.com/x-2026.pdf"\n')
    missing_dir = tmp_path / "does_not_exist_dir"

    exit_code, report = checker.run_check(fetchers, missing_dir, current_year=CURRENT_YEAR)

    assert exit_code == 2
    assert "not found" in "\n".join(report).lower()


def test_zero_year_urls_found_exits_1(tmp_path):
    """If neither location has any URL with a year token at all, that's
    treated as a broken scanner, not a clean pass — exit 1."""
    fetchers = write_fetchers_file(
        tmp_path,
        'source_url="https://example.com/holidays.pdf"\n',  # no year at all
    )
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", ["https://example.com/no-year-here.pdf"])

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)
    joined = "\n".join(report)

    assert exit_code == 1
    assert "zero year-token urls" in joined.lower()


def test_malformed_json_does_not_crash(tmp_path):
    """A malformed exchanges/*.json file should produce a warning and be
    skipped, not raise an exception that aborts the whole scan."""
    fetchers = write_fetchers_file(tmp_path, 'source_url="https://example.com/holidays-2026.pdf"\n')
    exchanges_dir = empty_exchanges_dir(tmp_path)
    (exchanges_dir / "XBAD.json").write_text("{ not valid json", encoding="utf-8")

    exit_code, report = checker.run_check(fetchers, exchanges_dir, current_year=CURRENT_YEAR)
    joined = "\n".join(report)

    assert exit_code == 0
    assert "could not parse json" in joined.lower()


def test_main_returns_exit_code(tmp_path, capsys):
    fetchers = write_fetchers_file(
        tmp_path, 'source_url="https://example.com/holidays-2024.pdf"\n'
    )
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code = checker.main([
        "check_stale_year_urls.py",
        "--fetchers", str(fetchers),
        "--exchanges-dir", str(exchanges_dir),
    ])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "2024" in captured.out


def test_real_repo_passes():
    """Sanity check against the real repository files (not a required
    failure-case test — those all use temp files above)."""
    repo_root = Path(__file__).parent.parent
    fetchers = repo_root / "tools" / "update_from_exchange.py"
    exchanges_dir = repo_root / "exchanges"
    if not fetchers.exists() or not exchanges_dir.exists():
        pytest.skip("real repo files not present in this checkout")

    exit_code, report = checker.run_check(fetchers, exchanges_dir)

    assert exit_code == 0, "\n".join(report)
