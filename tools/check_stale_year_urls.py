#!/usr/bin/env python3
"""
check_stale_year_urls.py — Flags hardcoded year tokens in source URLs that
have fallen behind the current year.

Some exchange data sources publish year-specific URLs (a PDF circular named
after the year it covers, a "{year}-Calendar_csv_e.csv" naming convention,
a page path with "/2026/" in it). When the year in a *hardcoded* URL slips
behind the current year, the fetcher (or the manually-curated JSON entry)
is very likely citing a stale, superseded, or dead resource, and nothing
else in this project's CI would notice, since the URL itself still looks
like a valid string.

This scans two places for such URLs:

    1. tools/update_from_exchange.py — literal `source_url = "..."` (or
       `source_url = f"..."`) assignments, and literal URL/template
       constants: any identifier containing "url" or "template"
       (case-insensitive; covers `source_url`, `BASE_PAGE_TEMPLATE`, and
       similarly-named attributes) assigned directly to a string literal.
    2. exchanges/*.json — the `source_url` field of every holiday entry
       under `holidays.explicit`.

For each URL found, every 4-digit year token in the range 2010-2099 is
extracted. If the *maximum* year token found in a URL is less than the
current year, that URL is flagged as stale.

How "dynamic" URLs are detected and skipped
--------------------------------------------
A matched string literal is treated as dynamic, and skipped with a warning
rather than guessed at, if its content contains any of:
    - a Python format/f-string placeholder: a literal "{" character
      (covers "{year}", "{YYYY}", "{anything}")
    - a strftime-style placeholder: "%Y", "%y", or "%d"

A `source_url` that is assigned from a variable, attribute access, or
method call — e.g. `source_url=self.source_url`, or
`source_url=self.BASE_PAGE_TEMPLATE.format(year=current_year)` — is never
captured as a literal in the first place: the extraction regex only
matches an `=` immediately followed by a quote (optionally preceded by an
`f`), so a non-literal right-hand side structurally fails to match rather
than being matched and then classified as dynamic. This is how "built
from a variable the checker cannot resolve" is handled: by never treating
it as a URL literal at all, rather than trying to resolve it.

The allowlist
-------------
Some stale-looking URLs cannot be fixed by the scanner's own rules: a DFM
circular or a ZSE news post has an opaque ID, so no URL can be generated
for next year, and a manually-curated JSON entry legitimately cites the
circular it was built from. These go in ALLOWLIST below, a dict of
`URL: "YYYY-MM-DD"` where the date is the LAST day the entry suppresses
anything (inclusive). The match is the exact URL string, so one entry
covers every location that cites the URL (a fetcher constant and the JSON
entries it produced).

An allowlist entry only ever suppresses a stale hit. Once today is past
the entry's date it suppresses nothing: the hit is reported as stale and
the script fails, with the expired entry named. An entry whose URL no
longer appears anywhere in the scanned files is reported as a WARNING
(delete it); it never fails the check. A date that is not a valid
YYYY-MM-DD is a configuration error (exit 2).

Usage:
    check_stale_year_urls.py [--fetchers PATH] [--exchanges-dir PATH]
                             [--today YYYY-MM-DD]

    --today simulates a date, e.g. `--today 2027-01-01` to preview the
    year rollover. It sets both the current year and the allowlist clock.

Exit codes:
    0 — At least one year-token URL was found and none is stale (stale
        URLs covered by an unexpired allowlist entry do not count)
    1 — At least one stale year-token URL was found that no unexpired
        allowlist entry covers, OR zero year-token URLs were found at all
        across both locations (a zero-URL result means the scanner's own
        patterns stopped matching something that should be there — that's
        a broken check, not a clean pass)
    2 — The fetchers file or the exchanges directory does not exist, or
        an allowlist entry has an invalid date
"""

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

# A 4-digit year token in [2010, 2099], not part of a longer digit run.
YEAR_TOKEN_RE = re.compile(r"(?<!\d)(20[1-9]\d)(?!\d)")

