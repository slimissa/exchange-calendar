#!/usr/bin/env python3
"""
check_country_codes.py — Cross-registry check: exchange country_code
fields resolve to active ISO 3166 entries, and country names match
the ISO 3166 name field byte-for-byte.

Loads a snapshot of the ISO 3166 registry (tools/iso3166_snapshot.json),
builds the alpha_2 -> name map from countries.active, and iterates
exchanges/*.json verifying:

  1. country_code is present and matches ^[A-Z]{2}$
  2. country_code is a key in the ISO 3166 active map
  3. country matches the map's value byte-for-byte

Usage:
    check_country_codes.py                    # default snapshot + exchanges/
    check_country_codes.py --refresh-from PATH
                                              # copy PATH to the snapshot
                                              # location, then check
    check_country_codes.py --snapshot PATH    # custom snapshot
    check_country_codes.py --exchanges-dir PATH
    check_country_codes.py --quiet
    check_country_codes.py --json

Exit codes:
    0 — all checks pass
    1 — one or more exchanges failed the check
    2 — snapshot missing or invalid, or exchanges dir missing
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SNAPSHOT = REPO_ROOT / "tools" / "iso3166_snapshot.json"
DEFAULT_EXCHANGES = REPO_ROOT / "exchanges"
ALPHA2_RE = re.compile(r"^[A-Z]{2}$")


def load_snapshot(path: Path) -> dict | None:
    """Load and validate the ISO 3166 snapshot. Returns None on failure."""
    if not path.exists():
        print(
            f"ERROR: ISO 3166 snapshot not found: {path}\n"
            f"Run with --refresh-from PATH to create it from a local clone,\n"
            f"e.g. --refresh-from ~/Documents/iso3166/iso3166.json",
            file=sys.stderr,
        )
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: snapshot {path} is not valid JSON: {e}", file=sys.stderr)
        return None
    if not isinstance(data.get("countries"), dict):
        print(f"ERROR: snapshot {path} missing countries object", file=sys.stderr)
        return None
    if not isinstance(data["countries"].get("active"), list):
        print(f"ERROR: snapshot {path} missing countries.active array", file=sys.stderr)
        return None
    return data


def build_lookup(snapshot: dict) -> dict[str, str] | None:
    """Return {alpha_2: name} for active entries, or None if shape is wrong."""
    lookup: dict[str, str] = {}
    for entry in snapshot["countries"]["active"]:
        if not isinstance(entry, dict):
            return None
        code = entry.get("alpha_2")
        name = entry.get("name")
        if not isinstance(code, str) or not isinstance(name, str):
            return None
        lookup[code] = name
    return lookup


def check_exchange(
    exchange: dict, filename: str, lookup: dict[str, str]
) -> list[str]:
    """Return a list of error strings for one exchange."""
    errors: list[str] = []
    code = exchange.get("country_code")
    name = exchange.get("country")

    if not code:
        errors.append(f"{filename}: missing country_code")
        return errors
    if not isinstance(code, str) or not ALPHA2_RE.fullmatch(code):
        errors.append(f"{filename}: country_code not ^[A-Z]{{2}}$: {code!r}")
        return errors
    if code not in lookup:
        errors.append(f"{filename}: country_code {code!r} not in ISO 3166 active set")
        return errors
    if not name:
        errors.append(f"{filename}: missing country")
        return errors
    expected = lookup[code]
    if name != expected:
        errors.append(
            f"{filename}: country {name!r} does not match ISO 3166 name "
            f"for {code}: {expected!r}"
        )
    return errors


def refresh_snapshot(source: Path, dest: Path) -> bool:
    """Copy source to dest after validating it looks like an ISO 3166 registry."""
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return False
    if source.resolve() == dest.resolve():
        print(
            f"ERROR: source and destination are the same file: {source}",
            file=sys.stderr,
        )
        return False
    try:
        data = json.loads(source.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: source {source} is not valid JSON: {e}", file=sys.stderr)
        return False
    if not isinstance(data.get("countries"), dict) or not isinstance(
        data["countries"].get("active"), list
    ):
        print(
            f"ERROR: source {source} does not look like an ISO 3166 registry",
            file=sys.stderr,
        )
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--snapshot",
        type=Path,
        default=DEFAULT_SNAPSHOT,
        help=f"ISO 3166 snapshot path (default: {DEFAULT_SNAPSHOT.name})",
    )
    ap.add_argument(
        "--exchanges-dir",
        type=Path,
        default=DEFAULT_EXCHANGES,
        help=f"Directory of exchange JSON files (default: {DEFAULT_EXCHANGES.name}/)",
    )
    ap.add_argument(
        "--refresh-from",
        type=Path,
        default=None,
        metavar="PATH",
        help="Copy PATH (a local iso3166.json) to the snapshot location, then check",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the final OK/FAIL line",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable summary to stdout",
    )
    args = ap.parse_args(argv)

    if args.quiet and args.json:
        print("ERROR: --quiet and --json are mutually exclusive", file=sys.stderr)
        return 2

    if args.refresh_from is not None:
        if not refresh_snapshot(args.refresh_from, args.snapshot):
            return 2
        if not args.quiet and not args.json:
            print(f"Refreshed snapshot: {args.snapshot}")

    snapshot = load_snapshot(args.snapshot)
    if snapshot is None:
        return 2
    lookup = build_lookup(snapshot)
    if lookup is None:
        print(
            f"ERROR: snapshot {args.snapshot} has malformed country entries",
            file=sys.stderr,
        )
        return 2

    if not args.exchanges_dir.exists():
        print(
            f"ERROR: exchanges dir not found: {args.exchanges_dir}",
            file=sys.stderr,
        )
        return 2

    files = sorted(args.exchanges_dir.glob("*.json"))
    if not files:
        print(
            f"ERROR: no exchange files found in {args.exchanges_dir}",
            file=sys.stderr,
        )
        return 2

    all_errors: list[str] = []
    per_file: list[dict] = []

    for p in files:
        try:
            d = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            msg = f"{p.name}: not valid JSON: {e}"
            all_errors.append(msg)
            per_file.append({"file": p.name, "ok": False, "errors": [msg]})
            continue
        errors = check_exchange(d, p.name, lookup)
        per_file.append({"file": p.name, "ok": not errors, "errors": errors})
        all_errors.extend(errors)

    version = snapshot.get("meta", {}).get("version", "unknown")

    if args.json:
        print(
            json.dumps(
                {
                    "snapshot": str(args.snapshot),
                    "iso3166_version": version,
                    "exchanges_checked": len(files),
                    "errors": all_errors,
                    "results": per_file,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if not all_errors else 1

    if all_errors:
        if args.quiet:
            print(f"FAIL — {len(all_errors)} error(s) across {len(files)} exchanges")
        else:
            print(f"Country-code check failed with {len(all_errors)} error(s):")
            for e in all_errors:
                print(f"  - {e}")
        return 1

    if args.quiet:
        print(f"OK — {len(files)} exchanges, all country codes resolve")
    else:
        print(f"OK: {len(files)} exchange(s) resolved against ISO 3166 v{version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
