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


# 4b7: every ADR keeps its title line and the "#", "##" and "###" headings
# it had when this guard was written. In 4b6 a session script truncated
# ADR 0014 to one table row and the gate passed; this test fails on a
# truncated or emptied ADR. Headings may be added; none may disappear.
ADR_HEADINGS = {
    "0008-removal-guard-semantics.md": [
        "# ADR 0008 — Removal Guard Semantics",
        "## Context",
        "## Decisions",
        "## Consequences"
    ],
    "0009-playwright-fetcher-category.md": [
        "# ADR 0009 — Playwright as a fetcher category",
        "## Context",
        "## Decisions",
        "### 1. Adopt Playwright, fetch mode first",
        "### 2. Defer render+OCR to ADR 0010",
        "### 3. CI cost is bounded and named",
        "### 4. Maintenance model: same as any other fetcher",
        "### 5. Playwright is EC-local, not shared",
        "## Consequences",
        "### Positive",
        "### Negative",
        "### Neutral",
        "## Alternatives considered",
        "### A. Do nothing — leave all five blocked",
        "### B. Adopt Playwright for both modes at once",
        "### C. Use a lighter headless tool (e.g. requests-html, pyppeteer)",
        "### D. Proxy or mirror the source",
        "## Open questions",
        "## Amendment — 2026-10-04",
        "## Related"
    ],
    "0010-render-mode.md": [
        "# ADR 0010 — Render mode and OCR for remaining blocked exchanges",
        "## Context",
        "## Reconnaissance",
        "### XKRX",
        "### XATH",
        "### XBKK",
        "## Decisions",
        "### D1 — XKRX",
        "### D2 — XATH",
        "### D3 — XBKK",
        "### D4 — CI cost",
        "### D5 — Generalization",
        "## Consequences",
        "### Positive",
        "### Negative",
        "### Neutral",
        "## Non-goals",
        "## Amendment — 2026-10-04 (v2.12.3)",
        "## Amendment — 2026-10-04 (v2.12.4)",
        "## Amendment — 2026-10-04 (v2.12.5)",
        "## Related"
    ],
    "0011-mic-lei-connector.md": [
        "# ADR 0011 — MIC→LEI connector",
        "## Context",
        "## Reconnaissance",
        "## Decision",
        "## Consequences",
        "### Positive",
        "### Negative",
        "### Neutral",
        "## Reopen condition",
        "## Related"
    ],
    "0012-export-shapes.md": [
        "# ADR 0012 — Export shapes (SQL, CSV, Parquet)",
        "## Context",
        "## Decisions",
        "### 1. One shape, three formats",
        "### 2. SQL",
        "### 2a. SQL types and CHECKs",
        "### 3. CSV",
        "### 4. Parquet",
        "### 5. Column order",
        "### 6. Dates and times",
        "### 7. Null handling",
        "### 8. Generated holidays",
        "## Prerequisite: `country_code`",
        "## Consequences",
        "## Rejected alternatives"
    ],
    "0013-close-convention.md": [
        "# ADR 0013 — Close time = end of the closing auction",
        "## Context",
        "## Decision",
        "### Random closing windows (maintainer decision, session 4b5)",
        "### Audit of the applied table against the random-closing rule (session 4b5)",
        "## Why",
        "## Consequences",
        "## Applied in 4c-R3.5",
        "## Exceptions left in place",
        "## Phase 4d plan"
    ],
    "0014-regular-hours-evidence.md": [
        "# ADR 0014 — Regular hours: segment, close rule, evidence",
        "## Context",
        "## Decision",
        "### 1. Which segment is \"regular\"",
        "### 2. Close rule (ADR 0013)",
        "### 3. What \"verified\" means",
        "### 4. Where the evidence lives",
        "### 5. Ratchet",
        "### 6. Hours the schema cannot express (`schema_limited`, session 4b2)",
        "### 7. What the evidence proves: `verified_from`, current and history (session 4b3)",
        "### 8. Undated current regimes (maintainer decision, session 4b5)",
        "## Consequences",
        "## Applied (filled as 4b-lite proceeds)"
    ],
    "0015-hours-evidence-exemptions.md": [
        "# ADR 0015 — Hours-evidence exemptions",
        "## Context",
        "## Decision",
        "### 1. Check 6 is blocking",
        "### 2. What an exemption records",
        "### 3. Lifetime",
        "### 4. When the gate fails",
        "### 5. When the gate warns",
        "### 6. What an exemption is not",
        "## Consequences"
    ],
    "0016-predicted-entries.md": [
        "# ADR 0016 — Predicted entries",
        "## Context",
        "## Decision",
        "### R1. Meaning",
        "### R2. Independence",
        "### R3. Every prediction carries the flag",
        "### R4. Predicted trading days",
        "### R5. Lifecycle",
        "### R6. Explicit `predicted: false`",
        "### R7. The name suffix",
        "### R8. No per-entry basis in 4e",
        "### R9. Year-level confidence",
        "### R10. Retired tool, and a warning instead",
        "### R11. Schema in 2.x",
        "### R12. Wrapper API",
        "### R13. Stale counts and examples",
        "### R14. Recheck dates in the gate",
        "## Consequences",
        "## Applied (filled as Phase 4e proceeds)",
        "## 4f backlog"
    ]
}


def test_every_adr_keeps_its_title_and_headings():
    present = {p.name for p in DECISIONS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")}
    assert set(ADR_HEADINGS) <= present, sorted(set(ADR_HEADINGS) - present)
    for name, headings in ADR_HEADINGS.items():
        lines = (DECISIONS_DIR / name).read_text(encoding="utf-8").splitlines()
        assert lines and lines[0] == headings[0], (name, "title line")
        missing = [h for h in headings if h not in lines]
        assert not missing, (name, missing)


def test_adr_heading_guard_catches_truncation(tmp_path, monkeypatch):
    # A copy of the decisions folder with ADR 0014 cut to one line fails.
    import shutil
    import sys
    for p in DECISIONS_DIR.glob("*.md"):
        shutil.copy(p, tmp_path / p.name)
    (tmp_path / "0014-regular-hours-evidence.md").write_text("| XMAD | row |\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "DECISIONS_DIR", tmp_path)
    with pytest.raises(AssertionError):
        test_every_adr_keeps_its_title_and_headings()