# Matches `<ident> = "<content>"` / `<ident> = f"<content>"` (optionally
# `<ident>: <type> = ...`) where <ident> contains "url" or "template"
# (case-insensitive) — e.g. `source_url =`, `self.source_url =`,
# `BASE_PAGE_TEMPLATE =`. Only matches when a quote immediately follows
# the `=` (after an optional `f` and whitespace), so a value that's a
# variable, attribute access, or call (no leading quote) is never
# captured — see module docstring.
FETCHER_LITERAL_RE = re.compile(
    r"(?:^|[.\s])(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:url|template)[A-Za-z0-9_]*)"
    r"\s*(?::\s*[A-Za-z_][A-Za-z0-9_]*\s*)?=\s*"
    r"(?P<fstring>f)?(?P<quote>[\"'])(?P<content>(?:\\.|(?!(?P=quote)).)*)(?P=quote)",
    re.IGNORECASE,
)

DYNAMIC_PLACEHOLDER_RE = re.compile(r"\{|%Y|%y|%d")

# URL -> last day (inclusive, "YYYY-MM-DD") on which the entry suppresses a
# stale hit. See "The allowlist" in the module docstring. Added in the
# 2027 rollover defusal: on 2027-01-01 these 7 URLs (12 hits) all become
# stale at once, and none can be made dynamic (opaque IDs) or is wrong to
# keep (JSON entries cite the 2026 circular for 2026 dates).
ALLOWLIST = {
    # XWBO fetcher (tools/update_from_exchange.py). The PDF name carries
    # the year; the file for the next year is not verifiable ahead of time.
    # Unblock: update source_url when Wiener Boerse publishes the new PDF.
    "https://www.wienerborse.at/uploads/u/cms/files/trading/stock-exchange-holidays-2026-en.pdf": "2027-03-31",
    # XBUD fetcher. Same annual-update pattern as XWBO.
    # Unblock: update source_url when BSE publishes the next resolution.
    "https://www.bse.hu/pfile/file?path=/site/Angol/Documents/Products_And_Services/trading-information/trading-holidays-2026": "2027-03-31",
    # XZAG fetcher. News-post ID (/3260) is not predictable.
    # Unblock: update source_url to the 2027 post (or the stable
    # zse.hr/en/non-trading-days/110 page listed in BLOCKED.md).
    "https://zse.hr/en/trading-calendar-in-2026/3260": "2027-03-31",
    # XDFM fetcher AND 5 XDFM.json entries (one URL, so one date; the
    # later date applies to both). Circular ID and sfvrsn hash are opaque.
    # Unblock: update XDFMFetcher.source_url when DFM issues the 2027
    # circular; decide how the 2026-dated JSON entries cite it.
    "https://assets.dfm.ae/docs/default-source/circulars/circular-12-2025-trading-and-settlementholidays-for-the-calendar-year-2026-for-securities-market-excluding-derivatives-contracts-english.pdf?sfvrsn=cffc8981_0": "2027-06-01",
    # XCAI.json entries 12 and 13 (Cairo news posts for 2026 dates).
    "https://www.cairo.gov.eg/en/news/news-eng/2026/bd6a361fe04f4d268157c39e3103c96d": "2027-06-01",
    "https://www.cairo.gov.eg/en/news/news-eng/2026/fda45a85d7f446c1b4cd55e0f8259f4e": "2027-06-01",
    # XMAD.json entry 9 (BME instruction for the 2026 calendar).
    "https://www.bolsasymercados.es/bme-exchange/docs/regula/sbolsas/esp/instrucc/2025/2025-65-IO-CALENDARIO-DE-SESIONES-2026.pdf": "2027-06-01",
    # XHKG.json entries for 2026-02-16, 2026-04-07 and 2026-10-19: the SEHK
    # circular CT/075/25 (Hong Kong Securities Market Holiday Schedule for
    # 2026). Added in v2.23.1. No fetcher reads it (XHKG is ci_unreachable).
    # Unblock: cite the 2027 schedule circular when entries for 2027 are checked.
    "https://www.hkex.com.hk/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2025/SEHK_CT_075_2025": "2027-06-01",
    # XHKG.json entries for 2027-02-05, 2027-02-08, 2027-02-09 and 2027-09-16: the
    # SEHK circular CT/077/26 (Hong Kong Securities Market Holiday Schedule for
    # 2027). Added in v2.23.2. Unblock: cite the 2028 schedule circular, due mid-2027.
    "https://www.hkex.com.hk/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2026/SEHK_CT_077_2026Jun01162846": "2027-06-01",
    # XHKG.json entry for 2025-01-28: SEHK circular CT/063/24 (2025 schedule).
    "https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2024/ce_SEHK_CT_063_2024.pdf": "2027-06-01",
}


