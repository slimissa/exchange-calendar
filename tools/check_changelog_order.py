#!/usr/bin/env python3
"""Check the order of CHANGELOG.md's version headings.

Rules, on every line that starts with "## [":
  - "## [Unreleased]", if present, is the first such heading (and appears once);
  - every other heading names a version X.Y.Z;
  - released versions are strictly descending from top to bottom, which also
    rules out a version appearing twice.

Session 4b5 appended its entries under an [Unreleased] heading placed below
[2.32.0]; release.sh then found the wrong top entry. This check runs in the
gate, in CI (validate.yml) and in release.sh's static preflight.

Usage: python3 tools/check_changelog_order.py [PATH]   (default CHANGELOG.md)
Exit 0 when the order is valid, 1 otherwise.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADING = re.compile(r"^## \[([^\]]*)\]")
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def problems(text):
    """Return a list of problems with the "## [" headings in ``text``."""
    out = []
    seen = {}
    previous = None  # (version tuple, line number) of the last release heading
    first = True
    for number, line in enumerate(text.splitlines(), 1):
        m = HEADING.match(line)
        if not m:
            continue
        label = m.group(1)
        if label == "Unreleased":
            if not first:
                out.append(f"line {number}: ## [Unreleased] is not the first '## [' heading")
            if "Unreleased" in seen:
                out.append(f"line {number}: ## [Unreleased] appears twice (first on line {seen['Unreleased']})")
            seen.setdefault("Unreleased", number)
            first = False
            continue
        first = False
        v = VERSION.match(label)
        if not v:
            out.append(f"line {number}: heading [{label}] is neither Unreleased nor a version X.Y.Z")
            continue
        key = tuple(int(x) for x in v.groups())
        if label in seen:
            out.append(f"line {number}: version {label} appears twice (first on line {seen[label]})")
        seen.setdefault(label, number)
        if previous is not None and not key < previous[0]:
            out.append(
                f"line {number}: version {label} is not below the version on line {previous[1]} "
                f"({'.'.join(map(str, previous[0]))}); released headings must be strictly descending"
            )
        previous = (key, number)
    if not seen:
        out.append("no '## [' headings found")
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0]) if argv else ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    found = problems(text)
    if found:
        for p in found:
            print(f"ERROR: {path.name}: {p}")
        return 1
    count = sum(1 for line in text.splitlines() if HEADING.match(line))
    top = next(HEADING.match(line).group(1) for line in text.splitlines() if HEADING.match(line))
    print(f"OK: {path.name}: {count} '## [' heading(s) in order; top is [{top}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
