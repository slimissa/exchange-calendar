"""tools/derive_verification.py must keep the authored `verification.coverage`.

The tests work on a temporary copy of the inputs (exchanges/, BLOCKED.md,
docs/DIVERGENCE.md); the real tree is only read.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import derive_verification as dv  # noqa: E402

COVERAGE = {
    "from": "2010-01-01",
    "to": "2029-12-31",
    "sources": [{"from": "2010-01-01", "to": "2024-12-31",
                 "source": "exchange_calendars", "sampled": None}],
}


def _tree(tmp_path):
    shutil.copytree(ROOT / "exchanges", tmp_path / "exchanges")
    (tmp_path / "docs").mkdir()
    shutil.copy(ROOT / "docs" / "DIVERGENCE.md", tmp_path / "docs" / "DIVERGENCE.md")
    shutil.copy(ROOT / "BLOCKED.md", tmp_path / "BLOCKED.md")
    return tmp_path


def _load(root, code):
    return json.loads((root / "exchanges" / f"{code}.json").read_text(encoding="utf-8"))


def test_coverage_survives_a_rewrite(tmp_path):
    root = _tree(tmp_path)
    path = root / "exchanges" / "XTSE.json"
    data = _load(root, "XTSE")
    right_class = data["verification"]["class"]
    data["verification"]["class"] = "single_source"  # force drift
    data["verification"]["coverage"] = COVERAGE
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")

    assert dv.main(["--root", str(root), "--date", "2026-11-12"]) == 0

    after = _load(root, "XTSE")["verification"]
    assert after["class"] == right_class
    assert after["coverage"] == COVERAGE


def test_coverage_alone_is_not_drift(tmp_path):
    root = _tree(tmp_path)
    path = root / "exchanges" / "XTSE.json"
    data = _load(root, "XTSE")
    data["verification"]["coverage"] = COVERAGE
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    assert dv.main(["--root", str(root), "--check"]) == 0