class UrlHit:
    """One URL found in either scanned location, with its year tokens."""

    def __init__(self, source, location, url):
        self.source = source        # file path, as a string
        self.location = location    # line number (int) or a JSON-entry description
        self.url = url
        self.years = sorted({int(y) for y in YEAR_TOKEN_RE.findall(url)})

    @property
    def max_year(self):
        return max(self.years) if self.years else None

    def is_stale(self, current_year):
        return self.max_year is not None and self.max_year < current_year


def is_dynamic(content):
    """True if this string literal is a template/placeholder rather than a
    concrete URL that's safe to check — see module docstring."""
    return bool(DYNAMIC_PLACEHOLDER_RE.search(content))


def scan_fetchers_file(path):
    """Scan tools/update_from_exchange.py for literal source_url / URL- or
    template-named string assignments containing an http(s) URL.

    Returns (hits, warnings).
    """
    hits = []
    warnings = []
    text = Path(path).read_text(encoding="utf-8")

    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in FETCHER_LITERAL_RE.finditer(line):
            content = m.group("content")
            if not content.startswith(("http://", "https://")):
                continue
            if is_dynamic(content):
                warnings.append(
                    f"{path}:{lineno}: skipped dynamic URL (template placeholder) "
                    f"in {m.group('name')!r}: {content}"
                )
                continue
            hits.append(UrlHit(str(path), lineno, content))

    return hits, warnings


def scan_exchanges_dir(dir_path):
    """Scan exchanges/*.json for source_url fields on explicit holiday
    entries.

    Returns (hits, warnings).
    """
    hits = []
    warnings = []

    for json_path in sorted(Path(dir_path).glob("*.json")):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"{json_path}: could not parse JSON ({exc}), skipping")
            continue

        entries = data.get("holidays", {}).get("explicit", [])
        for idx, entry in enumerate(entries):
            url = entry.get("source_url")
            if not url or not isinstance(url, str):
                continue
            if not url.startswith(("http://", "https://")):
                continue
            if is_dynamic(url):
                warnings.append(
                    f"{json_path}: entry #{idx} (date={entry.get('date', '?')}): "
                    f"skipped dynamic-looking URL: {url}"
                )
                continue
            location = f"holidays.explicit[{idx}] (date={entry.get('date', '?')})"
            hits.append(UrlHit(str(json_path), location, url))

    return hits, warnings


