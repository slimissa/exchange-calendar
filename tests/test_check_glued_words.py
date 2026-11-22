"""tools/check_glued_words.py (4b3): mechanical glued words in prose."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_glued_words as g  # noqa: E402


@pytest.mark.parametrize("text", [
    "the registry-level `isOpen`with no space",
    'the day is "closed"as the notice says',
    "a span `across\na line`break",
])
def test_glued_after_closing_delimiter_is_found(text):
    assert len(g.findings_in("X.md", text)) == 1


@pytest.mark.parametrize("text", [
    "the registry-level `isOpen`, with a space",
    'the day is "closed" as the notice says',
    "a span `across\na line` break",
    "an opening `quote`: fine, and `two` `spans`.",
    "```\ncode`with`glue\n```\nprose `ok` here",
    "a ``double `tick` span`` then text",
    "first paragraph has `one\n\nsecond`para",  # a blank line ends a paragraph
])
def test_clean_text_has_no_finding(text):
    assert g.findings_in("X.md", text) == []


def test_allowlist(monkeypatch):
    text = "see `foo`s here"
    hit = g.findings_in("X.md", text)
    assert len(hit) == 1
    snippet = hit[0].split(": ", 2)[2].strip("'")
    monkeypatch.setattr(g, "ALLOWLIST", {("X.md", snippet)})
    assert g.findings_in("X.md", text) == []


def test_exchange_notes_are_checked(tmp_path):
    (tmp_path / "exchanges").mkdir()
    (tmp_path / "exchanges" / "XTST.json").write_text(json.dumps(
        {"note": "closed `today`as announced", "verification": {"hours": [{"note": "fine"}]}}))
    assert g.main(["--root", str(tmp_path)]) == 1


def test_real_tree_is_clean():
    assert g.main([]) == 0
