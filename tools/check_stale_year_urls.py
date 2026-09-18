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

Usage:
    check_stale_year_urls.py [--fetchers PATH] [--exchanges-dir PATH]

Exit codes:
    0 — At least one year-token URL was found and none is stale
    1 — At least one stale year-token URL was found, OR zero year-token
        URLs were found at all across both locations (a zero-URL result
        means the scanner's own patterns stopped matching something that
        should be there — that's a broken check, not a clean pass)
    2 — The fetchers file or the exchanges directory does not exist
"""

import json
import re
import sys
from datetime import datetime
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


def run_check(fetchers_path, exchanges_dir, current_year=None):
    """Returns (exit_code, report_lines)."""
    if current_year is None:
        current_year = datetime.now().year

    fetchers_path = Path(fetchers_path)
    exchanges_dir = Path(exchanges_dir)

    if not fetchers_path.exists():
        return 2, [f"ERROR: fetchers file not found: {fetchers_path}"]
    if not exchanges_dir.exists():
        return 2, [f"ERROR: exchanges directory not found: {exchanges_dir}"]

    fetcher_hits, fetcher_warnings = scan_fetchers_file(fetchers_path)
    json_hits, json_warnings = scan_exchanges_dir(exchanges_dir)

    all_hits = fetcher_hits + json_hits
    all_warnings = fetcher_warnings + json_warnings

    year_hits = [h for h in all_hits if h.years]
    stale_hits = [h for h in year_hits if h.is_stale(current_year)]

    report = [
        f"Current year: {current_year}",
        f"Scanned {fetchers_path} and {exchanges_dir}/*.json.",
        f"URLs with a literal http(s) scheme found: {len(all_hits)}",
        f"  of which contain a year token (2010-2099): {len(year_hits)}",
    ]

    for w in all_warnings:
        report.append(f"WARNING: {w}")

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

    if not stale_hits:
        report.append("")
        report.append("All year-token URLs are current (max year >= current year).")
        return 0, report

    report.append("")
    report.append(f"STALE YEAR URLS ({len(stale_hits)}):")
    for h in stale_hits:
        report.append(
            f"  - {h.source}:{h.location}: max year found is {h.max_year}, "
            f"which is less than the current year ({current_year}) — {h.url}"
        )

    return 1, report


def main(argv):
    fetchers_path = "tools/update_from_exchange.py"
    exchanges_dir = "exchanges"

    args = list(argv[1:])
    i = 0
    while i < len(args):
        if args[i] == "--fetchers" and i + 1 < len(args):
            fetchers_path = args[i + 1]
            i += 2
        elif args[i] == "--exchanges-dir" and i + 1 < len(args):
            exchanges_dir = args[i + 1]
            i += 2
        else:
            i += 1

    exit_code, report = run_check(fetchers_path, exchanges_dir)
    for line in report:
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
