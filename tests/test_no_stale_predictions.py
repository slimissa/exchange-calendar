"""Global invariant: no past-due predicted entry may survive unless it is
held on doubt (ADR 0016 R5(d)).

Added after the 2026-09-17 reconciliation that removed ~101 past-due
predicted Islamic holidays across 15 exchanges. The per-exchange tests
that asserted specific dates were removed at the same time; this file
enforces the general property those tests were trying to verify.

Since session 4e2 (ADR 0016) the property is tools/validate.py M7's, run
here over the real data with validate.clock(): a past-due predicted entry
passes only while it is held on doubt (check 5b), its recheck_date has not
passed, and that date is at most 30 days after the entry's date. The rule
itself is tested with synthetic fixtures in tests/test_predicted_lifecycle.py.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXCHANGES = ROOT / "exchanges"
sys.path.insert(0, str(ROOT / "tools"))

import validate  # noqa: E402


def test_no_past_due_predicted_entries():
    today = validate.clock()
    offenders = []
    for path in sorted(EXCHANGES.glob("*.json")):
        data = json.loads(path.read_text())
        offenders.extend(validate.check_past_due_predictions(data, path.name, today))
    if offenders:
        pytest.fail(
            "Past-due predicted entries not held on doubt (ADR 0016 R5):\n  "
            + "\n  ".join(offenders)
        )
