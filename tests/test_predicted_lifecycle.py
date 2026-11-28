"""ADR 0016 R5(d) and R10 in tools/validate.py M7 (session 4e2).

Synthetic fixtures only; exchanges/*.json is never read here. The checks
take ``today`` as a parameter, so no test reads the wall clock.

R5(d): a past-due predicted entry passes iff it is held on doubt (check
5b's predicate, check_verification.held_on_doubt), its recheck_date has not
passed, and that recheck_date is at most 30 days after the entry's date.
R10: a predicted entry dated today to today + 14 warns; the exit code does
not change.
"""
import copy
import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_verification as cv  # noqa: E402
import validate  # noqa: E402

ENTRY_DATE = "2026-12-24"
TODAY_PAST = date(2026, 12, 25)  # the day after the entry


def _exchange(*, recheck="2026-12-31", label="BSX notices; 2026-12-24 unconfirmed",
              unconfirmed=(ENTRY_DATE,), last_checked="2026-11-28", predicted=True,
              coverage=True, where="explicit"):
    entry = {"date": ENTRY_DATE, "name": "Christmas Eve (predicted)", "status": "early_close",
             "early_close_time": "14:00", "source_url": "https://example.invalid/notice"}
    if predicted is not None:
        entry["predicted"] = predicted
    ex = {"code": "XTST", "holidays": {"explicit": []}, "ad_hoc_closures": [],
          "verification": {"last_checked": last_checked}}
    if where == "explicit":
        ex["holidays"]["explicit"].append(entry)
    else:
        ex["ad_hoc_closures"].append(entry)
    if coverage:
        span = {"from": "2025-01-01", "to": "2026-12-31", "source": label}
        if unconfirmed is not None:
            span["unconfirmed"] = list(unconfirmed)
        if recheck is not None:
            span["recheck_date"] = recheck
        ex["verification"]["coverage"] = {"from": "2025-01-01", "to": "2026-12-31",
                                          "sources": [span]}
    return ex


def _errors(ex, today=TODAY_PAST):
    return validate.check_past_due_predictions(ex, "XTST.json", today)


# --- R5(d): failing cases -------------------------------------------------

def test_past_due_not_held_fails():
    # Not listed unconfirmed: the span backs the date, nothing holds it.
    errs = _errors(_exchange(unconfirmed=()))
    assert len(errs) == 1 and "is not held on doubt" in errs[0]


def test_past_due_without_coverage_fails():
    # Exchanges without coverage spans keep the pre-ADR behaviour: red.
    errs = _errors(_exchange(coverage=False))
    assert len(errs) == 1 and "no coverage span holds it" in errs[0]


def test_held_but_label_does_not_say_unconfirmed_fails():
    errs = _errors(_exchange(label="BSX 2026 festive notice"))
    assert len(errs) == 1 and "is not held on doubt" in errs[0]


def test_held_but_recheck_over_check5b_cap_fails():
    # Check 5b's own cap: recheck_date more than 92 days after last_checked.
    errs = _errors(_exchange(last_checked="2026-09-01", recheck="2026-12-31"))
    assert len(errs) == 1 and "is not held on doubt" in errs[0]


def test_held_but_recheck_passed_fails():
    errs = _errors(_exchange(recheck="2026-12-22"))
    assert len(errs) == 1 and "recheck_date 2026-12-22" in errs[0] and "has passed" in errs[0]


def test_held_but_recheck_more_than_30_days_after_date_fails():
    # 2027-01-24 is 31 days after 2026-12-24; it is still within check 5b's cap.
    ex = _exchange(recheck="2027-01-24")
    assert cv.held_on_doubt(ex["verification"]["coverage"]["sources"][0], "2026-11-28")
    errs = _errors(ex)
    assert len(errs) == 1 and "more than 30 days after the entry's date" in errs[0]


def test_held_on_doubt_but_verified_fails():
    # R2: a predicted entry is never verified. In 2.x a holiday entry has no
    # `verified` field; the date is verified when its span backs it (not
    # listed unconfirmed) under a label that claims the exchange's notice.
    # Such an entry is not held on doubt, so M7 fails it once past due.
    ex = _exchange(label="BSX 2026 festive notice (verified)", unconfirmed=())
    errs = _errors(ex)
    assert len(errs) == 1 and "is not held on doubt" in errs[0]


