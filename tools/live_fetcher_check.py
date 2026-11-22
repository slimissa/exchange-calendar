#!/usr/bin/env python3
"""
live_fetcher_check.py — Run every registered fetcher against its LIVE source
and report one status per fetcher.

This is a read-only health check: it never writes to exchanges/, never opens
a PR, and never modifies calendar.json. Its only job is to answer "is each
fetcher's live parser still working today", since a page's HTML structure
can drift at any time regardless of how well-tested the fetcher's fixtures
are.

Statuses (4b3):
    PASS       the fetcher returned holidays
    TRANSIENT  the source had a bad day, after ATTEMPTS tries within this
               run (3 by default, delays RETRY_DELAY x 1, x 2): FetchError
               or RateLimitError (the fetcher's request failed: timeout,
               connection error, HTTP error incl. 5xx), a requests timeout,
               connection error or HTTP 5xx raised directly, or "no
               holidays" on a page that came back empty or in maintenance
    FAIL       deterministic, reported at once without retrying:
               ValidationError, conflicting rows, SourceMissingError (404,
               robots.txt), any other ParseError (or "no holidays") on a page
               that returned content, HTTP 4xx, any unexpected exception
    KNOWN      a failure matching an active entry of
               tools/known_source_faults.json (a defect in the exchange's own
               page): shown, not escalated, not failing the job, until the
               entry expires (then FAIL); a listed MIC that passes gets a
               "fault cleared, remove the entry" warning (4b4)
    SKIP       no fetcher registered

ParseError, ValidationError and SourceMissingError subclass FetchError, so
they are tested first.

Exit code is 1 if any fetcher FAILs, 0 otherwise. A TRANSIENT does not fail
this tool; tools/live_check_escalate.py fails the scheduled workflow when a
fetcher is TRANSIENT in two consecutive scheduled runs (or FAILs once).

Usage:
    python3 tools/live_fetcher_check.py [--mic MIC ...] [--only A,B] [--exclude A,B]
        [--attempts 3] [--retry-delay 30] [--json-out results.json]
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from update_from_exchange import (
    ExchangeFetcherRegistry, FetchError, ParseError, SourceMissingError, ValidationError,
)
import known_source_faults

ATTEMPTS = 3
RETRY_DELAY = 30.0  # seconds; attempt n waits RETRY_DELAY * n before it
# Text that marks a maintenance or holding page (several languages).
MAINTENANCE_RE = re.compile(
    r"maintenance|mantenimiento|manutenzione|maintenance en cours|bak[ıi]m|przerwa techniczna"
    r"|temporarily unavailable|service unavailable|under construction|be right back",
    re.IGNORECASE)
MIN_CONTENT_CHARS = 400  # visible text shorter than this counts as an empty page
# No page was recorded (the fetcher does not read through _make_request /
# _make_binary_request): whether the page was empty is unknown, so "no
# holidays" stays a FAIL rather than being excused as transient.
UNKNOWN = object()


def _visible_text(page) -> str:
    if page is None:
        return ""
    if isinstance(page, (bytes, bytearray)):
        return "x" * len(page) if page.startswith(b"%PDF") else page.decode("utf-8", "replace")
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def page_is_empty_or_maintenance(page) -> bool:
    """True when the page the fetcher read is missing, nearly empty, or a
    maintenance/holding page."""
    if page is UNKNOWN:
        return False
    text = _visible_text(page)
    return len(text) < MIN_CONTENT_CHARS or bool(MAINTENANCE_RE.search(text[:5000]))


def classify(exc, page) -> str:
    """'TRANSIENT' or 'FAIL' for an exception raised by fetch(); page is the
    last content _make_request/_make_binary_request returned (None when the
    request failed; UNKNOWN when nothing was recorded)."""
    try:
        import requests
        timeouts = (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
        http_error = requests.exceptions.HTTPError
    except ImportError:  # pragma: no cover
        timeouts, http_error = (), ()
    if isinstance(exc, (ValidationError, SourceMissingError)):
        return "FAIL"
    if isinstance(exc, ParseError):
        msg = str(exc)
        if "conflicting rows" in msg:
            return "FAIL"
        if "no holidays" in msg.lower() and page_is_empty_or_maintenance(page):
            return "TRANSIENT"
        return "FAIL"
    if isinstance(exc, FetchError):  # incl. RateLimitError: the request itself failed
        return "TRANSIENT"
    if timeouts and isinstance(exc, timeouts):
        return "TRANSIENT"
    if http_error and isinstance(exc, http_error):
        code = getattr(getattr(exc, "response", None), "status_code", None)
        return "TRANSIENT" if code is not None and code >= 500 else "FAIL"
    return "FAIL"


def _record_pages(fetcher, store: list) -> None:
    """Wrap the fetcher's request methods so the last page read is kept."""
    for name in ("_make_request", "_make_binary_request"):
        orig = getattr(fetcher, name, None)
        if orig is None or getattr(orig, "_recording", False):
            continue

        def wrapper(*a, _orig=orig, **k):
            page = _orig(*a, **k)
            store.append(page)
            return page
        wrapper._recording = True
        setattr(fetcher, name, wrapper)


