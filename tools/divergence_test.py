#!/usr/bin/env python3
"""Compare registry trading days against two reference libraries.

For each exchange and year (or inclusive range of years), this tool builds
three sets of trading days:

Only regular working days are compared. A day that falls on the exchange's
weekend_days (Saturday/Sunday for most exchanges, Friday/Saturday for the
Gulf exchanges and a few others) is skipped for all three sources.

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
    python3 tools/divergence_test.py --mode sessions --exchanges XNYS,XLON,XTKS,XASX

Modes (--mode):
    trading_days  (default) which days each source treats as a trading day.
    sessions      for days every source trades: open time, close time, whether
                  the day is a half day (early close) and the intraday break
                  (Tokyo's lunch break), all as exchange-local HH:MM strings.
                  A break belongs to one session; it is not a second trading
                  day. Writes /tmp/divergence_sessions.json by default.
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
DEFAULT_SESSIONS_OUTPUT = "/tmp/divergence_sessions.json"
MODES = ("trading_days", "sessions")

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


def _xc_calendar(code, start, end):
    """exchange_calendars calendar covering [start, end].

    get_calendar(code) alone only covers the last ~20 years from today
    (it starts 2006-10-27 in 2026), which made every earlier year come back
    empty. The explicit bounds are whole calendar years. A calendar that
    cannot reach back that far (XTKS before 1997, XHKG before 1960) raises,
    which _guarded() records as "unavailable" for that year.
    """
    import exchange_calendars as xc

    return xc.get_calendar(code, start=dt.date(start.year, 1, 1).isoformat(),
                           end=dt.date(end.year, 12, 31).isoformat())


def xc_trading_days(code, start, end):
    cal = _xc_calendar(code, start, end)
    sessions = cal.sessions
    sessions = sessions[(sessions >= start.isoformat()) & (sessions <= end.isoformat())]
    return {_to_date(ts) for ts in sessions}


# ---------------------------------------------------------------------------
# Comparison (pure function -- no I/O, easy to test)
# ---------------------------------------------------------------------------

def compare_sources(sources, start, end, early_closes=None, weekend=None):
    """Compare trading-day sets.

    sources: {name: set[date] | str}. A string value means the source has no
    data (it is recorded verbatim, e.g. "No reference data: <reason>") and is
    left out of the vote.

    weekend: weekday numbers (Monday=0) that are the exchange's weekend. Those
    days are skipped for every source: the reference libraries model one-off
    weekend sessions (Budget Day, Muhurat, Russian make-up Saturdays) that the
    registry does not, and which libraries and versions do not agree on. Only
    regular working days are compared. Defaults to Saturday and Sunday.
    """
    early_closes = early_closes or {}
    weekend = {5, 6} if weekend is None else set(weekend)
    available = {k: v for k, v in sources.items() if not isinstance(v, str)}
    unavailable = {k: v for k, v in sources.items() if isinstance(v, str)}

    agree_trading, agree_closed_weekdays, disagreements = [], [], []
    for day in iter_days(start, end):
        if day.weekday() in weekend:
            continue
        votes = {name: (day in days) for name, days in available.items()}
        if len(set(votes.values())) <= 1 and votes:
            if next(iter(votes.values())):
                agree_trading.append(day.isoformat())
            else:
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


# ---------------------------------------------------------------------------
# Session times. Every loader returns {date: day} where day is
#   {"open": "HH:MM", "close": "HH:MM", "break": "HH:MM-HH:MM" | None,
#    "half_day": bool}
# with times in the exchange's local timezone. Reference libraries publish UTC
# timestamps; they are converted with the exchange's IANA zone (zoneinfo), so
# DST changes are handled per date, never with a fixed offset.
# ---------------------------------------------------------------------------

SESSION_METRICS = ("open", "close", "half_day", "break")
METRIC_TYPE = {"open": "open_time", "close": "close_time",
               "half_day": "half_day", "break": "break"}
SOURCE_KEYS = {"registry": "registry", "pandas_market_calendars": "pmc",
               "exchange_calendars": "xc"}


def _local_hhmm(value, tz):
    """UTC (or tz-aware) timestamp -> exchange-local 'HH:MM'; NaT/None -> None."""
    import pandas as pd

    if value is None or pd.isna(value):
        return None
    ts = pd.Timestamp(value)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts
    return ts.tz_convert(tz).strftime("%H:%M")


def _break_text(start, end):
    return f"{start}-{end}" if start and end else None


def _flag_half_days(days):
    """Mark days that close earlier than the source's usual close that year.

    The reference libraries have no common half-day flag (PMC's
    early_closes() and EC's special closes are separate mechanisms), so a
    half day is derived from the data: the close is earlier than the most
    common close in the same calendar year. The registry does not need this;
    it flags early_close explicitly.
    """
    by_year = {}
    for day, rec in days.items():
        by_year.setdefault(day.year, []).append(rec["close"])
    usual = {y: max(set(c), key=c.count) for y, c in by_year.items()}
    for day, rec in days.items():
        rec["half_day"] = rec["close"] < usual[day.year]
    return days


def registry_regular_session(entry):
    """(open, close, break) the registry uses on a normal day."""
    sessions = entry.get("sessions", [])
    regular = (next((s for s in sessions if s.get("type") == "regular"), None)
               or entry.get("regular_hours") or {})
    lunch = next((s for s in sessions if s.get("type") == "lunch_break"), None)
    brk = _break_text(lunch["open"], lunch["close"]) if lunch else None
    return regular.get("open"), regular.get("close"), brk


def registry_sessions(entry, start, end):
    """Registry session times for every trading day in [start, end].

    A day uses the regular session, with the open replaced by delayed_open_time
    and the close by early_close_time where the registry says so.
    """
    open_, close, brk = registry_regular_session(entry)
    holidays = entry.get("holidays", {})
    records = list(holidays.get("explicit", [])) + list(holidays.get("generated", []))
    records += list(entry.get("ad_hoc_closures", []))
    special = {dt.date.fromisoformat(r["date"]): r for r in records
               if r.get("status") in ("early_close", "delayed_open")}
    out = {}
    for day in sorted(registry_trading_days(entry, start, end)):
        rec = special.get(day, {})
        early = rec.get("status") == "early_close"
        day_close = (rec.get("early_close_time") or close) if early else close
        out[day] = {
            "open": rec.get("delayed_open_time") or open_,
            "close": day_close,
            # a half day that closes before the break would end has no break
            "break": None if brk and day_close <= brk.split("-")[1] else brk,
            "half_day": early,
        }
    return out


def pmc_sessions(code, start, end, tz):
    import pandas_market_calendars as pmc

    cal = pmc.get_calendar(code)
    sched = cal.schedule(start_date=start.isoformat(), end_date=end.isoformat())
    has_break = {"break_start", "break_end"} <= set(sched.columns)
    out = {}
    for ts, row in sched.iterrows():
        brk = (_break_text(_local_hhmm(row["break_start"], tz),
                           _local_hhmm(row["break_end"], tz)) if has_break else None)
        out[_to_date(ts)] = {"open": _local_hhmm(row["market_open"], tz),
                             "close": _local_hhmm(row["market_close"], tz),
                             "break": brk}
    return _flag_half_days(out)


def xc_sessions(code, start, end, tz):
    cal = _xc_calendar(code, start, end)
    sched = cal.schedule.loc[start.isoformat():end.isoformat()]
    has_break = {"break_start", "break_end"} <= set(sched.columns)
    out = {}
    for ts, row in sched.iterrows():
        brk = (_break_text(_local_hhmm(row["break_start"], tz),
                           _local_hhmm(row["break_end"], tz)) if has_break else None)
        out[_to_date(ts)] = {"open": _local_hhmm(row["open"], tz),
                             "close": _local_hhmm(row["close"], tz),
                             "break": brk}
    return _flag_half_days(out)


def compare_sessions(sources, start, end, weekend=None):
    """Compare session times between sources.

    sources: {name: {date: day} | str}; a string means the source has no data
    and is left out of the vote, as in compare_sources(). Trading-day
    membership is compared first (same rules as compare_sources, weekend days
    skipped). Open, close, half_day and break are then compared only on days
    every available source trades, so a day missing from one source is
    reported once, as a trading-day disagreement, not again as a time mismatch.

    Returns {"trading_days": <compare_sources result>, "metrics": {metric:
    {"compared": n, "agree": n}}, "disagreements": [{"date", "type",
    "registry", "pmc", "xc"}, ...]}. A half-day mismatch normally comes with a
    close-time mismatch on the same date; the metric counters are independent.
    """
    available = {k: v for k, v in sources.items() if not isinstance(v, str)}
    day_sets = {k: (set(v) if k in available else v) for k, v in sources.items()}
    trading = compare_sources(day_sets, start, end, weekend=weekend)
    metrics = {m: {"compared": 0, "agree": 0} for m in SESSION_METRICS}
    rows = []
    for day_text in trading["all_agree_trading_days"]:
        day = dt.date.fromisoformat(day_text)
        recs = {name: days[day] for name, days in available.items()}
        for metric in SESSION_METRICS:
            values = {name: rec.get(metric) for name, rec in recs.items()}
            metrics[metric]["compared"] += 1
            if len(set(values.values())) <= 1:
                metrics[metric]["agree"] += 1
                continue
            row = {"date": day_text, "type": METRIC_TYPE[metric]}
            for name, key in SOURCE_KEYS.items():
                row[key] = values.get(name)
            rows.append(row)
    return {"trading_days": trading, "metrics": metrics, "disagreements": rows}


def run_exchange_sessions(code, year, calendar_path=DEFAULT_CALENDAR):
    start, end = year_bounds(year)
    entry = load_registry_entry(code, calendar_path)
    tz = entry["timezone"]
    if registry_covers(entry, start, end):
        registry = registry_sessions(entry, start, end)
    else:
        first, last = entry.get("generation_range", ["?", "?"])
        registry = (f"{NO_REGISTRY_DATA}: {year} is outside the registry's "
                    f"generation_range ({first} to {last})")
    sources = {
        "registry": registry,
        "pandas_market_calendars": _guarded(pmc_sessions, code, start, end, tz),
        "exchange_calendars": _guarded(xc_sessions, code, start, end, tz),
    }
    result = compare_sessions(sources, start, end,
                              weekend=entry.get("weekend_days", [5, 6]))
    result["timezone"] = tz
    result["pmc_mirrors_exchange_calendars"] = pmc_is_mirror(code)
    return result


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
    result = compare_sources(sources, start, end, registry_early_closes(entry),
                             weekend=entry.get("weekend_days", [5, 6]))
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
    parser.add_argument("--mode", choices=MODES, default="trading_days",
                        help="trading_days: compare which days are trading days; "
                             "sessions: compare open/close/half-day/break times "
                             "(default: %(default)s)")
    parser.add_argument("--output", default=None,
                        help=f"Output JSON path (default: {DEFAULT_OUTPUT}, or "
                             f"{DEFAULT_SESSIONS_OUTPUT} with --mode sessions)")
    args = parser.parse_args(argv)

    try:
        years = parse_years(args.year)
    except ValueError as exc:
        parser.error(str(exc))

    if args.exchanges.strip().lower() == "all":
        codes = registry_codes(args.calendar)
    else:
        codes = [c.strip().upper() for c in args.exchanges.split(",") if c.strip()]

    sessions = args.mode == "sessions"
    output = args.output or (DEFAULT_SESSIONS_OUTPUT if sessions else DEFAULT_OUTPUT)
    runner = run_exchange_sessions if sessions else run_exchange

    report = {
        "mode": args.mode,
        "years": years,
        "libraries": library_versions(),
        "exchanges": {},
    }
    for code in codes:
        try:
            report["exchanges"][code] = {
                "years": {str(y): runner(code, y, args.calendar) for y in years}
            }
        except KeyError as exc:
            report["exchanges"][code] = {"error": str(exc)}

    Path(output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for code, res in report["exchanges"].items():
        if "error" in res:
            print(f"{code}: ERROR {res['error']}")
            continue
        if sessions:
            diffs = sum(r["trading_days"]["summary"]["disagreements"]
                        + len(r["disagreements"]) for r in res["years"].values())
            missing = sorted({k for r in res["years"].values()
                              for k in r["trading_days"]["sources_unavailable"]})
        else:
            diffs = sum(r["summary"]["disagreements"] for r in res["years"].values())
            missing = sorted({k for r in res["years"].values()
                              for k in r["sources_unavailable"]})
        print(f"{code}: disagreements={diffs}"
              + (f" unavailable={','.join(missing)}" if missing else ""))
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
