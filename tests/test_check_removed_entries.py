"""Tests for tools/check_removed_entries.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import check_removed_entries as cre  # noqa: E402


# ── Fixture helpers ─────────────────────────────────────────────────

def _write_dir(tmp_path: Path, entries: dict) -> Path:
    """Write a directory of exchange JSONs.

    entries: {mic: {"name": str, "holidays": [date_str, ...]}}
    Returns the directory path.
    """
    d = tmp_path / "exchanges"
    d.mkdir(exist_ok=True)
    for mic, info in entries.items():
        payload = {
            "code": mic,
            "mic": mic,
            "name": info.get("name", f"Test {mic}"),
            "timezone": "UTC",
            "regular_hours": {"open": "09:00", "close": "17:00"},
            "holidays": {
                "explicit": [
                    {"date": dt, "name": "H", "status": "closed"}
                    for dt in info.get("holidays", [])
                ],
                "recurrence_rules": [],
            },
            "generation_range": ["2025-01-01", "2025-12-31"],
        }
        (d / f"{mic}.json").write_text(json.dumps(payload))
    return d


def _write_single_exchange(path: Path, mic: str, name: str,
                           holidays=None) -> Path:
    payload = {
        "code": mic, "mic": mic, "name": name,
        "timezone": "UTC",
        "regular_hours": {"open": "09:00", "close": "17:00"},
        "holidays": {
            "explicit": [
                {"date": dt, "name": "H", "status": "closed"}
                for dt in (holidays or [])
            ],
            "recurrence_rules": [],
        },
        "generation_range": ["2025-01-01", "2025-12-31"],
    }
    path.write_text(json.dumps(payload))
    return path


# ── load_dataset ────────────────────────────────────────────────────

def test_load_dataset_directory(tmp_path):
    d = _write_dir(tmp_path, {
        "XNYS": {"holidays": ["2025-01-01"]},
        "XLON": {"holidays": ["2025-12-25"]},
    })
    out = cre.load_dataset(d)
    assert out is not None
    assert set(out.keys()) == {"XNYS", "XLON"}


def test_load_dataset_empty_directory_returns_none(tmp_path, capsys):
    d = tmp_path / "exchanges"
    d.mkdir()
    assert cre.load_dataset(d) is None
    assert "no *.json" in capsys.readouterr().err


def test_load_dataset_missing_path_returns_none(tmp_path, capsys):
    assert cre.load_dataset(tmp_path / "nope") is None
    assert "not found" in capsys.readouterr().err


def test_load_dataset_malformed_json_returns_none(tmp_path, capsys):
    d = tmp_path / "exchanges"
    d.mkdir()
    (d / "XNYS.json").write_text("not json {")
    assert cre.load_dataset(d) is None
    assert "not valid JSON" in capsys.readouterr().err


def test_load_dataset_single_exchange_object(tmp_path):
    p = _write_single_exchange(tmp_path / "one.json", "XNYS", "NYSE")
    out = cre.load_dataset(p)
    assert out is not None
    assert "XNYS" in out


def test_load_dataset_list_shape(tmp_path):
    p = tmp_path / "list.json"
    p.write_text(json.dumps([
        {"mic": "XNYS", "name": "NYSE", "holidays": {"explicit": []}},
        {"mic": "XLON", "name": "LSE", "holidays": {"explicit": []}},
    ]))
    out = cre.load_dataset(p)
    assert out is not None
    assert set(out.keys()) == {"XNYS", "XLON"}


def test_load_dataset_exchanges_wrapper_shape(tmp_path):
    p = tmp_path / "wrapper.json"
    p.write_text(json.dumps({
        "meta": {"version": "x"},
        "exchanges": [
            {"mic": "XNYS", "name": "NYSE", "holidays": {"explicit": []}},
        ],
    }))
    out = cre.load_dataset(p)
    assert out is not None
    assert "XNYS" in out


def test_load_dataset_mic_keyed_dict(tmp_path):
    p = tmp_path / "dict.json"
    p.write_text(json.dumps({
        "XNYS": {"name": "NYSE", "holidays": {"explicit": []}},
        "XLON": {"name": "LSE", "holidays": {"explicit": []}},
    }))
    out = cre.load_dataset(p)
    assert out is not None
    assert set(out.keys()) == {"XNYS", "XLON"}


def test_load_dataset_unrecognized_shape_returns_none(tmp_path, capsys):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"some": "other", "shape": True}))
    assert cre.load_dataset(p) is None
    assert "unrecognized" in capsys.readouterr().err


# ── diff_removals ───────────────────────────────────────────────────

def test_diff_no_removals():
    old = {"XNYS": {"name": "NYSE", "holidays": {"explicit": [
        {"date": "2025-01-01"}, {"date": "2025-12-25"},
    ]}}}
    new = {"XNYS": {"name": "NYSE", "holidays": {"explicit": [
        {"date": "2025-01-01"}, {"date": "2025-12-25"},
    ]}}}
    r = cre.diff_removals(old, new)
    assert not cre.has_removals(r)


def test_diff_holiday_removed():
    old = {"XNYS": {"name": "NYSE", "holidays": {"explicit": [
        {"date": "2025-01-01"}, {"date": "2025-12-25"},
    ]}}}
    new = {"XNYS": {"name": "NYSE", "holidays": {"explicit": [
        {"date": "2025-12-25"},
    ]}}}
    r = cre.diff_removals(old, new)
    assert r["holidays"] == [("XNYS", "2025-01-01")]
    assert r["exchanges"] == []


def test_diff_all_holidays_removed():
    old = {"XNYS": {"name": "NYSE", "holidays": {"explicit": [
        {"date": "2025-01-01"}, {"date": "2025-12-25"},
    ]}}}
    new = {"XNYS": {"name": "NYSE", "holidays": {"explicit": []}}}
    r = cre.diff_removals(old, new)
    # Collapsed into one summary line, not two individual removals
    assert r["all_holidays_removed"] == [("XNYS", 2)]
    assert r["holidays"] == []


def test_diff_exchange_removed():
    old = {
        "XNYS": {"name": "NYSE", "holidays": {"explicit": []}},
        "XLON": {"name": "LSE", "holidays": {"explicit": []}},
    }
    new = {"XNYS": {"name": "NYSE", "holidays": {"explicit": []}}}
    r = cre.diff_removals(old, new)
    assert ("XLON",) in r["exchanges"]


def test_diff_mic_renamed():
    old = {"XNAS": {"name": "NASDAQ", "holidays": {"explicit": []}}}
    new = {"ZZZZ": {"name": "NASDAQ", "holidays": {"explicit": []}}}
    r = cre.diff_removals(old, new)
    assert r["mic_renames"] == [("XNAS", "ZZZZ", "NASDAQ")]
    assert r["exchanges"] == []


def test_diff_rename_without_name_match_is_removal():
    """An old MIC disappears, and a new MIC with a DIFFERENT name
    appears. Not a rename — an exchange removed plus an exchange
    added."""
    old = {"XNAS": {"name": "NASDAQ", "holidays": {"explicit": []}}}
    new = {"ZZZZ": {"name": "Something Else", "holidays": {"explicit": []}}}
    r = cre.diff_removals(old, new)
    assert r["mic_renames"] == []
    assert ("XNAS",) in r["exchanges"]


def test_diff_holiday_added_is_not_removal():
    old = {"XNYS": {"name": "NYSE", "holidays": {"explicit": [
        {"date": "2025-01-01"},
    ]}}}
    new = {"XNYS": {"name": "NYSE", "holidays": {"explicit": [
        {"date": "2025-01-01"}, {"date": "2025-12-25"},
    ]}}}
    r = cre.diff_removals(old, new)
    assert not cre.has_removals(r)


def test_diff_mic_added_is_not_removal():
    old = {"XNYS": {"name": "NYSE", "holidays": {"explicit": []}}}
    new = {
        "XNYS": {"name": "NYSE", "holidays": {"explicit": []}},
        "XLON": {"name": "LSE", "holidays": {"explicit": []}},
    }
    r = cre.diff_removals(old, new)
    assert not cre.has_removals(r)


def test_diff_mixed_removals():
    old = {
        "XNYS": {"name": "NYSE", "holidays": {"explicit": [
            {"date": "2025-01-01"},
        ]}},
        "XLON": {"name": "LSE", "holidays": {"explicit": []}},
        "XNAS": {"name": "NASDAQ", "holidays": {"explicit": []}},
    }
    new = {
        "XNYS": {"name": "NYSE", "holidays": {"explicit": []}},   # all removed
        # XLON removed entirely
        "ZZZZ": {"name": "NASDAQ", "holidays": {"explicit": []}},  # rename
    }
    r = cre.diff_removals(old, new)
    assert r["all_holidays_removed"] == [("XNYS", 1)]
    assert ("XLON",) in r["exchanges"]
    assert ("XNAS", "ZZZZ", "NASDAQ") in r["mic_renames"]


# ── has_removals ────────────────────────────────────────────────────

def test_has_removals_false():
    r = {"holidays": [], "all_holidays_removed": [],
         "exchanges": [], "mic_renames": []}
    assert not cre.has_removals(r)


def test_has_removals_true():
    r = {"holidays": [("XNYS", "2025-01-01")],
         "all_holidays_removed": [],
         "exchanges": [], "mic_renames": []}
    assert cre.has_removals(r)


# ── format_removals ─────────────────────────────────────────────────

def test_format_removals_names_all_classes():
    r = {
        "holidays": [("XNYS", "2025-01-01")],
        "all_holidays_removed": [("XLON", 5)],
        "exchanges": [("XZZZ",)],
        "mic_renames": [("XNAS", "ZZZZ", "NASDAQ")],
    }
    out = cre.format_removals(r)
    assert "XNYS" in out and "2025-01-01" in out
    assert "XLON" in out and "5" in out
    assert "XZZZ" in out
    assert "XNAS" in out and "ZZZZ" in out


# ── CLI: main ───────────────────────────────────────────────────────

def test_main_no_removals_exit_0(tmp_path):
    d = _write_dir(tmp_path, {"XNYS": {"holidays": ["2025-01-01"]}})
    assert cre.main(["--old", str(d), "--new", str(d)]) == 0


def test_main_removals_exit_1(tmp_path):
    old = _write_dir(tmp_path / "old", {"XNYS": {"holidays": ["2025-01-01"]}})
    new = _write_dir(tmp_path / "new", {"XNYS": {"holidays": []}})
    assert cre.main(["--old", str(old), "--new", str(new)]) == 1


def test_main_quiet_one_line(tmp_path, capsys):
    old = _write_dir(tmp_path / "old", {"XNYS": {"holidays": ["2025-01-01"]}})
    new = _write_dir(tmp_path / "new", {"XNYS": {"holidays": []}})
    rc = cre.main(["--old", str(old), "--new", str(new), "--quiet"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert out.count("\n") <= 2


def test_main_json_shape(tmp_path, capsys):
    old = _write_dir(tmp_path / "old", {"XNYS": {"holidays": ["2025-01-01"]}})
    new = _write_dir(tmp_path / "new", {"XNYS": {"holidays": []}})
    rc = cre.main(["--old", str(old), "--new", str(new), "--json"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["has_removals"] is True
    assert out["removals"]["all_holidays_removed"] == [
        {"mic": "XNYS", "count": 1}
    ]


def test_main_quiet_and_json_mutually_exclusive(tmp_path, capsys):
    d = _write_dir(tmp_path, {"XNYS": {"holidays": []}})
    rc = cre.main(["--old", str(d), "--new", str(d),
                   "--quiet", "--json"])
    assert rc == 2
    assert "mutually exclusive" in capsys.readouterr().err


def test_main_missing_old_exit_2(tmp_path, capsys):
    d = _write_dir(tmp_path, {"XNYS": {"holidays": []}})
    rc = cre.main(["--old", str(tmp_path / "nope"), "--new", str(d)])
    assert rc == 2
    assert "not found" in capsys.readouterr().err


def test_main_malformed_json_exit_2(tmp_path, capsys):
    d = tmp_path / "old"
    d.mkdir()
    (d / "XNYS.json").write_text("not json")
    n = _write_dir(tmp_path / "new", {"XNYS": {"holidays": []}})
    rc = cre.main(["--old", str(d), "--new", str(n)])
    assert rc == 2
    assert "not valid JSON" in capsys.readouterr().err


def test_main_new_json_alias(tmp_path):
    """--new-json is an alias for --new with a single file."""
    old = _write_dir(tmp_path / "old", {"XNYS": {"holidays": []}})
    f = _write_single_exchange(tmp_path / "one.json", "XNYS", "NYSE", [])
    assert cre.main(["--old", str(old), "--new-json", str(f)]) == 0


# ── Real repo ───────────────────────────────────────────────────────

def test_real_repo_no_removals():
    """Running the tool against the repo's own exchanges/ twice must
    report no removals."""
    repo_root = Path(__file__).resolve().parent.parent
    exchanges = repo_root / "exchanges"
    if not exchanges.exists():
        pytest.skip("exchanges/ not present")
    assert cre.main(["--old", str(exchanges), "--new", str(exchanges)]) == 0