def test_past_due_ad_hoc_closure_not_held_fails():
    errs = _errors(_exchange(where="ad_hoc", unconfirmed=()))
    assert len(errs) == 1


def test_error_names_the_r5_options_not_a_general_remove():
    msg = _errors(_exchange(unconfirmed=()))[0]
    for part in ("ADR 0016 R5", "(a) a notice confirms it", "(b) the notice gives another date",
                 "(c) the notice shows a trading day: remove the entry", "(d) no notice read yet"):
        assert part in msg, part
    assert "or remove the entry." not in msg


# --- R5(d): passing cases -------------------------------------------------

def test_held_and_within_cap_passes():
    assert _errors(_exchange(recheck="2026-12-31")) == []


def test_held_with_recheck_exactly_30_days_after_passes():
    assert _errors(_exchange(recheck="2027-01-23")) == []


def test_held_on_the_recheck_date_itself_passes():
    assert _errors(_exchange(recheck="2026-12-25")) == []


def test_not_yet_past_due_needs_no_hold():
    # On the entry's date and before it, M7 has nothing to say.
    ex = _exchange(coverage=False)
    assert _errors(ex, date(2026, 12, 24)) == []
    assert _errors(ex, date(2026, 12, 1)) == []


def test_unflagged_entries_are_ignored():
    for flag in (None, False):
        assert _errors(_exchange(predicted=flag, coverage=False)) == []


# --- R10: the 14-day warning ------------------------------------------------

def _warnings(ex, today):
    return validate.predicted_due_warnings(ex, "XTST.json", today)


def test_due_in_14_days_warns():
    w = _warnings(_exchange(), date(2026, 12, 10))
    assert len(w) == 1 and "due in 14 day(s)" in w[0]


def test_due_in_15_days_is_silent():
    assert _warnings(_exchange(), date(2026, 12, 9)) == []


def test_due_today_warns_and_past_is_silent():
    assert len(_warnings(_exchange(), date(2026, 12, 24))) == 1
    assert _warnings(_exchange(), TODAY_PAST) == []


def _write_tree(tmp_path, ex, monkeypatch):
    # main() runs every layer; the synthetic file is not a full exchange, so
    # the other layers are stubbed and only the M7 checks speak.
    for name in ("validate_schema", "validate_business_logic", "check_weekend_dates",
                 "check_islamic_holidays", "check_generation_range",
                 "check_predicted_consistency"):
        monkeypatch.setattr(validate, name, lambda *a, **k: [])
    monkeypatch.setattr(validate, "validate_cross_exchange", lambda *a, **k: [])
    d = tmp_path / "exchanges"
    d.mkdir()
    (d / "XTST.json").write_text(json.dumps(ex))
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"type": "object"}))
    return d, schema


def test_warning_does_not_change_exit_code(tmp_path, capsys, monkeypatch):
    d, schema = _write_tree(tmp_path, _exchange(), monkeypatch)
    with pytest.raises(SystemExit) as exc:
        validate.main([str(d), str(schema), "--today", "2026-12-10"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "WARNING: XTST.json: XTST predicted entry 2026-12-24" in out
    assert "OK: 1 exchange file(s) validated successfully" in out


def test_cli_today_fails_past_due_not_held(tmp_path, capsys, monkeypatch):
    d, schema = _write_tree(tmp_path, _exchange(unconfirmed=()), monkeypatch)
    with pytest.raises(SystemExit) as exc:
        validate.main([str(d), str(schema), "--today=2026-12-25"])
    assert exc.value.code == 1
    assert "is past-due and is not held on doubt" in capsys.readouterr().out


def test_cli_rejects_a_bad_today(tmp_path, monkeypatch):
    d, schema = _write_tree(tmp_path, _exchange(), monkeypatch)
    with pytest.raises(SystemExit) as exc:
        validate.main([str(d), str(schema), "--today", "25/12/2026"])
    assert exc.value.code == 2


# --- one predicate ------------------------------------------------------------

def test_m7_uses_check5b_predicate(monkeypatch):
    # validate.py has no copy of the held-on-doubt rule: replacing check 5b's
    # predicate changes M7's answer.
    ex = _exchange(recheck="2026-12-31")
    assert _errors(ex) == []
    monkeypatch.setattr(cv, "held_on_doubt", lambda span, last_checked: set())
    assert len(_errors(copy.deepcopy(ex))) == 1
