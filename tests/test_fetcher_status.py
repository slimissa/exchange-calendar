#!/usr/bin/env python3
"""
test_fetcher_status.py — Checks `fetcher_status` in exchanges/*.json against
the fetchers actually registered in tools/update_from_exchange.py.

The field is authored by hand, so nothing else stops it from drifting from the
code. These tests pin the part that can be checked mechanically:

    1. every exchange file carries a value from the schema enum
    2. "none" appears exactly for the MICs with no registered fetcher, and the
       other three values appear exactly for the MICs that have one
    3. no registered fetcher belongs to a MIC without an exchange file

Whether "implemented" really means CI verifies the source (as opposed to
"ci_unreachable") is not checkable offline; the workflow's exclusion list and
BLOCKED.md are the evidence for that.

Run:
    python3 -m pytest tests/test_fetcher_status.py -v
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import update_from_exchange as updater

ENUM = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))["properties"]["fetcher_status"]["enum"]
EXCHANGES = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "exchanges").glob("*.json"))}
REGISTERED = set(updater.ExchangeFetcherRegistry().fetchers)


def test_enum_is_the_documented_four():
    assert ENUM == ["implemented", "ci_unreachable", "blocked", "none"]


@pytest.mark.parametrize("mic", sorted(EXCHANGES))
def test_value_is_allowed_and_matches_registry(mic):
    status = EXCHANGES[mic].get("fetcher_status")
    assert status in ENUM, f"{mic}: fetcher_status {status!r} not in {ENUM}"
    if mic in REGISTERED:
        assert status != "none", f"{mic} has a registered fetcher but is marked none"
    else:
        assert status == "none", f"{mic} has no registered fetcher but is marked {status}"


def test_every_registered_fetcher_has_an_exchange_file():
    assert REGISTERED <= set(EXCHANGES), sorted(REGISTERED - set(EXCHANGES))
