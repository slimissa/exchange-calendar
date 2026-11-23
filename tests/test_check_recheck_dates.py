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
    # XNZE 2026-12-15 (4c10) was cleared in 4d2 by NZX memo 463713.
    # XRIS 2027-01-31 (4c12) was cleared in 4c13 by the January 2026 bulletin.
    # XBUE 2026-12-31 from 4d.1 (Holy Thursday 2025-04-17), brought forward to
    # 2026-12-22 in 4d2 for the 24 December 2026 13:00 early close it now shares.
    assert found == {("XPRA", "2027-01-04"), ("XDUB", "2027-11-30"), ("XETR", "2026-12-15"),
                     ("XJSE", "2026-12-15"), ("XWBO", "2026-12-15"),
                     ("XBDA", "2026-12-22"), ("XBUE", "2026-12-22"),
                     # XHKG 2027-02-19 (4b2): the 1990-2011 hours (10:00-16:00),
                     # read only for 2010 (HKEx consultation conclusions).
                     ("XHKG", "2027-02-19"),
                     # XMOS 2027-02-19 (4b2): 10:00-18:45 back to 2010.
                     ("XMOS", "2027-02-19"),
                     # 4b2 hours evidence, unconfirmed older entries: XOSL 2010
                     # and 2012-08-06, XETR 2010, XBUD 2010; XKAR (09:32 open
                     # undated). XPRA's 2027-01-04 is the date it already had.
                     ("XOSL", "2027-02-19"), ("XETR", "2027-02-19"),
                     ("XBUD", "2027-02-19"), ("XKAR", "2027-02-19"),
                     # 4b3 hours evidence, unconfirmed older entries: XTKS
                     # 1997, XPHS 2010, XSES 2010.
                     ("XTKS", "2027-02-19"), ("XPHS", "2027-02-19"),
                     ("XSES", "2027-02-19"),
                     # 4b4: XASX close 16:11 under ADR 0013, undated.
                     ("XASX", "2027-02-19"),
                     # 4b6: XATH earlier hours entry (ADR 0014 section 8).
                     ("XATH", "2027-02-19"),
                     # 4b6: XBKK earlier hours entry (ADR 0014 section 8).
                     ("XBKK", "2027-02-19"),
                     # 4b6: XMAD earlier hours entry (ADR 0014 section 8).
                     ("XMAD", "2027-02-19"),
                     # 4b5: XIST earlier hours entry (ADR 0014 section 8 or dated split).
                     ("XIST", "2027-02-19"),
                     # 4b5: DSMD earlier hours entry (ADR 0014 section 8 or dated split).
                     ("DSMD", "2027-02-19"),
                     # 4b5: XBRV earlier hours entry (ADR 0014 section 8 or dated split).
                     ("XBRV", "2027-02-19"),
                     # 4b5: XNSA earlier hours entry (ADR 0014 section 8 or dated split).
                     ("XNSA", "2027-02-19"),
                     # 4b5: XCAY earlier hours entry (ADR 0014 section 8 or dated split).
                     ("XCAY", "2027-02-19"),
                     # 4b5: XKUW earlier hours entry (ADR 0014 section 8 or dated split).
                     ("XKUW", "2027-02-19")}
    assert crd.main(["--today", "2026-11-20"]) == 0
    assert crd.main(["--today", "2027-01-05"]) == 1
