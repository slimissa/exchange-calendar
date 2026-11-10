"""Tests for tools/gen_readme_table.py: tmp trees only, the real tree is read once."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import gen_readme_table as g  # noqa: E402

OLD_HEADER = "| Exchange | MIC | Status | Source | Notes |\n|----------|-----|:------:|--------|-------|\n"
DIVERGENCE = """# Divergence

## Summary

| Exchange | Registry days | PMC | EC | Disagreements | Agreement |
|----------|---------------|-----|----|---------------|-----------|
| XAAA | 100 | 100 | 100 | 3 | 97.0% |
| XBBB | 100 | No reference data | No reference data | n/a | n/a |
| XCCC | 100 | No reference data | 100 | 0 | 100.0% |

- Exchanges in the registry: 3
"""


def make_tree(tmp_path, statuses=("implemented", "blocked", "ci_unreachable")):
    (tmp_path / "exchanges").mkdir()
    (tmp_path / "docs").mkdir()
    rows = ""
    for mic, status, cls in zip(("XAAA", "XBBB", "XCCC"), statuses,
                                ("reference_compared", "single_source", "ci_unreachable")):
        (tmp_path / "exchanges" / f"{mic}.json").write_text(json.dumps(
            {"code": mic, "fetcher_status": status, "verification": {"class": cls}}))
        rows += f"| Name {mic} | {mic} | ? | {mic.lower()}.example | old notes |\n"
    (tmp_path / "README.md").write_text("intro\n\n" + OLD_HEADER + rows + "\nafter\n")
    (tmp_path / "docs" / "DIVERGENCE.md").write_text(DIVERGENCE)
    return tmp_path


def test_generates_icons_links_class_and_disagreements(tmp_path):
    root = make_tree(tmp_path)
    assert g.main(["--root", str(root)]) == 0
    text = (root / "README.md").read_text()
    assert g.HEADER in text and text.startswith("intro\n") and text.endswith("\nafter\n")
    rows = {l.split(" | ")[1]: l for l in text.splitlines() if l.startswith("| Name ")}
    assert rows["XAAA"] == ("| Name XAAA | XAAA | \u2705 | xaaa.example | [#xaaa](docs/FETCHERS.md#xaaa) "
                            "| reference_compared | 3 |")
    # blocked with a registered fetcher: both links; "n/a" is kept, never turned into 0
    assert rows["XBBB"] == ("| Name XBBB | XBBB | \u26d4 | xbbb.example | [#xbbb](docs/FETCHERS.md#xbbb), "
                            "[BLOCKED.md#xbbb](BLOCKED.md#xbbb) | single_source | n/a |")
    assert rows["XCCC"].startswith("| Name XCCC | XCCC | \u26a0\ufe0f |")
    assert rows["XCCC"].endswith("| ci_unreachable | 0 |")


def test_check_passes_after_write_and_fails_on_drift(tmp_path, capsys):
    root = make_tree(tmp_path)
    assert g.main(["--root", str(root), "--check"]) == 1   # old five-column table
    assert g.main(["--root", str(root)]) == 0
    assert g.main(["--root", str(root), "--check"]) == 0   # idempotent
    # a status change in the data makes the README stale
    (root / "exchanges" / "XAAA.json").write_text(json.dumps(
        {"code": "XAAA", "fetcher_status": "none",
         "verification": {"class": "reference_compared"}}))
    capsys.readouterr()
    assert g.main(["--root", str(root), "--check"]) == 1
    assert "out of date" in capsys.readouterr().out
    # a new disagreement count in DIVERGENCE.md does too
    assert g.main(["--root", str(root)]) == 0
    (root / "docs" / "DIVERGENCE.md").write_text(DIVERGENCE.replace("| 3 | 97.0%", "| 4 | 96.0%"))
    assert g.main(["--root", str(root), "--check"]) == 1


def test_missing_row_or_class_is_fatal(tmp_path, capsys):
    root = make_tree(tmp_path)
    (root / "exchanges" / "XDDD.json").write_text(json.dumps(
        {"code": "XDDD", "fetcher_status": "none", "verification": {"class": "single_source"}}))
    assert g.main(["--root", str(root), "--check"]) == 2
    assert "XDDD" in capsys.readouterr().err


def test_real_readme_table_is_current():
    assert g.main(["--root", str(ROOT), "--check"]) == 0
