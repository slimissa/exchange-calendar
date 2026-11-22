#!/usr/bin/env python3
"""Verify that every MIC listed in a tier of the live-check workflow is either
a registered fetcher or documented in BLOCKED.md (4b3).

Restores the guard the "Verify tier coverage matches the registry" step ran
until commit 2994f2c replaced its script with a placeholder comment (from
then on the step checked nothing). The tier lists are read from the TIER*_MICS
lines of .github/workflows/live-fetcher-check.yml, so the workflow stays the
one place they are written.

Exit 1 if a tier MIC is neither registered nor blocked, if a registered
fetcher is in no tier, or if a MIC is listed in more than one tier (4b4: the
last two were warnings, and XBUL, XIST and XSWX sat in no tier).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "live-fetcher-check.yml"
TIER_RE = re.compile(r"^\s*TIER\d+_MICS(?:_BUILT)?:\s*'([^']*)'", re.M)


def tier_lists(workflow_text: str) -> list[list[str]]:
    return [[m.strip() for m in chunk.split(",") if m.strip()] for chunk in TIER_RE.findall(workflow_text)]


def tier_mics(workflow_text: str) -> set[str]:
    return {m for tier in tier_lists(workflow_text) for m in tier}


def duplicates(workflow_text: str) -> list[str]:
    seen: list[str] = [m for tier in tier_lists(workflow_text) for m in tier]
    return sorted({m for m in seen if seen.count(m) > 1})


def blocked_mics(blocked_text: str) -> set[str]:
    return set(re.findall(r"^##\s+(X[A-Z]{3})\b", blocked_text, re.M))


def check(documented: set[str], registered: set[str], blocked: set[str]) -> tuple[list[str], list[str]]:
    missing = sorted(documented - (registered | blocked))
    unexpected = sorted(registered - documented)
    return missing, unexpected


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.parse_args(argv)
    sys.path.insert(0, str(ROOT / "tools"))
    from update_from_exchange import ExchangeFetcherRegistry
    documented = tier_mics(WORKFLOW.read_text(encoding="utf-8"))
    blocked = blocked_mics((ROOT / "BLOCKED.md").read_text(encoding="utf-8"))
    registered = set(ExchangeFetcherRegistry().list_available())
    missing, unexpected = check(documented, registered, blocked)
    dupes = duplicates(WORKFLOW.read_text(encoding="utf-8"))
    if missing:
        print(f"::error::Documented in a tier but neither registered nor in BLOCKED.md: {missing}")
    if unexpected:
        print(f"::error::Registered but listed in no tier env var: {unexpected}")
    if dupes:
        print(f"::error::Listed in more than one tier: {dupes}")
    print(f"registered={len(registered)} blocked={len(blocked)} documented={len(documented)}")
    if not (missing or unexpected or dupes):
        print("OK: every registered fetcher is in exactly one tier; every tier MIC is registered or blocked")
    return 1 if (missing or unexpected or dupes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
