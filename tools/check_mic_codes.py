#!/usr/bin/env python3
"""
check_mic_codes.py — Cross-registry check: exchange mic fields resolve
to entries in the ISO 10383 MIC registry.

Loads a snapshot of the ISO 10383 registry (tools/iso10383_snapshot.json,
a flat list of MIC codes), and iterates exchanges/*.json verifying:

  1. mic is present and matches ^[A-Z0-9]{4}$
  2. mic equals the file's stem (filename minus .json)
  3. code equals mic, when code is present
  4. mic is in the ISO 10383 snapshot, or on the local allowlist

Usage:
    check_mic_codes.py                    # default snapshot + exchanges/
    check_mic_codes.py --refresh-from PATH
                                          # re-extract from a local
                                          # iso10383.json, then check
    check_mic_codes.py --snapshot PATH    # custom snapshot
    check_mic_codes.py --allowlist PATH   # custom allowlist
    check_mic_codes.py --exchanges-dir PATH
    check_mic_codes.py --quiet
    check_mic_codes.py --json

Exit codes:
    0 — all checks pass
    1 — one or more exchanges failed the check
    2 — snapshot missing or invalid, or exchanges dir missing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SNAPSHOT = REPO_ROOT / "tools" / "iso10383_snapshot.json"
DEFAULT_ALLOWLIST = REPO_ROOT / "tools" / "mic_allowlist.json"
DEFAULT_EXCHANGES = REPO_ROOT / "exchanges"
MIC_RE = re.compile(r"^[A-Z0-9]{4}$")


def load_snapshot(path: Path) -> dict | None:
    """Load and validate the ISO 10383 snapshot. Returns None on failure."""
    if not path.exists():
        print(
            f"ERROR: ISO 10383 snapshot not found: {path}\n"
            f"Run with --refresh-from PATH to create it from a local clone,\n"
            f"e.g. --refresh-from ~/Documents/iso10383/iso10383.json",
            file=sys.stderr,
        )
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: snapshot {path} is not valid JSON: {e}", file=sys.stderr)
        return None
    if not isinstance(data.get("mics"), list):
        print(f"ERROR: snapshot {path} missing 'mics' array", file=sys.stderr)
        return None
    return data


def build_mic_set(snapshot: dict) -> set[str] | None:
    """Return the set of MIC codes, or None if the shape is wrong."""
    out: set[str] = set()
    for entry in snapshot["mics"]:
        if not isinstance(entry, str):
            return None
        out.add(entry)
    return out


def load_allowlist(path: Path | None) -> set[str]:
    """Return the set of allowlisted MICs. Missing file is not an error."""
    if path is None or not path.exists():
        return set()
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: allowlist {path} is not valid JSON: {e}", file=sys.stderr)
        raise
    allowed = data.get("allowed", {})
    if not isinstance(allowed, dict):
        print(f"ERROR: allowlist {path} 'allowed' must be an object", file=sys.stderr)
        raise ValueError("bad allowlist shape")
    return set(allowed.keys())


def check_exchange(
    exchange: dict,
    filename: str,
    mics: set[str],
    allowlist: set[str],
) -> list[str]:
    """Return a list of error strings for one exchange."""
    errors: list[str] = []
    stem = Path(filename).stem
    mic = exchange.get("mic")
    code = exchange.get("code")

    if not mic:
        errors.append(f"{filename}: missing mic")
        return errors
    if not isinstance(mic, str) or not MIC_RE.fullmatch(mic):
        errors.append(f"{filename}: mic not ^[A-Z0-9]{{4}}$: {mic!r}")
        return errors
    if mic != stem:
        errors.append(f"{filename}: mic {mic!r} does not match filename stem {stem!r}")
    if code is not None and code != mic:
        errors.append(f"{filename}: code {code!r} does not match mic {mic!r}")
    if mic not in mics and mic not in allowlist:
        errors.append(
            f"{filename}: mic {mic!r} not in ISO 10383 snapshot "
            f"and not in allowlist"
        )
    return errors


def refresh_snapshot(source: Path, dest: Path) -> bool:
    """Re-extract the MIC set from a local iso10383.json."""
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return False
    try:
        data = json.loads(source.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: source {source} is not valid JSON: {e}", file=sys.stderr)
        return False
    if not isinstance(data.get("mics"), list):
        print(f"ERROR: source {source} missing 'mics' array", file=sys.stderr)
        return False

    mics = sorted({
        e["mic"]
        for e in data["mics"]
        if isinstance(e, dict)
        and isinstance(e.get("mic"), str)
        and len(e["mic"]) == 4
    })
    meta_src = data.get("meta", {})
    out = {
        "meta": {
            "source": "github.com/slimissa/iso10383",
            "source_version": meta_src.get("version", "unknown"),
            "refresh_cadence": "monthly",
            "review_by": "2027-03-01",
        },
        "mics": mics,
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Refreshed snapshot: {dest} ({len(mics)} MICs, "
          f"source_version {out['meta']['source_version']})")
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
        help=f"ISO 10383 snapshot path (default: {DEFAULT_SNAPSHOT.name})",
    )
    ap.add_argument(
        "--allowlist",
        type=Path,
        default=DEFAULT_ALLOWLIST,
        help=f"Local allowlist path (default: {DEFAULT_ALLOWLIST.name})",
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
        help="Re-extract the snapshot from PATH (a local iso10383.json), then check",
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

    snapshot = load_snapshot(args.snapshot)
    if snapshot is None:
        return 2
    mics = build_mic_set(snapshot)
    if mics is None:
        print(f"ERROR: snapshot {args.snapshot} has malformed MIC entries",
              file=sys.stderr)
        return 2

    try:
        allowlist = load_allowlist(args.allowlist)
    except (json.JSONDecodeError, ValueError):
        return 2

    if not args.exchanges_dir.exists():
        print(f"ERROR: exchanges dir not found: {args.exchanges_dir}", file=sys.stderr)
        return 2

    files = sorted(args.exchanges_dir.glob("*.json"))
    if not files:
        print(f"ERROR: no exchange files found in {args.exchanges_dir}", file=sys.stderr)
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
        errors = check_exchange(d, p.name, mics, allowlist)
        per_file.append({"file": p.name, "ok": not errors, "errors": errors})
        all_errors.extend(errors)

    version = snapshot.get("meta", {}).get("source_version", "unknown")

    if args.json:
        print(json.dumps({
            "snapshot": str(args.snapshot),
            "iso10383_version": version,
            "exchanges_checked": len(files),
            "allowlist_size": len(allowlist),
            "errors": all_errors,
            "results": per_file,
        }, indent=2, ensure_ascii=False))
        return 0 if not all_errors else 1

    if all_errors:
        if args.quiet:
            print(f"FAIL — {len(all_errors)} error(s) across {len(files)} exchanges")
        else:
            print(f"MIC-code check failed with {len(all_errors)} error(s):")
            for e in all_errors:
                print(f"  - {e}")
        return 1

    if args.quiet:
        print(f"OK — {len(files)} exchanges, all MICs resolve")
    else:
        print(f"OK: {len(files)} exchange(s) resolved against ISO 10383 v{version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
