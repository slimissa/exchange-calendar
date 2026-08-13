#!/usr/bin/env python3
"""
build.py — Build the single-file distribution artifact (calendar.json).

Reads every exchange file from exchanges/, expands recurrence rules into
explicit dates using generate_dates.py, and writes the concatenated result
to calendar.json.

The build is deterministic: given identical exchange files, the output is
byte-for-byte identical. Timestamps are omitted to preserve reproducibility.

Usage:
    build.py [exchanges_dir] [output_path]

Defaults:
    exchanges_dir = "exchanges"
    output_path   = "calendar.json"

Exit codes:
    0 — Build successful
    1 — Build failed (missing directory, invalid JSON, generation error)
"""

import json
import sys
from datetime import date
from pathlib import Path

# Import from sibling module
sys.path.insert(0, str(Path(__file__).parent))
from generate_dates import expand_exchange


REGISTRY_VERSION = "1.0.0"


def load_exchange(path: Path) -> dict:
    """Load and parse an exchange JSON file. Returns None on failure."""
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: {path.name}: Invalid JSON: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"ERROR: {path.name}: File not found", file=sys.stderr)
        return None


def merge_holidays(exchange: dict) -> dict:
    """
    Merge explicit holidays with generated recurrence dates.

    Returns a dict with:
        explicit: original explicit array (unchanged)
        generated: dates produced from recurrence rules (sorted)
    """
    try:
        generated = expand_exchange(exchange)
    except ValueError as e:
        print(f"ERROR: {exchange.get('code', 'unknown')}: {e}", file=sys.stderr)
        return None

    holidays = exchange.get("holidays", {})

    return {
        "explicit": holidays.get("explicit", []),
        "generated": generated,
    }


def build_registry(exchanges_dir: Path) -> dict:
    """Build the complete registry from all exchange files."""
    exchange_files = sorted(exchanges_dir.glob("*.json"))

    if not exchange_files:
        raise ValueError(f"No exchange files found in {exchanges_dir}")

    exchanges = []
    errors = 0

    for exchange_file in exchange_files:
        exchange = load_exchange(exchange_file)
        if exchange is None:
            errors += 1
            continue

        merged_holidays = merge_holidays(exchange)
        if merged_holidays is None:
            errors += 1
            continue

        # Build the output exchange object
        output_exchange = {
            "code": exchange.get("code"),
            "name": exchange.get("name"),
            "mic": exchange.get("mic"),
            "timezone": exchange.get("timezone"),
            "regular_hours": exchange.get("regular_hours", {}),
            "extended_hours": exchange.get("extended_hours", {}),
            "sessions": exchange.get("sessions", []),
            "holidays": merged_holidays,
            "ad_hoc_closures": exchange.get("ad_hoc_closures", []),
            "generation_range": exchange.get("generation_range", []),
        }

        exchanges.append(output_exchange)

    if errors > 0:
        raise ValueError(f"{errors} exchange file(s) failed to load or generate")

    # Verify no duplicate codes
    seen_codes = set()
    for exchange in exchanges:
        code = exchange["code"]
        if code in seen_codes:
            raise ValueError(f"Duplicate exchange code: {code}")
        seen_codes.add(code)

    # Sort exchanges by code for determinism
    exchanges.sort(key=lambda x: x["code"])

    return {
        "meta": {
            "version": REGISTRY_VERSION,
            "exchange_count": len(exchanges),
        },
        "exchanges": exchanges,
    }


def write_registry(registry: dict, output_path: Path) -> None:
    """Write the registry to the output file with deterministic formatting."""
    with open(output_path, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    exchanges_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("exchanges")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("calendar.json")

    if not exchanges_dir.exists():
        print(f"ERROR: Exchanges directory not found: {exchanges_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        registry = build_registry(exchanges_dir)
    except ValueError as e:
        print(f"ERROR: Build failed: {e}", file=sys.stderr)
        sys.exit(1)

    write_registry(registry, output_path)

    print(f"OK: Built {output_path} with {registry['meta']['exchange_count']} exchange(s)")
    sys.exit(0)


if __name__ == "__main__":
    main()