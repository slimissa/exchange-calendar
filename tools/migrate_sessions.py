#!/usr/bin/env python3
"""
tools/migrate_sessions.py

Migrate exchange JSON from scalar hours to a typed ``sessions`` array.

Two session shapes exist in the data:

  Interval (a window):        {"type": "...", "open": "HH:MM", "close": "HH:MM"}
  Point (an event):           {"type": "auction"|"halt", "at": "HH:MM"}

The migration populates three interval types from the scalar fields
(regular, pre_market, post_market) and preserves any pre-existing
sessions (auctions, lunch breaks). The scalar fields stay and are
regenerated as derived projections of the interval sessions, so the
two representations cannot disagree.

Exit codes:
    0  success (or --check passed)
    1  --check found files needing migration
    2  fatal
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional


EXIT_OK = 0
EXIT_NEEDS = 1
EXIT_FATAL = 2

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

# All valid session types. The migration *populates* regular/pre_market/
# post_market from scalars; the others are preserved from existing data.
SESSION_TYPES = (
    "pre_market", "regular", "lunch_break", "post_market", "auction", "halt",
)

# Tie-break order for sessions at the same time.
_TYPE_ORDER = {
    "pre_market": 0,
    "regular": 1,
    "lunch_break": 2,
    "post_market": 3,
    "auction": 4,
    "halt": 5,
}

# Types that carry {open, close}; all others carry {at}.
_INTERVAL_TYPES = {"regular", "pre_market", "post_market", "lunch_break"}
_POINT_TYPES = {"auction", "halt"}

# Interval types that map to a scalar field in the exchange record.
_EXT_KEY = {"pre_market": "pre_market", "post_market": "after_hours"}


def _is_time(v: Any) -> bool:
    return isinstance(v, str) and bool(_TIME_RE.match(v))


def _sort_time(s: dict) -> str:
    """Anchor time for sorting: `open` on interval sessions, `at` on
    point sessions. Unknown sorts to the end."""
    t = s.get("open") or s.get("at")
    return t if isinstance(t, str) else "99:99"


def _load(path: Path) -> Optional[dict]:
    try:
        d = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: {path}: {e}", file=sys.stderr)
        return None
    if not isinstance(d, dict):
        print(f"ERROR: {path}: not a JSON object", file=sys.stderr)
        return None
    return d


def _validate_session(s: Any) -> bool:
    if not isinstance(s, dict):
        return False
    t = s.get("type")
    if not isinstance(t, str) or t not in SESSION_TYPES:
        return False
    if t in _INTERVAL_TYPES:
        return _is_time(s.get("open")) and _is_time(s.get("close"))
    if t in _POINT_TYPES:
        return _is_time(s.get("at"))
    return False


def _derive_interval_sessions(d: dict, path: Path) -> Optional[list]:
    """Build regular/pre_market/post_market sessions from scalars.
    Returns None and prints an error on malformed input."""
    out: list = []

    rh = d.get("regular_hours")
    if not isinstance(rh, dict):
        print(f"ERROR: {path}: missing regular_hours", file=sys.stderr)
        return None
    if not (_is_time(rh.get("open")) and _is_time(rh.get("close"))):
        print(f"ERROR: {path}: regular_hours must be HH:MM", file=sys.stderr)
        return None
    if rh["open"] >= rh["close"]:
        print(f"ERROR: {path}: regular_hours.open >= close", file=sys.stderr)
        return None
    out.append({"type": "regular", "open": rh["open"], "close": rh["close"]})

    ext = d.get("extended_hours") or {}
    if not isinstance(ext, dict):
        print(f"ERROR: {path}: extended_hours must be an object", file=sys.stderr)
        return None

    for sess_type, ext_key in _EXT_KEY.items():
        block = ext.get(ext_key)
        if block is None:
            continue
        if not isinstance(block, dict):
            print(f"ERROR: {path}: extended_hours.{ext_key} must be object", file=sys.stderr)
            return None
        if not (_is_time(block.get("open")) and _is_time(block.get("close"))):
            print(f"ERROR: {path}: extended_hours.{ext_key} must be HH:MM", file=sys.stderr)
            return None
        if block["open"] >= block["close"]:
            print(f"ERROR: {path}: extended_hours.{ext_key}.open >= close", file=sys.stderr)
            return None
        out.append({"type": sess_type, "open": block["open"], "close": block["close"]})

    return out


def _derive_scalars_from_sessions(sessions: list) -> dict:
    """Regenerate regular_hours / extended_hours from interval sessions."""
    out: dict = {}

    regular = next((s for s in sessions if s.get("type") == "regular"), None)
    if regular and _is_time(regular.get("open")) and _is_time(regular.get("close")):
        out["regular_hours"] = {
            "open": regular["open"],
            "close": regular["close"],
        }

    ext: dict = {}
    for s in sessions:
        key = _EXT_KEY.get(s.get("type", ""))
        if key is None:
            continue
        if not (_is_time(s.get("open")) and _is_time(s.get("close"))):
            continue
        ext[key] = {"open": s["open"], "close": s["close"]}
    if ext:
        out["extended_hours"] = ext

    return out


def _canonical(d: dict, path: Path) -> Optional[dict]:
    """Return the canonical form of an exchange record, or None on error."""
    d = dict(d)

    sessions: list = []
    existing = d.get("sessions")
    if isinstance(existing, list):
        for s in existing:
            if not _validate_session(s):
                print(
                    f"ERROR: {path}: invalid existing session: "
                    f"{json.dumps(s)}",
                    file=sys.stderr,
                )
                return None
            sessions.append(dict(s))

    # Insert interval sessions from scalars, skipping types already present.
    derived = _derive_interval_sessions(d, path)
    if derived is None:
        return None
    have = {s["type"] for s in sessions if s.get("type") in _INTERVAL_TYPES}
    for s in derived:
        if s["type"] not in have:
            sessions.append(s)

    sessions.sort(
        key=lambda s: (_sort_time(s), _TYPE_ORDER.get(s.get("type", ""), 99))
    )
    d["sessions"] = sessions

    scalars = _derive_scalars_from_sessions(sessions)
    for k, v in scalars.items():
        d[k] = v
    if "extended_hours" not in scalars and "extended_hours" in d:
        del d["extended_hours"]

    return d


def _needs_migration(d: dict) -> bool:
    """True if the file is not in canonical form."""
    sessions = d.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        return True

    for s in sessions:
        if not _validate_session(s):
            return True

    if not any(s.get("type") == "regular" for s in sessions):
        return True

    derived = _derive_scalars_from_sessions(sessions)
    if "regular_hours" not in derived:
        return True
    for k, v in derived.items():
        if d.get(k) != v:
            return True
    if "extended_hours" in d and "extended_hours" not in derived:
        return True

    times = [
        (_sort_time(s), _TYPE_ORDER.get(s.get("type", ""), 99))
        for s in sessions
    ]
    if times != sorted(times):
        return True

    return False


def _write(path: Path, d: dict) -> None:
    text = json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def _collect_paths(args: list) -> list:
    if not args:
        args = ["exchanges"]
    out: list = []
    for a in args:
        p = Path(a)
        if not p.exists():
            print(f"ERROR: path not found: {p}", file=sys.stderr)
            return []
        if p.is_dir():
            out.extend(sorted(p.glob("*.json")))
        else:
            out.append(p)
    return out


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="migrate_sessions.py",
        description=(
            "Migrate exchange JSON from scalar hours to a sessions "
            "array. Additive: regular_hours and extended_hours stay "
            "as derived projections."
        ),
    )
    ap.add_argument("paths", nargs="*",
                    help="Exchange JSON files or directories (default: exchanges/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show planned changes without writing")
    ap.add_argument("--check", action="store_true",
                    help="Exit 1 if any file needs migration (CI mode)")
    ap.add_argument("--quiet", action="store_true",
                    help="Suppress per-file output")
    ap.add_argument("--json", action="store_true",
                    help="Emit a machine-readable summary")
    args = ap.parse_args(argv)

    if args.dry_run and args.check:
        print("ERROR: --dry-run and --check are mutually exclusive",
              file=sys.stderr)
        return EXIT_FATAL

    paths = _collect_paths(args.paths)
    if not paths:
        return EXIT_FATAL

    if not args.json and not args.quiet:
        mode = "CHECK" if args.check else ("DRY-RUN" if args.dry_run else "MIGRATE")
        print(f"MODE: {mode}   Paths: {len(paths)}")

    changed = already = failed = 0
    results: list = []

    for path in paths:
        d = _load(path)
        if d is None:
            failed += 1
            results.append({"path": str(path), "status": "fatal"})
            continue

        if not _needs_migration(d):
            already += 1
            results.append({"path": str(path), "status": "unchanged"})
            if not args.quiet and not args.json:
                print(f"  SKIP   {path}  (already canonical)")
            continue

        canonical = _canonical(d, path)
        if canonical is None:
            failed += 1
            results.append({"path": str(path), "status": "fatal"})
            continue

        if args.check:
            changed += 1
            results.append({"path": str(path), "status": "needs"})
            if not args.quiet and not args.json:
                print(f"  NEEDS  {path}")
            continue

        if args.dry_run:
            changed += 1
            old = d.get("sessions") or []
            new = canonical.get("sessions") or []
            results.append({"path": str(path), "status": "would-migrate"})
            if not args.quiet and not args.json:
                print(f"  WOULD  {path}  ({len(old)} -> {len(new)} sessions)")
            continue

        _write(path, canonical)
        changed += 1
        results.append({"path": str(path), "status": "migrated"})
        if not args.quiet and not args.json:
            print(f"  OK     {path}")

    if args.json:
        print(json.dumps({
            "total": len(paths),
            "changed": changed,
            "already": already,
            "failed": failed,
            "check_mode": args.check,
            "dry_run": args.dry_run,
            "results": results,
        }, indent=2))
    elif not args.quiet:
        print()
        print(f"Total: {len(paths)}  Changed: {changed}  "
              f"Already canonical: {already}  Failed: {failed}")

    if failed:
        return EXIT_FATAL
    if args.check and changed > 0:
        if not args.quiet and not args.json:
            print(f"CHECK FAILED: {changed} file(s) need migration.")
        return EXIT_NEEDS
    if args.check and not args.quiet and not args.json:
        print("CHECK OK: all files are canonical.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
