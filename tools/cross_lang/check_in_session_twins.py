#!/usr/bin/env python3
"""Check the in_session twins of the is_open probes (session 4d2).

In 2.x the registry-level `in_session` is the any-session alias of
`is_open` (both delegate to one function in every wrapper). The fixture
tests/cross_language_queries.json must give every `is_open` probe an
`in_session` twin, labelled `in_session_<suffix>` for `is_open_<suffix>`,
with the same args; every twin must answer the same as its `is_open` probe.

Usage:
    check_in_session_twins.py                 # fixture structure only
    check_in_session_twins.py OUT.json [...]  # also each runner's output

Exit 0 when every check passes, 1 otherwise.
"""
import json
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "cross_language_queries.json"


def pairs(queries: list[dict]) -> tuple[list[tuple[str, str]], list[str]]:
    """[(is_open label, in_session label)] and the structural problems."""
    by_label = {q["label"]: q for q in queries}
    found, problems = [], []
    for q in queries:
        if q["op"] != "is_open":
            continue
        if not q["label"].startswith("is_open_"):
            problems.append(f"is_open probe {q['label']!r} is not labelled is_open_<suffix>")
            continue
        twin = "in_session_" + q["label"][len("is_open_"):]
        t = by_label.get(twin)
        if t is None:
            problems.append(f"{q['label']}: no in_session twin {twin!r}")
        elif t["op"] != "in_session" or t["args"] != q["args"]:
            problems.append(f"{twin}: op/args differ from {q['label']} "
                            f"({t['op']} {t['args']} vs is_open {q['args']})")
        else:
            found.append((q["label"], twin))
    for q in queries:
        if q["op"] != "in_session":
            continue
        partner = "is_open_" + q["label"].removeprefix("in_session_")
        if not q["label"].startswith("in_session_") or by_label.get(partner, {}).get("op") != "is_open":
            problems.append(f"in_session probe {q['label']!r} has no is_open probe")
    return found, problems


def main(argv: list[str]) -> int:
    queries = json.loads(FIXTURE.read_text(encoding="utf-8"))["queries"]
    found, problems = pairs(queries)
    for path in argv:
        out = json.loads(Path(path).read_text(encoding="utf-8"))
        for a, b in found:
            if a not in out or b not in out:
                problems.append(f"{path}: missing {a if a not in out else b}")
            elif out[a] != out[b]:
                problems.append(f"{path}: {b} = {out[b]!r} but {a} = {out[a]!r}")
    if problems:
        for p in problems:
            print(f"ERROR: {p}", file=sys.stderr)
        return 1
    print(f"OK: {len(found)} in_session twin(s) match their is_open probes"
          + (f" in {len(argv)} output(s)" if argv else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
