"""Calendar coverage of the cross-language fixture (4b3).

The Rust registry-level is_open read every date a day early from schema 2.1
to v2.29.0 and no hand-picked probe fell on a Monday. These tests fail if,
for any MIC the generator covers, a weekday (Monday to Sunday) is missing at
the registry level or at the exchange level, if the boundary, holiday or
early-close probes are missing, or if the generated block has drifted from
tools/gen_cross_lang_probes.py.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_cross_lang_probes as gen  # noqa: E402

QUERIES = json.loads((ROOT / "tests" / "cross_language_queries.json").read_text(encoding="utf-8"))["queries"]
# MICs with an early close in their data (XTKS, XSAU and XCAI have none).
EARLY = {"XNYS", "XLON", "XHKG", "XBUE"}


def _weekdays(op: str, mic: str) -> set[int]:
    return {dt.date.fromisoformat(q["args"][1]).weekday() for q in QUERIES
            if q["op"] == op and q["args"][0] == mic}


@pytest.mark.parametrize("mic", gen.MICS)
@pytest.mark.parametrize("op", ["is_open", "in_session", "status_at"])
def test_every_weekday_is_probed(mic, op):
    missing = set(range(7)) - _weekdays(op, mic)
    names = [gen.DAYS[d] for d in sorted(missing)]
    assert not missing, f"{mic}: no {op} probe on {names}"


def test_the_required_mics_are_covered():
    assert {"XNYS", "XLON", "XTKS", "XHKG", "XSAU", "XBUE"} <= set(gen.MICS)
    # One non Sat-Sun weekend exchange besides XSAU.
    assert "XCAI" in gen.MICS


@pytest.mark.parametrize("mic", gen.MICS)
def test_boundary_and_holiday_probes(mic):
    labels = {q["label"] for q in QUERIES}
    low = mic.lower()
    for tag in ("boundary_open_m1", "boundary_open", "boundary_close_m1", "boundary_close", "holiday"):
        assert any(l.startswith(f"is_open_gen_{low}_{tag}_") for l in labels), (mic, tag)
        assert any(l.startswith(f"in_session_gen_{low}_{tag}_") for l in labels), (mic, tag)


@pytest.mark.parametrize("mic", sorted(EARLY))
def test_exchange_level_early_close_probes(mic):
    labels = {q["label"] for q in QUERIES}
    low = mic.lower()
    for op in ("status_at", "exchange_is_open"):
        for tag in ("early_m1", "early"):
            assert any(l.startswith(f"{op}_gen_{low}_{tag}_") for l in labels), (mic, op, tag)
    assert any(l.startswith(f"is_open_gen_{low}_early_") for l in labels)


def test_generated_block_is_current():
    assert gen.main(["--check"]) == 0


def test_generated_labels_are_recognised():
    assert gen.is_generated("is_open_gen_xnys_week_mon_2026_01_05_1000")
    assert gen.is_generated("exchange_is_open_gen_x")
    assert not gen.is_generated("is_open_xnys_2026_11_23_monday_1000")
