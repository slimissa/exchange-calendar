"""tools/wrapper_test_counts.py keeps README section 15's test counts current
(session 4b1: the hand-written counts had gone stale)."""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import wrapper_test_counts as wtc  # noqa: E402


def test_counts_are_positive_for_all_four():
    found = wtc.counts(ROOT)
    assert set(found) == {"Python", "JavaScript", "Go", "Rust"}
    assert all(n > 0 for n in found.values()), found


def test_readme_is_current():
    assert wtc.main(["--root", str(ROOT)]) == 0


def _tree(tmp_path):
    for rel in ("README.md", "tests/test_wrappers.py"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    for rel in ("wrappers/javascript/tests", "wrappers/go", "wrappers/rust/src"):
        shutil.copytree(ROOT / rel, tmp_path / rel, ignore=shutil.ignore_patterns("target"))
    return tmp_path


def test_a_new_test_makes_the_readme_stale_and_write_fixes_it(tmp_path, capsys):
    root = _tree(tmp_path)
    before = wtc.counts(root)["Python"]
    with open(root / "tests" / "test_wrappers.py", "a", encoding="utf-8") as f:
        f.write("\n\ndef test_added_in_a_later_session():\n    pass\n")
    assert wtc.main(["--root", str(root)]) == 1
    assert f"Python {before + 1}" in capsys.readouterr().out
    assert wtc.main(["--root", str(root), "--write"]) == 0
    assert f"| {before + 1} declarations (root suite" in (root / "README.md").read_text(encoding="utf-8")
    assert wtc.main(["--root", str(root)]) == 0


def test_missing_row_is_an_error():
    with pytest.raises(SystemExit, match="no wrapper row for Rust"):
        wtc.render("| Python | a | b | c | 1 |\n| JavaScript | a | b | c | 1 |\n| Go | a | b | c | 1 |\n",
                   {"Python": 1, "JavaScript": 1, "Go": 1, "Rust": 1})
