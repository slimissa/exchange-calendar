"""Tests for tools/check_mic_codes.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import check_mic_codes as cmc  # noqa: E402


# ── Fixtures ────────────────────────────────────────────────────────

def _make_snapshot(tmp_path: Path, mics: list[str]) -> Path:
    """Write a minimal ISO 10383 snapshot with the given MIC list."""
    snap = tmp_path / "iso10383_snapshot.json"
    snap.write_text(json.dumps({
        "meta": {
            "source": "github.com/slimissa/iso10383",
            "source_version": "0.0.0-test",
            "refresh_cadence": "monthly",
            "review_by": "2027-03-01",
        },
        "mics": mics,
    }, indent=2))
    return snap


def _make_exchange(tmp_path: Path, mic: str, code: str | None = None) -> Path:
    """Write a minimal exchange JSON. `code` defaults to `mic`."""
    d = {
        "code": code if code is not None else mic,
        "mic": mic,
        "name": f"Test {mic}",
        "timezone": "UTC",
        "regular_hours": {"open": "09:00", "close": "17:00"},
        "holidays": {"explicit": [], "recurrence_rules": []},
        "generation_range": ["2025-01-01", "2025-12-31"],
    }
    exch = tmp_path / "exchanges"
    exch.mkdir(exist_ok=True)
    (exch / f"{mic}.json").write_text(json.dumps(d, indent=2))
    return exch


def _make_allowlist(tmp_path: Path, allowed: dict) -> Path:
    p = tmp_path / "mic_allowlist.json"
    p.write_text(json.dumps({"_comment": "test", "allowed": allowed}, indent=2))
    return p


# ── Happy path ──────────────────────────────────────────────────────

def test_all_match_passes(tmp_path):
    snap = _make_snapshot(tmp_path, ["XNYS", "XLON"])
    exch = _make_exchange(tmp_path, "XNYS")
    _make_exchange(tmp_path, "XLON")
    assert cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)]) == 0


def test_quiet_mode_passes(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = _make_exchange(tmp_path, "XNYS")
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch),
                   "--quiet"])
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_json_mode_shape(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = _make_exchange(tmp_path, "XNYS")
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch),
                   "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["exchanges_checked"] == 1
    assert out["errors"] == []
    assert out["iso10383_version"] == "0.0.0-test"


# ── Failure cases ───────────────────────────────────────────────────

def test_unknown_mic_fails(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = _make_exchange(tmp_path, "ZZZZ")
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "ZZZZ" in capsys.readouterr().out


def test_missing_mic_fails(tmp_path, capsys):
    """Exchange JSON with no `mic` field."""
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = tmp_path / "exchanges"
    exch.mkdir()
    (exch / "XNYS.json").write_text(json.dumps({
        "code": "XNYS",
        "name": "Test",
        "timezone": "UTC",
    }))
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "missing mic" in capsys.readouterr().out


def test_mic_not_matching_filename_fails(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, ["XNYS", "XLON"])
    exch = _make_exchange(tmp_path, "XNYS")
    # Hand-write a file whose stem != its mic field
    (exch / "XLON.json").write_text(json.dumps({
        "code": "XNAS", "mic": "XNAS", "name": "Test",
        "timezone": "UTC",
        "regular_hours": {"open": "09:00", "close": "17:00"},
        "holidays": {"explicit": [], "recurrence_rules": []},
        "generation_range": ["2025-01-01", "2025-12-31"],
    }))
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "does not match filename" in capsys.readouterr().out


def test_code_differs_from_mic_fails(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = _make_exchange(tmp_path, "XNYS", code="ZZZZ")
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "does not match mic" in capsys.readouterr().out


def test_bad_mic_pattern_fails(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, ["xnys"])
    # lowercase mic
    exch = _make_exchange(tmp_path, "xnys")
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "mic not" in capsys.readouterr().out


# ── Allowlist ───────────────────────────────────────────────────────

def test_allowlisted_mic_passes(tmp_path):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = _make_exchange(tmp_path, "ZZZZ")
    al = _make_allowlist(tmp_path, {"ZZZZ": "documented reason"})
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch),
                   "--allowlist", str(al)])
    assert rc == 0


def test_allowlist_missing_is_ok(tmp_path):
    """No allowlist file at the given path → treated as empty."""
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = _make_exchange(tmp_path, "XNYS")
    al = tmp_path / "does-not-exist.json"
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch),
                   "--allowlist", str(al)])
    assert rc == 0


def test_allowlist_malformed_exits_2(tmp_path):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = _make_exchange(tmp_path, "XNYS")
    al = tmp_path / "mic_allowlist.json"
    al.write_text("not json at all {")
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch),
                   "--allowlist", str(al)])
    assert rc == 2


# ── Environment failure cases (exit 2) ──────────────────────────────

def test_missing_snapshot_exits_2(tmp_path):
    exch = _make_exchange(tmp_path, "XNYS")
    rc = cmc.main(["--snapshot", str(tmp_path / "nope.json"),
                   "--exchanges-dir", str(exch)])
    assert rc == 2


def test_invalid_snapshot_json_exits_2(tmp_path):
    snap = tmp_path / "iso10383_snapshot.json"
    snap.write_text("not json {")
    exch = _make_exchange(tmp_path, "XNYS")
    assert cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)]) == 2


def test_snapshot_missing_mics_array_exits_2(tmp_path):
    snap = tmp_path / "iso10383_snapshot.json"
    snap.write_text(json.dumps({"meta": {}}))
    exch = _make_exchange(tmp_path, "XNYS")
    assert cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)]) == 2


def test_missing_exchanges_dir_exits_2(tmp_path):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    rc = cmc.main(["--snapshot", str(snap),
                   "--exchanges-dir", str(tmp_path / "nope")])
    assert rc == 2


def test_empty_exchanges_dir_exits_2(tmp_path):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    empty = tmp_path / "exchanges"
    empty.mkdir()
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(empty)])
    assert rc == 2


# ── Refresh ─────────────────────────────────────────────────────────

def test_refresh_from_copies_file(tmp_path):
    src = tmp_path / "source-iso10383.json"
    src.write_text(json.dumps({
        "meta": {"version": "9.9.9"},
        "mics": [
            {"mic": "XNYS", "mic_type": "OPERATING", "status": "ACTIVE"},
            {"mic": "XLON", "mic_type": "OPERATING", "status": "ACTIVE"},
        ],
    }))
    dest = tmp_path / "iso10383_snapshot.json"
    exch = _make_exchange(tmp_path, "XNYS")
    _make_exchange(tmp_path, "XLON")
    rc = cmc.main(["--snapshot", str(dest), "--exchanges-dir", str(exch),
                   "--refresh-from", str(src), "--quiet"])
    assert rc == 0
    d = json.loads(dest.read_text())
    assert "XNYS" in d["mics"]
    assert d["meta"]["source_version"] == "9.9.9"


def test_refresh_from_invalid_source_exits_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    dest = tmp_path / "iso10383_snapshot.json"
    exch = _make_exchange(tmp_path, "XNYS")
    rc = cmc.main(["--snapshot", str(dest), "--exchanges-dir", str(exch),
                   "--refresh-from", str(bad)])
    assert rc == 2


# ── Args ────────────────────────────────────────────────────────────

def test_quiet_and_json_mutually_exclusive(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, ["XNYS"])
    exch = _make_exchange(tmp_path, "XNYS")
    rc = cmc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch),
                   "--quiet", "--json"])
    assert rc == 2
    assert "mutually exclusive" in capsys.readouterr().err
