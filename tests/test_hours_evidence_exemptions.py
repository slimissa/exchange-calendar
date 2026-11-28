"""Hours-evidence exemptions and the blocking check 6 (ADR 0015, session 4b13).

Every date is injected: `today` is a parameter of the checker, never the
wall clock, so these tests do not change outcome as days pass.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_verification as cv  # noqa: E402
import hours_evidence_exemptions as hx  # noqa: E402

TODAY = dt.date(2026, 11, 28)


def exchanges() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "exchanges").glob("*.json"))]


def exemption(mic: str, added: str = "2026-11-28", expires: str = "2027-02-06", **extra) -> dict:
    e = {
        "mic": mic,
        "reason": "official hours page renders by script; print empty",
        "sources_tried": [{"source": "https://example.invalid/hours", "tried": "2026-11-28",
                           "outcome": "renders by script; print empty"}],
        "leads": [{"label": "unread lead", "pointer": "a rulebook named by the maintainer"}],
        "added": added,
        "expires": expires,
        "next_action": "read the rulebook",
    }
    e.update(extra)
    return e


UNCOVERED = ("XBOG", "XBOM", "XLIM", "XNSE", "XSGO")


def all_five() -> list[dict]:
    return [exemption(m) for m in UNCOVERED]


def test_blocking_without_exemptions_names_exactly_the_five():
    r = cv.check6(exchanges(), [], TODAY)
    assert r["uncovered"] == list(UNCOVERED)
    assert len(r["errors"]) == 5 and all("without verified current hours" in e for e in r["errors"])
    assert (len(r["verified"]), len(r["schema_limited"]), r["total_rc"]) == (41, 2, 48)
    assert r["schema_limited"] == ["XKAR", "XMEX"]


def test_valid_exemptions_pass():
    r = cv.check6(exchanges(), all_five(), TODAY)
    assert r["errors"] == [] and r["warnings"] == []
    assert r["exempt"] == list(UNCOVERED) and r["uncovered"] == []


def test_expired_exemption_fails_and_uncovers_its_mic():
    entries = all_five()
    entries[3] = exemption("XNSE", expires="2026-12-28")
    on_last_day = cv.check6(exchanges(), entries, dt.date(2026, 12, 28))
    assert on_last_day["errors"] == []
    after = cv.check6(exchanges(), entries, dt.date(2026, 12, 29))
    assert any("XNSE: exemption expired on 2026-12-28" in e for e in after["errors"])
    assert "XNSE" in after["uncovered"] and "XNSE" not in after["exempt"]


def test_stale_exemption_fails():
    # XNYS has verified current hours; XKAR has a schema_limited item.
    for mic in ("XNYS", "XKAR"):
        r = cv.check6(exchanges(), all_five() + [exemption(mic)], TODAY)
        assert any(e.startswith(f"{mic}: stale exemption") for e in r["errors"]), mic


def test_exemption_for_a_non_reference_exchange_fails():
    data = exchanges()
    non_rc = next(d["code"] for d in data if d["verification"]["class"] != "reference_compared")
    r = cv.check6(data, all_five() + [exemption(non_rc)], TODAY)
    assert any(f"{non_rc}: exemption for an exchange that is not reference_compared" in e
               for e in r["errors"])
    r = cv.check6(data, all_five() + [exemption("XZZZ")], TODAY)
    assert any("XZZZ: exemption names no exchange" in e for e in r["errors"])


def test_more_than_seventy_days_fails():
    entries = all_five()
    entries[0] = exemption("XBOG", added="2026-11-28", expires="2027-02-07")  # 71 days
    r = cv.check6(exchanges(), entries, TODAY)
    assert any("more than 70 days after added" in e for e in r["errors"])
    assert "XBOG" in r["uncovered"]
    entries[0] = exemption("XBOG", added="2026-11-28", expires="2027-02-06")  # 70 days
    assert cv.check6(exchanges(), entries, TODAY)["errors"] == []


@pytest.mark.parametrize("field", hx.FIELDS)
def test_missing_field_fails(field):
    entries = all_five()
    broken = copy.deepcopy(entries[1])
    broken.pop(field)
    entries[1] = broken
    r = cv.check6(exchanges(), entries, TODAY)
    assert r["errors"], field
    if field != "mic":
        assert any("missing " + field in e for e in r["errors"]), r["errors"]
        assert "XBOM" in r["uncovered"]


def test_incomplete_source_record_or_unlabelled_lead_fails():
    entries = all_five()
    entries[2] = exemption("XLIM", sources_tried=[{"source": "https://example.invalid", "tried": "2026-11-28"}])
    entries[4] = exemption("XSGO", leads=[{"label": "lead", "pointer": "x"}])
    r = cv.check6(exchanges(), entries, TODAY)
    assert any("sources_tried[0] lacks outcome" in e for e in r["errors"])
    assert any("leads[0].label is 'lead', expected 'unread lead'" in e for e in r["errors"])
    assert {"XLIM", "XSGO"} <= set(r["uncovered"])


def test_duplicate_exemption_fails():
    r = cv.check6(exchanges(), all_five() + [exemption("XBOM")], TODAY)
    assert any("XBOM: more than one exemption" in e for e in r["errors"])


def test_warns_within_fourteen_days_only():
    entries = all_five()
    entries[3] = exemption("XNSE", expires="2026-12-28")
    assert cv.check6(exchanges(), entries, dt.date(2026, 12, 13))["warnings"] == []  # 15 days
    warn = cv.check6(exchanges(), entries, dt.date(2026, 12, 14))  # 14 days
    assert warn["errors"] == [] and warn["warnings"] == ["XNSE: exemption expires on 2026-12-28, 14 day(s) from 2026-12-14"]


def test_exemptions_raise_no_count():
    # An exemption is not evidence: the facts do not move with it.
    data = exchanges()
    before = sum(cv.current_hours_verified(d) for d in data)
    cv.check6(data, all_five(), TODAY)
    assert sum(cv.current_hours_verified(d) for d in data) == before
    assert not any(cv.current_hours_verified(d) for d in data if d["code"] in UNCOVERED)


def run_cli(tmp_path, entries, today, capsys, strict=True):
    path = tmp_path / "exemptions.json"
    path.write_text(json.dumps({"exemptions": entries}), encoding="utf-8")
    argv = ["--today", today, "--exemptions", str(path)] + (["--strict-hours"] if strict else [])
    code = cv.main(argv)
    return code, capsys.readouterr().out


def test_cli_blocks_without_exemptions(tmp_path, capsys):
    code, out = run_cli(tmp_path, [], "2026-11-28", capsys)
    assert code == 1
    assert "check 6 (blocking): 48 reference_compared = 41 verified + 2 schema_limited + 0 exempt + 5 uncovered" in out


def test_cli_passes_with_the_five_and_reports_the_nearest_expiry(tmp_path, capsys):
    entries = all_five()
    entries[3] = exemption("XNSE", expires="2026-12-28")
    code, out = run_cli(tmp_path, entries, "2026-11-28", capsys)
    assert code == 0, out
    assert ("check 6 (blocking): 48 reference_compared = 41 verified + 2 schema_limited + 5 exempt; "
            "exemptions 5, nearest expiry 2026-12-28 (XNSE); checked on 2026-11-28") in out


def test_cli_fails_once_an_exemption_has_expired(tmp_path, capsys):
    entries = all_five()
    entries[3] = exemption("XNSE", expires="2026-12-28")
    code, out = run_cli(tmp_path, entries, "2026-12-29", capsys)
    assert code == 1
    assert "check 6: XNSE: exemption expired on 2026-12-28 (today 2026-12-29)" in out


def test_exemption_file_validates():
    entries = hx.load()
    assert hx.shape_problems(entries) == []
