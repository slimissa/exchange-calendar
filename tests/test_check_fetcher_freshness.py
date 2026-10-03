"""Tests for tools/check_fetcher_freshness.py."""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import check_fetcher_freshness as cff  # noqa: E402


# ── Fixtures ────────────────────────────────────────────────────────

def _make_manifest(tmp_path: Path, fetches: dict) -> Path:
    p = tmp_path / "fetcher_manifest.json"
    p.write_text(json.dumps({
        "meta": {"schema_version": "1.0.0"},
        "fetches": fetches,
    }, indent=2))
    return p


def _entry(fetched_at: str, max_age_days: int = 30,
           status: str = "ok") -> dict:
    return {
        "fetched_at": fetched_at,
        "source_url": "https://example.com",
        "sha256": "0" * 64,
        "bytes": 100,
        "max_age_days": max_age_days,
        "status": status,
    }


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


# ── Happy path ──────────────────────────────────────────────────────

def test_empty_manifest_passes(tmp_path):
    m = _make_manifest(tmp_path, {})
    assert cff.main(["--manifest", str(m)]) == 0


def test_single_fresh_entry_passes(tmp_path):
    m = _make_manifest(tmp_path, {"XNYS": _entry(_days_ago(5))})
    assert cff.main(["--manifest", str(m)]) == 0


def test_multiple_fresh_entries_pass(tmp_path):
    m = _make_manifest(tmp_path, {
        "XNYS": _entry(_days_ago(5)),
        "XLON": _entry(_days_ago(10), max_age_days=90),
        "XTKS": _entry(_days_ago(1), max_age_days=400),
    })
    assert cff.main(["--manifest", str(m)]) == 0


