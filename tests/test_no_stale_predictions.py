"""Global invariant: no past-due predicted entry may survive.

Added after the 2026-09-17 reconciliation that removed ~101 past-due
predicted Islamic holidays across 15 exchanges. The per-exchange tests
that asserted specific dates were removed at the same time; this file
enforces the general property those tests were trying to verify.
"""
import json
from datetime import date
from pathlib import Path

import pytest

EXCHANGES = Path(__file__).resolve().parent.parent / "exchanges"


def test_no_past_due_predicted_entries():
    today = date.today().isoformat()
    offenders = []
    for path in sorted(EXCHANGES.glob("*.json")):
        data = json.loads(path.read_text())
        for h in data.get("holidays", {}).get("explicit", []):
            if h.get("predicted") and h.get("date", "") < today:
                offenders.append(f"{path.stem}: {h['date']} {h['name']}")
    if offenders:
        pytest.fail(
            "Past-due predicted entries found:\n  "
            + "\n  ".join(offenders)
        )
