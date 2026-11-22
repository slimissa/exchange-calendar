"""tools/live_check_escalate.py (4b3): escalation of the weekly live check."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import live_check_escalate as esc  # noqa: E402


def R(mic, status, attempts=1, reason=""):
    return {"mic": mic, "status": status, "attempts": attempts, "reason": reason, "holiday_count": 9}


def step(results, body=""):
    state = esc.next_state(results, esc.parse_state(body))
    d = esc.decide(results, state, issue_open=bool(body.strip()))
    return d, esc.render_body(results, state, d)


def test_all_green_no_issue():
    d, _ = step([R("XNYS", "PASS"), R("XXXX", "SKIP")])
    assert d == {"escalate": False, "all_green": True, "action": "none", "failing": [], "repeated_transient": [],
                 "known": []}


def test_one_transient_watches_without_failing():
    d, body = step([R("XNYS", "PASS"), R("XCAY", "TRANSIENT", 3, "FetchError: Failed to fetch CSX page")])
    assert d["escalate"] is False and d["action"] == "upsert"
    assert "**Watching**" in body and "| XCAY | TRANSIENT | 3 |" in body
    assert esc.parse_state(body)["streaks"] == {"XCAY": {"kind": "TRANSIENT", "count": 1}}


def test_transient_in_two_consecutive_runs_escalates():
    _, body1 = step([R("XCAY", "TRANSIENT", 3)])
    d, body2 = step([R("XCAY", "TRANSIENT", 3)], body1)
    assert d["escalate"] is True and d["repeated_transient"] == ["XCAY"]
    assert "**Failing**" in body2 and "| XCAY | TRANSIENT | 2 |" in body2


def test_different_fetchers_transient_on_alternate_weeks_do_not_escalate():
    # The 2026-10-25 .. 11-15 pattern: a different site each week.
    _, b1 = step([R("XCAY", "TRANSIENT"), R("XMEX", "PASS")])
    d, b2 = step([R("XCAY", "PASS"), R("XMEX", "TRANSIENT")], b1)
    assert d["escalate"] is False
    assert esc.parse_state(b2)["streaks"] == {"XMEX": {"kind": "TRANSIENT", "count": 1}}


def test_deterministic_failure_escalates_at_once():
    d, body = step([R("XMAD", "FAIL", 1, "ValidationError: Duplicate holiday date: 2026-01-01")])
    assert d["escalate"] is True and d["failing"] == ["XMAD"]
    assert "Deterministic failures" in body and "XMAD" in body


def test_kind_change_restarts_the_count():
    _, b1 = step([R("XMEX", "TRANSIENT")])
    _, b2 = step([R("XMEX", "FAIL")], b1)
    assert esc.parse_state(b2)["streaks"]["XMEX"] == {"kind": "FAIL", "count": 1}


def test_green_run_closes_the_open_issue():
    _, b1 = step([R("XMAD", "FAIL")])
    d, _ = step([R("XMAD", "PASS"), R("XNYS", "PASS")], b1)
    assert d["action"] == "close" and d["escalate"] is False


def test_unreadable_state_starts_fresh():
    assert esc.parse_state("<!-- live-check-state: {not json} -->") == {"streaks": {}}
    assert esc.parse_state("") == {"streaks": {}}


def test_pipe_in_reason_is_escaped():
    _, body = step([R("XIST", "FAIL", 1, "a|b")])
    assert "a\\|b" in body


def test_main_writes_body_and_decision(tmp_path):
    res = tmp_path / "r.json"
    res.write_text(json.dumps({"run_at": "2026-11-29T00:00:00Z",
                               "results": [R("XCAY", "TRANSIENT", 3, "FetchError: x")]}))
    prev = tmp_path / "prev.md"
    prev.write_text("")
    body, dec = tmp_path / "b.md", tmp_path / "d.json"
    assert esc.main(["--results", str(res), "--previous-body", str(prev), "--body-out", str(body),
                     "--decision-out", str(dec), "--run-url", "https://example.invalid/run/1"]) == 0
    assert json.loads(dec.read_text())["action"] == "upsert"
    assert "https://example.invalid/run/1" in body.read_text()


def test_known_faults_are_listed_but_never_escalate_or_streak():
    known = dict(R("XMAD", "KNOWN", 1, "ParseError: x"),
                 known_fault={"reason": "BME page lists 2027 under 2026", "opened": "2026-11-22",
                              "expires": "2027-01-31"})
    _, b1 = step([known, R("XCAY", "TRANSIENT")])
    d, b2 = step([known], b1)
    assert d["escalate"] is False and d["known"] == ["XMAD"]
    assert "XMAD" not in esc.parse_state(b2)["streaks"]
    assert "Known source faults" in b1 and "BME page lists 2027 under 2026" in b1


def test_fault_cleared_warning_reaches_the_body():
    r = dict(R("XMAD", "PASS"), warning="fault cleared, remove the entry for XMAD")
    _, body = step([r, R("XCAY", "FAIL")])
    assert "Warning: XMAD: fault cleared, remove the entry" in body