def _attempt(fetcher, pages: list) -> dict:
    start = time.monotonic()
    pages.clear()
    try:
        data = fetcher.fetch()
        elapsed = time.monotonic() - start
        if data is None or not data.holidays:
            page = pages[-1] if pages else UNKNOWN
            status = "TRANSIENT" if page_is_empty_or_maintenance(page) else "FAIL"
            return {"status": status, "reason": "fetch() returned no holidays", "elapsed": elapsed}
        return {"status": "PASS", "holiday_count": len(data.holidays),
                "sample_date": data.holidays[0].date, "elapsed": elapsed}
    except Exception as e:  # noqa: BLE001 -- a health check: every exception is a result
        page = pages[-1] if pages else UNKNOWN
        kind = classify(e, page)
        prefix = "" if isinstance(e, FetchError) else "Unexpected " if kind == "FAIL" else ""
        return {"status": kind, "reason": f"{prefix}{type(e).__name__}: {e}",
                "elapsed": time.monotonic() - start}


def check_fetcher(mic: str, fetcher, attempts: int = ATTEMPTS, retry_delay: float = RETRY_DELAY,
                  sleep=time.sleep) -> dict:
    """Run one fetcher live and return a result dict. Never raises.
    TRANSIENT outcomes are retried up to `attempts` times in all, waiting
    retry_delay x n before attempt n+1; PASS and FAIL end the loop at once."""
    result = {"mic": mic, "name": fetcher.name, "source_url": fetcher.source_url}
    pages: list = []
    _record_pages(fetcher, pages)
    for n in range(1, max(1, attempts) + 1):
        outcome = _attempt(fetcher, pages)
        if outcome["status"] != "TRANSIENT" or n == attempts:
            break
        sleep(retry_delay * n)
    result.update(outcome, attempts=n)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mic", action="append", help="Only check this MIC (repeatable)")
    parser.add_argument("--only", default="", help="Comma-separated MICs to include")
    parser.add_argument("--exclude", default="", help="Comma-separated MICs to skip")
    parser.add_argument("--attempts", type=int, default=ATTEMPTS,
                        help="tries per fetcher for transient failures (default 3)")
    parser.add_argument("--retry-delay", type=float, default=RETRY_DELAY,
                        help="seconds; attempt n+1 waits this x n (default 30)")
    parser.add_argument("--json-out", default="", help="write the results as JSON to this path")
    parser.add_argument("--known-faults", default=str(known_source_faults.PATH),
                        help="known-source-fault entries (default tools/known_source_faults.json)")
    parser.add_argument("--today", default="", help="ISO date for expiry checks (default: today, UTC)")
    args = parser.parse_args(argv)
    faults = known_source_faults.load(Path(args.known_faults))
    bad = known_source_faults.problems(faults)
    if bad:
        print("Invalid known-source-fault entries:\n  " + "\n  ".join(bad))
        return 2
    today = (datetime.fromisoformat(args.today).date() if args.today
             else datetime.now(timezone.utc).date())

    registry = ExchangeFetcherRegistry()
    mics = args.mic or sorted(registry.list_available())

    if args.only:
        wanted = {m.strip() for m in args.only.split(",") if m.strip()}
        mics = [m for m in mics if m in wanted]
    if args.exclude:
        unwanted = {m.strip() for m in args.exclude.split(",") if m.strip()}
        mics = [m for m in mics if m not in unwanted]
    if not mics:
        print("No MICs selected after --only/--exclude filtering.")
        return 2

    print(f"Checking {len(mics)} fetcher(s) against LIVE sources...\n")
    results = []
    for mic in mics:
        fetcher = registry.get(mic)
        if fetcher is None:
            results.append({"mic": mic, "status": "SKIP", "reason": "no fetcher registered", "attempts": 0})
            continue
        print(f"  -> {mic} ({fetcher.name}) ... ", end="", flush=True)
        r = check_fetcher(mic, fetcher, attempts=args.attempts, retry_delay=args.retry_delay)
        r = known_source_faults.apply(r, faults, today)
        results.append(r)
        print(f"{r['status']} ({r['attempts']} attempt{'s' if r['attempts'] != 1 else ''})")

    print(summary_table(results))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps({
            "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "results": [{k: r.get(k) for k in ("mic", "status", "attempts", "reason",
                                                  "holiday_count", "sample_date", "known_fault", "warning")}
                        for r in results],
        }, indent=2) + "\n", encoding="utf-8")
    return 1 if any(r["status"] == "FAIL" for r in results) else 0


def summary_table(results) -> str:
    lines = ["", "=" * 78, f"{'MIC':<8}{'STATUS':<11}{'TRIES':<7}DETAIL", "=" * 78]
    for r in results:
        if r["status"] == "PASS":
            detail = f"{r.get('holiday_count', '?')} holidays, first={r.get('sample_date', '?')}"
            if r.get("warning"):
                detail += f" -- WARNING: {r['warning']}"
        elif r["status"] == "KNOWN":
            kf = r.get("known_fault") or {}
            detail = f"{r.get('reason', '')} [known source fault until {kf.get('expires')}: {kf.get('reason')}]"
        else:
            detail = r.get("reason", "")
        lines.append(f"{r['mic']:<8}{r['status']:<11}{r.get('attempts', 0):<7}{detail}")
    lines.append("=" * 78)
    count = {k: sum(1 for r in results if r["status"] == k) for k in ("PASS", "TRANSIENT", "FAIL", "KNOWN", "SKIP")}
    lines.append(f"\n{count['PASS']}/{len(results)} passed, {count['TRANSIENT']} transient, "
                 f"{count['FAIL']} failed, {count['KNOWN']} known source fault(s), {count['SKIP']} skipped")
    if count["TRANSIENT"]:
        lines.append("TRANSIENT: " + ", ".join(r["mic"] for r in results if r["status"] == "TRANSIENT")
                     + " -- source unreliable today; fails the scheduled workflow only if it repeats next run")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