def parse_allowlist(allowlist):
    """Validate an allowlist dict. Returns ({url: date}, [error strings])."""
    parsed = {}
    errors = []
    for url, expiry in allowlist.items():
        try:
            parsed[url] = datetime.strptime(expiry, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            errors.append(
                f"allowlist entry has an invalid expiry date {expiry!r} "
                f"(want YYYY-MM-DD): {url}"
            )
    return parsed, errors


def run_check(fetchers_path, exchanges_dir, current_year=None,
              allowlist=None, today=None):
    """Returns (exit_code, report_lines).

    today: a datetime.date used for allowlist expiry (default: the real
    date). current_year defaults to today.year. allowlist defaults to the
    module-level ALLOWLIST.
    """
    if today is None:
        today = date.today()
    if current_year is None:
        current_year = today.year
    if allowlist is None:
        allowlist = ALLOWLIST

    fetchers_path = Path(fetchers_path)
    exchanges_dir = Path(exchanges_dir)

    if not fetchers_path.exists():
        return 2, [f"ERROR: fetchers file not found: {fetchers_path}"]
    if not exchanges_dir.exists():
        return 2, [f"ERROR: exchanges directory not found: {exchanges_dir}"]

    expiries, allowlist_errors = parse_allowlist(allowlist)
    if allowlist_errors:
        return 2, [f"ERROR: {e}" for e in allowlist_errors]

    fetcher_hits, fetcher_warnings = scan_fetchers_file(fetchers_path)
    json_hits, json_warnings = scan_exchanges_dir(exchanges_dir)

    all_hits = fetcher_hits + json_hits
    all_warnings = fetcher_warnings + json_warnings

    year_hits = [h for h in all_hits if h.years]
    stale_hits = [h for h in year_hits if h.is_stale(current_year)]

    # Split stale hits by allowlist coverage.
    suppressed = []   # covered by an unexpired entry
    expired = []      # covered by an entry whose date has passed
    failing = []      # not on the allowlist at all
    for h in stale_hits:
        if h.url in expiries:
            (suppressed if today <= expiries[h.url] else expired).append(h)
        else:
            failing.append(h)

    seen_urls = {h.url for h in all_hits}

    report = [
        f"Current year: {current_year}",
        f"Today (allowlist clock): {today.isoformat()}",
        f"Scanned {fetchers_path} and {exchanges_dir}/*.json.",
        f"URLs with a literal http(s) scheme found: {len(all_hits)}",
        f"  of which contain a year token (2010-2099): {len(year_hits)}",
    ]

    for w in all_warnings:
        report.append(f"WARNING: {w}")

    for url in sorted(expiries):
        if url not in seen_urls:
            report.append(
                f"WARNING: allowlist entry (expires {expiries[url].isoformat()}) "
                f"matches no scanned URL, delete it: {url}"
            )

    if not year_hits:
        report.append("")
        report.append(
            "FAIL: zero year-token URLs found across both locations. That "
            "means either there is genuinely nothing left to check (very "
            "unlikely given this project's history) or the scanner's own "
            "patterns stopped matching something real — treated as a "
            "failure rather than a silent pass."
        )
        return 1, report

    if suppressed:
        urls = sorted({h.url for h in suppressed})
        report.append("")
        report.append(
            f"ALLOWLISTED ({len(suppressed)} hits, {len(urls)} URLs; "
            f"suppressed until the date shown):"
        )
        for u in urls:
            n = sum(1 for h in suppressed if h.url == u)
            report.append(f"  - until {expiries[u].isoformat()} ({n} hits): {u}")

    if not failing and not expired:
        report.append("")
        if suppressed:
            report.append(
                "No stale year-token URLs outside the allowlist "
                "(allowlisted URLs above still need a manual update)."
            )
        else:
            report.append("All year-token URLs are current (max year >= current year).")
        return 0, report

    if expired:
        urls = sorted({h.url for h in expired})
        report.append("")
        report.append(
            f"EXPIRED ALLOWLIST ENTRIES ({len(expired)} hits, {len(urls)} URLs). "
            f"The allowlist date has passed; update the URL or, if it is "
            f"deliberately kept, extend the date in ALLOWLIST:"
        )
        for u in urls:
            report.append(f"  - expired {expiries[u].isoformat()}: {u}")
        for h in expired:
            report.append(
                f"      {h.source}:{h.location}: max year found is {h.max_year}"
            )

    if failing:
        report.append("")
        report.append(f"STALE YEAR URLS ({len(failing)}):")
        for h in failing:
            report.append(
                f"  - {h.source}:{h.location}: max year found is {h.max_year}, "
                f"which is less than the current year ({current_year}) — {h.url}"
            )

    return 1, report


def main(argv):
    fetchers_path = "tools/update_from_exchange.py"
    exchanges_dir = "exchanges"
    today = None

    args = list(argv[1:])
    i = 0
    while i < len(args):
        if args[i] == "--fetchers" and i + 1 < len(args):
            fetchers_path = args[i + 1]
            i += 2
        elif args[i] == "--exchanges-dir" and i + 1 < len(args):
            exchanges_dir = args[i + 1]
            i += 2
        elif args[i] == "--today" and i + 1 < len(args):
            try:
                today = datetime.strptime(args[i + 1], "%Y-%m-%d").date()
            except ValueError:
                print(f"ERROR: --today wants YYYY-MM-DD, got {args[i + 1]!r}")
                return 2
            i += 2
        else:
            i += 1

    exit_code, report = run_check(fetchers_path, exchanges_dir, today=today)
    for line in report:
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
