#!/usr/bin/env python3
"""Generate the calendar-covering probes of the cross-language fixture (4b3).

Hand-picked probe dates are not coverage: the Rust registry-level `is_open`
read every date a day early from schema 2.1 to v2.29.0 and no probe fell on a
Monday. This tool writes, for each MIC in MICS, a deterministic probe set into
tests/cross_language_queries.json (labels `<op>_gen_<suffix>`; every other
query is left as it is):

  week      every day, Monday to Sunday, of the first ordinary week (no
            holiday, early close or delayed open on any of its seven days)
            of the year YEAR: registry `is_open` + `in_session` twin at
            open + 30 minutes, and exchange-level `status_at` and
            `exchange_is_open` at the same time;
  boundary  on that week's first trading day: one minute before and at the
            open, one minute before and at the close (registry-level with
            twins, and `status_at`);
  holiday   the first full-day holiday of YEAR at open + 30 minutes
            (registry-level with twin, and `status_at`);
  early     the first early-close day of YEAR or later (else the latest
            earlier one; none for an exchange that has no early close in
            its data, which --report shows) at the EXCHANGE level, which honours early
            closes: `status_at` and `exchange_is_open` one minute before and
            at the early-close time; plus the registry-level `is_open` with
            twin at the early-close time, which by contract still answers
            from regular hours.

The fixture stores queries, never answers: the four wrappers must agree with
each other (tools/check_cross_language.sh). The Python wrapper is used here
only to pick the dates.

Usage:
  python3 tools/gen_cross_lang_probes.py          # rewrite the gen_ block
  python3 tools/gen_cross_lang_probes.py --check  # fail on drift (gate, CI)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "cross_language_queries.json"
sys.path.insert(0, str(ROOT / "wrappers" / "python"))

# Sat-Sun weekends, plus XSAU and XCAI (Fri-Sat weekends; the only other
# weekend in the registry).
MICS = ("XNYS", "XLON", "XTKS", "XHKG", "XSAU", "XCAI", "XBUE")
YEAR = 2026
GEN_OPS = ("is_open", "in_session", "status_at", "exchange_is_open")
MARK = "_gen_"  # labels are <op>_gen_<suffix>, so the in_session twin rule applies unchanged
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _shift(hhmm: str, minutes: int) -> str:
    h, m = map(int, hhmm.split(":"))
    t = (h * 60 + m + minutes) % (24 * 60)
    return f"{t // 60:02d}:{t % 60:02d}"


def is_generated(label: str) -> bool:
    return any(label.startswith(op + MARK) for op in GEN_OPS)


def _q(op: str, args: list, suffix: str) -> dict:
    return {"op": op, "args": args, "label": f"{op}{MARK}{suffix}"}


def _registry_pair(mic: str, day: str, time: str, tag: str) -> list[dict]:
    base = f"{mic.lower()}_{tag}_{day.replace('-', '_')}_{time.replace(':', '')}"
    return [_q("is_open", [mic, day, time], base),
            _q("in_session", [mic, day, time], base)]


def _exchange_pair(mic: str, day: str, time: str, tag: str, with_is_open: bool = True) -> list[dict]:
    base = f"{mic.lower()}_{tag}_{day.replace('-', '_')}_{time.replace(':', '')}"
    out = [_q("status_at", [mic, day, time], base)]
    if with_is_open:
        out.append(_q("exchange_is_open", [mic, day, time], base))
    return out


def probes_for(reg, mic: str) -> tuple[list[dict], dict]:
    ex = reg.get(mic)
    rows = {h["date"]: h for h in ex.list_holidays()}
    special = {d for d, h in rows.items()}
    info: dict = {"mic": mic}
    out: list[dict] = []

    # 1. First ordinary week of YEAR: a Monday-to-Sunday week with no row.
    day = dt.date(YEAR, 1, 5)
    day -= dt.timedelta(days=day.weekday())  # Monday
    while True:
        week = [day + dt.timedelta(days=i) for i in range(7)]
        if not any(d.isoformat() in special for d in week):
            break
        day += dt.timedelta(days=7)
    info["week"] = week[0].isoformat()
    first_trading = None
    for i, d in enumerate(week):
        iso = d.isoformat()
        hours = ex.regular_hours_on(iso)
        t = _shift(hours["open"], 30)
        out += _registry_pair(mic, iso, t, f"week_{DAYS[i]}")
        out += _exchange_pair(mic, iso, t, f"week_{DAYS[i]}")
        if first_trading is None and d.weekday() not in ex.weekend_days:
            first_trading = iso
    info["weekend_days"] = list(ex.weekend_days)

    # 2. Boundaries on the week's first trading day.
    hours = ex.regular_hours_on(first_trading)
    for t, tag in ((_shift(hours["open"], -1), "open_m1"), (hours["open"], "open"),
                   (_shift(hours["close"], -1), "close_m1"), (hours["close"], "close")):
        out += _registry_pair(mic, first_trading, t, f"boundary_{tag}")
        out += _exchange_pair(mic, first_trading, t, f"boundary_{tag}", with_is_open=False)
    info["boundary_day"] = first_trading

    # 3. First full-day holiday of YEAR.
    hol = next((d for d in sorted(rows) if d.startswith(str(YEAR)) and rows[d].get("status") == "closed"
                and dt.date.fromisoformat(d).weekday() not in ex.weekend_days), None)
    if hol:
        t = _shift(ex.regular_hours_on(hol)["open"], 30)
        out += _registry_pair(mic, hol, t, "holiday")
        out += _exchange_pair(mic, hol, t, "holiday", with_is_open=False)
    info["holiday"] = hol

    # 4. First early close of YEAR or later, at the exchange level.
    earlies = [d for d in sorted(rows) if rows[d].get("status") == "early_close" and rows[d].get("early_close_time")]
    early = next((d for d in earlies if d >= f"{YEAR}-01-01"), earlies[-1] if earlies else None)
    if early:
        ect = rows[early]["early_close_time"]
        out += _exchange_pair(mic, early, _shift(ect, -1), "early_m1")
        out += _exchange_pair(mic, early, ect, "early")
        out += _registry_pair(mic, early, ect, "early")
    info["early_close"] = early
    return out, info


def generate() -> tuple[list[dict], list[dict]]:
    from exchange_calendar import CalendarRegistry
    reg = CalendarRegistry()
    queries: list[dict] = []
    infos: list[dict] = []
    for mic in MICS:
        q, info = probes_for(reg, mic)
        queries += q
        infos.append(info)
    return queries, infos


def render(fixture_text: str, generated: list[dict]) -> str:
    data = json.loads(fixture_text)
    kept = [q for q in data["queries"] if not is_generated(q["label"])]
    lines = fixture_text.split("\n")
    # Keep the hand-written part byte-for-byte: rebuild only the query list
    # tail. Each query is one line, as in the hand-written fixture.
    head_end = next(i for i, l in enumerate(lines) if l.strip().startswith('"queries"'))
    body = [json.dumps(q, ensure_ascii=False) for q in kept + generated]
    out = lines[:head_end + 1] + ["    " + b + ("," if i < len(body) - 1 else "") for i, b in enumerate(body)]
    out += ["  ]", "}"]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--check", action="store_true", help="fail if the gen_ block is out of date")
    p.add_argument("--report", action="store_true", help="print the dates picked per MIC")
    args = p.parse_args(argv)
    generated, infos = generate()
    current = FIXTURE.read_text(encoding="utf-8")
    new = render(current, generated)
    if args.report:
        for info in infos:
            print(json.dumps(info))
    if args.check:
        if new != current:
            print("error: tests/cross_language_queries.json gen_ probes are out of date; "
                  "run python3 tools/gen_cross_lang_probes.py", file=sys.stderr)
            return 1
        print(f"OK: {len(generated)} generated probe(s) for {len(MICS)} MICs are current")
        return 0
    FIXTURE.write_text(new, encoding="utf-8")
    print(f"wrote {len(generated)} generated probe(s) for {len(MICS)} MICs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
