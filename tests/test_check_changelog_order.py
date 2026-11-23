"""Tests for tools/check_changelog_order.py (session 4b6)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_changelog_order as cco  # noqa: E402

HEAD = "# Changelog\n\nAll notable changes.\n\n"


def doc(*headings):
    return HEAD + "".join(f"{h}\n\n- entry\n\n" for h in headings)


def test_real_changelog_passes():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert cco.problems(text) == []


def test_real_changelog_passes_from_the_command_line():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_changelog_order.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("OK: CHANGELOG.md:")


def test_unreleased_on_top_passes():
    text = doc("## [Unreleased]", "## [2.33.0] - 2026-11-22", "## [2.32.0] - 2026-11-22")
    assert cco.problems(text) == []


def test_no_unreleased_passes():
    assert cco.problems(doc("## [2.33.0] - 2026-11-22", "## [2.32.0] - 2026-11-22")) == []


def test_unreleased_below_a_release_fails():
    # The 4b5 mistake: entries appended under [Unreleased] below [2.32.0].
    text = doc("## [2.32.0] - 2026-11-22", "## [Unreleased]", "## [2.31.0] - 2026-11-22")
    found = cco.problems(text)
    assert len(found) == 1 and "[Unreleased] is not the first" in found[0]


def test_out_of_order_fails():
    text = doc("## [2.31.0] - 2026-11-22", "## [2.32.0] - 2026-11-22")
    found = cco.problems(text)
    assert len(found) == 1 and "strictly descending" in found[0]


def test_numeric_not_lexical_order():
    # 2.10.0 is above 2.9.0 even though "2.10.0" < "2.9.0" as text.
    assert cco.problems(doc("## [2.10.0] - x", "## [2.9.0] - x")) == []
    assert cco.problems(doc("## [2.9.0] - x", "## [2.10.0] - x")) != []


def test_duplicate_fails():
    text = doc("## [2.33.0] - 2026-11-22", "## [2.33.0] - 2026-11-22", "## [2.32.0] - 2026-11-22")
    found = cco.problems(text)
    assert any("appears twice" in p for p in found)


def test_duplicate_unreleased_fails():
    text = doc("## [Unreleased]", "## [2.33.0] - x", "## [Unreleased]")
    found = cco.problems(text)
    assert any("appears twice" in p for p in found)


def test_bad_label_fails():
    found = cco.problems(doc("## [Unreleased]", "## [next] - x"))
    assert any("neither Unreleased nor a version" in p for p in found)


def test_cli_exit_code_on_failure(tmp_path):
    p = tmp_path / "CHANGELOG.md"
    p.write_text(doc("## [2.32.0] - x", "## [Unreleased]"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_changelog_order.py"), str(p)],
                       capture_output=True, text=True)
    assert r.returncode == 1
    assert "ERROR: CHANGELOG.md: line" in r.stdout


def test_wired_into_gate_points():
    validate = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
    release = (ROOT / "scripts" / "release.sh").read_text(encoding="utf-8")
    assert "python3 tools/check_changelog_order.py" in validate
    pre = release[release.index('say "Static preflight"'):release.index("# ── preconditions")]
    assert "tools/check_changelog_order.py" in pre
