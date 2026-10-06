#!/usr/bin/env python3
"""Schema freeze audit.

Validates every exchange file in exchanges/ against schema.json, and the
built calendar.json against the shape the wrappers and exports consume.
Reports:

  1. Fields with a population rate below 100% that schema.json does not
     mark optional (i.e. not required at that level).
  2. Enum values that appear in data but not in schema.json.
  3. Time-of-day values that are not HH:MM, dates not real YYYY-MM-DD.
  4. Nested-array shape violations (sessions, holidays.explicit,
     holidays.generated, ad_hoc_closures, confidence).
  5. Session type coverage (populated vs reserved).
  6. Generated holiday dates outside generation_range, or on the
     exchange's own weekend_days.
  7. checksums.json covers exactly the files tools/generate_checksums.py
     collects, and every recorded hash matches the file on disk.

Exit code 0 when every gap is either absent or listed in KNOWN_OPEN, 1
otherwise. KNOWN_OPEN items print as OPEN with a reference; INFO lines
never affect the exit code.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import jsonschema

from generate_checksums import collect_files, sha256_of  # same directory

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema.json").read_text())
SOURCE = [json.loads(p.read_text()) for p in sorted((ROOT / "exchanges").glob("*.json"))]
BUILT = json.loads((ROOT / "calendar.json").read_text())["exchanges"]

HHMM = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_FIELDS = {"open", "close", "at", "early_close_time", "delayed_open_time"}
DATE_FIELDS = {"date", "last_verified"}

# Deviations that are understood, documented and deliberately not fixed in the
# audit commit. Keyed by a substring of the gap message.
KNOWN_OPEN = {
}

gaps: list[str] = []
known: list[str] = []


def gap(msg: str) -> None:
    for key, ref in KNOWN_OPEN.items():
        if key in msg:
            known.append(msg)
            print(f"OPEN {msg}\n       -> {ref}")
            return
    gaps.append(msg)
    print(f"GAP  {msg}")


def info(msg: str) -> None:
    print(f"INFO {msg}")


def schema_required(path: tuple[str, ...]) -> set[str]:
    """Required keys at a schema path like ('holidays','explicit','items')."""
    node = SCHEMA
    for part in path:
        if part == "items":
            node = node["items"]
        elif part == "additional":
            node = node["additionalProperties"]
        else:
            node = node["properties"][part]
    return set(node.get("required", []))


def population(label: str, records: list[dict], required: set[str]) -> None:
    n = len(records)
    if n == 0:
        info(f"{label}: no records in data, population not measurable")
        return
    keys = Counter(k for r in records for k in r)
    for k, c in sorted(keys.items()):
        if c < n:
            if k in required:
                gap(f"{label}.{k}: required but populated {c}/{n}")
            else:
                info(f"{label}.{k}: optional, populated {c}/{n} ({100*c/n:.1f}%)")
    for k in required - keys.keys():
        gap(f"{label}.{k}: required but populated 0/{n}")


def check_time_date(label: str, rec: dict) -> None:
    for k, v in rec.items():
        if k in TIME_FIELDS and isinstance(v, str) and not HHMM.match(v):
            gap(f"{label}.{k}={v!r} is not HH:MM")
        if k in DATE_FIELDS and isinstance(v, str):
            if not ISO.match(v):
                gap(f"{label}.{k}={v!r} is not YYYY-MM-DD")
            else:
                try:
                    date.fromisoformat(v)
                except ValueError:
                    gap(f"{label}.{k}={v!r} is not a real date")


# --- 0. schema validation of every source file -----------------------------
validator = jsonschema.Draft7Validator(SCHEMA)
bad = 0
for ex in SOURCE:
    errs = list(validator.iter_errors(ex))
    for e in errs:
        bad += 1
        gap(f"{ex.get('code')}: schema violation at {list(e.absolute_path)}: {e.message[:90]}")
print(f"source files validated: {len(SOURCE)}, schema errors: {bad}")

# --- 1. population rates ----------------------------------------------------
print("\n== Population (source files) ==")
population("exchange", SOURCE, set(SCHEMA["required"]))
population(
    "session",
    [s for e in SOURCE for s in e["sessions"]],
    schema_required(("sessions", "items")),
)
population(
    "holidays.explicit",
    [h for e in SOURCE for h in e["holidays"].get("explicit", [])],
    schema_required(("holidays", "explicit", "items")),
)
population(
    "ad_hoc_closures",
    [h for e in SOURCE for h in e.get("ad_hoc_closures", [])],
    schema_required(("ad_hoc_closures", "items")),
)
population(
    "confidence",
    [c for e in SOURCE for c in e.get("confidence", {}).values()],
    schema_required(("confidence", "additional")),
)

print("\n== Population (built calendar.json) ==")
built_required = {"code", "name", "mic", "timezone", "weekend_days", "regular_hours",
                  "holidays", "generation_range", "sessions", "confidence",
                  "ad_hoc_closures", "extended_hours"}
population("built.exchange", BUILT, built_required)
for k in ("country", "country_code"):
    n_k = sum(1 for e in BUILT if e.get(k))
    print(f"built.exchange.{k}: populated {n_k}/{len(BUILT)}")
for k in ("country", "country_code"):
    if k in SCHEMA["required"] and not any(k in e for e in BUILT):
        gap(f"built.{k}: required by schema.json, populated 0/{len(BUILT)} in calendar.json "
            f"(tools/build.py must carry it)")
population(
    "built.holidays.generated",
    [h for e in BUILT for h in e["holidays"]["generated"]],
    schema_required(("holidays", "explicit", "items")),
)

# --- 2. enums --------------------------------------------------------------
print("\n== Enums ==")


def enum_at(*path) -> set[str]:
    node = SCHEMA
    for p in path:
        node = node["properties"][p] if p not in ("items", "additional") else (
            node["items"] if p == "items" else node["additionalProperties"])
    return set(node["enum"])


checks = [
    ("session.type", enum_at("sessions", "items", "type"),
     Counter(s["type"] for e in BUILT for s in e["sessions"])),
    ("holiday.status", enum_at("holidays", "explicit", "items", "status"),
     Counter(h["status"] for e in BUILT for k in ("explicit", "generated") for h in e["holidays"][k])),
    ("ad_hoc.status", enum_at("ad_hoc_closures", "items", "status"),
     Counter(h["status"] for e in BUILT for h in e["ad_hoc_closures"])),
    ("confidence.level", enum_at("confidence", "additional", "level"),
     Counter(c["level"] for e in BUILT for c in e["confidence"].values())),
    ("confidence.source", enum_at("confidence", "additional", "source"),
     Counter(c["source"] for e in BUILT for c in e["confidence"].values())),
]
for name, allowed, seen in checks:
    extra = set(seen) - allowed
    unused = allowed - set(seen)
    print(f"{name}: schema={sorted(allowed)} seen={dict(seen)}")
    for v in sorted(extra):
        gap(f"{name}: value {v!r} in data but not in schema")
    for v in sorted(unused):
        info(f"{name}: {v!r} is in schema but unused in data")

# --- 3. HH:MM / YYYY-MM-DD --------------------------------------------------
print("\n== Time and date formats (built calendar.json) ==")
n_checked = 0
for e in BUILT:
    c = e["code"]
    for k in ("open", "close"):
        check_time_date(f"{c}.regular_hours", {k: e["regular_hours"][k]})
        n_checked += 1
    for ek, w in e["extended_hours"].items():
        check_time_date(f"{c}.extended_hours.{ek}", w)
    for i, s in enumerate(e["sessions"]):
        check_time_date(f"{c}.sessions[{i}]", s)
    for k in ("explicit", "generated"):
        for h in e["holidays"][k]:
            check_time_date(f"{c}.holidays.{k}[{h['date']}]", h)
            n_checked += 1
    for h in e["ad_hoc_closures"]:
        check_time_date(f"{c}.ad_hoc[{h['date']}]", h)
    for d in e["generation_range"]:
        check_time_date(f"{c}.generation_range", {"date": d})
    for y, cf in e["confidence"].items():
        check_time_date(f"{c}.confidence.{y}", cf)
print(f"records checked: {n_checked}")

# --- 4. nested array shapes -------------------------------------------------
print("\n== Nested shapes (built calendar.json) ==")
allowed_keys = {
    "session": {"type", "open", "close", "at"},
    "holiday": {"date", "name", "status", "early_close_time", "delayed_open_time",
                "source_url", "predicted", "weekend_exception"},
    "confidence": {"source", "last_verified", "level", "note"},
}
for e in BUILT:
    c = e["code"]
    for s in e["sessions"]:
        if set(s) - allowed_keys["session"]:
            gap(f"{c}.sessions: unexpected keys {set(s) - allowed_keys['session']}")
    for k in ("explicit", "generated"):
        for h in e["holidays"][k]:
            if set(h) - allowed_keys["holiday"]:
                gap(f"{c}.holidays.{k}: unexpected keys {set(h) - allowed_keys['holiday']}")
            if h["status"] == "early_close" and "early_close_time" not in h:
                gap(f"{c}.holidays.{k}[{h['date']}]: early_close without early_close_time")
            if h["status"] == "delayed_open" and "delayed_open_time" not in h:
                gap(f"{c}.holidays.{k}[{h['date']}]: delayed_open without delayed_open_time")
    if not isinstance(e["confidence"], dict) or not e["confidence"]:
        gap(f"{c}.confidence: empty or not an object")
    for y, cf in e["confidence"].items():
        if not re.fullmatch(r"\d{4}", y):
            gap(f"{c}.confidence key {y!r} is not a year string")
        if set(cf) - allowed_keys["confidence"] or not {"source", "level"} <= set(cf):
            gap(f"{c}.confidence.{y}: bad keys {sorted(cf)}")
        if "last_verified" not in cf:
            gap(f"{c}.confidence.{y}: last_verified missing (must be string or null)")
    dates = [h["date"] for h in e["holidays"]["explicit"]]
    if len(dates) != len(set(dates)):
        gap(f"{c}.holidays.explicit: duplicate dates")
    both = set(dates) & {h["date"] for h in e["holidays"]["generated"]}
    if both:
        gap(f"{c}: dates in both explicit and generated: {sorted(both)[:3]}")
print("checked: sessions, holidays.explicit/generated, ad_hoc_closures, confidence")

# --- 5. session type coverage ----------------------------------------------
print("\n== Session type coverage ==")
allowed = enum_at("sessions", "items", "type")
used = Counter(s["type"] for e in BUILT for s in e["sessions"])
print(f"schema types ({len(allowed)}): {sorted(allowed)}")
print(f"populated ({len(used)}): {dict(used)}")
print(f"reserved ({len(allowed - set(used))}): {sorted(allowed - set(used))}")
for e in BUILT:
    c = e["code"]
    types = [s["type"] for s in e["sessions"]]
    if types.count("regular") != 1:
        gap(f"{c}: expected exactly one regular session, found {types.count('regular')}")
    reg = next((s for s in e["sessions"] if s["type"] == "regular"), None)
    if reg and (reg["open"], reg["close"]) != (e["regular_hours"]["open"], e["regular_hours"]["close"]):
        gap(f"{c}: regular session differs from regular_hours")

# --- 6. generation_range ----------------------------------------------------
print("\n== generated dates vs generation_range ==")
for e in BUILT:
    lo, hi = e["generation_range"]
    for h in e["holidays"]["generated"]:
        if not lo <= h["date"] <= hi:
            gap(f"{e['code']}: generated {h['date']} ({h['name']}) outside generation_range [{lo}, {hi}]")

for e in BUILT:
    wd = set(e["weekend_days"])
    for h in e["holidays"]["generated"]:
        if date.fromisoformat(h["date"]).weekday() in wd and not h.get("weekend_exception"):
            gap(f"{e['code']}: generated {h['date']} ({h['name']}) falls on the exchange's own weekend")

# --- 7. checksums.json ------------------------------------------------------
print("\n== checksums.json ==")
manifest = json.loads((ROOT / "checksums.json").read_text())["files"]
expected = {str(p.relative_to(ROOT)): p for p in collect_files()}
for rel in sorted(expected.keys() - manifest.keys()):
    gap(f"checksums.json: no entry for {rel}")
for rel in sorted(manifest.keys() - expected.keys()):
    gap(f"checksums.json: entry for {rel} which is not a covered file")
drift = [rel for rel, p in expected.items() if rel in manifest and sha256_of(p) != manifest[rel]]
for rel in drift:
    gap(f"checksums.json: hash mismatch for {rel}")
print(f"entries: {len(manifest)}, covered files: {len(expected)}, drifted: {len(drift)}")

print(f"\n{len(gaps)} gap(s), {len(known)} known-open")
sys.exit(1 if gaps else 0)
