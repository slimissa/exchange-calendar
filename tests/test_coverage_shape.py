#!/usr/bin/env python3
"""
test_coverage_shape.py — verification.coverage must have the shape the
wrappers deserialize.

The Rust wrapper's `Coverage` struct requires `from` and `to`, and its
`CoverageSource` struct requires `from`, `to` and `source`
(wrappers/rust/src/exchange.rs). Session 4c8 wrote an XETR coverage with
only `sources`; every Python check passed and both Rust CI jobs failed
(fixed in d0344f7). This test applies the Rust requirement to every
exchange file, and checks that schema.json (2.2.3) rejects the bad shape
too.
"""

import copy
import json
import re
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
EXCHANGES = sorted((ROOT / "exchanges").glob("*.json"))
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _iso(value):
    """Return a date for an ISO YYYY-MM-DD string, or None."""
    if not isinstance(value, str) or not ISO.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def coverage_problems(exchange):
    """Every way this exchange's coverage would fail the Rust wrapper."""
    cov = exchange.get("verification", {}).get("coverage")
    if cov is None:
        return []
    if not isinstance(cov, dict):
        return ["coverage is not an object"]
    problems = []
    lo, hi = _iso(cov.get("from")), _iso(cov.get("to"))
    if lo is None:
        problems.append("coverage.from missing or not an ISO date")
    if hi is None:
        problems.append("coverage.to missing or not an ISO date")
    if lo and hi and lo > hi:
        problems.append("coverage.from is after coverage.to")
    sources = cov.get("sources", [])
    if not isinstance(sources, list):
        return problems + ["coverage.sources is not a list"]
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            problems.append(f"sources[{i}] is not an object")
            continue
        s_lo, s_hi = _iso(src.get("from")), _iso(src.get("to"))
        if s_lo is None:
            problems.append(f"sources[{i}].from missing or not an ISO date")
        if s_hi is None:
            problems.append(f"sources[{i}].to missing or not an ISO date")
        if s_lo and s_hi and s_lo > s_hi:
            problems.append(f"sources[{i}].from is after its to")
        if not isinstance(src.get("source"), str) or not src.get("source"):
            problems.append(f"sources[{i}].source missing or empty")
    return problems


def _load(path):
    with open(path) as f:
        return json.load(f)


@pytest.mark.parametrize("path", EXCHANGES, ids=[p.stem for p in EXCHANGES])
def test_coverage_has_the_fields_the_rust_wrapper_requires(path):
    assert coverage_problems(_load(path)) == []


def test_some_exchanges_have_coverage():
    """Guard against the parametrized test passing vacuously."""
    with_cov = [p.stem for p in EXCHANGES
                if "coverage" in _load(p).get("verification", {})]
    # 30 at d0344f7: the backfilled exchanges except the six sessions-mode
    # ones (XASX, XHKG, XLON, XNAS, XNYS, XTKS), which carry no coverage.
    # Each 4c9 backfill adds one; update the count with the commit.
    # 31: + XNZE (4c9). 32: + XKLS (4c9). 33: + XBKK (4c9). 34: + XLUX (4c9). 35: + XLIT (4c9).
    assert len(with_cov) == 35


def _xetr_without_bounds():
    xetr = _load(ROOT / "exchanges" / "XETR.json")
    bad = copy.deepcopy(xetr)
    bad["verification"]["coverage"].pop("from")
    bad["verification"]["coverage"].pop("to")
    return xetr, bad


def test_checker_rejects_xetr_without_from_and_to():
    """The 4c8 failure: XETR's coverage with only `sources`."""
    good, bad = _xetr_without_bounds()
    assert coverage_problems(good) == []
    assert coverage_problems(bad) == [
        "coverage.from missing or not an ISO date",
        "coverage.to missing or not an ISO date",
    ]


def test_checker_rejects_a_source_without_its_bounds():
    good, _ = _xetr_without_bounds()
    bad = copy.deepcopy(good)
    del bad["verification"]["coverage"]["sources"][0]["to"]
    del bad["verification"]["coverage"]["sources"][1]["source"]
    assert coverage_problems(bad) == [
        "sources[0].to missing or not an ISO date",
        "sources[1].source missing or empty",
    ]


def test_schema_rejects_xetr_without_from_and_to():
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load(ROOT / "schema.json")
    validator = jsonschema.Draft7Validator(schema)
    good, bad = _xetr_without_bounds()
    assert list(validator.iter_errors(good)) == []
    messages = sorted(e.message for e in validator.iter_errors(bad))
    assert messages == ["'from' is a required property", "'to' is a required property"]
