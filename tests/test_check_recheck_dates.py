"""Tests for tools/check_recheck_dates.py (session 4c-R5)."""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import check_recheck_dates as crd  # noqa: E402


def _write(directory: Path, mic: str, coverage_sources: list) -> None:
    data = {"mic": mic, "verification": {"coverage": {"sources": coverage_sources}}}
    (directory / f"{mic}.json").write_text(json.dumps(data), encoding="utf-8")


def _span(**extra):
    return {"from": "2025-01-01", "to": "2027-12-31", "source": "x", **extra}


def test_past_date_fails(tmp_path, capsys):
    _write(tmp_path, "XAAA", [_span(unconfirmed=["2027-01-04"], recheck_date="2027-01-04")])
    rc = crd.main(["--exchanges", str(tmp_path), "--today", "2027-01-05"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "PASSED: XAAA 2027-01-04 at verification.coverage.sources[0]" in out
    assert "unconfirmed: 2027-01-04" in out
    assert "FAIL: 1 recheck date(s) before 2027-01-05" in out


def test_due_today_passes(tmp_path):
    _write(tmp_path, "XAAA", [_span(recheck_date="2027-01-04")])
    assert crd.main(["--exchanges", str(tmp_path), "--today", "2027-01-04"]) == 0


def test_future_date_passes(tmp_path, capsys):
    _write(tmp_path, "XAAA", [_span(recheck_date="2027-11-30")])
    rc = crd.main(["--exchanges", str(tmp_path), "--today", "2026-11-20"])
    assert rc == 0
    assert "OK: 1 recheck date(s), none before 2026-11-20" in capsys.readouterr().out


def test_no_dates_passes(tmp_path, capsys):
    _write(tmp_path, "XAAA", [_span()])
    assert crd.main(["--exchanges", str(tmp_path), "--today", "2026-11-20"]) == 0
    assert "OK: 0 recheck date(s)" in capsys.readouterr().out


@pytest.mark.parametrize("bad", ["2027-13-01", "2027/01/04", "2027-1-4", 20270104, None])
def test_malformed_date_is_an_error(tmp_path, capsys, bad):
    _write(tmp_path, "XAAA", [_span(recheck_date=bad)])
    assert crd.main(["--exchanges", str(tmp_path), "--today", "2026-11-20"]) == 2
    assert "ERROR: XAAA: recheck_date at verification.coverage.sources[0]" in capsys.readouterr().err


def test_missing_directory_is_an_error(tmp_path):
    assert crd.main(["--exchanges", str(tmp_path / "nope")]) == 2


def test_one_past_among_several(tmp_path):
    _write(tmp_path, "XAAA", [_span(recheck_date="2027-11-30")])
    _write(tmp_path, "XBBB", [_span(recheck_date="2027-01-04")])
    found = crd.collect(tmp_path)
    assert [(r.mic, r.recheck) for r in found] == [
        ("XBBB", date(2027, 1, 4)), ("XAAA", date(2027, 11, 30))]
    assert crd.main(["--exchanges", str(tmp_path), "--today", "2027-02-01"]) == 1


def test_registry_dates_today():
    """The registry's own recheck dates (XPRA 2027-01-04, XDUB 2027-11-30,
    XETR 2026-12-15 from 4c8: the 2026 final-session time) are found, and
    none had passed on 2026-11-20. XOSL's 2027-03-01 (4c-R5) was removed in
    4c8 when the 2025 and 2027 schedules were read."""
    found = {(r.mic, r.recheck.isoformat()) for r in crd.collect()}
    # XJSE 2026-12-15 from 4c8: JSE's December 2026 early-close hotline.
    # XWBO 2026-12-15 from 4c8: Wiener Börse's 2026 last-trading-day notice.
    # XNZE 2026-12-15 from 4c10: NZX's 2026/2028 holiday memo (abbreviated days).
    # XRIS 2027-01-31 from 4c12: 2026-01-02 against the January 2026 bulletin.
    assert found == {("XPRA", "2027-01-04"), ("XDUB", "2027-11-30"), ("XETR", "2026-12-15"),
                     ("XJSE", "2026-12-15"), ("XWBO", "2026-12-15"), ("XNZE", "2026-12-15"),
                     ("XBDA", "2026-12-22"), ("XRIS", "2027-01-31")}
    assert crd.main(["--today", "2026-11-20"]) == 0
    assert crd.main(["--today", "2027-01-05"]) == 1
