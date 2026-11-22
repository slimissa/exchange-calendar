#!/usr/bin/env python3
"""Fail on mechanically glued words in prose (4b3).

Checks CHANGELOG.md, README.md, docs/decisions/*.md and the prose fields of
exchanges/*.json (note, verification.reference_note, verification.hours[].note)
for a closing inline-code backtick or a closing straight double quote followed
immediately by a letter: "`isOpen`with", "\"closed\"as". Words glued without
any delimiter ("closedas") cannot be found mechanically; they are a review
item, not a gate.

Backticks and quotes are paired per paragraph (a blank line ends a paragraph;
fenced code blocks are skipped), since a Markdown code span may run across a
line break. A known-good occurrence goes in ALLOWLIST as (file, snippet).

Exit 0 clean, 1 findings.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (file, exact text around the hit) pairs that are correct as written.
ALLOWLIST: set[tuple[str, str]] = set()


def _paragraphs(text: str) -> list[str]:
    text = re.sub(r"^```.*?^```[^\n]*$", "", text, flags=re.M | re.S)
    return re.split(r"\n[ \t]*\n", text)


def findings_in(name: str, text: str) -> list[str]:
    out: list[str] = []
    for para in _paragraphs(text):
        for ch, kind in (("`", "backtick"), ('"', "quote")):
            pos = [m.start() for m in re.finditer(re.escape(ch), para)]
            if ch == "`":
                # A run of backticks (``) opens/closes as one delimiter.
                pos = [p for p in pos if not (p > 0 and para[p - 1] == "`")
                       and not (p + 1 < len(para) and para[p + 1] == "`")]
            for k in range(1, len(pos), 2):
                j = pos[k] + 1
                if j < len(para) and para[j].isalpha():
                    snippet = para[max(0, pos[k] - 25):j + 15].replace("\n", " ")
                    if (name, snippet) in ALLOWLIST:
                        continue
                    out.append(f"{name}: closing {kind} followed by a letter: {snippet!r}")
    return out


def sources(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for rel in ["CHANGELOG.md", "README.md"] + sorted(
            str(Path(p).relative_to(root)) for p in glob.glob(str(root / "docs" / "decisions" / "*.md"))):
        p = root / rel
        if p.exists():
            out.append((rel, p.read_text(encoding="utf-8")))
    for p in sorted((root / "exchanges").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        v = d.get("verification") or {}
        parts = [d.get("note") or "", v.get("reference_note") or ""]
        parts += [i.get("note") or "" for i in v.get("hours") or []]
        for i, part in enumerate(parts):
            if part:
                out.append((f"exchanges/{p.name}#{i}", part))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    found: list[str] = []
    srcs = sources(args.root)
    for name, text in srcs:
        found += findings_in(name, text)
    for line in found:
        print(line)
    if found:
        print(f"\n{len(found)} glued word(s); fix them or add (file, snippet) to ALLOWLIST.")
        return 1
    print(f"OK: no glued words in {len(srcs)} prose source(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
