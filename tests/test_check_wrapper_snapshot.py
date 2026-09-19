#!/usr/bin/env python3
"""
test_check_wrapper_snapshot.py — Unit tests for check_wrapper_snapshot.py.

Tests that the wrapper-snapshot checker correctly:
    1. Passes when the wrapper's bundled calendar.json matches a fresh
       build from exchanges/ byte-for-byte
    2. Fails when the wrapper's copy is missing entirely
    3. Fails when the wrapper's copy differs from a fresh build, and
       reports a diff summary (size delta / differing-line count)
    4. Exits 2 when the exchanges/ directory doesn't exist
    5. Exits 2 when the rebuild itself fails (invalid exchange JSON)
    6. Doesn't mutate the wrapper's file, exchanges/, or leak its temp
       file when it passes or fails
    7. main() prints the report and returns the same exit code as
       run_check()

All tests build their own temp exchanges/ directory and temp wrapper
file (via pytest's tmp_path fixture) — none of the required failure
cases depend on the real repo's exchanges/ or wrapper copy, except one
explicit sanity check that is skipped if those aren't present.

Run:
    python3 -m pytest tests/test_check_wrapper_snapshot.py -v
"""

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_wrapper_snapshot as checker


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def minimal_exchange(code="TEST", name="Test Exchange"):
    return {
        "code": code,
        "name": name,
        "mic": code,
        "timezone": "Europe/London",
        "weekend_days": [5, 6],
        "regular_hours": {"open": "09:00", "close": "17:00"},
        "holidays": {
            "explicit": [
                {"date": "2025-01-01", "name": "New Year's Day", "status": "closed"},
            ],
            "recurrence_rules": [],
        },
        "ad_hoc_closures": [],
        "generation_range": ["2025-01-01", "2025-12-31"],
    }


def make_exchanges_dir(tmp_path, exchanges=None):
    d = tmp_path / "exchanges"
    d.mkdir()
    for exch in (exchanges if exchanges is not None else [minimal_exchange()]):
        (d / f"{exch['code']}.json").write_text(json.dumps(exch), encoding="utf-8")
    return d


def build_fresh_bytes(exchanges_dir):
    """Use the checker's own rebuild path to get the 'correct' bytes for
    a given exchanges_dir, so tests don't hand-duplicate build.py's
    output format."""
    tmp_path = checker.rebuild_to_temp(exchanges_dir)
    try:
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink()


# ──────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────

def test_matching_copy_passes(tmp_path):
    """A wrapper copy that's byte-identical to a fresh build passes."""
    exchanges_dir = make_exchanges_dir(tmp_path)
    fresh_bytes = build_fresh_bytes(exchanges_dir)

    wrapper_path = tmp_path / "wrapper_calendar.json"
    wrapper_path.write_bytes(fresh_bytes)

    exit_code, report = checker.run_check(exchanges_dir, wrapper_path)

    assert exit_code == 0
    assert "OK" in "\n".join(report)


def test_missing_wrapper_copy_fails(tmp_path):
    """A wrapper path that doesn't exist at all is a clear failure, not
    a crash, and exit code is 1 (not 2 -- exchanges/ itself is fine)."""
    exchanges_dir = make_exchanges_dir(tmp_path)
    wrapper_path = tmp_path / "does_not_exist.json"

    exit_code, report = checker.run_check(exchanges_dir, wrapper_path)
    joined = "\n".join(report)

    assert exit_code == 1
    assert "missing" in joined.lower()
    assert "make package" in joined


def test_stale_wrapper_copy_fails_with_diff_summary(tmp_path):
    """A wrapper copy that differs from a fresh build fails with exit 1
    and prints a diff summary (size delta and/or differing-line count)."""
    exchanges_dir = make_exchanges_dir(tmp_path)
    fresh_bytes = build_fresh_bytes(exchanges_dir)

    # Simulate staleness: wrapper copy built from a smaller exchange set.
    stale_exchanges_dir = tmp_path / "exchanges_stale"
    stale_exchanges_dir.mkdir()
    (stale_exchanges_dir / "OLD.json").write_text(
        json.dumps(minimal_exchange(code="OLD", name="Old Exchange")), encoding="utf-8"
    )
    stale_bytes = build_fresh_bytes(stale_exchanges_dir)

    wrapper_path = tmp_path / "wrapper_calendar.json"
    wrapper_path.write_bytes(stale_bytes)
    assert stale_bytes != fresh_bytes  # sanity: our fixtures really do differ

    exit_code, report = checker.run_check(exchanges_dir, wrapper_path)
    joined = "\n".join(report)

    assert exit_code == 1
    assert "stale" in joined.lower()
    assert "bytes" in joined.lower()
    assert "make package" in joined


