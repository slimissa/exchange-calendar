#!/usr/bin/env python3
"""
tools/check_fetcher_freshness.py

Reads fetcher_manifest.json (repo root) and verifies that each
fetcher's last successful fetch is within its declared freshness
window.

The manifest is written by ExchangeFetcher._record_manifest on every
fetch. Each entry carries:

  fetched_at     ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
  source_url     the URL the fetch was made against
  sha256         hex digest of the raw response bytes (null on failure)
  bytes          length of the raw response
  max_age_days   per-fetcher freshness window
  status         "ok" or "failed"

Semantics:

  - Empty `fetches` object         pass (exit 0 with a warning;
                                   fetchers have not run yet)
  - status == "failed"             fail (the last attempt failed)
  - age > max_age_days             fail
  - age <= max_age_days            pass (boundary inclusive)
  - missing/malformed fetched_at   fail
  - missing/invalid max_age_days   fail

Usage:
    python3 tools/check_fetcher_freshness.py
    python3 tools/check_fetcher_freshness.py --quiet
    python3 tools/check_fetcher_freshness.py --json
    python3 tools/check_fetcher_freshness.py --manifest PATH
    python3 tools/check_fetcher_freshness.py --today 2027-01-01

Exit codes:
    0  all fetchers fresh (or manifest empty)
    1  at least one fetcher stale or failed
    2  fatal (manifest missing or malformed, bad --today)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "fetcher_manifest.json"

EXIT_OK = 0
EXIT_STALE = 1
EXIT_FATAL = 2


def parse_iso_date(value: Any) -> Optional[date]:
    """Accept 'YYYY-MM-DD' or full ISO 8601 with optional trailing Z."""
    if value is None:
        return None
    s = str(value)
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def evaluate(mic: str, entry: Any, today: date) -> dict:
    """Return a result dict for one manifest entry."""
    out: dict = {"mic": mic, "status": "ok", "reason": ""}

    if not isinstance(entry, dict):
        out.update(status="fail", reason="entry is not an object")
        return out

    status = entry.get("status")
    if status == "failed":
        out.update(status="fail", reason="last fetch failed")
        return out
    if status != "ok":
        out.update(status="fail", reason=f"unknown status: {status!r}")
        return out

    fetched_at = parse_iso_date(entry.get("fetched_at"))
    if fetched_at is None:
        out.update(status="fail",
                   reason="missing or malformed fetched_at")
        return out

    max_age = entry.get("max_age_days")
    if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age <= 0:
        out.update(status="fail",
                   reason=f"missing or invalid max_age_days: {max_age!r}")
        return out

    age = (today - fetched_at).days
    out["fetched_at"] = fetched_at.isoformat()
    out["max_age_days"] = max_age
    out["age_days"] = age

    if age > max_age:
        out.update(status="fail",
                   reason=f"age {age}d > max_age {max_age}d")
    else:
        out.update(status="ok",
                   reason=f"age {age}d <= max_age {max_age}d")
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="check_fetcher_freshness.py",
        description="Verify each fetcher's last successful fetch is "
                    "within its declared freshness window.",
    )
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST,
                    help=f"Path to fetcher manifest (default: {DEFAULT_MANIFEST.name})")
    ap.add_argument("--today", default=None,
                    help="Override today's date (YYYY-MM-DD) for testing")
    ap.add_argument("--quiet", action="store_true",
                    help="Print only the final OK/FAIL line")
    ap.add_argument("--json", action="store_true",
                    help="Emit machine-readable JSON")
    args = ap.parse_args(argv)

    if args.quiet and args.json:
        print("ERROR: --quiet and --json are mutually exclusive",
              file=sys.stderr)
        return EXIT_FATAL

    if args.today is not None:
        today = parse_iso_date(args.today)
        if today is None:
            print(f"ERROR: --today must be YYYY-MM-DD, got {args.today!r}",
                  file=sys.stderr)
            return EXIT_FATAL
    else:
        today = date.today()

    if not args.manifest.exists():
        print(f"ERROR: manifest not found: {args.manifest}",
              file=sys.stderr)
        return EXIT_FATAL

    try:
        data = json.loads(args.manifest.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: manifest {args.manifest} is not valid JSON: {e}",
              file=sys.stderr)
        return EXIT_FATAL

    if not isinstance(data, dict) or not isinstance(data.get("fetches"), dict):
        print(f"ERROR: manifest {args.manifest} missing 'fetches' object",
              file=sys.stderr)
        return EXIT_FATAL

    fetches = data["fetches"]
    results = [evaluate(mic, entry, today)
               for mic, entry in sorted(fetches.items())]
    stale = [r for r in results if r["status"] != "ok"]

    if args.json:
        print(json.dumps({
            "manifest": str(args.manifest),
            "today": today.isoformat(),
            "checked": len(results),
            "stale": len(stale),
            "results": results,
        }, indent=2, ensure_ascii=False))
        return EXIT_STALE if stale else EXIT_OK

    if args.quiet:
        if stale:
            print(f"FAIL — {len(stale)} stale fetcher(s) of {len(results)}")
            return EXIT_STALE
        print(f"OK — {len(results)} fetcher(s), all fresh")
        return EXIT_OK

    # Verbose
    if not results:
        print("WARNING: manifest has no fetch entries "
              "(fetchers have not run yet).")
        return EXIT_OK

    for r in results:
        marker = "OK  " if r["status"] == "ok" else "FAIL"
        print(f"  [{marker}] {r['mic']}: {r['reason']}")

    if stale:
        print(f"\nFAIL: {len(stale)} stale fetcher(s) of {len(results)}")
        return EXIT_STALE
    print(f"\nOK: {len(results)} fetcher(s) fresh")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
