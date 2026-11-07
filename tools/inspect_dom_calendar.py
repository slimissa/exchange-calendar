#!/usr/bin/env python3
"""Probe a page's DOM for a calendar-like element.

Used by Phase 3 sessions before writing a per-exchange fetcher. Renders the
page with Playwright, selects elements matching a CSS selector, lists every
match (class, size, first 200 chars), and shows date-like patterns and
holiday-name fragments with context.

Every match is listed because a loose selector like `[class*=calendar]` can
hit navigation or widget markup, not only a holiday table. The reconnaissance
output is what decides whether a fetcher is possible for an exchange.

Usage:
    python3 tools/inspect_dom_calendar.py --url <URL> [--selector <SEL>] \
        [--output-html /tmp/inspect-dom.html] [--timeout 30] \
        [--holiday-words "New Year,Good Friday,Easter,Christmas"]

The output is meant to be pasted into a session's report, not committed.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bs4 import BeautifulSoup  # noqa: E402
import fetch_render  # noqa: E402


def ctx(html, m, n=100):
    return html[max(0, m.start() - n): m.end() + n].replace("\n", " ")


def main():
    p = argparse.ArgumentParser(
        description="Probe a page's DOM for a calendar-like element. "
                    "Used by Phase 3 sessions before writing a per-exchange fetcher."
    )
    p.add_argument("--url", required=True,
                   help="Page URL to render with Playwright.")
    p.add_argument("--selector", default="[class*=calendar]",
                   help="CSS selector to match. Default: [class*=calendar].")
    p.add_argument("--output-html", default="/tmp/inspect-dom.html",
                   help="Where to save the rendered HTML. Default: /tmp/inspect-dom.html.")
    p.add_argument("--holiday-words",
                   default="New Year,Good Friday,Easter,Christmas,Ascension,Whit,"
                           "Corpus,All Saints,Immaculate,Boxing",
                   help="Comma-separated holiday name fragments to look for.")
    p.add_argument("--timeout", type=int, default=30,
                   help="Playwright timeout in seconds. Default: 30.")
    args = p.parse_args()

    url = args.url
    sel = args.selector
    output_html = args.output_html
    names = [w.strip() for w in args.holiday_words.split(",") if w.strip()]
    timeout = args.timeout
    date_res = [r"\d{1,2}\.\d{1,2}\.\d{4}", r"\d{4}-\d{2}-\d{2}", r"\d{2}/\d{2}/\d{4}"]

    html = fetch_render.render_js(url, sel, timeout=timeout)
    Path(output_html).write_text(html, encoding="utf-8")
    print(f"rendered HTML: {len(html)} chars -> {output_html}")

    soup = BeautifulSoup(html, "html.parser")
    els = soup.select(sel)
    print(f"\n== {len(els)} element(s) match {sel}")
    for i, el in enumerate(els):
        txt = el.get_text(" ", strip=True)
        print(f"[{i}] <{el.name} class={el.get('class')}> {len(str(el))} chars html, "
              f"{len(txt)} chars text: {txt[:200]!r}")

    if not els:
        print("\n== no matches; the selector may be wrong, or the page is a SPA")
        return

    biggest = max(els, key=lambda e: len(str(e)))
    print("\n== first 3000 chars of the largest matched element")
    print(str(biggest)[:3000])

    scope = str(biggest)
    print("\n== date-like patterns (inside largest matched element)")
    for pat in date_res:
        for m in re.finditer(pat, scope):
            print(f"[{pat}] ...{ctx(scope, m)}...")

    print("\n== holiday names (inside largest matched element)")
    for name in names:
        for m in re.finditer(re.escape(name), scope):
            print(f"[{name}] ...{ctx(scope, m)}...")

    print("\n== same date patterns over the WHOLE page (count only)")
    for pat in date_res:
        print(pat, len(re.findall(pat, html)))


if __name__ == "__main__":
    main()