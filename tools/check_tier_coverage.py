#!/usr/bin/env python3
"""Verify that every MIC listed in a tier of the live-check workflow is either
a registered fetcher or documented in BLOCKED.md (4b3).

Restores the guard the "Verify tier coverage matches the registry" step ran
until commit 2994f2c replaced its script with a placeholder comment (from
then on the step checked nothing). The tier lists are read from the TIER*_MICS
lines of .github/workflows/live-fetcher-check.yml, so the workflow stays the
one place they are written.

Exit 1 if a tier MIC is neither registered nor blocked; a registered fetcher
missing from every tier is a warning.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "live-fetcher-check.yml"
TIER_RE = re.compile(r"^\s*TIER\d+_MICS(?:_BUILT)?:\s*'([^']*)'", re.M)


def tier_mics(workflow_text: str) -> set[str]:
    return {m.strip() for chunk in TIER_RE.findall(workflow_text) for m in chunk.split(",") if m.strip()}


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
    if missing:
        print(f"::error::Documented in a tier but neither registered nor in BLOCKED.md: {missing}")
    if unexpected:
        print(f"::warning::Registered but not listed in any tier env var (verify intentional): {unexpected}")
    print(f"registered={len(registered)} blocked={len(blocked)} documented={len(documented)}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
