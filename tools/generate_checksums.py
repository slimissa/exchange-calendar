#!/usr/bin/env python3
"""Generate a SHA-256 checksum manifest for the registry's data and
tooling files.

Covers:
  - exchanges/*.json  (all 74 exchange data files)
  - schema.json
  - tools/*.py         (this script and its siblings)

Deliberately does NOT cover calendar.json (a build artifact, not a
source file -- checksumming it would just checksum the other files a
second time) or wrapper/test source (out of scope for data-integrity
verification; use normal code review / CI for those).

Output: checksums.json at the repo root, in the form:
  {
    "generated": "<UTC ISO-8601 timestamp>",
    "algorithm": "sha256",
    "files": {
      "exchanges/XSAU.json": "<hex digest>",
      ...
    }
  }

Usage:
  python3 tools/generate_checksums.py
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files() -> list[Path]:
    files = sorted((REPO_ROOT / "exchanges").glob("*.json"))
    files.append(REPO_ROOT / "schema.json")
    files.extend(sorted((REPO_ROOT / "tools").glob("*.py")))
    return files


def main() -> int:
    files = collect_files()
    manifest = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "algorithm": "sha256",
        "files": {},
    }

    missing = []
    for path in files:
        if not path.is_file():
            missing.append(str(path.relative_to(REPO_ROOT)))
            continue
        rel = str(path.relative_to(REPO_ROOT))
        manifest["files"][rel] = sha256_of(path)

    if missing:
        print(f"ERROR: {len(missing)} expected file(s) not found:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1

    out_path = REPO_ROOT / "checksums.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"OK: wrote {len(manifest['files'])} checksum(s) to {out_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
