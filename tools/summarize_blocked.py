#!/usr/bin/env python3
"""One-line summary of blocked_by_removal entries in an update log."""
import json
import sys


def main(path: str) -> int:
    with open(path) as f:
        data = json.load(f)
    blocked = sorted(
        m for m, v in data.items()
        if v.get("status") == "blocked_by_removal"
    )
    if not blocked:
        print("no exchanges blocked")
        return 0
    print(f"{len(blocked)} exchange(s) blocked: {', '.join(blocked)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
