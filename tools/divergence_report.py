#!/usr/bin/env python3
"""Render the JSON written by tools/divergence_test.py as docs/DIVERGENCE.md.

The output is deterministic (no timestamps, sorted exchanges and dates), so
re-running the two tools on an unchanged tree reproduces the file byte for
byte.

Hand-checked verdicts are read from docs/divergence_triage.json (when it
exists) and shown next to the dates they cover, so a verified library error is
not mistaken for an open registry bug.

When a sessions file from `divergence_test.py --mode sessions` exists, a
"Session Times" section (open, close, half-day and break agreement per
exchange) is added to the report. Without it the section is left out.

Usage:
    python3 tools/divergence_test.py --exchanges all --year 2024-2026
    python3 tools/divergence_test.py --mode sessions --exchanges XNYS,XLON,XTKS,XASX
    python3 tools/divergence_report.py
    python3 tools/divergence_report.py --input /tmp/divergence.json \\
        --triage docs/divergence_triage.json --output docs/DIVERGENCE.md

Exit codes:
    0  report written
    2  input missing or not a divergence report
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = "/tmp/divergence.json"
DEFAULT_SESSIONS = "/tmp/divergence_sessions.json"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "DIVERGENCE.md"
DEFAULT_TRIAGE = REPO_ROOT / "docs" / "divergence_triage.json"

VERDICT_LABEL = {
    "registry_error": "Registry error",
    "library_error": "Library error",
    "convention_difference": "Convention difference",
}
VERDICT_TAG = {
    "registry_error": "registry error",
    "library_error": "library error",
    "convention_difference": "convention difference",
}

REGISTRY = "registry"
PMC = "pandas_market_calendars"
EC = "exchange_calendars"
SOURCE_ORDER = (REGISTRY, PMC, EC)
LABEL = {REGISTRY: "registry", PMC: "PMC", EC: "EC"}
NO_REFERENCE_DATA = "No reference data"


def _years(exchange):
    return exchange["years"]


def _scope_years(exchange):
    """Years compared three ways: those where the registry has data.

    If the registry has no data in any requested year, every year is in scope
    so the exchange still gets a row.
    """
    years = _years(exchange)
    with_registry = [y for y, r in years.items() if REGISTRY not in r["sources_unavailable"]]
    return sorted(with_registry or years)


def _source_total(exchange, years, source):
    """Sum of trading days for a source over the years it has data.

    Returns (total, partial). total is None when the source has no data in
    any of the years; partial is True when it is missing in some of them.
    """
    values = []
    for y in years:
        v = _years(exchange)[y]["total_trading_days"].get(source)
        if isinstance(v, int):
            values.append(v)
    if not values:
        return None, False
    return sum(values), len(values) < len(years)


def summarise(code, exchange):
    years = _scope_years(exchange)
    row = {"code": code, "years": years, "totals": {}, "partial": {}}
    for source in SOURCE_ORDER:
        total, partial = _source_total(exchange, years, source)
        row["totals"][source] = total
        row["partial"][source] = partial
    agree = sum(_years(exchange)[y]["summary"]["agree_trading"] for y in years)
    diffs = sum(_years(exchange)[y]["summary"]["disagreements"] for y in years)
    refs = [s for s in (PMC, EC) if row["totals"][s] is not None]
    row["agree"] = agree
    row["disagreements"] = diffs
    row["references"] = refs
    row["rate"] = (agree / (agree + diffs)) if refs and (agree + diffs) else None
    return row


def _cell(row, source):
    total = row["totals"][source]
    if total is None:
        return "n/a" if source == REGISTRY else NO_REFERENCE_DATA
    return f"{total}*" if row["partial"][source] else str(total)


def _rate(rate):
    return "n/a" if rate is None else f"{rate * 100:.1f}%"


def _group_disagreements(exchange, years):
    """{pattern: [(date, weekday)]} over the given years.

    pattern is the ordered tuple of (source label, open/closed) pairs, so
    dates that split the sources the same way are listed together.
    """
    groups = {}
    for year in sorted(years):
        for item in _years(exchange)[year]["disagreements"]:
            pattern = tuple(
                (LABEL[s], item["says"][s]) for s in SOURCE_ORDER if s in item["says"]
            )
            groups.setdefault(pattern, []).append((item["date"], item["weekday"][:2]))
    return groups


def _pattern_text(pattern):
    return ", ".join(f"{name} {state}" for name, state in pattern)


def _triage_index(triage):
    """{(exchange, date): verdict} for every date a triage entry covers."""
    index = {}
    for entry in (triage or {}).get("entries", []):
        for day in entry["dates"]:
            index[(entry["exchange"], day)] = entry["verdict"]
    return index


SESSION_COLUMNS = (("open", "Open"), ("close", "Close"), ("half_day", "Half-days"),
                   ("break", "Break"))
TYPE_LABEL = {"open_time": "open", "close_time": "close", "half_day": "half-day",
              "break": "break"}


def _pct(agree, compared):
    return "n/a" if not compared else f"{agree / compared * 100:.1f}%"


def summarise_sessions(code, exchange):
    """One table row for the Session Times section.

    Counted over the years where the registry has data and at least one
    reference library does; other years have nothing to compare the registry
    against and are left out.
    """
    years = []
    for y, r in sorted(exchange["years"].items()):
        compared = set(r["trading_days"]["sources_compared"])
        if REGISTRY in compared and compared - {REGISTRY}:
            years.append(y)
    row = {"code": code, "years": years, "notes": []}
    days = [exchange["years"][y]["trading_days"]["summary"] for y in years]
    row["trading_days"] = (sum(d["agree_trading"] for d in days),
                           sum(d["agree_trading"] + d["disagreements"] for d in days))
    for metric, _ in SESSION_COLUMNS:
        row[metric] = (
            sum(exchange["years"][y]["metrics"][metric]["agree"] for y in years),
            sum(exchange["years"][y]["metrics"][metric]["compared"] for y in years))
    for y in years:
        r = exchange["years"][y]
        for item in r["trading_days"]["disagreements"]:
            row["notes"].append(f"{item['date']} trading day")
        for item in r["disagreements"]:
            vals = ", ".join(f"{LABEL_BY_KEY[k]} {item[k]}" for k in ("registry", "pmc", "xc"))
            row["notes"].append(f"{item['date']} {TYPE_LABEL[item['type']]} ({vals})")
    return row


LABEL_BY_KEY = {"registry": "registry", "pmc": "PMC", "xc": "EC"}


def render_sessions(sessions):
    """Markdown lines for the Session Times section."""
    rows = [summarise_sessions(c, e) for c, e in sorted(sessions["exchanges"].items())
            if "years" in e]
    errors = {c: e["error"] for c, e in sorted(sessions["exchanges"].items()) if "error" in e}
    years = sessions["years"]
    out = []
    w = out.append
    w("## Session Times")
    w("")
    w("Open time, close time, half-day status and intraday break, compared "
      "between the registry and the two reference libraries. Generated from "
      "`python3 tools/divergence_test.py --mode sessions --exchanges "
      + ",".join(sorted(sessions["exchanges"])) + f" --year {years[0]}-{years[-1]}`.")
    w("")
    w("- Times are exchange-local `HH:MM`. The libraries publish UTC "
      "timestamps; each is converted with the exchange's IANA timezone, per "
      "date, so DST changes are handled.")
    w("- Open, close, half-day and break are compared only on days all sources "
      "trade. A day one source lacks is a trading-day disagreement, counted in "
      "the first column and not again in the others.")
    w("- Registry: the regular session, with `early_close_time` and "
      "`delayed_open_time` applied on those dates; a half day is a date with "
      "status `early_close`. Libraries: a half day is a close earlier than that "
      "library's usual close in the same calendar year.")
    w("- A break (Tokyo's lunch break) is part of one session. It is compared "
      "as a single `HH:MM-HH:MM` value and is `none` for exchanges without one.")
    w("- A half-day mismatch normally appears with a close mismatch on the same "
      "date, so the two columns are not independent.")
    w("- Years: the registry only has data inside each exchange's "
      "`generation_range`, so only years where the registry and a library both "
      "have data are counted. PMC and EC are not independent for exchanges PMC "
      "mirrors from EC, so agreement with both is agreement with one reference.")
    w("")
    w("| Exchange | Years | Trading days agree | Open agree | Close agree | "
      "Half-days agree | Break agree | Notes |")
    w("|---|---|---:|---:|---:|---:|---:|---|")
    for r in rows:
        yrs = ", ".join(r["years"]) if r["years"] else "none"
        cells = [_pct(*r["trading_days"])] + [_pct(*r[m]) for m, _ in SESSION_COLUMNS]
        note = "; ".join(r["notes"]) if r["notes"] else (
            "No disagreements" if r["years"] else "No registry data to compare")
        w(f"| {r['code']} | {yrs} | " + " | ".join(cells) + f" | {note} |")
    w("")
    flagged = [r for r in rows if r["notes"]]
    if flagged:
        w("Disagreements are not classified until checked by hand against the "
          "exchange's own publication; record each verdict in "
          "`docs/divergence_triage.json`.")
    else:
        w("No disagreements, so there is nothing to classify as a registry "
          "error, library error or convention difference.")
    w("")
    for code, message in errors.items():
        w(f"- {code}: {message}")
    if errors:
        w("")
    return out


def render(report, triage=None, sessions=None):
    triage_index = _triage_index(triage)
    exchanges = report["exchanges"]
    years = report["years"]
    libs = report.get("libraries", {})
    rows = [summarise(c, e) for c, e in sorted(exchanges.items()) if "years" in e]
    errors = {c: e["error"] for c, e in sorted(exchanges.items()) if "error" in e}

    out = []
    w = out.append

    w("# Divergence report")
    w("")
    w("Generated by `tools/divergence_report.py` from the output of "
      "`tools/divergence_test.py`. Do not edit by hand; regenerate with:")
    w("")
    w("```")
    w(f"python3 tools/divergence_test.py --exchanges all --year {years[0]}-{years[-1]}")
    if sessions is not None:
        w(f"python3 tools/divergence_test.py --mode sessions --exchanges "
          f"{','.join(sorted(sessions['exchanges']))} "
          f"--year {sessions['years'][0]}-{sessions['years'][-1]}")
    w("python3 tools/divergence_report.py")
    w("```")
    w("")
    w("This file is regenerated automatically every Monday at 08:00 UTC by the "
      "Divergence workflow (`.github/workflows/divergence.yml`), which opens a "
      "pull request when it changes. Manual edits will be overwritten; record "
      "verdicts in `docs/divergence_triage.json` instead.")
    w("")
    w("Reference libraries: "
      + ", ".join(f"`{name}` {version}" for name, version in sorted(libs.items()))
      + ". PMC is `pandas_market_calendars`, EC is `exchange_calendars`.")
    w("")

    # ---- how to read ------------------------------------------------------
    registry_years = sorted({
        y for e in exchanges.values() if "years" in e
        for y, r in e["years"].items() if REGISTRY not in r["sources_unavailable"]
    })
    ref_only_years = [str(y) for y in years if str(y) not in registry_years]
    w("## How to read this")
    w("")
    w(f"- Years requested: {years[0]} to {years[-1]}. The registry only has data "
      f"inside each exchange's `generation_range`, so the registry is compared "
      f"for {', '.join(registry_years) if registry_years else 'no year'}"
      + (f"; {', '.join(ref_only_years)} compares the two libraries with each other only"
         if ref_only_years else "") + ".")
    w("- For the registry, a trading day is a date that is not one of the "
      "exchange's `weekend_days` and not a `closed` holiday or ad-hoc closure. "
      "`early_close` and `delayed_open` days are trading days, so half days "
      "are not disagreements.")
    w("- Only regular working days are compared. A date on the exchange's "
      "`weekend_days` is skipped for all three sources, because the "
      "libraries model one-off weekend sessions (Budget Day, Muhurat, "
      "make-up Saturdays) that the registry does not and that differ "
      "between library versions.")
    w("- Registry, PMC and EC columns are trading days summed over the "
      "registry years above. `n/a` means the registry has no data; "
      f"`{NO_REFERENCE_DATA}` means that library does not know the exchange. "
      "A trailing `*` means the library was missing in some of those years.")
    w("- Agreement is trading days on which every available source agrees, "
      "divided by that count plus the disagreeing days. Days all sources "
      "agree are closed (weekends, shared holidays) are not counted. It is "
      "`n/a` when neither library has data.")
    mirrored = sorted(
        c for c, e in exchanges.items() if "years" in e
        and any(r.get("pmc_mirrors_exchange_calendars")
                and PMC not in r["sources_unavailable"]
                and EC not in r["sources_unavailable"]
                for r in e["years"].values())
    )
    independent = sorted(
        c for c, e in exchanges.items() if "years" in e
        and any(r.get("pmc_mirrors_exchange_calendars") is False for r in e["years"].values())
    )
    w(f"- PMC and EC are not independent. PMC serves {len(mirrored)} of the "
      "exchanges that both libraries cover straight from `exchange_calendars` "
      "(its mirror calendars), so for those the PMC and EC columns are one "
      "source counted twice. PMC has its own implementation for "
      + (", ".join(independent) if independent else "no exchange here")
      + ". Effectively the registry is being compared against one reference "
      "for the rest.")
    w("- A disagreement says nothing about which source is right. Nothing "
      "below has been checked against the exchange's own calendar unless "
      "stated.")
    w("")

    # ---- summary ----------------------------------------------------------
    w("## Summary")
    w("")
    w("| Exchange | Registry | PMC | EC | Disagreements | Agreement |")
    w("|---|---:|---:|---:|---:|---:|")
    for r in rows:
        diffs = str(r["disagreements"]) if r["references"] else "n/a"
        w(f"| {r['code']} | {_cell(r, REGISTRY)} | {_cell(r, PMC)} | "
          f"{_cell(r, EC)} | {diffs} | {_rate(r['rate'])} |")
    w("")

    compared = [r for r in rows if r["references"]]
    total_agree = sum(r["agree"] for r in compared)
    total_diffs = sum(r["disagreements"] for r in compared)
    clean = [r for r in compared if r["disagreements"] == 0]
    w(f"- Exchanges in the registry: {len(rows)}.")
    w(f"- Exchanges with at least one reference library: {len(compared)}; "
      f"with none: {len(rows) - len(compared)}.")
    w(f"- Exchanges with no disagreement: {len(clean)} of {len(compared)}.")
    if total_agree + total_diffs:
        w(f"- Trading days on which all available sources agree: {total_agree} of "
          f"{total_agree + total_diffs} "
          f"({total_agree / (total_agree + total_diffs) * 100:.1f}%).")
    w("")

    # ---- no reference data ------------------------------------------------
    w("## No reference data")
    w("")
    missing = []
    for code, e in sorted(exchanges.items()):
        if "years" not in e:
            continue
        reasons = {}
        for source in (PMC, EC):
            for y in sorted(e["years"]):
                msg = e["years"][y]["sources_unavailable"].get(source)
                if msg:
                    reasons.setdefault(source, msg)
        if reasons:
            missing.append((code, reasons))
    both = [c for c, r in missing if PMC in r and EC in r]
    only_pmc = [c for c, r in missing if PMC in r and EC not in r]
    only_ec = [c for c, r in missing if EC in r and PMC not in r]
    w(f"- Neither library ({len(both)}): " + (", ".join(both) or "none"))
    w(f"- Only PMC missing, EC has it ({len(only_pmc)}): " + (", ".join(only_pmc) or "none"))
    w(f"- Only EC missing, PMC has it ({len(only_ec)}): " + (", ".join(only_ec) or "none"))
    w("")
    if missing:
        w("| Exchange | PMC | EC |")
        w("|---|---|---|")
        for code, reasons in missing:
            def msg(source):
                text = reasons.get(source)
                if not text:
                    return "available"
                text = text.replace(NO_REFERENCE_DATA + ": ", "").replace("|", "/")
                return text if len(text) <= 70 else text[:67] + "..."
            w(f"| {code} | {msg(PMC)} | {msg(EC)} |")
        w("")

    # ---- disagreements ----------------------------------------------------
    w("## Disagreements")
    w("")
    any_diff = False
    for code, e in sorted(exchanges.items()):
        if "years" not in e:
            continue
        # Only registry-year disagreements are listed here; years without
        # registry data get their own section below.
        groups = _group_disagreements(e, _scope_years(e))
        if not groups:
            continue
        any_diff = True
        total = sum(len(v) for v in groups.values())
        w(f"### {code} ({total})")
        w("")
        for pattern, dates in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            listing = ", ".join(
                f"{d} {wd}" + (f" [{VERDICT_TAG[triage_index[(code, d)]]}]"
                               if (code, d) in triage_index else "")
                for d, wd in dates)
            w(f"- {_pattern_text(pattern)} ({len(dates)}): {listing}")
        w("")
    if not any_diff:
        w("None.")
        w("")

    # ---- triage -----------------------------------------------------------
    entries = (triage or {}).get("entries", [])
    if entries:
        w("## Triage")
        w("")
        w("Verdicts checked by hand against each exchange's own publication. "
          "Dates marked in the list above are the ones still disagreeing; "
          "\"fixed\" entries are already corrected in the registry, so their "
          "dates no longer appear there.")
        w("")
        counts = {}
        for e in entries:
            counts[e["verdict"]] = counts.get(e["verdict"], 0) + len(e["dates"])
        w("- " + "; ".join(f"{VERDICT_LABEL[v]}: {n} dates"
                           for v, n in sorted(counts.items())) + ".")
        w("")
        for e in sorted(entries, key=lambda e: (e["exchange"], e["verdict"])):
            state = (f"fixed in {e['fixed_in']}" if e.get("status") == "fixed"
                     else "registry verified, no change")
            w(f"### {e['exchange']}: {VERDICT_LABEL[e['verdict']]} ({len(e['dates'])}, {state})")
            w("")
            w(e["summary"])
            w("")
            w("Dates: " + ", ".join(e["dates"]) + ".")
            w("")
            w(f"Source: {e['source_url']}")
            w("")

    # ---- reference-only years --------------------------------------------
    if ref_only_years:
        w("## Libraries only (years outside the registry range)")
        w("")
        w(f"Years {', '.join(ref_only_years)}: PMC against EC, for exchanges where "
          "both have data.")
        w("")
        found = False
        both_libs = 0
        for code, e in sorted(exchanges.items()):
            if "years" not in e:
                continue
            lines = []
            has_both = False
            for y in ref_only_years:
                r = e["years"].get(y)
                if not r or set(r["sources_compared"]) != {PMC, EC}:
                    continue
                has_both = True
                for item in r["disagreements"]:
                    lines.append(
                        f"{item['date']} {item['weekday'][:2]} "
                        f"(PMC {item['says'][PMC]}, EC {item['says'][EC]})")
            both_libs += 1 if has_both else 0
            if lines:
                found = True
                w(f"- {code} ({len(lines)}): " + ", ".join(lines))
        if both_libs:
            w(f"- Exchanges compared this way: {both_libs}.")
        if not found:
            w("- No disagreement between the two libraries.")
        w("")

    if sessions is not None:
        out.extend(render_sessions(sessions))

    if errors:
        w("## Errors")
        w("")
        for code, message in errors.items():
            w(f"- {code}: {message}")
        w("")

    return "\n".join(out).rstrip("\n") + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input", default=DEFAULT_INPUT,
                        help="JSON from tools/divergence_test.py (default: %(default)s)")
    parser.add_argument("--sessions", default=DEFAULT_SESSIONS,
                        help="JSON from divergence_test.py --mode sessions; the "
                             "Session Times section is added when it exists "
                             "(default: %(default)s)")
    parser.add_argument("--triage", default=str(DEFAULT_TRIAGE),
                        help="Hand-checked verdicts, optional (default: %(default)s)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="Markdown file to write (default: %(default)s)")
    args = parser.parse_args(argv)

    try:
        report = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(report.get("exchanges"), dict) or "years" not in report:
            raise ValueError("not a divergence report (missing 'years' or 'exchanges')")
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read {args.input}: {exc}", file=sys.stderr)
        return 2

    triage = None
    if Path(args.triage).exists():
        try:
            triage = json.loads(Path(args.triage).read_text(encoding="utf-8"))
            for entry in triage.get("entries", []):
                if entry["verdict"] not in VERDICT_LABEL:
                    raise ValueError(f"unknown verdict {entry['verdict']!r}")
        except (OSError, ValueError, KeyError) as exc:
            print(f"ERROR: cannot read {args.triage}: {exc}", file=sys.stderr)
            return 2

    sessions = None
    if Path(args.sessions).exists():
        try:
            sessions = json.loads(Path(args.sessions).read_text(encoding="utf-8"))
            if sessions.get("mode") != "sessions" or "years" not in sessions:
                raise ValueError("not a sessions report (run divergence_test.py "
                                 "--mode sessions)")
        except (OSError, ValueError) as exc:
            print(f"ERROR: cannot read {args.sessions}: {exc}", file=sys.stderr)
            return 2

    text = render(report, triage, sessions)
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"Wrote {args.output} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
