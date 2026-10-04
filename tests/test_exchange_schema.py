

# ── v2.11.0: sessions ───────────────────────────────────────────────

import json
from pathlib import Path
import pytest

EXCHANGES_DIR = Path(__file__).resolve().parent.parent / "exchanges"


def _all_exchanges():
    return sorted(EXCHANGES_DIR.glob("*.json"))


def test_every_exchange_has_a_regular_session():
    """Every exchange carries at least one `regular` session."""
    missing = []
    for path in _all_exchanges():
        d = json.loads(path.read_text())
        sessions = d.get("sessions") or []
        if not any(s.get("type") == "regular" for s in sessions):
            missing.append(path.name)
    assert not missing, f"no regular session in: {missing}"


def test_regular_hours_matches_first_regular_session():
    """The scalar `regular_hours` is derived from the first `regular`
    session. If the two ever disagree, the derivation was skipped."""
    mismatches = []
    for path in _all_exchanges():
        d = json.loads(path.read_text())
        rh = d.get("regular_hours") or {}
        regular = next(
            (s for s in (d.get("sessions") or [])
             if s.get("type") == "regular"),
            None,
        )
        if regular is None:
            continue
        if rh.get("open") != regular.get("open") or \
           rh.get("close") != regular.get("close"):
            mismatches.append((path.name, rh, regular))
    assert not mismatches, f"scalar/session mismatch: {mismatches[:3]}"


def test_sessions_sorted_and_no_duplicates():
    """Sessions are ordered by time; no two sessions share type+time."""
    problems = []
    for path in _all_exchanges():
        d = json.loads(path.read_text())
        sessions = d.get("sessions") or []
        times = [(s.get("open") or s.get("at")) for s in sessions]
        if times != sorted(times):
            problems.append((path.name, "unsorted", times))
        seen = set()
        for s in sessions:
            key = (s.get("type"), s.get("open"), s.get("at"))
            if key in seen:
                problems.append((path.name, "duplicate", key))
            seen.add(key)
    assert not problems, f"sessions structural problems: {problems[:3]}"
