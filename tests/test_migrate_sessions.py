"""Tests for tools/migrate_sessions.py."""
import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import migrate_sessions as ms  # noqa: E402


def _write(tmp_path, name, payload):
    p = tmp_path / name
    p.write_text(json.dumps(payload))
    return p


def test_scalars_only_produce_one_regular(tmp_path):
    p = _write(tmp_path, "X.json", {
        "regular_hours": {"open": "09:30", "close": "16:00"},
        "extended_hours": {},
        "sessions": [],
    })
    d = json.loads(p.read_text())
    out = ms._canonical(d, p)
    assert out is not None
    assert len(out["sessions"]) == 1
    assert out["sessions"][0]["type"] == "regular"


def test_scalars_with_extended_produce_three(tmp_path):
    p = _write(tmp_path, "X.json", {
        "regular_hours": {"open": "09:30", "close": "16:00"},
        "extended_hours": {
            "pre_market": {"open": "04:00", "close": "09:30"},
            "after_hours": {"open": "16:00", "close": "20:00"},
        },
        "sessions": [],
    })
    d = json.loads(p.read_text())
    out = ms._canonical(d, p)
    assert out is not None
    assert [s["type"] for s in out["sessions"]] == \
        ["pre_market", "regular", "post_market"]


def test_preexisting_lunch_break_preserved(tmp_path):
    p = _write(tmp_path, "X.json", {
        "regular_hours": {"open": "09:00", "close": "15:00"},
        "extended_hours": {},
        "sessions": [
            {"type": "lunch_break", "open": "11:30", "close": "12:30"},
        ],
    })
    d = json.loads(p.read_text())
    out = ms._canonical(d, p)
    assert out is not None
    types = [s["type"] for s in out["sessions"]]
    assert "lunch_break" in types
    assert "regular" in types
    # regular opens at 09:00, lunch break at 11:30 → regular first
    assert types == ["regular", "lunch_break"]


def test_preexisting_auction_preserved(tmp_path):
    p = _write(tmp_path, "X.json", {
        "regular_hours": {"open": "09:30", "close": "16:00"},
        "extended_hours": {},
        "sessions": [
            {"type": "auction", "at": "16:00"},
        ],
    })
    d = json.loads(p.read_text())
    out = ms._canonical(d, p)
    assert out is not None
    types = [s["type"] for s in out["sessions"]]
    assert "auction" in types
    assert "regular" in types


def test_check_exits_zero_on_canonical(tmp_path):
    p = _write(tmp_path, "X.json", {
        "regular_hours": {"open": "09:30", "close": "16:00"},
        "extended_hours": {},
        "sessions": [{"type": "regular", "open": "09:30", "close": "16:00"}],
    })
    rc = ms.main(["--check", "--quiet", str(p)])
    assert rc == 0


def test_check_exits_one_when_migration_needed(tmp_path):
    p = _write(tmp_path, "X.json", {
        "regular_hours": {"open": "09:30", "close": "16:00"},
        "extended_hours": {},
        "sessions": [],
    })
    rc = ms.main(["--check", "--quiet", str(p)])
    assert rc == 1
