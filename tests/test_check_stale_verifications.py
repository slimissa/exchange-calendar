#!/usr/bin/env python3
"""
test_check_stale_verifications.py — Unit tests for check_stale_verifications.py.

Tests that the staleness checker correctly:
    1. Passes sections with a recent `Last verified` date
    2. Fails sections whose `Last verified` date is older than 18 months
    3. Flags sections with no `Last verified` line at all
    4. Flags sections with a malformed `Last verified` date

All failure-case tests use a temp file (pytest's tmp_path fixture) so they
never depend on the real BLOCKED.md.

Run:
    python3 -m pytest tests/test_check_stale_verifications.py -v
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

# Add tools/ to path, matching the convention used by tests/test_validate.py
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_stale_verifications as checker


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def write_blocked_md(tmp_path, body, filename="BLOCKED.md"):
    """Write a BLOCKED.md-shaped file with the given body and return its path."""
    path = tmp_path / filename
    path.write_text(body, encoding="utf-8")
    return path


def section(heading, last_verified_line, extra="- **Verdict:** BLOCKED.\n"):
    """Build one '## HEADING\\n\\n<last_verified_line>\\n\\n<extra>' block.

    last_verified_line may be None to omit the Last verified line entirely.
    """
    parts = [f"{heading}\n\n"]
    if last_verified_line is not None:
        parts.append(f"**Last verified:** {last_verified_line}\n\n")
    parts.append(extra)
    return "".join(parts)


# ──────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────

def test_current_entry_passes(tmp_path):
    """A Last verified date well within 18 months should not be flagged."""
    recent = (date.today() - timedelta(days=10)).isoformat()
    body = "# Blocked / Not Automated\n\n" + section("## XFOO — Foo Exchange", recent)
    path = write_blocked_md(tmp_path, body)

    exit_code, report = checker.check(str(path))

    assert exit_code == 0
    assert "STALE ENTRIES" not in "\n".join(report)


def test_stale_entry_fails(tmp_path):
    """A Last verified date older than 549 days should fail with exit 1."""
    stale = (date.today() - timedelta(days=600)).isoformat()
    body = "# Blocked / Not Automated\n\n" + section("## XFOO — Foo Exchange", stale)
    path = write_blocked_md(tmp_path, body)

    exit_code, report = checker.check(str(path))

    assert exit_code == 1
    joined = "\n".join(report)
    assert "XFOO" in joined
    assert stale in joined


def test_missing_date_flagged(tmp_path):
    """A section heading with no Last verified line at all should be flagged,
    not silently skipped or crash the script."""
    body = "# Blocked / Not Automated\n\n" + section(
        "## XFOO — Foo Exchange", None
    )
    path = write_blocked_md(tmp_path, body)

    exit_code, report = checker.check(str(path))

    assert exit_code == 1
    joined = "\n".join(report)
    assert "XFOO" in joined
    assert "missing" in joined.lower()


def test_malformed_date_flagged(tmp_path):
    """A Last verified value that isn't a valid YYYY-MM-DD date should be
    flagged as an error, not raise an exception."""
    body = "# Blocked / Not Automated\n\n" + section(
        "## XFOO — Foo Exchange", "not-a-real-date"
    )
    path = write_blocked_md(tmp_path, body)

    exit_code, report = checker.check(str(path))

    assert exit_code == 1
    joined = "\n".join(report)
    assert "XFOO" in joined
    assert "malformed" in joined.lower()


def test_multiple_sections_mixed_results(tmp_path):
    """A file with one current, one stale, one missing, and one malformed
    section should report exactly the three bad ones and still exit 1."""
    recent = (date.today() - timedelta(days=5)).isoformat()
    stale = (date.today() - timedelta(days=1000)).isoformat()

    body = (
        "# Blocked / Not Automated\n\n"
        + section("## XGOOD — Good Exchange", recent)
        + section("## XSTALE — Stale Exchange", stale)
        + section("## XMISSING — Missing Exchange", None)
        + section("## XBAD — Bad Date Exchange", "2026-13-99")
    )
    path = write_blocked_md(tmp_path, body)

    exit_code, report = checker.check(str(path))
    joined = "\n".join(report)
    stale_section = joined.split("STALE ENTRIES", 1)[1]

    assert exit_code == 1
    assert "XGOOD" not in stale_section
    assert "XSTALE" in stale_section
    assert "XMISSING" in stale_section
    assert "XBAD" in stale_section


def test_boundary_exactly_549_days_passes(tmp_path):
    """A date exactly 549 days old is the edge of the window and should
    still pass (cutoff is today - 549 days; the entry equals the cutoff)."""
    boundary = (date.today() - timedelta(days=549)).isoformat()
    body = "# Blocked / Not Automated\n\n" + section("## XEDGE — Edge Exchange", boundary)
    path = write_blocked_md(tmp_path, body)

    exit_code, report = checker.check(str(path))

    assert exit_code == 0


def test_boundary_550_days_fails(tmp_path):
    """One day past the 18-month window should fail."""
    just_over = (date.today() - timedelta(days=550)).isoformat()
    body = "# Blocked / Not Automated\n\n" + section("## XEDGE — Edge Exchange", just_over)
    path = write_blocked_md(tmp_path, body)

    exit_code, report = checker.check(str(path))

    assert exit_code == 1


def test_missing_file_exits_2(tmp_path):
    """Pointing the checker at a nonexistent file should fail cleanly with
    exit code 2, not crash."""
    missing_path = tmp_path / "does_not_exist.md"

    exit_code, report = checker.check(str(missing_path))

    assert exit_code == 2
    assert "could not read" in "\n".join(report).lower()


def test_real_blocked_md_passes():
    """Sanity check: the real repo BLOCKED.md, as of this test's writing,
    should have no stale entries. This guards the real file without the
    failure-case tests depending on it."""
    repo_root = Path(__file__).parent.parent
    real_path = repo_root / "BLOCKED.md"
    if not real_path.exists():
        pytest.skip("BLOCKED.md not present in this checkout")

    exit_code, report = checker.check(str(real_path))

    assert exit_code == 0, "\n".join(report)


def test_main_returns_exit_code(tmp_path, capsys):
    """main() should print the report and return the same exit code as check()."""
    stale = (date.today() - timedelta(days=600)).isoformat()
    body = "# Blocked / Not Automated\n\n" + section("## XFOO — Foo Exchange", stale)
    path = write_blocked_md(tmp_path, body)

    exit_code = checker.main(["check_stale_verifications.py", str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "XFOO" in captured.out
