"""tools/cross_lang/check_in_session_twins.py (session 4d2).

Every is_open probe in tests/cross_language_queries.json has an in_session
twin with the same args and the same answer.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "cross_lang"))
sys.path.insert(0, str(ROOT / "wrappers" / "python"))

import check_in_session_twins as tw  # noqa: E402
from exchange_calendar import CalendarRegistry  # noqa: E402

FIXTURE = json.loads((ROOT / "tests" / "cross_language_queries.json").read_text(encoding="utf-8"))


def _q(op, label, args=("XNYS", "2026-01-02", "10:00")):
    return {"op": op, "label": label, "args": list(args)}


def test_real_fixture_has_a_twin_for_every_is_open_probe():
    found, problems = tw.pairs(FIXTURE["queries"])
    assert problems == []
    n_is_open = sum(1 for q in FIXTURE["queries"] if q["op"] == "is_open")
    # 17 in 4d2; + 3 XBUE regular-hours probes in 4b1; + 3 XBUE year-end
    # probes in 4b2; + 4 weekday probes in 4b2 (the Rust weekday fix);
    # + 3 XHKG closing-auction probes in 4b2; + 7 XMOS regular-hours probes in 4b2;
    # + 2 XMOS security-group probes in 4b3; + 88 generated probes in 4b3
    # (tools/gen_cross_lang_probes.py: week, boundaries, holiday, early close).
    # + 4 XKUW regular-hours probes in 4b5 (old and new open/close).
    # + 4 XCAY regular-hours probes in 4b5 (old and new open/close).
    # + 4 XNSA regular-hours probes in 4b5 (old and new open/close).
    # + 4 XBRV regular-hours probes in 4b5 (old and new open/close).
    # + 4 DSMD regular-hours probes in 4b5 (old and new open/close).
    # + 2 XIST regular-hours probes in 4b5 (old and new open/close).
    # + 1 XBRV probe in 4b6 (14:30, the corrected close).
    # + 2 XMAD regular-hours probes in 4b6.
    # + 2 XBKK regular-hours probes in 4b6.
    # + 2 XATH regular-hours probes in 4b6.
    # + 2 XKAR regular-hours probes in 4b6.
    # 4b7: XATH probes re-dated (2025-08-29 old regime, 2025-09-01 new) + 1 pair.
    assert len(found) == n_is_open == 159


def test_real_fixture_twins_answer_the_same_in_python():
    r = CalendarRegistry(ROOT / "calendar.json")
    by_label = {q["label"]: q for q in FIXTURE["queries"]}
    for a, b in tw.pairs(FIXTURE["queries"])[0]:
        args = by_label[a]["args"]
        assert r.in_session(*by_label[b]["args"]) is r.is_open(*args), (a, b)


def test_missing_twin_fails():
    _, problems = tw.pairs([_q("is_open", "is_open_x")])
    assert problems == ["is_open_x: no in_session twin 'in_session_x'"]


def test_twin_with_other_args_fails():
    _, problems = tw.pairs([_q("is_open", "is_open_x"),
                            _q("in_session", "in_session_x", ("XNYS", "2026-01-02", "11:00"))])
    assert len(problems) == 1 and "op/args differ" in problems[0]


def test_orphan_in_session_probe_fails():
    _, problems = tw.pairs([_q("in_session", "in_session_y")])
    assert problems == ["in_session probe 'in_session_y' has no is_open probe"]


def test_different_answer_in_an_output_fails(tmp_path, monkeypatch):
    fixture = tmp_path / "q.json"
    fixture.write_text(json.dumps({"queries": [_q("is_open", "is_open_x"),
                                               _q("in_session", "in_session_x")]}))
    monkeypatch.setattr(tw, "FIXTURE", fixture)
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    good.write_text(json.dumps({"is_open_x": True, "in_session_x": True}))
    bad.write_text(json.dumps({"is_open_x": True, "in_session_x": False}))
    assert tw.main([str(good)]) == 0
    assert tw.main([str(good), str(bad)]) == 1