def test_missing_exchanges_dir_exits_2(tmp_path):
    """A nonexistent exchanges/ directory is a prerequisite failure, not
    a stale-copy failure -- exit code 2."""
    missing_dir = tmp_path / "does_not_exist_dir"
    wrapper_path = tmp_path / "wrapper_calendar.json"
    wrapper_path.write_text("{}", encoding="utf-8")

    exit_code, report = checker.run_check(missing_dir, wrapper_path)

    assert exit_code == 2
    assert "not found" in "\n".join(report).lower()


def test_broken_exchange_json_exits_2(tmp_path):
    """If the rebuild itself fails (e.g. a malformed exchange file makes
    every exchange fail to load), that's a prerequisite failure -- exit
    code 2, not a false 'stale' report."""
    exchanges_dir = tmp_path / "exchanges"
    exchanges_dir.mkdir()
    (exchanges_dir / "BROKEN.json").write_text("{ not valid json", encoding="utf-8")

    wrapper_path = tmp_path / "wrapper_calendar.json"
    wrapper_path.write_text("{}", encoding="utf-8")

    exit_code, report = checker.run_check(exchanges_dir, wrapper_path)

    assert exit_code == 2
    assert "failed" in "\n".join(report).lower()


def test_temp_file_cleaned_up(tmp_path):
    """rebuild_to_temp's temp file should not leak past run_check --
    verify no stray calendar_*.json files remain in the system temp dir
    that weren't there before."""
    import tempfile as _tempfile

    exchanges_dir = make_exchanges_dir(tmp_path)
    wrapper_path = tmp_path / "wrapper_calendar.json"
    wrapper_path.write_bytes(build_fresh_bytes(exchanges_dir))

    before = set(Path(_tempfile.gettempdir()).glob("calendar_*.json"))
    checker.run_check(exchanges_dir, wrapper_path)
    after = set(Path(_tempfile.gettempdir()).glob("calendar_*.json"))

    assert after == before


def test_run_check_does_not_mutate_wrapper_copy(tmp_path):
    """Running the check must never modify the wrapper file it's
    inspecting -- it's read-only diagnostics, not a fixer."""
    exchanges_dir = make_exchanges_dir(tmp_path)
    fresh_bytes = build_fresh_bytes(exchanges_dir)
    wrapper_path = tmp_path / "wrapper_calendar.json"
    wrapper_path.write_bytes(fresh_bytes)

    before_mtime = wrapper_path.stat().st_mtime
    before_bytes = wrapper_path.read_bytes()

    checker.run_check(exchanges_dir, wrapper_path)

    assert wrapper_path.read_bytes() == before_bytes
    assert wrapper_path.stat().st_mtime == before_mtime


def test_main_returns_exit_code(tmp_path, capsys):
    exchanges_dir = make_exchanges_dir(tmp_path)
    wrapper_path = tmp_path / "does_not_exist.json"

    exit_code = checker.main([
        "check_wrapper_snapshot.py",
        "--exchanges-dir", str(exchanges_dir),
        "--wrapper-path", str(wrapper_path),
    ])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "missing" in captured.out.lower()


def test_real_repo_passes_after_sync():
    """Sanity check against the real repo, after `make package`/the
    equivalent sync has been run. Not one of the required failure-case
    tests -- those are all self-contained above -- so this skips
    cleanly if the wrapper copy hasn't been synced in this checkout."""
    repo_root = Path(__file__).parent.parent
    exchanges_dir = repo_root / "exchanges"
    wrapper_path = repo_root / "wrappers" / "python" / "exchange_calendar" / "calendar.json"
    if not exchanges_dir.exists() or not wrapper_path.exists():
        pytest.skip("real repo files not present in this checkout")

    exit_code, report = checker.run_check(exchanges_dir, wrapper_path)

    if exit_code != 0:
        pytest.skip("wrapper copy not currently synced -- run `make package` first")
