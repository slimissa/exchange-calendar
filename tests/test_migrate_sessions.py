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


# ── 4b11.1: dated regular_hours ─────────────────────────────────────
# release.sh 2.39.0 stopped at `migrate_sessions --check` (NEEDS XASX), and
# write mode collapsed XASX's dated list to one object and moved
# after_hours back to 16:00. pytest never ran the check.

import validate as vd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATED = {
    "regular_hours": [
        {"effective_from": "1990-01-01", "open": "10:00", "close": "16:00"},
        {"effective_from": "2026-11-22", "open": "10:00", "close": "16:10"},
    ],
    "extended_hours": {
        "pre_market": {"open": "07:00", "close": "10:00"},
        "after_hours": {"open": "16:10", "close": "16:12"},
    },
    "sessions": [
        {"type": "pre_market", "open": "07:00", "close": "10:00"},
        {"type": "regular", "open": "10:00", "close": "16:10"},
        {"type": "auction", "at": "10:00"},
        {"type": "post_market", "open": "16:00", "close": "16:12"},
        {"type": "auction", "at": "16:00"},
    ],
}


def test_dated_list_round_trips_unchanged_and_is_idempotent(tmp_path):
    p = _write(tmp_path, "X.json", DATED)
    d = json.loads(p.read_text())
    assert ms._needs_migration(d) is False
    once = ms._canonical(d, p)
    assert once == DATED
    assert ms._canonical(once, p) == once
    assert ms.main([str(p), "--quiet"]) == 0
    assert json.loads(p.read_text()) == DATED


def test_dated_list_survives_a_real_migration(tmp_path):
    # A file that does need migrating (no sessions yet) keeps every entry.
    payload = {k: v for k, v in DATED.items() if k != "sessions"}
    payload["extended_hours"] = {"after_hours": {"open": "16:10", "close": "16:12"}}
    p = _write(tmp_path, "X.json", payload)
    assert ms.main([str(p), "--quiet"]) == 0
    out = json.loads(p.read_text())
    assert out["regular_hours"] == DATED["regular_hours"]
    assert out["extended_hours"] == {"after_hours": {"open": "16:10", "close": "16:12"}}
    assert {"type": "regular", "open": "10:00", "close": "16:10"} in out["sessions"]
    assert ms._needs_migration(out) is False


def test_regular_session_follows_the_latest_dated_entry(tmp_path):
    payload = json.loads(json.dumps(DATED))
    payload["sessions"][1] = {"type": "regular", "open": "10:00", "close": "16:00"}
    p = _write(tmp_path, "X.json", payload)
    d = json.loads(p.read_text())
    assert ms._needs_migration(d) is True
    out = ms._canonical(d, p)
    assert out["regular_hours"] == DATED["regular_hours"]
    assert {"type": "regular", "open": "10:00", "close": "16:10"} in out["sessions"]


def test_repo_is_canonical():
    # The release gate's `migrate_sessions.py --check`, run by pytest too.
    assert ms.main([str(ROOT / "exchanges"), "--check", "--quiet"]) == 0


@pytest.mark.parametrize("path", sorted((ROOT / "exchanges").glob("*.json")), ids=lambda p: p.stem)
def test_migrate_and_validate_agree_on_extended_hours(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    # Write mode would change nothing, dated lists included.
    assert ms._canonical(d, path) == d
    # validate.py's alignment (latest regular entry) holds for the same data.
    errors = [e for e in vd.validate_business_logic(d, path.name)
              if "pre_market close" in e or "after_hours open" in e]
    assert errors == []
    # Both tools align to the same entry.
    latest = ms._latest_regular(d, d.get("sessions") or [])
    ext = d.get("extended_hours") or {}
    if "after_hours" in ext:
        assert ext["after_hours"]["open"] == latest["close"]
    if "pre_market" in ext:
        assert ext["pre_market"]["close"] == latest["open"]
