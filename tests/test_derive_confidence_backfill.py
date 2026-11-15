"""Backfilled years (coverage spans with a `sampled` key) derive as low."""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import derive_confidence as dc  # noqa: E402

TODAY = date(2026, 11, 15)
BACKFILLED = ["XTSE", "XSWX", "XSHG", "XKRX", "XSHE"]


def _ex(sources):
    return {
        "holidays": {"explicit": [{"date": f"{y}-01-01"} for y in range(2010, 2030)]},
        "verification": {"coverage": {"sources": sources}},
    }


def test_backfilled_span_is_low_and_later_years_stay_medium():
    ex = _ex([
        {"from": "2010-01-01", "to": "2024-12-31", "source": "exchange_calendars", "sampled": None},
        {"from": "2025-01-01", "to": "2029-12-31", "source": "exchange_calendars"},
    ])
    conf = dc.derive_confidence(ex, None, TODAY)
    for y in range(2010, 2025):
        assert conf[str(y)] == {
            "source": "manual",
            "last_verified": None,
            "level": "low",
            "note": "backfilled from exchange_calendars; not independently verified",
        }
    assert conf["2025"] == {"source": "manual", "last_verified": None, "level": "medium"}
    assert conf["2029"]["note"] == "predicted"


def test_non_exchange_calendars_label_is_named_in_the_note():
    ex = _ex([{"from": "2010-01-01", "to": "2024-12-31", "source": "inferred from XSHG", "sampled": None}])
    note = dc.derive_confidence(ex, None, TODAY)["2010"]["note"]
    assert note == "backfilled (inferred from XSHG); not independently verified"


def test_fetch_year_wins_over_backfill():
    ex = _ex([{"from": "2010-01-01", "to": "2029-12-31", "source": "exchange_calendars", "sampled": None}])
    manifest = {"fetched_at": "2026-11-01T00:00:00Z", "status": "ok", "max_age_days": 60}
    conf = dc.derive_confidence(ex, manifest, TODAY)
    assert conf["2026"]["source"] == "fetcher" and conf["2026"]["level"] == "high"
    assert conf["2025"]["level"] == "low"


def test_no_coverage_means_unchanged_rule():
    ex = {"holidays": {"explicit": [{"date": "2025-01-01"}]}}
    assert dc.derive_confidence(ex, None, TODAY)["2025"]["level"] == "medium"


def test_registry_backfilled_years_are_low_and_2025_on_is_not():
    for mic in BACKFILLED:
        conf = json.loads((ROOT / "exchanges" / f"{mic}.json").read_text())["confidence"]
        for y, entry in conf.items():
            if int(y) <= 2024:
                assert entry["level"] == "low" and entry["last_verified"] is None, (mic, y)
                assert entry["note"].startswith("backfilled"), (mic, y)
            else:
                assert entry["level"] != "low", (mic, y)


def test_high_years_of_other_exchanges_are_untouched():
    for mic in ["XBUD", "XDFM", "XIST", "XWBO"]:
        conf = json.loads((ROOT / "exchanges" / f"{mic}.json").read_text())["confidence"]
        assert any(e["level"] == "high" for e in conf.values()), mic
        assert not any(e.get("note", "").startswith("backfilled") for e in conf.values()), mic
