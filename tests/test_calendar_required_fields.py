"""Every field schema.json requires must be present on every exchange in
calendar.json.

schema.json describes a source file; build.py projects it into
calendar.json. Until v2.15.0 build.py silently dropped `country` and
`country_code`, which the schema requires, and nothing failed. This test
closes that gap: a required field absent from the built file fails here,
not in a consumer.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema.json").read_text())
EXCHANGES = json.loads((ROOT / "calendar.json").read_text())["exchanges"]


@pytest.mark.parametrize("field", sorted(SCHEMA["required"]))
def test_schema_required_field_present_in_calendar_json(field):
    missing = [e["code"] for e in EXCHANGES if e.get(field) in (None, "")]
    assert not missing, (
        f"schema.json requires {field!r} but calendar.json lacks it on "
        f"{len(missing)} exchange(s): {missing[:5]}. Carry it through "
        f"tools/build.py."
    )


def test_country_code_is_iso_alpha2():
    bad = [e["code"] for e in EXCHANGES if not (len(e["country_code"]) == 2 and e["country_code"].isupper())]
    assert not bad, bad
