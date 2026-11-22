#!/usr/bin/env python3
"""Escalate the scheduled live fetcher check across runs (4b3).

Reads this run's results (live_fetcher_check.py --json-out) and the body of
the open "Live fetcher check failing" issue, if any, which carries the
per-MIC streak state in a hidden block:

    <!-- live-check-state: {"streaks": {"XCAY": {"kind": "TRANSIENT", "count": 1}}} -->

and decides:

  escalate   a fetcher FAILed (deterministic), or is TRANSIENT in two
             consecutive scheduled runs: the workflow fails.
  action     "close"  -- every fetcher passed (SKIP ignored): close the issue
             "upsert" -- something did not pass: create or update the issue
                         (one issue, label `live-check`) with the summary
                         table and the streaks
             "none"   -- all green and no issue to close

The issue is the only state (no commits from CI, no artifacts, so the
workflow needs `issues: write` and nothing else). A first transient failure
opens the issue as "Watching"; it becomes "Failing" when the workflow fails.

Usage:
  python3 tools/live_check_escalate.py --results r.json --previous-body prev.md \
      --body-out body.md --decision-out decision.json [--run-url URL]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TITLE = "Live fetcher check failing"
LABEL = "live-check"
STATE_RE = re.compile(r"<!--\s*live-check-state:\s*(\{.*?\})\s*-->", re.S)


def parse_state(body: str) -> dict:
    m = STATE_RE.search(body or "")
    if not m:
        return {"streaks": {}}
    try:
        state = json.loads(m.group(1))
    except ValueError:
        return {"streaks": {}}
    return {"streaks": dict(state.get("streaks") or {})}


def next_state(results: list[dict], previous: dict) -> dict:
    """Streak per MIC: PASS clears it; TRANSIENT and FAIL count consecutive
    runs of the same kind (a change of kind restarts the count)."""
    prev = previous.get("streaks", {})
    streaks: dict = {}
    for r in results:
        st = r.get("status")
        if st not in ("TRANSIENT", "FAIL"):  # PASS, SKIP and KNOWN (4b4) carry no streak
            continue
        old = prev.get(r["mic"]) or {}
        count = old.get("count", 0) + 1 if old.get("kind") == st else 1
        streaks[r["mic"]] = {"kind": st, "count": count}
    return {"streaks": streaks}


def decide(results: list[dict], state: dict, issue_open: bool) -> dict:
    streaks = state["streaks"]
    failing = sorted(m for m, s in streaks.items() if s["kind"] == "FAIL")
    repeated = sorted(m for m, s in streaks.items() if s["kind"] == "TRANSIENT" and s["count"] >= 2)
    all_green = not streaks
    escalate = bool(failing or repeated)
    action = "close" if all_green and issue_open else "none" if all_green else "upsert"
    known = sorted(r["mic"] for r in results if r.get("status") == "KNOWN")
    return {"escalate": escalate, "all_green": all_green, "action": action,
            "failing": failing, "repeated_transient": repeated, "known": known}


def render_body(results: list[dict], state: dict, decision: dict, run_url: str = "", run_at: str = "") -> str:
    head = ("**Failing**: the scheduled workflow failed"
            if decision["escalate"] else
            "**Watching**: a fetcher failed transiently once; the workflow fails if it repeats next run")
    lines = [f"Status: {head}.", ""]
    if decision["failing"]:
        lines.append("Deterministic failures (fix the fetcher or the data): " + ", ".join(decision["failing"]))
    if decision["repeated_transient"]:
        lines.append("Transient in two or more consecutive scheduled runs: "
                     + ", ".join(decision["repeated_transient"]))
    known = [r for r in results if r.get("status") == "KNOWN"]
    if known:
        lines.append("Known source faults (shown, not escalated; tools/known_source_faults.json):")
        for r in known:
            kf = r.get("known_fault") or {}
            lines.append(f"- {r['mic']}: {kf.get('reason')} (opened {kf.get('opened')}, expires {kf.get('expires')})")
    cleared = [r for r in results if r.get("warning")]
    for r in cleared:
        lines.append(f"Warning: {r['mic']}: {r['warning']}")
    if run_url or run_at:
        lines.append(f"Run: {run_url or '-'} ({run_at or '-'})")
    lines += ["", "| MIC | Status | Attempts | Detail |", "|-----|--------|----------|--------|"]
    for r in results:
        if r.get("status") == "PASS":
            detail = f"{r.get('holiday_count', '?')} holidays"
        else:
            detail = (r.get("reason") or "").replace("|", "\\|").replace("\n", " ")[:200]
        lines.append(f"| {r['mic']} | {r.get('status')} | {r.get('attempts', 0)} | {detail} |")
    lines += ["", "Streaks (consecutive scheduled runs):", "",
              "| MIC | Kind | Runs |", "|-----|------|------|"]
    for mic, s in sorted(state["streaks"].items()):
        lines.append(f"| {mic} | {s['kind']} | {s['count']} |")
    if not state["streaks"]:
        lines.append("| - | - | - |")
    lines += ["", "Closed automatically on the next fully green scheduled run.",
              "", f"<!-- live-check-state: {json.dumps(state, sort_keys=True)} -->", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--previous-body", type=Path, default=None,
                    help="body of the open issue (missing or empty file: no open issue)")
    ap.add_argument("--body-out", required=True, type=Path)
    ap.add_argument("--decision-out", required=True, type=Path)
    ap.add_argument("--run-url", default="")
    args = ap.parse_args(argv)
    data = json.loads(args.results.read_text(encoding="utf-8"))
    results = data["results"]
    prev_body = args.previous_body.read_text(encoding="utf-8") if args.previous_body and args.previous_body.exists() else ""
    issue_open = bool(prev_body.strip())
    state = next_state(results, parse_state(prev_body))
    decision = decide(results, state, issue_open)
    args.body_out.write_text(render_body(results, state, decision, args.run_url, data.get("run_at", "")),
                             encoding="utf-8")
    args.decision_out.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
