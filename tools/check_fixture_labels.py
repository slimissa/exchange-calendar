#!/usr/bin/env python3
"""Fail if tests/cross_language_queries.json has duplicate labels.

Duplicate labels are silently accepted by the runners (dict assignment
overwrites), so the cross-language check can pass while the fixture
contains accidental duplicates. See 4ed6f00 for the incident.
"""
import json
import sys
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "tests" / "cross_language_queries.json"
data = json.loads(p.read_text())
labels = [q["label"] for q in data["queries"]]
dupes = sorted({l for l in labels if labels.count(l) > 1})
if dupes:
    print(f"ERROR: duplicate labels in {p}: {dupes}", file=sys.stderr)
    for d in dupes:
        positions = [i for i, l in enumerate(labels) if l == d]
        print(f"  {d}: positions {positions}", file=sys.stderr)
    sys.exit(1)
print(f"OK: {len(labels)} unique labels in {p.name}")
