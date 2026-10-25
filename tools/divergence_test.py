#!/usr/bin/env python3
"""Compare registry trading days against two reference libraries.

For each exchange and year, this tool builds three sets of trading days:

  registry  -- calendar.json: a day is a trading day unless it falls on one of
               the exchange's weekend_days or on a holiday / ad-hoc closure
               whose status is "closed". early_close and delayed_open days are
               still trading days.
  pmc       -- pandas_market_calendars: calendar.schedule(start, end)
  xc        -- exchange_calendars: calendar.sessions_in_range(start, end)

and reports where the three sources agree and disagree. A reference library
that does not know an exchange (or cannot cover the requested range) is
recorded as "No reference data" instead of crashing the run.

Reference libraries are dev-only dependencies (requirements-dev.txt).

Usage:
    python3 tools/divergence_test.py
    python3 tools/divergence_test.py --exchanges XNYS,XLON --year 2026
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CALENDAR = REPO_ROOT / "calendar.json"
DEFAULT_EXCHANGES = "XNYS,XLON,XTKS,XASX"
DEFAULT_YEAR = 2026
DEFAULT_OUTPUT = "/tmp/divergence.json"

SOURCES = ("registry", "pandas_market_calendars", "exchange_calendars")
NO_REFERENCE_DATA = "No reference data"

# Registry statuses that mean the exchange does not trade that day.
CLOSED_STATUSES = {"closed"}


def year_bounds(year):
    return dt.date(year, 1, 1), dt.date(year, 12, 31)


def iter_days(start, end):
    day = start
    while day <= end:
        yield day
        day += dt.timedelta(days=1)


def _to_date(value):
    """Normalise a pandas Timestamp / datetime / date to a plain date.

    Reference libraries differ on whether session labels are tz-naive or
    tz-aware; the label is already the session date, so tz info is dropped
    rather than converted (converting would shift dates by the UTC offset).
    """
    if hasattr(value, "tz_localize") and getattr(value, "tzinfo", None) is not None:
        value = value.tz_localize(None)
    if hasattr(value, "date"):
        return value.date()
    return value


# ---------------------------------------------------------------------------
# Source loaders. Each returns a set of datetime.date trading days, or raises.
# ---------------------------------------------------------------------------

def load_registry_entry(code, calendar_path=DEFAULT_CALENDAR):
    with open(calendar_path, encoding="utf-8") as fh:
        data = json.load(fh)
    for entry in data["exchanges"]:
        if entry["code"] == code:
            return entry
    raise KeyError(f"{code} not found in {calendar_path}")


def registry_closed_dates(entry):
    """Dates the registry marks as non-trading (status 'closed')."""
    closed = set()
    holidays = entry.get("holidays", {})
    records = list(holidays.get("explicit", [])) + list(holidays.get("generated", []))
    records += list(entry.get("ad_hoc_closures", []))
    for rec in records:
        if rec.get("status", "closed") in CLOSED_STATUSES:
            closed.add(dt.date.fromisoformat(rec["date"]))
    return closed


def registry_early_closes(entry):
    """Map of date -> early_close_time for registry half days."""
    out = {}
    holidays = entry.get("holidays", {})
    records = list(holidays.get("explicit", [])) + list(holidays.get("generated", []))
    records += list(entry.get("ad_hoc_closures", []))
    for rec in records:
        if rec.get("status") == "early_close":
            out[dt.date.fromisoformat(rec["date"])] = rec.get("early_close_time")
    return out


def registry_trading_days(entry, start, end):
    weekend = set(entry.get("weekend_days", [5, 6]))
    closed = registry_closed_dates(entry)
    return {
        d for d in iter_days(start, end)
        if d.weekday() not in weekend and d not in closed
    }


def pmc_trading_days(code, start, end):
    import pandas_market_calendars as pmc

    cal = pmc.get_calendar(code)
    schedule = cal.schedule(start_date=start.isoformat(), end_date=end.isoformat())
    return {_to_date(ts) for ts in schedule.index}


def xc_trading_days(code, start, end):
    import exchange_calendars as xc

    cal = xc.get_calendar(code)
    sessions = cal.sessions_in_range(start.isoformat(), end.isoformat())
    return {_to_date(ts) for ts in sessions}


# ---------------------------------------------------------------------------
# Comparison (pure function -- no I/O, easy to test)
# ---------------------------------------------------------------------------

def compare_sources(sources, start, end, early_closes=None):
    """Compare trading-day sets.

    sources: {name: set[date] | str}. A string value means the source has no
    data (it is recorded verbatim, e.g. "No reference data: <reason>") and is
    left out of the vote.
    """
    early_closes = early_closes or {}
    available = {k: v for k, v in sources.items() if not isinstance(v, str)}
    unavailable = {k: v for k, v in sources.items() if isinstance(v, str)}

    agree_trading, agree_closed_weekdays, disagreements = [], [], []
    for day in iter_days(start, end):
        votes = {name: (day in days) for name, days in available.items()}
        if len(set(votes.values())) <= 1 and votes:
            if next(iter(votes.values())):
                agree_trading.append(day.isoformat())
            elif day.weekday() < 5:
                agree_closed_weekdays.append(day.isoformat())
        elif votes:
            row = {
                "date": day.isoformat(),
                "weekday": day.strftime("%a"),
                "says": {n: ("open" if v else "closed") for n, v in votes.items()},
            }
            if day in early_closes:
                row["registry_early_close"] = early_closes[day]
            disagreements.append(row)

    return {
        "total_trading_days": {
            **{k: len(v) for k, v in available.items()},
            **unavailable,
        },
        "sources_compared": sorted(available),
        "sources_unavailable": unavailable,
        "all_agree_trading_days": agree_trading,
        "all_agree_closed_weekdays": agree_closed_weekdays,
        "disagreements": disagreements,
        "summary": {
            "agree_trading": len(agree_trading),
            "agree_closed_weekdays": len(agree_closed_weekdays),
            "disagreements": len(disagreements),
        },
    }


def _guarded(loader, *args):
    try:
        return loader(*args)
    except ImportError as exc:
        return f"{NO_REFERENCE_DATA}: library not installed ({exc})"
    except Exception as exc:  # unsupported exchange, range out of bounds, ...
        return f"{NO_REFERENCE_DATA}: {type(exc).__name__}: {exc}"


def run_exchange(code, year, calendar_path=DEFAULT_CALENDAR):
    start, end = year_bounds(year)
    entry = load_registry_entry(code, calendar_path)
    sources = {
        "registry": registry_trading_days(entry, start, end),
        "pandas_market_calendars": _guarded(pmc_trading_days, code, start, end),
        "exchange_calendars": _guarded(xc_trading_days, code, start, end),
    }
    return compare_sources(sources, start, end, registry_early_closes(entry))


def library_versions():
    versions = {}
    try:
        from importlib import metadata
        for dist in ("pandas_market_calendars", "exchange_calendars"):
            try:
                versions[dist] = metadata.version(dist)
            except metadata.PackageNotFoundError:
                versions[dist] = None
    except ImportError:  # pragma: no cover
        pass
    return versions


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--exchanges", default=DEFAULT_EXCHANGES,
                        help="Comma-separated MIC codes (default: %(default)s)")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR,
                        help="Year to compare (default: %(default)s)")
    parser.add_argument("--calendar", default=str(DEFAULT_CALENDAR),
                        help="Path to calendar.json (default: repo root)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help="Output JSON path (default: %(default)s)")
    args = parser.parse_args(argv)

    codes = [c.strip().upper() for c in args.exchanges.split(",") if c.strip()]
    report = {
        "year": args.year,
        "libraries": library_versions(),
        "exchanges": {},
    }
    for code in codes:
        try:
            report["exchanges"][code] = run_exchange(code, args.year, args.calendar)
        except KeyError as exc:
            report["exchanges"][code] = {"error": str(exc)}

    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for code, res in report["exchanges"].items():
        if "error" in res:
            print(f"{code}: ERROR {res['error']}")
            continue
        print(f"{code}: totals={res['total_trading_days']} "
              f"disagreements={res['summary']['disagreements']}")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
