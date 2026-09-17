#!/usr/bin/env python3
"""
reconcile_past_due.py — Helper for removing past-due predicted holidays.

WARNING: this tool deletes entries unconditionally. It is appropriate
only when the exchange's source is unreachable (404, timeout, DNS
failure, or robots.txt block). If the source is reachable, fetch it
first and reconcile the confirmed dates instead of deleting them.
See tools/update_from_exchange.py for the fetcher that knows the URL.

Usage:
    reconcile_past_due.py --list                     # show remaining allow-list
    reconcile_past_due.py --mic XTAD                 # preview past-due for one exchange
    reconcile_past_due.py --mic XTAD --delete        # remove them and update allow-list
    reconcile_past_due.py --mic XTAD --delete --no-validate  # skip the validate step

For each exchange, removes every explicit holiday entry whose `predicted`
field is true and whose date is in the past. Also removes the MIC from
KNOWN_PAST_DUE in tools/validate.py.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXCHANGES = ROOT / "exchanges"
VALIDATE = ROOT / "tools" / "validate.py"


def load_allow_list() -> set:
    text = VALIDATE.read_text()
    match = re.search(r"KNOWN_PAST_DUE = \{([^}]+)\}", text, re.DOTALL)
    if not match:
        sys.exit("Could not find KNOWN_PAST_DUE in tools/validate.py")
    return set(re.findall(r'"([A-Z]{4})"', match.group(1)))


def save_allow_list(mics: set) -> None:
    text = VALIDATE.read_text()
    today = date.today().isoformat()
    body = ",\n        ".join(
        '"' + m + '"' for m in sorted(mics)
    ) if mics else ""
    new_set = f"KNOWN_PAST_DUE = {{\n        {body},\n    }}" if mics else "KNOWN_PAST_DUE = set()"
    text = re.sub(r"KNOWN_PAST_DUE = \{[^}]+\}", new_set, text, count=1, flags=re.DOTALL)
    VALIDATE.write_text(text)


def past_due_for(mic: str) -> list:
    with open(EXCHANGES / f"{mic}.json") as f:
        data = json.load(f)
    today = date.today().isoformat()
    return [
        h for h in data["holidays"]["explicit"]
        if h.get("predicted") and h["date"] < today
    ]


def delete_past_due(mic: str) -> int:
    path = EXCHANGES / f"{mic}.json"
    with open(path) as f:
        data = json.load(f)
    today = date.today().isoformat()
    before = len(data["holidays"]["explicit"])
    data["holidays"]["explicit"] = [
        h for h in data["holidays"]["explicit"]
        if not (h.get("predicted") and h["date"] < today)
    ]
    after = len(data["holidays"]["explicit"])
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return before - after


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--list", action="store_true", help="Show remaining allow-list")
    p.add_argument("--mic", help="Exchange MIC to process")
    p.add_argument("--delete", action="store_true", help="Actually delete (default: preview only)")
    p.add_argument("--no-validate", action="store_true", help="Skip tools/validate.py check")
    args = p.parse_args()

    if args.list or not args.mic:
        print("Remaining in KNOWN_PAST_DUE:")
        for mic in sorted(load_allow_list()):
            entries = past_due_for(mic)
            print(f"  {mic}: {len(entries)} entries")
        return

    mic = args.mic.upper()
    entries = past_due_for(mic)
    print(f"{mic}: {len(entries)} past-due entries")
    for h in entries:
        print(f"  {h['date']} | {h['name']} | {h.get('source_url', 'no source')}")

    if not entries:
        print("Nothing to delete.")
        return

    if not args.delete:
        print("\n(dry run — pass --delete to remove)")
        return

    removed = delete_past_due(mic)
    print(f"\nRemoved {removed} entries from exchanges/{mic}.json")

    allow = load_allow_list()
    allow.discard(mic)
    save_allow_list(allow)
    print(f"Removed {mic} from KNOWN_PAST_DUE ({len(allow)} remaining)")

    if not args.no_validate:
        result = subprocess.run(
            [sys.executable, str(VALIDATE)],
            capture_output=True, text=True,
        )
        print(result.stdout.strip().split("\n")[-1])


if __name__ == "__main__":
    main()