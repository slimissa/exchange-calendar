"""Tests for docs/decisions/*.md — no placeholders in shipped ADRs.

Decision records are shipped documents. A template skeleton with
`<...>` placeholders is a claim that a decision exists where none
does. This test is the fix for the v2.12.0 release, where ADR 0010
shipped as an unfilled template and the release-claims gate matched
the section headings rather than the decisions.

An ADR may declare itself "Draft" in its status line; that exemption
exists so a work-in-progress ADR can be committed while it is being
written. "Accepted" ADRs must have no placeholders.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

DECISIONS_DIR = Path(__file__).resolve().parent.parent / "docs" / "decisions"

# A placeholder is any `<word>` or `[word]` on a line that is not inside
# a fenced code block, and does not look like a legitimate bracketed term.
# Legitimate uses we deliberately allow:
#   - `[Unreleased]`, `[2.11.0]` — CHANGELOG-style version refs
#   - `[text](url)` — markdown links
#   - `[a, b]` — inline examples
# Placeholders we catch:
#   - `<file>` `<URL>` `<action>` `<attempt|permanent-block>` `<N>` etc.
_PLACEHOLDER = re.compile(r"<[a-zA-Z][a-zA-Z0-9 _\-|]+>")

_FENCE = re.compile(r"^```")


def _adrs() -> list[Path]:
    return sorted(DECISIONS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"))


def _read_until_status(path: Path) -> tuple[str, str]:
    """Return (status_line_value, whole_text)."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^\*\*Status:\*\*\s*(.+)$", text, re.MULTILINE)
    return (m.group(1).strip() if m else "", text)


def _strip_fenced_blocks(text: str) -> str:
    lines = text.splitlines()
    out = []
    in_fence = False
    for line in lines:
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def test_all_adrs_are_discoverable():
    adrs = _adrs()
    assert adrs, "no ADRs found under docs/decisions/"


@pytest.mark.parametrize("path", _adrs(), ids=lambda p: p.name)
def test_accepted_adrs_have_no_placeholders(path: Path):
    status, text = _read_until_status(path)
    if "draft" in status.lower():
        pytest.skip(f"{path.name}: status is Draft — placeholders permitted")
    body = _strip_fenced_blocks(text)
    hits = _PLACEHOLDER.findall(body)
    assert not hits, (
        f"{path.name}: status is {status!r} but contains placeholders: "
        f"{hits}. Fill them in or set status to 'Draft'."
    )
