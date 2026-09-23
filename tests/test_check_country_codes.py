"""Tests for tools/check_country_codes.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import check_country_codes as ccc  # noqa: E402


# ── Fixtures ────────────────────────────────────────────────────────

def _make_snapshot(tmp_path: Path, entries: list[tuple[str, str]]) -> Path:
    """entries is a list of (alpha_2, name) tuples."""
    snap = tmp_path / "iso3166_snapshot.json"
    snap.write_text(json.dumps({
        "meta": {"version": "0.0.0-test"},
        "countries": {
            "active": [{"alpha_2": c, "name": n} for c, n in entries]
        },
    }, indent=2))
    return snap


def _make_exchange(tmp_path: Path, mic: str, code: str | None, name: str | None) -> Path:
    d = {
        "code": mic, "mic": mic, "name": f"Test {mic}",
        "timezone": "UTC",
        "regular_hours": {"open": "09:00", "close": "17:00"},
        "holidays": {"explicit": [], "recurrence_rules": []},
        "generation_range": ["2025-01-01", "2025-12-31"],
    }
    if code is not None:
        d["country_code"] = code
    if name is not None:
        d["country"] = name
    exch = tmp_path / "exchanges"
    exch.mkdir(exist_ok=True)
    (exch / f"{mic}.json").write_text(json.dumps(d, indent=2))
    return exch


# ── Happy path ──────────────────────────────────────────────────────

def test_all_match_passes(tmp_path):
    snap = _make_snapshot(tmp_path, [("US", "United States of America"),
                                     ("GB", "United Kingdom")])
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    _make_exchange(tmp_path, "XLON", "GB", "United Kingdom")
    assert ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)]) == 0


def test_quiet_mode_passes(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch), "--quiet"])
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_json_mode_shape(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch), "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["exchanges_checked"] == 1
    assert out["errors"] == []


# ── Failure cases ───────────────────────────────────────────────────

def test_unknown_country_code_fails(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "ZZ", "Nowhere")
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "not in ISO 3166" in capsys.readouterr().out


def test_mismatched_country_name_fails(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States")  # short form
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "does not match" in capsys.readouterr().out


def test_missing_country_code_fails(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", None, "United States of America")
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "missing country_code" in capsys.readouterr().out


def test_missing_country_name_fails(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "US", None)
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)])
    assert rc == 1
    assert "missing country" in capsys.readouterr().out


def test_lowercase_country_code_fails(tmp_path):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "us", "United States of America")
    assert ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)]) == 1


def test_three_letter_country_code_fails(tmp_path):
    snap = _make_snapshot(tmp_path, [("USA", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "USA", "United States of America")
    assert ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)]) == 1


# ── Environment failure cases (exit 2) ──────────────────────────────

def test_missing_snapshot_exits_2(tmp_path):
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    rc = ccc.main(["--snapshot", str(tmp_path / "nope.json"),
                   "--exchanges-dir", str(exch)])
    assert rc == 2


def test_invalid_snapshot_json_exits_2(tmp_path):
    snap = tmp_path / "iso3166_snapshot.json"
    snap.write_text("not json at all {")
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    assert ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)]) == 2


def test_snapshot_missing_active_array_exits_2(tmp_path):
    snap = tmp_path / "iso3166_snapshot.json"
    snap.write_text(json.dumps({"meta": {}, "countries": {}}))
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    assert ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch)]) == 2


def test_missing_exchanges_dir_exits_2(tmp_path):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    rc = ccc.main(["--snapshot", str(snap),
                   "--exchanges-dir", str(tmp_path / "nope")])
    assert rc == 2


def test_empty_exchanges_dir_exits_2(tmp_path):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    empty = tmp_path / "exchanges"
    empty.mkdir()
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(empty)])
    assert rc == 2


# ── Refresh snapshot ────────────────────────────────────────────────

def test_refresh_from_copies_file(tmp_path):
    source = _make_snapshot(tmp_path, [("US", "United States of America")])
    dest = tmp_path / "dest" / "iso3166_snapshot.json"
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    rc = ccc.main(["--snapshot", str(dest), "--exchanges-dir", str(exch),
                   "--refresh-from", str(source), "--quiet"])
    assert rc == 0
    assert dest.exists()
    assert json.loads(dest.read_text()) == json.loads(source.read_text())


def test_refresh_from_invalid_source_exits_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    dest = tmp_path / "dest.json"
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    rc = ccc.main(["--snapshot", str(dest), "--exchanges-dir", str(exch),
                   "--refresh-from", str(bad)])
    assert rc == 2


def test_refresh_from_same_path_exits_2(tmp_path):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch),
                   "--refresh-from", str(snap)])
    assert rc == 2


# ── Argument handling ───────────────────────────────────────────────

def test_quiet_and_json_mutually_exclusive(tmp_path, capsys):
    snap = _make_snapshot(tmp_path, [("US", "United States of America")])
    exch = _make_exchange(tmp_path, "XNYS", "US", "United States of America")
    rc = ccc.main(["--snapshot", str(snap), "--exchanges-dir", str(exch),
                   "--quiet", "--json"])
    assert rc == 2
    assert "mutually exclusive" in capsys.readouterr().err
