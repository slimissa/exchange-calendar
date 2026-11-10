#!/usr/bin/env python3
"""
tools/gen_readme_table.py

Generate the README's "The 74 exchanges" table from exchanges/*.json and
docs/DIVERGENCE.md, so the status icon, the notes links, the verification class
and the disagreement count cannot drift from the data.

Columns:  Exchange | MIC | Status | Source | Notes | Verification | Disagreements

  Status         the fetcher_status icon, unchanged: ✅ implemented,
                 ⚠️ ci_unreachable, ⛔ blocked or none. The README text and
                 tools/check_doc_links.py both define the icon this way. It is
                 not derived from the verification class: a class of
                 reference_compared says a reference library covers the
                 exchange, and says nothing about whether a fetcher runs.
  Notes          links to docs/FETCHERS.md (a fetcher is registered:
                 implemented, ci_unreachable, blocked) and to BLOCKED.md
                 (ci_unreachable, blocked, none).
  Verification   verification.class from the exchange file.
  Disagreements  the count in the Summary table of docs/DIVERGENCE.md, or
                 "n/a" when no reference library covers the exchange (the
                 report's own wording). 0 is never printed for "not compared":
                 0 would read as "compared and agrees". The count is generated,
                 not stored in the exchange files, because the report is
                 regenerated every week.
  Exchange, Source  hand-written; read back from the existing table rows (they
                 are not in the exchange files). A new exchange needs a row
                 with its name and source added by hand first.

Rows are sorted by MIC. Run without --check to rewrite README.md; with --check
exit 1 if the table in README.md differs from the generated one.
Because the disagreement counts come from docs/DIVERGENCE.md, regenerate the
table after the report is regenerated.

Exit codes: 0 ok, 1 --check found a difference, 2 fatal.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HEADER = "| Exchange | MIC | Status | Source | Notes | Verification | Disagreements |"
ALIGN = "|----------|-----|:------:|--------|-------|--------------|--------------:|"
ICONS = {"implemented": "\u2705", "ci_unreachable": "\u26a0\ufe0f",
         "blocked": "\u26d4", "none": "\u26d4"}
FETCHER_LINK = {"implemented", "ci_unreachable", "blocked"}
BLOCKED_LINK = {"ci_unreachable", "blocked", "none"}
MIC_RE = re.compile(r"DSMD|X[A-Z]{3}")


class GenError(Exception):
    pass


def divergence_counts(text: str) -> dict[str, str]:
    """MIC -> the Disagreements cell of the report's Summary table."""
    start = text.find("## Summary")
    end = text.find("\n- Exchanges in the registry", start)
    if start < 0 or end < 0:
        raise GenError("docs/DIVERGENCE.md: Summary table not found")
    counts = {}
    for line in text[start:end].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and MIC_RE.fullmatch(cells[0]) and len(cells) >= 5:
            if not (cells[4].isdigit() or cells[4] == "n/a"):
                raise GenError(f"docs/DIVERGENCE.md: {cells[0]} Disagreements "
                               f"cell {cells[4]!r} is not a number or n/a")
            counts[cells[0]] = cells[4]
    return counts


def table_span(lines: list[str]) -> tuple[int, int]:
    """Index of the table's header line and one past its last row."""
    for i, line in enumerate(lines):
        if line.startswith("| Exchange | MIC | Status | Source | Notes |"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            return i, j
    raise GenError("README.md: exchange table not found")


def existing_cells(lines: list[str], span: tuple[int, int]) -> dict[str, tuple[str, str]]:
    """MIC -> (Exchange, Source), the hand-written cells."""
    cells_by_mic = {}
    for line in lines[span[0] + 2:span[1]]:
        cells = line[2:-2].split(" | ")
        if len(cells) >= 5 and MIC_RE.fullmatch(cells[1]):
            cells_by_mic[cells[1]] = (cells[0], cells[3])
    return cells_by_mic


def generate(root: Path) -> tuple[list[str], list[str], tuple[int, int], list[str]]:
    """Return (generated table lines, README lines, table span, notes)."""
    try:
        readme_lines = (root / "README.md").read_text(encoding="utf-8").split("\n")
        divergence = (root / "docs" / "DIVERGENCE.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise GenError(f"cannot read input: {exc}") from None
    span = table_span(readme_lines)
    hand = existing_cells(readme_lines, span)
    counts = divergence_counts(divergence)
    files = sorted((root / "exchanges").glob("*.json"))
    if not files:
        raise GenError("exchanges/: no *.json files")
    rows = []
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        mic, status = d["code"], d.get("fetcher_status")
        if status not in ICONS:
            raise GenError(f"{f.name}: fetcher_status {status!r} has no icon")
        if mic not in hand:
            raise GenError(f"README.md: no row for {mic} to take its name and source from")
        if mic not in counts:
            raise GenError(f"docs/DIVERGENCE.md: no Summary row for {mic}")
        verification = (d.get("verification") or {}).get("class")
        if not verification:
            raise GenError(f"{f.name}: no verification.class")
        anchor = mic.lower()
        links = []
        if status in FETCHER_LINK:
            links.append(f"[#{anchor}](docs/FETCHERS.md#{anchor})")
        if status in BLOCKED_LINK:
            links.append(f"[BLOCKED.md#{anchor}](BLOCKED.md#{anchor})")
        name, source = hand[mic]
        rows.append(f"| {name} | {mic} | {ICONS[status]} | {source} | {', '.join(links)} "
                    f"| {verification} | {counts[mic]} |")
    extra = sorted(set(hand) - {json.loads(f.read_text(encoding="utf-8"))["code"] for f in files})
    if extra:
        raise GenError(f"README.md: rows with no exchange file: {', '.join(extra)}")
    return [HEADER, ALIGN, *rows], readme_lines, span, []


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    p.add_argument("--check", action="store_true",
                   help="exit 1 if README.md's table differs from the generated one")
    args = p.parse_args(argv)
    try:
        table, readme_lines, span, _ = generate(args.root)
    except (GenError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    current = readme_lines[span[0]:span[1]]
    if current == table:
        print(f"OK: README table matches exchanges/ and docs/DIVERGENCE.md ({len(table) - 2} rows)")
        return 0
    if args.check:
        for line in list(difflib.unified_diff(current, table, "README.md", "generated",
                                              lineterm="", n=0))[:20]:
            print(line)
        print("README table is out of date. Run tools/gen_readme_table.py.")
        return 1
    readme_lines[span[0]:span[1]] = table
    (args.root / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")
    print(f"wrote README table ({len(table) - 2} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
