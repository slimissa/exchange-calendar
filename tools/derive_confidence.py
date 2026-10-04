#!/usr/bin/env python3
"""
tools/derive_confidence.py

Derive the per-year ``confidence`` map on every exchange from
``fetcher_manifest.json`` and the years present in ``holidays.explicit``.

Rule (for each year Y appearing in an exchange's explicit holidays):

    If a fetch entry exists for this MIC and Y == the fetch year:
        source         = "fetcher"
        last_verified  = manifest.fetched_at[:10]
        level          = "high"  if fetch is within max_age_days
                       = "low"   otherwise (note explains the staleness)

    Otherwise:
        source         = "manual"
        last_verified  = null
        level          = "medium"
        note           = "predicted"  if Y > current year

Idempotent. ``--check`` exits 1 if any file's confidence is out of
sync with what the rule would produce today.

Usage:
    derive_confidence.py --dry-run
    derive_confidence.py --dry-run exchanges/XNYS.json
    derive_confidence.py --check
    derive_confidence.py --check --quiet
    derive_confidence.py --json
    derive_confidence.py --today 2026-10-04      # override for tests

Exit codes:
    0  success (or --check passed)
    1  --check found files needing update
    2  fatal (missing input, malformed JSON)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional


EXIT_OK = 0
EXIT_NEEDS = 1
EXIT_FATAL = 2

MANIFEST_PATH = Path("fetcher_manifest.json")
EXCHANGES_DIR = Path("exchanges")


# ── loading ────────────────────────────────────────────────────────

def _load_manifest() -> dict:
    """Return the manifest's fetches map, or {} if missing/malformed."""
    if not MANIFEST_PATH.exists():
        return {}
    try:
        doc = json.loads(MANIFEST_PATH.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARNING: {MANIFEST_PATH}: {e}", file=sys.stderr)
        return {}
    fetches = doc.get("fetches")
    return fetches if isinstance(fetches, dict) else {}


def _load_exchange(path: Path) -> Optional[dict]:
    try:
        d = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: {path}: {e}", file=sys.stderr)
        return None
    if not isinstance(d, dict):
        print(f"ERROR: {path}: not a JSON object", file=sys.stderr)
        return None
    return d


# ── derivation ─────────────────────────────────────────────────────

def _years_in(ex: dict) -> list[str]:
    """Sorted unique years (as strings) from holidays.explicit."""
    years: set[str] = set()
    hols = ex.get("holidays")
    if isinstance(hols, dict):
        explicit = hols.get("explicit")
        if isinstance(explicit, list):
            for h in explicit:
                if not isinstance(h, dict):
                    continue
                d = h.get("date")
                if isinstance(d, str) and len(d) >= 4 and d[:4].isdigit():
                    years.add(d[:4])
    return sorted(years)


def _fetch_date(fetched_at: Any) -> Optional[date]:
    """Parse the manifest's fetched_at into a date, or None if bad."""
    if not isinstance(fetched_at, str) or len(fetched_at) < 10:
        return None
    head = fetched_at[:10]
    try:
        return date.fromisoformat(head)
    except ValueError:
        return None


def _derive_entry_for_year(
    year: str,
    manifest_entry: Optional[dict],
    today: date,
) -> dict:
    """Build a single confidence entry for one year."""
    yi = int(year)

    # Path 1: this year matches the fetch's year.
    if manifest_entry:
        fetched_at = manifest_entry.get("fetched_at")
        fetch_date = _fetch_date(fetched_at)
        fetch_status = manifest_entry.get("status", "ok")

        if fetch_date is not None and fetch_date.year == yi:
            max_age = manifest_entry.get("max_age_days")
            age = (today - fetch_date).days
            entry: dict = {
                "source": "fetcher",
                "last_verified": fetch_date.isoformat(),
            }
            if fetch_status != "ok":
                entry["level"] = "low"
                entry["note"] = f"fetch status={fetch_status!r}"
            elif isinstance(max_age, int) and age > max_age:
                entry["level"] = "low"
                entry["note"] = (
                    f"fetch is {age}d old; max_age_days={max_age}"
                )
            else:
                entry["level"] = "high"
            return entry

    # Path 2: no fetch covers this year; treat as manual.
    entry = {
        "source": "manual",
        "last_verified": None,
        "level": "medium",
    }
    if yi > today.year:
        entry["note"] = "predicted"
    return entry


def derive_confidence(
    ex: dict,
    manifest_entry: Optional[dict],
    today: date,
) -> dict:
    """Return the full confidence map for an exchange."""
    return {
        y: _derive_entry_for_year(y, manifest_entry, today)
        for y in _years_in(ex)
    }


def _needs_update(
    ex: dict,
    manifest_entry: Optional[dict],
    today: date,
) -> bool:
    desired = derive_confidence(ex, manifest_entry, today)
    return ex.get("confidence") != desired


# ── IO ─────────────────────────────────────────────────────────────

def _write(path: Path, ex: dict) -> None:
    text = json.dumps(ex, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def _collect_paths(args: list) -> list:
    if not args:
        args = [str(EXCHANGES_DIR)]
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


def _parse_today(s: Optional[str]) -> date:
    if s is None:
        return datetime.now(timezone.utc).date()
    try:
        return date.fromisoformat(s)
    except ValueError:
        print(f"ERROR: --today must be YYYY-MM-DD, got {s!r}",
              file=sys.stderr)
        sys.exit(EXIT_FATAL)


# ── CLI ────────────────────────────────────────────────────────────

def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="derive_confidence.py",
        description=(
            "Derive the `confidence` map on every exchange from the "
            "fetch manifest and the years in holidays.explicit."
        ),
    )
    ap.add_argument("paths", nargs="*",
                    help="Exchange JSON files or directories (default: exchanges/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show planned changes without writing")
    ap.add_argument("--check", action="store_true",
                    help="Exit 1 if any file's confidence is stale")
    ap.add_argument("--quiet", action="store_true",
                    help="Suppress per-file output")
    ap.add_argument("--json", action="store_true",
                    help="Emit a machine-readable summary")
    ap.add_argument("--today", default=None,
                    help="Override today (YYYY-MM-DD); useful in tests")
    args = ap.parse_args(argv)

    if args.dry_run and args.check:
        print("ERROR: --dry-run and --check are mutually exclusive",
              file=sys.stderr)
        return EXIT_FATAL

    today = _parse_today(args.today)
    manifest = _load_manifest()
    paths = _collect_paths(args.paths)
    if not paths:
        return EXIT_FATAL

    if not args.json and not args.quiet:
        mode = "CHECK" if args.check else ("DRY-RUN" if args.dry_run else "DERIVE")
        print(f"MODE: {mode}   Paths: {len(paths)}   Today: {today.isoformat()}")
        print(f"Manifest entries: {len(manifest)}")

    changed = already = failed = 0
    results: list = []

    for path in paths:
        ex = _load_exchange(path)
        if ex is None:
            failed += 1
            results.append({"path": str(path), "status": "fatal"})
            continue

        m_entry = manifest.get(path.stem)

        if not _needs_update(ex, m_entry, today):
            already += 1
            results.append({"path": str(path), "status": "unchanged"})
            if not args.quiet and not args.json:
                print(f"  SKIP   {path}  (already current)")
            continue

        new_conf = derive_confidence(ex, m_entry, today)
        old_conf = ex.get("confidence") or {}

        if args.check:
            changed += 1
            results.append({"path": str(path), "status": "needs"})
            if not args.quiet and not args.json:
                print(f"  NEEDS  {path}")
            continue

        if args.dry_run:
            changed += 1
            results.append({"path": str(path), "status": "would-update"})
            if not args.quiet and not args.json:
                old_years = sorted(old_conf.keys())
                new_years = sorted(new_conf.keys())
                tag = (f"{old_years} -> {new_years}"
                       if old_years != new_years
                       else f"same years, values differ ({len(new_years)})")
                print(f"  WOULD  {path}  {tag}")
            continue

        ex["confidence"] = new_conf
        _write(path, ex)
        changed += 1
        results.append({"path": str(path), "status": "updated"})
        if not args.quiet and not args.json:
            print(f"  OK     {path}")

    # ── report ──────────────────────────────────────────────────
    if args.json:
        print(json.dumps({
            "total": len(paths),
            "changed": changed,
            "already": already,
            "failed": failed,
            "check_mode": args.check,
            "dry_run": args.dry_run,
            "today": today.isoformat(),
            "results": results,
        }, indent=2))
    elif not args.quiet:
        print()
        print(f"Total: {len(paths)}  Changed: {changed}  "
              f"Already current: {already}  Failed: {failed}")

    if failed:
        return EXIT_FATAL
    if args.check and changed > 0:
        if not args.quiet and not args.json:
            print(f"CHECK FAILED: {changed} file(s) need confidence update.")
        return EXIT_NEEDS
    if args.check and not args.quiet and not args.json:
        print("CHECK OK: confidence is current everywhere.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
