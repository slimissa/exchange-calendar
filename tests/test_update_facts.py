#!/usr/bin/env python3
"""
test_update_facts.py — Unit tests for update_facts.py.

Tests that the facts generator:
    1. Counts exchanges and each fetcher_status from calendar.json
    2. Derives fetchers_registered and exchanges_blocked_total from them
    3. Counts export files by extension at the repository root only
    4. Writes sorted, stable JSON, and --check passes right after a write
    5. --check exits 1 and names the fact when the tree has moved on
    6. --check ignores tests_total unless --with-tests is given
    7. Exits 2 for an unreadable calendar.json, an unknown status, a missing
       facts.json, and a failed test collection
    8. The real docs/facts.json matches the real tree

Run:
    python3 -m pytest tests/test_update_facts.py -v
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import update_facts as uf


def make_tree(tmp_path, statuses=("implemented", "implemented", "ci_unreachable", "blocked", "none", "none")):
    exchanges = [{"code": f"X{i:03d}", "fetcher_status": s} for i, s in enumerate(statuses)]
    (tmp_path / "calendar.json").write_text(json.dumps({"exchanges": exchanges, "meta": {}}))
    (tmp_path / "docs").mkdir()
    for name in ("a.sql", "b.sql", "t.csv", "t.european.csv", "t.tsv", "t.parquet"):
        (tmp_path / name).write_text("x")
    (tmp_path / "tests").mkdir()
    for name in ("test_xaaa_holidays.py", "test_xbbb_holidays.py", "test_validate.py", "helper_holidays.py"):
        (tmp_path / "tests" / name).write_text("x")
    return tmp_path


class TestDerive:
    def test_counts(self, tmp_path):
        f = uf.derive(make_tree(tmp_path), with_tests=False)
        assert f["exchanges_total"] == 6
        assert f["fetchers_implemented"] == 2
        assert f["fetchers_ci_unreachable"] == 1
        assert f["fetchers_blocked"] == 1
        assert f["exchanges_no_fetcher"] == 2

    def test_derived_totals(self, tmp_path):
        f = uf.derive(make_tree(tmp_path), with_tests=False)
        assert f["fetchers_registered"] == 4
        assert f["exchanges_blocked_total"] == 3
        assert f["fetchers_registered"] + f["exchanges_no_fetcher"] == f["exchanges_total"]

    def test_file_counts(self, tmp_path):
        f = uf.derive(make_tree(tmp_path), with_tests=False)
        assert (f["sql_files"], f["csv_tsv_files"], f["parquet_files"]) == (2, 3, 1)

    def test_test_files_count_matches_only_holiday_test_files(self, tmp_path):
        assert uf.derive(make_tree(tmp_path), with_tests=False)["test_files_count"] == 2

    def test_files_in_subdirectories_are_not_counted(self, tmp_path):
        root = make_tree(tmp_path)
        (root / "docs" / "nested.sql").write_text("x")
        assert uf.derive(root, with_tests=False)["sql_files"] == 2

    def test_no_tests_key_without_tests(self, tmp_path):
        assert "tests_total" not in uf.derive(make_tree(tmp_path), with_tests=False)

    def test_keys_are_sorted(self, tmp_path):
        keys = list(uf.derive(make_tree(tmp_path), with_tests=False))
        assert keys == sorted(keys)


class TestCheck:
    def write(self, root):
        assert uf.main(["--root", str(root)]) == 2  # no tests/ dir: collection must fail loudly
        (root / "docs" / "facts.json").write_text(uf.render(uf.derive(root, with_tests=False)))

    def test_passes_right_after_write(self, tmp_path, capsys):
        root = make_tree(tmp_path)
        self.write(root)
        assert uf.main(["--root", str(root), "--check"]) == 0

    def test_fails_when_tree_moves(self, tmp_path, capsys):
        root = make_tree(tmp_path)
        self.write(root)
        (root / "c.sql").write_text("x")
        assert uf.main(["--root", str(root), "--check"]) == 1
        assert "sql_files" in capsys.readouterr().out

    def test_fails_when_facts_json_is_edited(self, tmp_path, capsys):
        root = make_tree(tmp_path)
        self.write(root)
        p = root / "docs" / "facts.json"
        d = json.loads(p.read_text()); d["exchanges_total"] = 99; p.write_text(json.dumps(d))
        assert uf.main(["--root", str(root), "--check"]) == 1
        assert "exchanges_total" in capsys.readouterr().out

    def test_tests_total_is_ignored_without_flag(self, tmp_path):
        root = make_tree(tmp_path)
        self.write(root)
        p = root / "docs" / "facts.json"
        d = json.loads(p.read_text()); d["tests_total"] = 1; p.write_text(json.dumps(d))
        assert uf.main(["--root", str(root), "--check"]) == 0

    def test_with_tests_flag_collects(self, tmp_path, capsys):
        root = make_tree(tmp_path)
        self.write(root)
        assert uf.main(["--root", str(root), "--check", "--with-tests"]) == 2  # nothing to collect here


class TestExitTwo:
    def test_missing_calendar(self, tmp_path, capsys):
        (tmp_path / "docs").mkdir()
        assert uf.main(["--root", str(tmp_path), "--check"]) == 2
        assert "calendar.json" in capsys.readouterr().err

    def test_unknown_status(self, tmp_path, capsys):
        root = make_tree(tmp_path, statuses=("working",))
        assert uf.main(["--root", str(root), "--check"]) == 2
        assert "fetcher_status" in capsys.readouterr().err

    def test_missing_facts_json(self, tmp_path, capsys):
        root = make_tree(tmp_path)
        assert uf.main(["--root", str(root), "--check"]) == 2
        assert "facts.json" in capsys.readouterr().err


class TestRealTree:
    def test_real_facts_match_the_tree(self):
        assert uf.main(["--check"]) == 0

    def test_real_facts_are_consistent(self):
        f = json.loads((ROOT / "docs" / "facts.json").read_text())
        assert f["fetchers_registered"] + f["exchanges_no_fetcher"] == f["exchanges_total"]
        assert f["exchanges_blocked_total"] == f["fetchers_blocked"] + f["exchanges_no_fetcher"]

    def test_one_holiday_test_file_per_exchange(self):
        f = json.loads((ROOT / "docs" / "facts.json").read_text())
        assert f["test_files_count"] == f["exchanges_total"]
