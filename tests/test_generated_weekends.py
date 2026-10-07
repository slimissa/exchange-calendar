"""No generated holiday in calendar.json lands on the exchange's own weekend.

Explicit holidays on a weekend day are rejected by tools/validate.py unless
they carry weekend_exception. Generated holidays are held to the same rule:
a generated date on a closed day is a no-op that inflates the count of real
closures (v2.15.0: 215 of 267 generated dates were such no-ops).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCHANGES = json.loads((ROOT / "calendar.json").read_text())["exchanges"]


def test_no_generated_holiday_on_own_weekend():
    bad = [
        (e["code"], h["date"], h["name"])
        for e in EXCHANGES
        for h in e["holidays"]["generated"]
        if date.fromisoformat(h["date"]).weekday() in e["weekend_days"]
        and not h.get("weekend_exception")
    ]
    assert not bad, f"{len(bad)} generated holiday(s) on own weekend: {bad[:5]}"
