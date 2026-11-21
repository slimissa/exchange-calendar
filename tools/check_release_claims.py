#!/usr/bin/env python3
"""
tools/check_release_claims.py

Read tools/release_claims.json and verify every claim for a given
version against the current repository state.

Each claim is one of:

  {"file": "path"}                     — path must exist
  {"file": "path", "contains": "text"} — path must exist and include text

Usage:
    python3 tools/check_release_claims.py 1.6.5
    python3 tools/check_release_claims.py 1.6.5 --list
    python3 tools/check_release_claims.py 1.6.5 --json

Claims are a snapshot, not a permanent check on the tree
---------------------------------------------------------
Each version's claims record what that release shipped. scripts/release.sh
checks them for the version being released, at release time. Later work may
legitimately break an older release's claims (a schema bump changes
schema.json's "version"; a renamed file moves), so many older versions fail
on today's tree, and that is expected. Do not run an already released
version's claims in the per-commit gate, and do not edit released claims to
make them pass: the gate runs only the claims of the next, unreleased
version. (Decided in session 4b1, after a brief asked the gate to keep
v2.28.0's claims passing across the schema 2.3.0 bump.)

Exit codes:
    0  all claims verified
    1  at least one claim failed
    2  fatal (manifest missing, version not in manifest, malformed entry)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT_ROOT / "tools" / "release_claims.json"


class FatalError(SystemExit):
    def __init__(self, message: str, code: int = 2) -> None:
        print(f"error: {message}", file=sys.stderr)
        super().__init__(code)


def load_manifest() -> dict:
    if not MANIFEST.exists():
        raise FatalError(f"manifest not found: {MANIFEST}")
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FatalError(f"{MANIFEST}: invalid JSON: {exc}") from exc


def check_claim(claim: dict) -> tuple[bool, str]:
    if "file" not in claim:
        return False, "claim has no 'file' key"
    path = PROJECT_ROOT / claim["file"]
    if not path.exists():
        return False, f"missing file: {claim['file']}"
    if "contains" in claim:
        needle = claim["contains"]
        if needle not in path.read_text(encoding="utf-8"):
            return False, f"{claim['file']} does not contain {needle!r}"
        return True, f"{claim['file']} contains {needle!r}"
    return True, f"{claim['file']} exists"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="check_release_claims")
    p.add_argument("version")
    p.add_argument("--list", action="store_true",
                   help="Print claims without checking")
    p.add_argument("--json", action="store_true",
                   help="Machine-readable output")
    args = p.parse_args(argv)

    manifest = load_manifest()
    claims = manifest.get(args.version)
    if claims is None:
        raise FatalError(
            f"no claims for version {args.version} in {MANIFEST.name}. "
            f"Every release must have a manifest entry."
        )
    if not isinstance(claims, list):
        raise FatalError(f"claims for {args.version} is not a list")

    results = []
    for claim in claims:
        if not isinstance(claim, dict):
            results.append((False, f"not an object: {claim!r}"))
            continue
        results.append(check_claim(claim))

    if args.json:
        print(json.dumps({
            "version": args.version,
            "total": len(results),
            "passed": sum(1 for ok, _ in results if ok),
            "failed": sum(1 for ok, _ in results if not ok),
            "results": [{"ok": ok, "detail": d} for ok, d in results],
        }, indent=2))
    else:
        rule = "=" * 60
        print(rule)
        print(f"  release claims — v{args.version}")
        print(rule)
        for ok, detail in results:
            marker = "OK  " if ok else "FAIL"
            print(f"  [{marker}] {detail}")
        print(rule)
        failed = [d for ok, d in results if not ok]
        if failed:
            print(f"  {len(failed)} claim(s) failed")
        else:
            print(f"  all {len(results)} claim(s) verified")

    return 0 if all(ok for ok, _ in results) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FatalError as exc:
        sys.exit(exc.code)
