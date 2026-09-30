#!/usr/bin/env python3
"""
tools/check_removed_entries.py

Compare two exchange datasets and classify removals. Three classes:

  - Holiday removed     a date no longer present in an exchange's
                        holidays.explicit
  - Exchange removed    an old MIC has no counterpart in the new dataset
  - MIC renamed         an old MIC is absent, and a new MIC in the new
                        dataset shares the old entry's `name`

A removal is the change class most likely to break a downstream
consumer. This tool makes it a deliberate decision, not a silent one.

Usage:
    check_removed_entries.py --old exchanges/ --new proposed/
    check_removed_entries.py --old exchanges/ --new-json payload.json
    check_removed_entries.py --old exchanges/ --new exchanges/ --json
    check_removed_entries.py --old exchanges/ --new proposed/ --quiet

Exit codes:
    0  no removals
    1  at least one removal (see output)
    2  fatal (missing input, malformed JSON, unrecognized shape)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional


EXIT_OK = 0
EXIT_REMOVED = 1
EXIT_FATAL = 2

_MIC_RE = re.compile(r"^[A-Z0-9]{4}$")


# ── Loading ────────────────────────────────────────────────────────

def load_dataset(path: Path) -> Optional[dict[str, dict]]:
    """Load a directory of exchange JSONs or a single JSON file.

    Returns {mic: exchange_dict} keyed by filename stem when a
    directory is given, or by the exchange's `mic` field when a file
    is given. Returns None on any failure (and prints the reason).
    """
    if not path.exists():
        print(f"ERROR: path not found: {path}", file=sys.stderr)
        return None

    out: dict[str, dict] = {}

    if path.is_dir():
        files = sorted(path.glob("*.json"))
        if not files:
            print(f"ERROR: no *.json files in {path}", file=sys.stderr)
            return None
        for f in files:
            try:
                d = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError) as e:
                print(f"ERROR: {f}: not valid JSON: {e}", file=sys.stderr)
                return None
            if not isinstance(d, dict):
                print(f"ERROR: {f}: not a JSON object", file=sys.stderr)
                return None
            out[f.stem] = d
        return out if out else None

    # Single file
    try:
        d = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: {path}: not valid JSON: {e}", file=sys.stderr)
        return None

    # Shape 1: {"exchanges": [ {...}, ... ]}
    if isinstance(d, dict) and isinstance(d.get("exchanges"), list):
        for ex in d["exchanges"]:
            if isinstance(ex, dict) and isinstance(ex.get("mic"), str):
                out[ex["mic"]] = ex
        return out if out else _shape_error(path)

    # Shape 2: [ {...}, ... ]
    if isinstance(d, list):
        for ex in d:
            if isinstance(ex, dict) and isinstance(ex.get("mic"), str):
                out[ex["mic"]] = ex
        return out if out else _shape_error(path)

    # Shape 3: a single exchange object with `mic`
    if isinstance(d, dict) and isinstance(d.get("mic"), str):
        out[d["mic"]] = d
        return out

    # Shape 4: { MIC: {...}, ... } with MIC-shaped keys
    if isinstance(d, dict):
        for k, v in d.items():
            if _MIC_RE.match(k) and isinstance(v, dict):
                out[k] = v
        return out if out else _shape_error(path)

    return _shape_error(path)


def _shape_error(path: Path) -> None:
    print(
        f"ERROR: {path}: unrecognized JSON shape. Expected a directory "
        f"of exchange files, a list of exchanges, an {{\"exchanges\": "
        f"[...]}} object, a single exchange with a `mic` field, or a "
        f"dict keyed by MIC.",
        file=sys.stderr,
    )
    return None


# ── Diff ───────────────────────────────────────────────────────────

def _holiday_dates(exchange: dict) -> set[str]:
    """Return the set of dates in holidays.explicit. Empty on any
    shape mismatch."""
    holidays = exchange.get("holidays")
    if not isinstance(holidays, dict):
        return set()
    explicit = holidays.get("explicit")
    if not isinstance(explicit, list):
        return set()
    dates: set[str] = set()
    for h in explicit:
        if isinstance(h, dict):
            d = h.get("date")
            if isinstance(d, str):
                dates.add(d)
    return dates


def _exchange_name(exchange: dict) -> str:
    n = exchange.get("name")
    return n if isinstance(n, str) else ""


def diff_removals(
    old: dict[str, dict],
    new: dict[str, dict],
) -> dict[str, list]:
    """Classify removals.

    Returns:
      {
        "holidays":              [(mic, date), ...],
        "all_holidays_removed":  [(mic, count), ...],
        "exchanges":             [(mic,), ...],
        "mic_renames":           [(old_mic, new_mic, name), ...],
      }
    """
    out: dict[str, list] = {
        "holidays": [],
        "all_holidays_removed": [],
        "exchanges": [],
        "mic_renames": [],
    }

    # name -> [new MICs], for rename detection
    by_name: dict[str, list[str]] = {}
    for mic, ex in new.items():
        name = _exchange_name(ex)
        if name:
            by_name.setdefault(name, []).append(mic)

    old_mics = set(old.keys())
    new_mics = set(new.keys())

    for mic in sorted(old_mics):
        old_ex = old[mic]

        if mic in new_mics:
            old_dates = _holiday_dates(old_ex)
            new_dates = _holiday_dates(new[mic])
            if old_dates and not new_dates:
                out["all_holidays_removed"].append((mic, len(old_dates)))
            else:
                for d in sorted(old_dates - new_dates):
                    out["holidays"].append((mic, d))
            continue

        # MIC absent — removal or rename?
        old_name = _exchange_name(old_ex)
        candidates = [m for m in by_name.get(old_name, []) if m not in old_mics]
        if len(candidates) == 1:
            out["mic_renames"].append((mic, candidates[0], old_name))
        else:
            out["exchanges"].append((mic,))

    return out


def has_removals(removals: dict[str, list]) -> bool:
    return any(removals[k] for k in (
        "holidays", "all_holidays_removed", "exchanges", "mic_renames"
    ))


def _total(removals: dict[str, list]) -> int:
    return sum(len(v) for v in removals.values())


# ── Reporting ──────────────────────────────────────────────────────

def format_removals(removals: dict[str, list]) -> str:
    lines: list[str] = []
    lines.append(f"Removals detected ({_total(removals)}):")
    lines.append("")

    if removals["all_holidays_removed"]:
        n = len(removals["all_holidays_removed"])
        lines.append(f"Holidays removed (all, {n} exchange(s)):")
        for mic, count in removals["all_holidays_removed"]:
            lines.append(
                f"  {mic}: all {count} holidays removed (empty in new)"
            )
        lines.append("")

    if removals["holidays"]:
        lines.append(f"Holidays removed ({len(removals['holidays'])}):")
        for mic, date in removals["holidays"]:
            lines.append(
                f"  {mic} {date} — a consumer that referenced this "
                f"date is now wrong"
            )
        lines.append("")

    if removals["exchanges"]:
        lines.append(f"Exchanges removed ({len(removals['exchanges'])}):")
        for (mic,) in removals["exchanges"]:
            lines.append(
                f"  {mic} — a consumer that mapped a country to this "
                f"venue has lost it"
            )
        lines.append("")

    if removals["mic_renames"]:
        lines.append(f"MIC renames ({len(removals['mic_renames'])}):")
        for old_mic, new_mic, _name in removals["mic_renames"]:
            lines.append(
                f"  {old_mic} → {new_mic} — a consumer keyed on "
                f"{old_mic} sees a rename"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ── CLI ────────────────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="check_removed_entries.py",
        description="Classify removals between two exchange datasets.",
    )
    ap.add_argument("--old", required=True, type=Path,
                    help="Current dataset: directory of exchange JSONs, "
                         "or a single JSON file")
    new_group = ap.add_mutually_exclusive_group(required=True)
    new_group.add_argument("--new", type=Path, default=None,
                           help="Proposed dataset: directory or single "
                                "JSON file")
    new_group.add_argument("--new-json", type=Path, default=None,
                           dest="new_json",
                           help="Alias for --new; single JSON file")
    ap.add_argument("--quiet", action="store_true",
                    help="Print only the final OK/FAIL line")
    ap.add_argument("--json", action="store_true",
                    help="Emit machine-readable JSON")
    args = ap.parse_args(argv)

    if args.quiet and args.json:
        print("ERROR: --quiet and --json are mutually exclusive",
              file=sys.stderr)
        return EXIT_FATAL

    new_path: Path = args.new if args.new is not None else args.new_json

    old = load_dataset(args.old)
    if old is None:
        return EXIT_FATAL
    new = load_dataset(new_path)
    if new is None:
        return EXIT_FATAL

    removals = diff_removals(old, new)
    found = has_removals(removals)

    if args.json:
        print(json.dumps({
            "old": str(args.old),
            "new": str(new_path),
            "old_count": len(old),
            "new_count": len(new),
            "has_removals": found,
            "removals": {
                "holidays": [
                    {"mic": m, "date": d} for m, d in removals["holidays"]
                ],
                "all_holidays_removed": [
                    {"mic": m, "count": n}
                    for m, n in removals["all_holidays_removed"]
                ],
                "exchanges": [m for (m,) in removals["exchanges"]],
                "mic_renames": [
                    {"old": o, "new": nn, "name": name}
                    for o, nn, name in removals["mic_renames"]
                ],
            },
        }, indent=2, ensure_ascii=False))
        return EXIT_REMOVED if found else EXIT_OK

    if not found:
        if args.quiet:
            print("OK — no removals")
        else:
            print(f"OK: no removals between {args.old} and {new_path}")
        return EXIT_OK

    if args.quiet:
        print(f"FAIL — {_total(removals)} removal(s) detected")
        return EXIT_REMOVED

    print(format_removals(removals), end="")
    return EXIT_REMOVED


if __name__ == "__main__":
    sys.exit(main())
