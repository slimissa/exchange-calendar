#!/usr/bin/env python3
"""Session 2, Task 1 recon for XSWX. Throwaway: do not commit.

Run from the repo root, in an environment with network + Playwright:
    python3 /path/to/inspect_xswx.py > /tmp/xswx-recon.txt

Unlike the spec's wording, render_js() returns the whole page, so the
matched elements are selected here with BeautifulSoup. Every match is listed
(class, size, first 200 chars) because `[class*=calendar]` is a loose selector
that can hit navigation or widget markup, not only a holiday table.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "tools"))
from bs4 import BeautifulSoup  # noqa: E402
import fetch_render  # noqa: E402

URL = ("https://www.six-group.com/en/market-data/news-tools/"
       "trading-currency-holiday-calendar.html")
SEL = "[class*=calendar]"
DATE_RES = [r"\d{1,2}\.\d{1,2}\.\d{4}", r"\d{4}-\d{2}-\d{2}", r"\d{2}/\d{2}/\d{4}"]
NAMES = ["New Year", "Good Friday", "Easter", "Christmas", "Ascension", "Whit",
         "Corpus", "All Saints", "Immaculate", "Boxing"]


def ctx(html, m, n=100):
    return html[max(0, m.start() - n): m.end() + n].replace("\n", " ")


html = fetch_render.render_js(URL, SEL, timeout=30)
Path("/tmp/xswx-calendar.html").write_text(html, encoding="utf-8")
print(f"rendered HTML: {len(html)} chars -> /tmp/xswx-calendar.html")

soup = BeautifulSoup(html, "html.parser")
els = soup.select(SEL)
print(f"\n== {len(els)} element(s) match {SEL}")
for i, el in enumerate(els):
    txt = el.get_text(" ", strip=True)
    print(f"[{i}] <{el.name} class={el.get('class')}> {len(str(el))} chars html, "
          f"{len(txt)} chars text: {txt[:200]!r}")

if els:
    biggest = max(els, key=lambda e: len(str(e)))
    print("\n== first 3000 chars of the largest matched element")
    print(str(biggest)[:3000])

scope = str(biggest) if els else html
print("\n== date-like patterns (inside largest matched element)")
for pat in DATE_RES:
    for m in re.finditer(pat, scope):
        print(f"[{pat}] ...{ctx(scope, m)}...")

print("\n== holiday names (inside largest matched element)")
for name in NAMES:
    for m in re.finditer(re.escape(name), scope):
        print(f"[{name}] ...{ctx(scope, m)}...")

print("\n== same date patterns over the WHOLE page (count only)")
for pat in DATE_RES:
    print(pat, len(re.findall(pat, html)))
