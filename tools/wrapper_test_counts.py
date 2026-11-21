#!/usr/bin/env python3
"""Count each wrapper's test declarations and keep the README table current.

README section 15 ("Language wrappers") lists a test count per wrapper. It
was hand-written, mixed counts from running the suites (Python, JS) with
static counts (Go, Rust), and went stale (JS 100, Go 86, Rust 83 until
session 4b1). This tool counts declarations statically, the same way for
all four, so it needs no Go, Rust or Node toolchain and gives the same
number on every machine:

    Python      `def test_...` in tests/test_wrappers.py
    JavaScript  `test(` / `it(` calls in wrappers/javascript/tests/*.js
    Go          `func Test...` in wrappers/go/**/*_test.go
    Rust        `#[test]` in wrappers/rust/src/**/*.rs and wrappers/rust/tests/**/*.rs

A declaration is not a run: pytest parametrization, Go subtests and Rust
doctests make the run counts larger. CI (.github/workflows/validate.yml)
runs every suite.

Usage:
    wrapper_test_counts.py           # --check (default): exit 1 if the README is stale
    wrapper_test_counts.py --write   # rewrite the README cells
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "Python": (["tests/test_wrappers.py"], re.compile(r"^\s*def test_", re.M)),
    "JavaScript": (["wrappers/javascript/tests/*.js"], re.compile(r"^\s*(?:test|it)\(", re.M)),
    "Go": (["wrappers/go/**/*_test.go"], re.compile(r"^func Test", re.M)),
    "Rust": (["wrappers/rust/src/**/*.rs", "wrappers/rust/tests/**/*.rs"], re.compile(r"#\[test\]")),
}

# The Tests cell of each wrapper row in README section 15.
ROW = re.compile(r"^(\| (Python|JavaScript|Go|Rust) \|(?:[^|\n]*\|){3}) ([^|\n]*?) \|$", re.M)


def counts(root: Path = ROOT) -> dict[str, int]:
    out = {}
    for lang, (globs, rx) in PATTERNS.items():
        files = sorted({p for g in globs for p in root.glob(g)})
        out[lang] = sum(len(rx.findall(p.read_text(encoding="utf-8"))) for p in files)
    return out


def cell(lang: str, n: int) -> str:
    return f"{n} declarations" + (" (root suite, `tests/test_wrappers.py`)" if lang == "Python" else "")


def render(readme: str, found: dict[str, int]) -> str:
    seen = set()

    def sub(m: re.Match) -> str:
        seen.add(m.group(2))
        return f"{m.group(1)} {cell(m.group(2), found[m.group(2)])} |"

    text = ROW.sub(sub, readme)
    missing = set(PATTERNS) - seen
    if missing:
        raise SystemExit(f"README: no wrapper row for {', '.join(sorted(missing))}")
    return text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--write", action="store_true", help="rewrite the README cells")
    p.add_argument("--check", action="store_true", help="exit 1 if the README is stale (default)")
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args(argv)
    readme_path = args.root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    found = counts(args.root)
    want = render(readme, found)
    summary = ", ".join(f"{k} {v}" for k, v in found.items())
    if args.write:
        if want != readme:
            readme_path.write_text(want, encoding="utf-8")
            print(f"Wrote README wrapper test counts: {summary}")
        else:
            print(f"OK: README wrapper test counts already current: {summary}")
        return 0
    if want != readme:
        print(f"README wrapper test counts are stale; expected {summary}. "
              "Run tools/wrapper_test_counts.py --write.")
        return 1
    print(f"OK: README wrapper test counts match: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
