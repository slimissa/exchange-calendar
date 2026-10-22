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
    9. Allowlist: a stale URL on an unexpired allowlist entry passes, the
       expiry date itself is still covered, the day after fails with the
       entry named, non-allowlisted stale URLs still fail, an invalid date
       exits 2, and an entry matching no scanned URL only warns
   10. The real repo passes a simulated 2027-01-01 rollover (via the real
       ALLOWLIST) and fails once every entry has expired

All tests build their own temp fetchers file and/or temp exchanges/
directory (via pytest's tmp_path fixture) — none of them depend on the
real repo's tools/update_from_exchange.py or exchanges/*.json content,
except the one explicit sanity check against the real files.

Run:
    python3 -m pytest tests/test_check_stale_year_urls.py -v
"""

import json
import sys
from datetime import date
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


# ──────────────────────────────────────────────────────────────
# Allowlist
# ──────────────────────────────────────────────────────────────

STALE_URL = "https://example.com/circular-2026.pdf"


def stale_setup(tmp_path):
    """A fetchers file whose only year-token URL is STALE_URL, judged
    against a 2027 'current year'."""
    fetchers = write_fetchers_file(tmp_path, f'source_url="{STALE_URL}"\n')
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])
    return fetchers, exchanges_dir


def test_allowlisted_stale_url_passes_before_expiry(tmp_path):
    fetchers, exchanges_dir = stale_setup(tmp_path)

    exit_code, report = checker.run_check(
        fetchers, exchanges_dir, current_year=2027,
        allowlist={STALE_URL: "2027-06-01"}, today=date(2027, 1, 1),
    )
    joined = "\n".join(report)

    assert exit_code == 0
    assert "ALLOWLISTED" in joined
    assert "2027-06-01" in joined
    assert "STALE YEAR URLS" not in joined


def test_allowlist_covers_the_expiry_date_itself(tmp_path):
    fetchers, exchanges_dir = stale_setup(tmp_path)

    exit_code, _ = checker.run_check(
        fetchers, exchanges_dir, current_year=2027,
        allowlist={STALE_URL: "2027-06-01"}, today=date(2027, 6, 1),
    )

    assert exit_code == 0


def test_allowlist_expired_day_after_fails(tmp_path):
    fetchers, exchanges_dir = stale_setup(tmp_path)

    exit_code, report = checker.run_check(
        fetchers, exchanges_dir, current_year=2027,
        allowlist={STALE_URL: "2027-06-01"}, today=date(2027, 6, 2),
    )
    joined = "\n".join(report)

    assert exit_code == 1
    assert "EXPIRED ALLOWLIST ENTRIES" in joined
    assert "expired 2027-06-01" in joined
    assert STALE_URL in joined


def test_allowlist_does_not_cover_other_stale_urls(tmp_path):
    fetchers = write_fetchers_file(
        tmp_path,
        f'source_url="{STALE_URL}"\n'
        'source_url="https://example.com/other-2025.pdf"\n',
    )
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code, report = checker.run_check(
        fetchers, exchanges_dir, current_year=2027,
        allowlist={STALE_URL: "2027-06-01"}, today=date(2027, 1, 1),
    )
    joined = "\n".join(report)

    assert exit_code == 1
    assert "STALE YEAR URLS (1)" in joined
    assert "other-2025.pdf" in joined


def test_allowlist_matches_json_and_fetcher_hits_for_one_url(tmp_path):
    """One URL cited by a fetcher constant and by JSON entries is covered
    by a single allowlist entry."""
    fetchers = write_fetchers_file(tmp_path, f'source_url="{STALE_URL}"\n')
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [STALE_URL, STALE_URL])

    exit_code, report = checker.run_check(
        fetchers, exchanges_dir, current_year=2027,
        allowlist={STALE_URL: "2027-06-01"}, today=date(2027, 1, 1),
    )

    assert exit_code == 0
    assert "(3 hits)" in "\n".join(report)


def test_allowlist_invalid_date_exits_2(tmp_path):
    fetchers, exchanges_dir = stale_setup(tmp_path)

    exit_code, report = checker.run_check(
        fetchers, exchanges_dir, current_year=2027,
        allowlist={STALE_URL: "June 2027"}, today=date(2027, 1, 1),
    )

    assert exit_code == 2
    assert "invalid expiry date" in "\n".join(report)


def test_allowlist_entry_matching_nothing_only_warns(tmp_path):
    fetchers = write_fetchers_file(tmp_path, 'source_url="https://example.com/x-2027.pdf"\n')
    exchanges_dir = empty_exchanges_dir(tmp_path)
    write_exchange_json(exchanges_dir, "XTST.json", [])

    exit_code, report = checker.run_check(
        fetchers, exchanges_dir, current_year=2027,
        allowlist={STALE_URL: "2027-06-01"}, today=date(2027, 1, 1),
    )
    joined = "\n".join(report)

    assert exit_code == 0
    assert "matches no scanned URL" in joined


def test_main_today_flag_simulates_a_date(tmp_path, capsys):
    fetchers, exchanges_dir = stale_setup(tmp_path)
    args = ["check_stale_year_urls.py", "--fetchers", str(fetchers),
            "--exchanges-dir", str(exchanges_dir)]

    # STALE_URL is not on the real ALLOWLIST, so a 2027 date must fail.
    assert checker.main(args + ["--today", "2027-01-01"]) == 1
    assert "Current year: 2027" in capsys.readouterr().out
    assert checker.main(args + ["--today", "not-a-date"]) == 2


def test_real_repo_survives_2027_rollover_until_allowlist_expires():
    """The release-blocking property this allowlist exists for: on
    2027-01-01 the real repo's 12 stale hits are all covered, and once
    the latest entry has expired the check fails again."""
    repo_root = Path(__file__).parent.parent
    fetchers = repo_root / "tools" / "update_from_exchange.py"
    exchanges_dir = repo_root / "exchanges"
    if not fetchers.exists() or not exchanges_dir.exists():
        pytest.skip("real repo files not present in this checkout")

    latest = max(date.fromisoformat(d) for d in checker.ALLOWLIST.values())

    exit_code, report = checker.run_check(
        fetchers, exchanges_dir, today=date(2027, 1, 1)
    )
    assert exit_code == 0, "\n".join(report)

    exit_code, report = checker.run_check(
        fetchers, exchanges_dir, today=date.fromordinal(latest.toordinal() + 1)
    )
    assert exit_code == 1, "\n".join(report)
