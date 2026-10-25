#!/usr/bin/env python3
"""Compare registry trading days against two reference libraries.

For each exchange and year (or inclusive range of years), this tool builds
three sets of trading days:

  registry  -- calendar.json: a day is a trading day unless it falls on one of
               the exchange's weekend_days or on a holiday / ad-hoc closure
               whose status is "closed". early_close and delayed_open days are
               still trading days.
  pmc       -- pandas_market_calendars: calendar.schedule(start, end)
  xc        -- exchange_calendars: calendar.sessions_in_range(start, end)

and reports where the three sources agree and disagree. A reference library
that does not know an exchange (or cannot cover the requested range) is
recorded as "No reference data" instead of crashing the run. The registry
only has data inside each exchange's generation_range; a year outside it is
recorded as "No registry data" and the two libraries are compared alone.

pandas_market_calendars serves most exchanges from exchange_calendars (its
"mirror" calendars). For those the two libraries are one source counted twice;
the result records this as pmc_mirrors_exchange_calendars.

Reference libraries are dev-only dependencies (requirements-dev.txt).

Usage:
    python3 tools/divergence_test.py
    python3 tools/divergence_test.py --exchanges XNYS,XLON --year 2026
    python3 tools/divergence_test.py --exchanges all --year 2024-2026
"""

import argparse
import datetime as dt
import functools
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CALENDAR = REPO_ROOT / "calendar.json"
DEFAULT_EXCHANGES = "XNYS,XLON,XTKS,XASX"
DEFAULT_YEARS = "2024-2026"
DEFAULT_OUTPUT = "/tmp/divergence.json"

SOURCES = ("registry", "pandas_market_calendars", "exchange_calendars")
NO_REFERENCE_DATA = "No reference data"
NO_REGISTRY_DATA = "No registry data"

# Registry statuses that mean the exchange does not trade that day.
CLOSED_STATUSES = {"closed"}


def year_bounds(year):
    return dt.date(year, 1, 1), dt.date(year, 12, 31)


def parse_years(text):
    """Parse "2026" or an inclusive range "2024-2026" into a list of years."""
    text = str(text).strip()
    try:
        if "-" in text:
            first, last = (int(part) for part in text.split("-", 1))
        else:
            first = last = int(text)
    except ValueError:
        raise ValueError(f"invalid year or range: {text!r} (use 2026 or 2024-2026)")
    if first > last:
        raise ValueError(f"invalid year range: {text!r} (start is after end)")
    return list(range(first, last + 1))


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

@functools.lru_cache(maxsize=4)
def _load_calendar(calendar_path):
    with open(calendar_path, encoding="utf-8") as fh:
        return json.load(fh)


def registry_codes(calendar_path=DEFAULT_CALENDAR):
    return sorted(e["code"] for e in _load_calendar(str(calendar_path))["exchanges"])


def load_registry_entry(code, calendar_path=DEFAULT_CALENDAR):
    data = _load_calendar(str(calendar_path))
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


def registry_covers(entry, start, end):
    """True when [start, end] lies inside the entry's generation_range."""
    first, last = entry.get("generation_range", [None, None])
    if not first or not last:
        return False
    return dt.date.fromisoformat(first) <= start and end <= dt.date.fromisoformat(last)


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


def pmc_is_mirror(code):
    """True when pandas_market_calendars serves this exchange from
    exchange_calendars (its "mirror" calendars), False when it has its own
    implementation, None when it does not know the exchange.

    A mirrored exchange makes PMC and EC one source counted twice, so their
    agreement says nothing about whether either is right.
    """
    try:
        import pandas_market_calendars as pmc

        cal = pmc.get_calendar(code)
    except Exception:
        return None
    return type(cal).__module__.rsplit(".", 1)[-1] == "mirror"


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
    if registry_covers(entry, start, end):
        registry = registry_trading_days(entry, start, end)
    else:
        first, last = entry.get("generation_range", ["?", "?"])
        registry = (f"{NO_REGISTRY_DATA}: {year} is outside the registry's "
                    f"generation_range ({first} to {last})")
    sources = {
        "registry": registry,
        "pandas_market_calendars": _guarded(pmc_trading_days, code, start, end),
        "exchange_calendars": _guarded(xc_trading_days, code, start, end),
    }
    result = compare_sources(sources, start, end, registry_early_closes(entry))
    result["pmc_mirrors_exchange_calendars"] = pmc_is_mirror(code)
    return result


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
                        help="Comma-separated MIC codes, or 'all' for every "
                             "registry exchange (default: %(default)s)")
    parser.add_argument("--year", default=DEFAULT_YEARS,
                        help="Year or inclusive range, e.g. 2026 or 2024-2026 "
                             "(default: %(default)s)")
    parser.add_argument("--calendar", default=str(DEFAULT_CALENDAR),
                        help="Path to calendar.json (default: repo root)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help="Output JSON path (default: %(default)s)")
    args = parser.parse_args(argv)

    try:
        years = parse_years(args.year)
    except ValueError as exc:
        parser.error(str(exc))

    if args.exchanges.strip().lower() == "all":
        codes = registry_codes(args.calendar)
    else:
        codes = [c.strip().upper() for c in args.exchanges.split(",") if c.strip()]

    report = {
        "years": years,
        "libraries": library_versions(),
        "exchanges": {},
    }
    for code in codes:
        try:
            report["exchanges"][code] = {
                "years": {str(y): run_exchange(code, y, args.calendar) for y in years}
            }
        except KeyError as exc:
            report["exchanges"][code] = {"error": str(exc)}

    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for code, res in report["exchanges"].items():
        if "error" in res:
            print(f"{code}: ERROR {res['error']}")
            continue
        diffs = sum(r["summary"]["disagreements"] for r in res["years"].values())
        missing = sorted({k for r in res["years"].values()
                          for k in r["sources_unavailable"]})
        print(f"{code}: disagreements={diffs}"
              + (f" unavailable={','.join(missing)}" if missing else ""))
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
