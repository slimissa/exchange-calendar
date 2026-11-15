#!/usr/bin/env python3
"""
live_fetcher_check.py — Run every registered fetcher against its LIVE source
and report pass/fail per fetcher.

This is a read-only health check: it never writes to exchanges/, never opens
a PR, and never modifies calendar.json. Its only job is to answer "is each
fetcher's live parser still working today", since a page's HTML structure
can drift at any time regardless of how well-tested the fetcher's fixtures
are.

Statuses:
    PASS   the fetcher returned holidays
    WARN   FetchError (or RateLimitError) after the fetcher's own retries: the
           source was unreliable today (network, WAF or error page, not a
           PDF). The job still passes; the warning is printed.
    FAIL   ParseError / ValidationError (the page changed and the parser
           needs a fix), no holidays, or an unexpected exception.
    SKIP   no fetcher registered

ParseError and ValidationError subclass FetchError, so they are tested first.

Exit code is 1 if any fetcher FAILs, 0 otherwise (WARN does not fail the job)
-- suitable for use as a CI gate that surfaces drift without silently
ignoring it.

Usage:
    python3 tools/live_fetcher_check.py [--mic MIC ...]
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from update_from_exchange import ExchangeFetcherRegistry, FetchError, ParseError, ValidationError


def check_fetcher(mic: str, fetcher) -> dict:
    """Run one fetcher live and return a result dict. Never raises."""
    start = time.monotonic()
    result = {"mic": mic, "name": fetcher.name, "source_url": fetcher.source_url}

    try:
        data = fetcher.fetch()
        elapsed = time.monotonic() - start
        if data is None or not data.holidays:
            result.update(status="FAIL", reason="fetch() returned no holidays", elapsed=elapsed)
        else:
            result.update(
                status="PASS",
                holiday_count=len(data.holidays),
                sample_date=data.holidays[0].date if data.holidays else None,
                elapsed=elapsed,
            )
    except (ParseError, ValidationError) as e:
        # Subclasses of FetchError: the source answered but the content is not
        # what the parser expects. Must be caught before FetchError.
        result.update(status="FAIL", reason=f"{type(e).__name__}: {e}", elapsed=time.monotonic() - start)
    except FetchError as e:
        # The fetcher already retried; the source is flaky today.
        result.update(status="WARN", reason=f"{type(e).__name__}: {e}", elapsed=time.monotonic() - start)
    except Exception as e:  # noqa: BLE001 -- deliberately broad: this is a health check,
        # an unexpected exception is itself a signal the live page changed shape
        result.update(status="FAIL", reason=f"Unexpected {type(e).__name__}: {e}", elapsed=time.monotonic() - start)

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mic", action="append", help="Only check this MIC (repeatable)")
    parser.add_argument("--only", default="", help="Comma-separated MICs to include")
    parser.add_argument("--exclude", default="", help="Comma-separated MICs to skip")
    args = parser.parse_args()

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
        sys.exit(2)

    print(f"Checking {len(mics)} fetcher(s) against LIVE sources...\n")
    results = []
    for mic in mics:
        fetcher = registry.get(mic)
        if fetcher is None:
            results.append({"mic": mic, "status": "SKIP", "reason": "no fetcher registered"})
            continue
        print(f"  -> {mic} ({fetcher.name}) ... ", end="", flush=True)
        r = check_fetcher(mic, fetcher)
        results.append(r)
        print(r["status"])

    print("\n" + "=" * 70)
    print(f"{'MIC':<8}{'STATUS':<8}{'DETAIL'}")
    print("=" * 70)
    failures = warnings = 0
    for r in results:
        if r["status"] == "PASS":
            detail = f"{r.get('holiday_count', '?')} holidays, first={r.get('sample_date', '?')}"
        elif r["status"] == "SKIP":
            detail = r.get("reason", "")
        elif r["status"] == "WARN":
            detail = r.get("reason", "source unreliable")
            warnings += 1
        else:
            detail = r.get("reason", "unknown failure")
            failures += 1
        print(f"{r['mic']:<8}{r['status']:<8}{detail}")
    print("=" * 70)
    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"\n{passed}/{len(results)} fetchers passed, {warnings} warned, {failures} failed")
    if warnings:
        print("WARN: " + ", ".join(r["mic"] for r in results if r["status"] == "WARN")
              + " -- source unreliable today; does not fail the job")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
