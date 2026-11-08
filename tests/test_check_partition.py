"""Tests for the fetcher_status partition check in tools/check_doc_facts.py.

The real tree is only read. The tests that change a status or a count work on
a temporary tree whose exchanges/*.json are stubs carrying the real
fetcher_status values, and whose docs/facts.json is a copy of the real one.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_doc_facts as cdf  # noqa: E402

STATUS_KEYS = {
    "implemented": "fetchers_implemented",
    "ci_unreachable": "fetchers_ci_unreachable",
    "blocked": "fetchers_blocked",
    "none": "exchanges_no_fetcher",
}


@pytest.fixture
def tmp_tree(tmp_path):
    """A copy of the registry's statuses and facts that a test may change."""
    (tmp_path / "exchanges").mkdir()
    (tmp_path / "docs").mkdir()
    for f in sorted((ROOT / "exchanges").glob("*.json")):
        status = json.loads(f.read_text(encoding="utf-8"))["fetcher_status"]
        (tmp_path / "exchanges" / f.name).write_text(json.dumps({"fetcher_status": status}))
    shutil.copy(ROOT / "docs" / "facts.json", tmp_path / "docs" / "facts.json")
    (tmp_path / "VERSION").write_text((ROOT / "VERSION").read_text())
    return tmp_path


def facts_of(root):
    return json.loads((root / "docs" / "facts.json").read_text(encoding="utf-8"))


def test_partition_sums_to_74():
    facts = facts_of(ROOT)
    problems, summary = cdf.check_partition(ROOT, facts)

    assert problems == []
    counts = [int(n) for n in summary.split(" = ")[0].split(" + ")]
    assert sum(counts) == len(list((ROOT / "exchanges").glob("*.json"))) == 74
    assert counts == [facts[key] for key in STATUS_KEYS.values()]


def test_partition_catches_wrong_status(tmp_tree, capsys):
    # XBUL is blocked; the slip that shipped in v2.25.0 was ci_unreachable.
    xbul = tmp_tree / "exchanges" / "XBUL.json"
    assert json.loads(xbul.read_text())["fetcher_status"] == "blocked"
    xbul.write_text(json.dumps({"fetcher_status": "ci_unreachable"}))

    problems, summary = cdf.check_partition(tmp_tree, facts_of(tmp_tree))
    assert summary == "42 + 4 + 2 + 26 = 74"
    assert any(p.startswith("fetchers_ci_unreachable: exchanges/ has 4") for p in problems)
    assert any(p.startswith("fetchers_blocked: exchanges/ has 2") for p in problems)

    # through main(): exit 1, with the tree's counts in the output
    (tmp_tree / "README.md").write_text("74 exchanges across 6.\n")
    code = cdf.main(["--root", str(tmp_tree), "--files", "README.md"])
    out = capsys.readouterr().out
    assert code == 1
    assert "fetchers_ci_unreachable: exchanges/ has 4" in out


def test_partition_catches_wrong_count(tmp_tree, capsys):
    facts = facts_of(tmp_tree)
    facts["fetchers_blocked"] = 4
    (tmp_tree / "docs" / "facts.json").write_text(json.dumps(facts))

    problems, summary = cdf.check_partition(tmp_tree, facts)
    assert summary == "42 + 3 + 3 + 26 = 74"  # the tree itself is fine
    assert any(p.startswith("fetchers_blocked: exchanges/ has 3") and "has 4" in p
               for p in problems)
    # facts.json's own four counts no longer add up either
    assert any(p.startswith("partition in docs/facts.json: 42 + 3 + 4 + 26 = 75 "
                            "(expected 74)") for p in problems)

    # through main(): exit 1 and the counts and the sum are printed
    (tmp_tree / "README.md").write_text("74 exchanges across 6.\n")
    code = cdf.main(["--root", str(tmp_tree), "--files", "README.md"])
    out = capsys.readouterr().out
    assert code == 1
    assert "fetcher_status partition does not hold" in out
    assert "42 + 3 + 4 + 26 = 75" in out


def test_partition_unknown_status_is_reported(tmp_tree):
    (tmp_tree / "exchanges" / "XBUL.json").write_text(
        json.dumps({"fetcher_status": "resolved"}))

    problems, summary = cdf.check_partition(tmp_tree, facts_of(tmp_tree))
    assert any("XBUL.json" in p and "'resolved'" in p for p in problems)
    assert summary.endswith("= 73")
    assert any(p == "partition: 42 + 3 + 2 + 26 = 73 (expected 74)" for p in problems)