def test_quiet_mode_passes(tmp_path, capsys):
    m = _make_manifest(tmp_path, {"XNYS": _entry(_days_ago(5))})
    rc = cff.main(["--manifest", str(m), "--quiet"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out
    assert "XNYS" not in out  # quiet mode prints no per-fetcher lines


def test_json_mode_shape(tmp_path, capsys):
    m = _make_manifest(tmp_path, {"XNYS": _entry(_days_ago(5))})
    rc = cff.main(["--manifest", str(m), "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["checked"] == 1
    assert out["stale"] == 0
    assert out["results"][0]["mic"] == "XNYS"
    assert out["results"][0]["status"] == "ok"


# ── Stale cases ─────────────────────────────────────────────────────

def test_stale_entry_fails(tmp_path, capsys):
    m = _make_manifest(tmp_path,
                       {"XNYS": _entry(_days_ago(100), max_age_days=30)})
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    assert "XNYS" in capsys.readouterr().out


def test_boundary_exactly_at_max_age_passes(tmp_path):
    m = _make_manifest(tmp_path,
                       {"XNYS": _entry(_days_ago(30), max_age_days=30)})
    assert cff.main(["--manifest", str(m)]) == 0


def test_boundary_one_day_past_fails(tmp_path):
    m = _make_manifest(tmp_path,
                       {"XNYS": _entry(_days_ago(31), max_age_days=30)})
    assert cff.main(["--manifest", str(m)]) == 1


def test_today_override(tmp_path):
    m = _make_manifest(tmp_path,
                       {"XNYS": _entry("2026-01-01", max_age_days=30)})
    # age = 30 exactly → pass
    assert cff.main(["--manifest", str(m), "--today", "2026-01-31"]) == 0
    # age = 31 → fail
    assert cff.main(["--manifest", str(m), "--today", "2026-02-01"]) == 1


def test_status_failed_fails(tmp_path, capsys):
    m = _make_manifest(tmp_path,
                       {"XNYS": _entry(_days_ago(1), status="failed")})
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    assert "failed" in capsys.readouterr().out.lower()


def test_status_unknown_fails(tmp_path, capsys):
    m = _make_manifest(tmp_path,
                       {"XNYS": _entry(_days_ago(1), status="weird")})
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    assert "unknown" in capsys.readouterr().out.lower()


def test_multiple_stale_all_named(tmp_path, capsys):
    m = _make_manifest(tmp_path, {
        "XNYS": _entry(_days_ago(100), max_age_days=30),
        "XLON": _entry(_days_ago(200), max_age_days=30),
    })
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "XNYS" in out and "XLON" in out


def test_missing_fetched_at_fails(tmp_path, capsys):
    m = _make_manifest(tmp_path,
                       {"XNYS": {"status": "ok", "max_age_days": 30}})
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    assert "fetched_at" in capsys.readouterr().out


def test_missing_max_age_days_fails(tmp_path, capsys):
    m = _make_manifest(tmp_path,
                       {"XNYS": {"status": "ok",
                                 "fetched_at": "2026-01-01"}})
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    assert "max_age_days" in capsys.readouterr().out


def test_malformed_fetched_at_fails(tmp_path, capsys):
    m = _make_manifest(tmp_path,
                       {"XNYS": {"status": "ok",
                                 "fetched_at": "not-a-date",
                                 "max_age_days": 30}})
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    assert "fetched_at" in capsys.readouterr().out


def test_negative_max_age_days_fails(tmp_path, capsys):
    m = _make_manifest(tmp_path,
                       {"XNYS": _entry(_days_ago(1), max_age_days=-1)})
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    assert "max_age_days" in capsys.readouterr().out


def test_entry_not_object_fails(tmp_path, capsys):
    m = _make_manifest(tmp_path, {"XNYS": "not a dict"})
    rc = cff.main(["--manifest", str(m)])
    assert rc == 1
    assert "not an object" in capsys.readouterr().out


# ── Environment failure cases ───────────────────────────────────────

def test_missing_manifest_exits_2(tmp_path, capsys):
    rc = cff.main(["--manifest", str(tmp_path / "nope.json")])
    assert rc == 2
    assert "not found" in capsys.readouterr().err


def test_invalid_manifest_json_exits_2(tmp_path, capsys):
    p = tmp_path / "fetcher_manifest.json"
    p.write_text("not json {")
    rc = cff.main(["--manifest", str(p)])
    assert rc == 2
    assert "not valid JSON" in capsys.readouterr().err


def test_manifest_missing_fetches_exits_2(tmp_path, capsys):
    p = tmp_path / "fetcher_manifest.json"
    p.write_text(json.dumps({"meta": {}}))
    rc = cff.main(["--manifest", str(p)])
    assert rc == 2
    assert "fetches" in capsys.readouterr().err


def test_manifest_fetches_not_object_exits_2(tmp_path, capsys):
    p = tmp_path / "fetcher_manifest.json"
    p.write_text(json.dumps({"fetches": []}))
    rc = cff.main(["--manifest", str(p)])
    assert rc == 2
    assert "fetches" in capsys.readouterr().err


def test_bad_today_exits_2(tmp_path, capsys):
    m = _make_manifest(tmp_path, {})
    rc = cff.main(["--manifest", str(m), "--today", "not-a-date"])
    assert rc == 2
    assert "--today" in capsys.readouterr().err


# ── Args ────────────────────────────────────────────────────────────

def test_quiet_and_json_mutually_exclusive(tmp_path, capsys):
    m = _make_manifest(tmp_path, {})
    rc = cff.main(["--manifest", str(m), "--quiet", "--json"])
    assert rc == 2
    assert "mutually exclusive" in capsys.readouterr().err


# ── Real repo ───────────────────────────────────────────────────────

def test_real_manifest_passes():
    """The repo's own fetcher_manifest.json must pass."""
    repo_root = Path(__file__).resolve().parent.parent
    manifest = repo_root / "fetcher_manifest.json"
    if not manifest.exists():
        pytest.skip("fetcher_manifest.json not present")
    assert cff.main(["--manifest", str(manifest)]) == 0


# ── v2.9.4: manifest write is skipped when content is unchanged ─────

def test_record_manifest_skips_write_when_content_unchanged(tmp_path):
    """Re-fetching identical bytes leaves `fetched_at` untouched. The
    field records when the source last changed, not when we last
    looked; a write that only moves the timestamp dirties the tree
    for no reason."""
    import json
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
    import update_from_exchange as ufe

    # Point the module at a scratch manifest and enable the write path.
    manifest = tmp_path / "fetcher_manifest.json"
    manifest.write_text('{"fetches": {}, "meta": {"schema_version": "1.0.0"}}\n')
    monkey_manifest_path = manifest
    saved = ufe._FETCHER_MANIFEST_PATH
    saved_env = __import__("os").environ.pop("FETCHER_MANIFEST_DISABLE", None)
    ufe._FETCHER_MANIFEST_PATH = monkey_manifest_path
    try:
        f = ufe.NYSEFetcher()
        content = b"%PDF-1.7 fake bytes"
        f._record_manifest(content, status="ok")
        first = json.loads(manifest.read_text())
        assert "XNYS" in first["fetches"]
        ts1 = first["fetches"]["XNYS"]["fetched_at"]

        # Same bytes again: no write, timestamp stays.
        f._record_manifest(content, status="ok")
        second = json.loads(manifest.read_text())
        assert second["fetches"]["XNYS"]["fetched_at"] == ts1

        # Different bytes: entry updates.
        f._record_manifest(b"%PDF-1.7 other bytes", status="ok")
        third = json.loads(manifest.read_text())
        assert third["fetches"]["XNYS"]["sha256"] != first["fetches"]["XNYS"]["sha256"]
    finally:
        ufe._FETCHER_MANIFEST_PATH = saved
        if saved_env is not None:
            __import__("os").environ["FETCHER_MANIFEST_DISABLE"] = saved_env
