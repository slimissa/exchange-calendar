# Fetcher notes

Per-exchange notes for the 46 fetchers registered in `tools/update_from_exchange.py`, moved out of `README.md` in Phase 1a. The 29 sections that existed as README notes were copied from there; in Session 4 the ones that disagreed with `BLOCKED.md`, the README table or the data files were corrected, and each correction names its date and source. Five fetchers had no README note (XETR, XASX, XTKS, XPRA, XIST) and have a short stub, placed after the notes. The 28 exchanges that are blocked and have no fetcher are not here; they are in [`BLOCKED.md`](../BLOCKED.md). Status per exchange is in the exchange table in [`README.md`](../README.md).

**Anchors.** Every MIC has an anchor in lowercase, placed above its section: link to `FETCHERS.md#xpar`, not to a heading. Heading text may change; the MIC anchors are the stable reference. Three families also have a name anchor: `#euronext-family`, `#nasdaq-nordic`, `#nasdaq-baltic`.

**Status source of truth.** The status of each exchange is the `fetcher_status` field in `exchanges/<MIC>.json`: `implemented`, `ci_unreachable`, `blocked` or `none` (see `docs/exchange_schema.md`). It is not tracked anywhere else. The README Status column repeats it and `tools/check_doc_links.py` fails CI when an icon or a FETCHERS.md link disagrees with the field; `tests/test_fetcher_status.py` fails CI when the field disagrees with the fetchers registered in `tools/update_from_exchange.py`. Counts written in prose, such as "46 fetchers" in the README intro and above, are not checked yet: when a status changes, change the JSON first, then recount the prose.

## Expiring sources

Sources that will stop being current on a known trigger, or that already depend on a manual annual update. Triggers come from the README notes and the fetcher docstrings; where only a docstring says it, the row says so. "URL gate" refers to `ALLOWLIST` in `tools/check_stale_year_urls.py`: until the listed date the gate tolerates the stale URL, and after it the CI step fails.

| Exchange | Source | Expiry / trigger | Action needed |
|---|---|---|---|
| [XNYS](#xnys) (XNAS follows) | ir.theice.com press release covering 2026 to 2028 | ICE posts a new release every year or two, at an unpredictable URL (note). The fetcher docstring dates the two latest releases 2024-11-08 and 2025-12-23, so the next is plausible in Nov-Dec 2026 (inferred, not announced). Covered until 2028-12-31, so `check_expiring_sources.py` fails from 2029-01-01; the URL gate flags the same URL that day | Replace `NYSEFetcher.source_url` when the new release appears |
| [XDFM](#xdfm) | DFM circular PDF for 2026 (opaque circular ID and `sfvrsn` hash) | DFM issues the 2027 circular. URL gate: allowlisted until 2027-06-01 (the same URL is cited by 5 entries in `XDFM.json`) | Update `XDFMFetcher.source_url`; decide how the 2026-dated JSON entries cite the circular |
| [XWBO](#xwbo) | wienerborse.at PDF `stock-exchange-holidays-2026-en.pdf` | Single-year, year-specific URL (docstring; not stated in the README note). URL gate: allowlisted until 2027-03-31 | Update `source_url` when the 2027 PDF is published |
| [XBUD](#xbud) | bse.hu resolution `trading-holidays-2026` | Single-year, year-specific URL (docstring; not stated in the README note). URL gate: allowlisted until 2027-03-31 | Update `source_url` when the next resolution is published |
| [XZAG](#xzag) | zse.hr news post `trading-calendar-in-2026/3260` | Single-year source (note), news-post ID not predictable. URL gate: allowlisted until 2027-03-31. BLOCKED.md lists zse.hr/en/non-trading-days/110 as a stable page with the 2026 and 2027 lists (see its section) | Update `source_url`, or switch to the stable page |
| [XIST](#xist) | borsaistanbul.com `equity-market-2026-holiday-schedule.pdf` | Single-year, year-specific URL (docstring). Invisible to the URL gate; covered only by the freshness check in `fetcher_manifest.json` (`max_age_days` 400) | Update `source_url` when the 2027 PDF is published |
| [XHKG](#xhkg) | HKEX Stock Connect CSV, URL template `{year}-Calendar_csv_e.csv` | The note says the fetcher tries the current and the next year, and the template may need updating if HKEX changes its naming. The URL gate skips template URLs (warning only) | Confirm the 2027 CSV resolves once published; edit `BASE_PAGE_TEMPLATE` only if the naming changes |
| [XMOS](#xmos) | moex.com news post (year-specific ID, no predictable pattern) | Each new year's schedule is a new post. No year token, so the URL gate cannot see it | Find the new post each year and update `source_url` |
| [XMAD](#xmad), [XKUW](#xkuw), [XMEX](#xmex) | Respective exchange pages, `current_year_only = True` | The page shows only the current year, so there is no forward coverage; the page changes each January. XKUW is also blocked (HTTP 403 on 2026-09-17, see its section) | Annual refresh |
| [XBDA](#xbda) | bsx.com trading-hours-and-holidays page | The note records a table covering 2024 to 2027 | Look for a 2028 table during 2027 |
| [XTSE](#xtse), [XSAU](#xsau) | tsx.com holiday page; Saudi Exchange table | Point-in-time claims: XTSE "2025 and 2026 both present at verification time"; XSAU "table spanning 2020 to 2029" (moot while XSAU is blocked) | Re-verify before relying on the year range |
| [XDFM](#xdfm), XCAI, [XMAD](#xmad) | 8 `source_url` fields in `exchanges/*.json` (XDFM x5, XCAI x2, XMAD x1) that cite 2026 documents | URL gate: allowlisted until 2027-06-01 | Re-source, or teach the gate that an entry dated 2026 may cite a 2026 document |

`tools/check_expiring_sources.py` runs in CI and fails when a row in this table has expired. It reads only dates stated as an expiry in the `Expiry / trigger` column: `until`, `expires`, `expiry` or `expiring` followed by `YYYY-MM-DD`, `YYYY-MM` or `YYYY`, or a coverage range `YYYY to YYYY` (expires at the end of the second year). Other dates in that column, such as release dates, are context and are ignored. A row with none of these (for example "current year") is not checked. When you add a row with a known expiry, write it in one of these forms.

Only four fetchers (XBUD, XDFM, XIST, XWBO) have a freshness entry in `fetcher_manifest.json`; the rest have no staleness signal beyond the URL gate.

<a id="xnys"></a>
## NYSE (XNYS)

**NYSE note:** nyse.com blocks programmatic requests at the WAF level
("bot detection" — confirmed via `web_fetch`, not fixable with a different
User-Agent since it's not a header check; an earlier report of a plain
"403" from a sandboxed tool call was actually the sandbox's own network
allowlist, a mistake worth naming rather than glossing over). `NYSEFetcher`
now points at NYSE Group's own Investor Relations press release on
`ir.theice.com`, which publishes the same authoritative 3-year holiday table
and isn't blocked. BLOCKED.md (2026-10-07) cites
`nyse.com/trade/hours-calendars` as the tier-1 source for the 2026 list, so
nyse.com is a tier-1 source for 2026 even though its WAF makes it hard for the
fetcher to read. **Updated again 2026-08-29** to the newer 2026-2028
release after the previous 2025-2027 one was flagged as going stale — this
had sat unfixed for two rounds after first being noted, fixed now rather
than deferred again. **This URL will need manual updating once the 2028
window it covers passes** — ICE posts a new press release, at an
unpredictable URL, roughly every year or two.

<a id="xnas"></a>
## NASDAQ (XNAS)

**NASDAQ note:** nasdaq.com/trading-calendar renders its calendar client-side
(confirmed by direct fetch — the raw HTML contains no holiday data, just a
blank day grid). Rather than ship a scraper against a page that doesn't
expose its data, `NASDAQFetcher` reuses `NYSEFetcher`'s parser against
whichever source `NYSEFetcher` itself currently uses (read dynamically, not
hardcoded, so the two can't silently drift apart the way they briefly did),
since NASDAQ and NYSE observe an identical US equity holiday calendar.
BLOCKED.md (2026-10-07) cites a different nasdaq.com page,
`nasdaq.com/market-activity/stock-market-holiday-schedule`, as the tier-1
source for 2026, so nasdaq.com is a tier-1 source for 2026 even though the
fetcher does not read it.

<a id="xlon"></a>
## London (XLON)

**LSE note:** londonstockexchange.com does not publish its own scrapable
holiday table. `LSEFetcher` uses the UK government's bank-holidays JSON API
as a documented proxy. This has not been independently cross-checked
holiday-by-holiday against LSE's actual closures.

<a id="xshg"></a>
<a id="xshe"></a>
## Shanghai and Shenzhen (XSHG, XSHE)

**XSHG/XSHE note:** both pages describe closures as natural-language date
ranges ("close from X to Y") rather than one row per date, so these fetchers
expand ranges into individual weekdays rather than reading dates directly.
Both fetchers read whatever year sections exist on the page rather than
hardcoding a year, so they pick up new years automatically once published,
but don't assume current-year coverage without checking the returned dates.
(`XSHG.json` and `XSHE.json` both carry the October 2026 National Day closures,
from 2026-10-01.)

<a id="xhkg"></a>
## Hong Kong (XHKG)

**XHKG note:** uses HKEX's own Stock Connect trading-calendar CSV, reading
only the "Hong Kong" column (not the combined Stock Connect / mainland
columns, which can show "Closed" on days HKEX itself is actually open — this
was verified against a real row where only the mainland side was marked
closed). This source doesn't provide specific holiday names, only
"Holiday"/"Half Day" — `HKEXFetcher` labels entries generically rather than
inventing names. Like NYSE, the CSV's URL is year-specific; `fetch()` tries
the current and next year automatically, but the URL template may need
updating if HKEX changes its naming convention.

<a id="xtse"></a>
## Toronto (XTSE)

**XTSE note:** tsx.com separates "Canadian Holidays" (real TSX closures)
from "U.S. Holidays" (settlement-schedule notices for USD-denominated
issues, not actual TSX closures) in the same accordion widget.
`TSXFetcher` only parses the Canadian section. Covers multiple years
(2025 and 2026 both present at verification time).

<a id="xmad"></a>
## Madrid (XMAD)

**XMAD note:** bolsasymercados.es gives no holiday names at all — only
"Nth of Month / Weekday" pairs — and the page the fetcher reads
(`bolsasymercados.es/en/bme-exchange/trading/trading-calendar.html`) shows
only the current year, with no multi-year table. BME does publish multi-year
calendars elsewhere on `bolsasymercados.es`: its operational
instructions (Instrucciones Operativas) cover 2022 (53/2021), 2024 (45/2023),
2025 (52/2024) and 2026 (65/2025), and BLOCKED.md uses them as its tier-1
source. `BMEMadridFetcher` uses generic labels ("BME Non-Trading
Day") rather than guessing real names, and exposes a
`current_year_only = True` class attribute so callers know not to expect
forward coverage the way NYSE/XETR/XSAU provide.

<a id="xsau"></a>
## Saudi Arabia (XSAU)

**Status (BLOCKED.md, 2026-09-17): blocked, not CI-unreachable.** The parser
was written against a live fetch on 2026-08-27. On 2026-09-17 the page
returned HTTP 403 to both GitHub Actions runners and a residential IP with a
browser User-Agent, so "works locally" is not currently shown and the
exchange is not filed as CI-unreachable. One probe on one day: not shown to
be permanent. `SaudiExchangeFetcher` stays registered; the informational job
`live-check-blocked` in `live-fetcher-check.yml` still runs it, and a pass
would reopen it. Until then the calendar is maintained by hand. The note
below describes the table as it looked on 2026-08-27.

**XSAU note:** the richest Tier 2 source found — a real static table
spanning 2020-2029. The same table mixes in unrelated IPO "Listing of..."
announcement rows, filtered out via an allowlist (only rows mentioning
"Founding Day", "National Day", or "Eid Al") rather than a blacklist.
Weekend exclusion uses Friday/Saturday, not the Sat/Sun default used
elsewhere. `HolidayEntry.predicted` (defined in the schema and already used
by hand-maintained `XSAU.json` data, but never actually implemented by the
fetcher framework until now) is set to `True` for Eid dates still in the
future relative to when `fetch()` runs, `False` once they're in the past —
Founding Day and National Day are fixed Gregorian dates and are never
predicted. One row in the source table has an internally inverted date
range (end before start) relative to its own prose description;
`SaudiExchangeFetcher` skips that row and logs a warning rather than
guessing which value is correct.

<a id="xdfm"></a>
## Dubai (XDFM)

**XDFM note:** the first fetcher in this codebase to use `PDFFetcher` —
dfm.ae's annual holiday circular is a real, clean, text-based PDF (not a
scanned image), added specifically because PDF-only sources turned out to
be the single most common blocker across all three tiers checked so far.
Islamic holidays are footnoted "*" by DFM itself as tentative, mapped
directly onto `HolidayEntry.predicted`. Like NYSE/HKEX, the PDF's URL is
circular-specific and year-specific; will need a manual update once DFM
issues its 2027 circular. **Divergence recorded 2026-10-03 (BLOCKED.md):**
the PDF omits 2026-12-01 (Commemoration Day) while `XDFM.json` keeps it as a
closure. The two disagree, and the file keeps the entry. The fetcher is
present but not authoritative for that date, and the removal guard blocks a
refresh until a third source (the prior-year DFM circular or a UAE regulatory
notice) settles it.

<a id="xkuw"></a>
## Kuwait (XKUW)

**Status (BLOCKED.md, 2026-09-17): blocked by bot detection.** On
2026-09-17 boursakuwait.com.kw returned HTTP 403 to both GitHub Actions
runners and a residential IP with a browser User-Agent; header spoofing did
not get past it. One probe on one day: not shown to be permanent.
`BoursaKuwaitFetcher` stays registered and `live-check-blocked` still runs
it. Until then the calendar is maintained by hand.

**XKUW note:** as verified live on 2026-08-27 (before the block),
boursakuwait.com.kw is Gatsby-generated (built at compile time), so its
holiday table was present in the raw static HTML despite the site otherwise
looking like a JS app. Single-year only, same `current_year_only` pattern as
XMAD.

<a id="xmos"></a>
## Moscow (XMOS)

**XMOS note:** confirmed NOT sanctions-blocked, contrary to the initial
concern going into Tier 3 — moex.com is a real, accessible, static
English-language page. The actual problem is source fragility: the URL is
a year-specific news-post ID with no predictable naming pattern for future
years, worse than every other year-specific source in this registry. Format
is prose, not a table, and gives no per-day holiday name — only a combined
closure-date list, labeled generically as "Russian Public Holiday."

<a id="xwbo"></a>
## Vienna (XWBO)

**XWBO note:** wienerborse.at's PDF has a 2-column layout — the left column
("Stock exchange holidays") is real closures, but the RIGHT column
("Additional holiday trading days") lists days the exchange stays OPEN
despite being Austrian public holidays. `ViennaFetcher` only keeps the left
column; discarding the right is deliberate, not an omission.

<a id="xwar"></a>
<a id="xbud"></a>
## Warsaw and Budapest (XWAR, XBUD)

**XWAR/XBUD notes:** XWAR (gpw.pl) gives no holiday names, generic labels
used. XBUD (bse.hu PDF) does give real names; a footnote about certain
Saturdays being declared non-trading days is deliberately not parsed
separately, since those fall on the weekend already.

<a id="xpar"></a>
<a id="xams"></a>
<a id="xdub"></a>
<a id="xbru"></a>
<a id="xlis"></a>
<a id="xosl"></a>
<a id="euronext-family"></a>
## Euronext family

**Euronext family note (XPAR/XAMS/XDUB/XBRU/XLIS/XOSL):** all six markets
share one page and one fetcher class. **XOSL (Oslo Bors) was originally
assumed to need a separate "Nasdaq Nordic" source — that assumption was
wrong.** Oslo has been part of the Euronext group since 2019 and its
holiday data is a column in the same table already used for XPAR/XAMS since
Tier 1. Oslo trades in NOK, not EUR like the other five — confirmed
separately, not assumed. **A real bug was found and fixed while extending
this fetcher**: it previously only checked for `'closed'` in a cell,
silently skipping "Half Trading Day" cells — meaning XPAR and XAMS had been
missing their Dec 24/31 early closes since Tier 1. Fixed for all six
markets at once.

<a id="xsto"></a>
<a id="xhel"></a>
<a id="xcse"></a>
<a id="xice"></a>
<a id="nasdaq-nordic"></a>
## Nasdaq Nordic

**Nasdaq Nordic note (XSTO/XHEL/XCSE/XICE):** one shared page
(nasdaq.com/european-market-activity/trading-hours) hands over
pre-aggregated "Closed" and "Half trading days" date lists per market
directly in the page text — the richest single source found across every
tier. The same page also lists Norway's holidays, deliberately not used for
XOSL since that MIC already has a working Euronext-sourced fetcher and
using two sources for one MIC risks silent disagreement. No per-day holiday
names given, only a combined list per market.

**How the page is read (code, XICE included).** The fetcher requests
`https://www.nasdaq.com/european-market-activity/trading-hours`. For each
"Exchange Holiday Schedule <year>" section it finds the market's row ("Iceland"
for XICE) and takes the second cell, the Equity/Equity derivatives column.
It splits that cell at "Half trading days:". In the part before it (the
"Closed" cell) it reads every `Mon D, YYYY` date; the part after it gives the
half days. So a "Closed" cell is parsed only if the dates are in its text. On
2026-10-07 BLOCKED.md recorded that, from the environment used for the sweep,
this page showed "Closed" cells without dates for Iceland, and that the
`source_url` on the existing XICE entries is
`nasdaqomxnordic.com/trading-hours`, a different page from the one the fetcher
reads. With no dates found for a market the fetcher raises `ParseError`.

<a id="xtal"></a>
<a id="xris"></a>
<a id="xlit"></a>
<a id="nasdaq-baltic"></a>
## Nasdaq Baltic

**Nasdaq Baltic note (XTAL/XRIS/XLIT):** one shared page
(nasdaqbaltic.com) with a single table covering all three markets, where a
"Market" column lists which of TLN/RIG/VLN close on each date — some
holidays are shared across all three, some are market-specific (e.g. Jan 2
is Riga-only). No holiday names given, generic labels used.

<a id="xbsp"></a>
## Brazil (XBSP)

**XBSP note (Brazil):** the most complex fetcher in this registry.
b3.com.br mixes real Brazilian closures with US-holiday settlement-only
notices in the same table, plus delayed-open special-hours rows (Ash
Wednesday) and pure settlement-lag footnotes — none of which are actual
market closures. `B3BrazilFetcher` requires explicit "no trading on the
equity" language AND excludes the US-only settlement phrase, rather than
relying on a single icon or keyword check.

<a id="xmex"></a>
## Mexico (XMEX)

**XMEX note (Mexico):** the simplest Tier 6 source — a clean two-column
table with real names, current-year-only.

<a id="xbue"></a>
## Argentina (XBUE)

**XBUE note (Argentina):** byma.com.ar uses a footnote-reference system
per row (1)/(2)/(3)/(4); only (3) — "no settlement, but trading continues"
— is excluded from closures. Spanish month names are parsed via an
explicit lookup table, not locale-dependent `strptime`, since this
environment's C locale doesn't reliably support Spanish month names.

<a id="xstc"></a>
## Vietnam (XSTC)

**XSTC note (Vietnam):** the source PDF's prose has nested parentheses (a
lunar-calendar cross-reference nested inside a rescheduling note) that
required stripping repeatedly, not just once, before date-range extraction
would work. The document also explicitly confirms that government-mandated
"make-up workday" Saturdays don't apply to the exchange, so no special
date-shifting logic was needed beyond standard weekend exclusion.

<a id="xnsa"></a>
## Nigeria (XNSA)

**XNSA note (Nigeria):** real static table, includes Eidul-Fitr and Eid
el-Kabir (both `predicted=True`, footnoted by NGX itself as dependent on
government announcement). Showing 2024 data at the 2026-09-06 verification — treated
as "not yet updated" rather than a structural blocker, since it's a plain
table with no evidence of the postback-gating that made XCAI's staleness
permanent. **Status (BLOCKED.md, 2026-09-17): CI-unreachable, parser
works.** On 2026-09-17 the page fetched cleanly from a residential IP (12
holidays; the year of those rows was not recorded). From GitHub Actions the
same fetch fails with `ParseError: No holidays found`: the site is behind
Sucuri, which serves a challenge page instead of the table to datacenter IP
ranges. This is the CI WAF, not a parser bug. The 2024 data seen on
2026-09-06 is therefore not the current explanation for a CI failure.

<a id="xbrv"></a>
## BRVM (XBRV)

**XBRV note (8 UEMOA countries):** a single shared page and fetcher covers
Benin, Burkina Faso, Guinea-Bissau, Cote d'Ivoire, Mali, Niger, Senegal,
and Togo under one MIC — the hypothesized shared-infrastructure pattern,
confirmed. Islamic holidays footnoted `(*)` by BRVM itself, mapped to
`predicted=True`.

<a id="xcol"></a>
## Sri Lanka (XCOL)

**XCOL note (Sri Lanka):** includes Buddhist Poya (full-moon) holidays and
Islamic holidays (predicted). Poya days are not safely computable: they move
about eleven days a year, and CSE's observance can differ from the
astronomical full moon by a day. In 2026 twelve entries had been 2025 dates
repeated, and all 2026 dates are now CSE's own circular (BLOCKED.md,
2026-10-07 and 2026-10-11). The 2027 Poya entries were removed, not predicted.

*Vesak week.* Two holidays can share a date (May Day and Vesak Poya both fall
on 2026-05-01); since `ExchangeData.validate()` rejects duplicate dates,
same-date entries are merged into one with a combined name rather than
changing that core validation rule. The merge loses the Vesak name:
`XCOL.json` reads only "May Day" on 2026-05-01. The circular also lists a half
holiday on 2026-04-30, in lieu of the day after Vesak Poya. The Government
moved the day after Vesak from 2 May to 31 May by Extraordinary Gazette
(Daily Mirror, 24 April 2026), and CSE issued Circular 03-04-2026
("Holidays for 2026 - Amended", 20 April 2026), whose text was not retrieved.
Whether it removed the 30 April half holiday is not known, and no
`early_close` entry exists.

<a id="xgse"></a>
## Ghana (XGSE)

**XGSE note (Ghana):** resolved via direct site navigation, not search —
found the real "Events & Holidays" nav link on the site's own homepage
after two earlier search-based attempts came up empty. Handles
alternate-date rows ("Friday July 1st/3rd") by matching each candidate
date's computed weekday against the row's stated weekday, confirmed
correct against the real 2026 calendar.

<a id="xbda"></a>
## Bermuda (XBDA)

**XBDA note (Bermuda):** one of the cleanest sources in this entire
registry — real, static, multi-year (2024-2027). A bug was caught during
testing (not after shipping): early-close detection for Christmas Eve
initially checked the wrong table cell for the "AST Close" marker.

<a id="xcay"></a>
## Cayman (XCAY)

**XCAY note (Cayman):** two full year sections exist on the page with no
explicit year heading — the year is inferred per table by testing which
candidate year makes the first row's stated weekday match a computed date.

<a id="xlux"></a>
## Luxembourg (XLUX)

**XLUX note (Luxembourg):** `XLUX.json` has 10 closures for 2026 (New Year's
Day, Good Friday, Easter Monday, Labour Day, Ascension Day, Whit Monday,
National Day, Christmas Eve, Christmas Day, and a substituted Boxing Day on
2026-12-28). Entries carry no `note`: `schema.json` allows none on explicit
holiday entries. LuxSE is primarily a listing venue, not a
high-volume equity market; whether the calendar is complete is not recorded
here.

<a id="xmal"></a>
## Malta (XMAL)

**XMAL note (Malta):** an explicit "TRADING" column distinguishes real MSE
closures from foreign-holiday settlement-only notices ("US Holiday" / "UK
Holiday") — the same foreign-holiday-exclusion pattern already seen in
XTSE and XBSP.

<a id="xzag"></a>
## Zagreb (XZAG)

**XZAG note (Zagreb):** real, clean source with real names. The fetcher
reads a news post stamped 2026 (`zse.hr/en/trading-calendar-in-2026/3260`)
and returns one year. The source is not single-year: ZSE's stable page
`zse.hr/en/non-trading-days/110` lists 2026 and 2027, and ZSE also has its own
2025 post (BLOCKED.md, re-read 2026-10-11). The fetcher has not been pointed
at that page.

<a id="xetr"></a>
## Xetra (XETR)

*Stub: the README had no note for this exchange. The facts below come from the README tier table (as it stood at `9b75ff2`) and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table at `9b75ff2`): implemented
- Fetcher: `XETRFetcher`
- Source: <https://www.cashmarket.deutsche-boerse.com/cash-en/trading/trading-calendar-and-trading-hours>
- Source column (README tier table at `9b75ff2`): cashmarket.deutsche-boerse.com
- Verified live 2026-08-26 (per the docstring): a server-rendered HTML table with one row per holiday name and one column per year (2026 to 2032). The fetcher extracts every `Mon DD, YYYY` date in a row, computes the weekday itself and drops Saturdays and Sundays, so it does not depend on cell styling.

<a id="xasx"></a>
## ASX (XASX)

*Stub: the README had no note for this exchange. The facts below come from the README tier table (as it stood at `9b75ff2`) and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table at `9b75ff2`): implemented
- Fetcher: `ASXFetcher`
- Source: <https://www.asx.com.au/markets/market-resources/trading-hours-calendar/cash-market-trading-hours/trading-calendar>
- Source column (README tier table at `9b75ff2`): asx.com.au
- Verified live 2026-08-26 (per the docstring): server-rendered HTML. The page carries two tables (2026 and 2027), each with its own `Dates for <year>` header, and the fetcher reads the year per table. The Trading Day column maps `CLOSED` to a closure and `CLOSE EARLY` to an early close.

<a id="xtks"></a>
## Tokyo (XTKS)

*Stub: the README had no note for this exchange. The facts below come from the README tier table (as it stood at `9b75ff2`) and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table at `9b75ff2`): implemented
- Fetcher: `TokyoFetcher`
- Source: <https://www.jpx.co.jp/english/corporate/about-jpx/calendar/index.html>
- Source column (README tier table at `9b75ff2`): jpx.co.jp (English-language table)
- Verified live 2026-08-26 (per the docstring): a server-rendered English table under per-year headings, with dates written like `Jan. 1 (Thu.)`. The year comes from the nearest preceding heading.

<a id="xpra"></a>
## Prague (XPRA)

*Stub: the README had no note for this exchange. The facts below come from the README tier table (as it stood at `9b75ff2`) and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table at `9b75ff2`): implemented
- Fetcher: `PragueFetcher`
- Source: <https://www.pse.cz/en/trading/trading-information/trading-calendar>
- Source column (README tier table at `9b75ff2`): pse.cz
- Verified live 2026-08-31 (per the docstring): static HTML with real holiday names, grouped under `YYYY Non-business days` headings, with 2025 and 2026 both present at verification time.

<a id="xist"></a>
## Borsa Istanbul (XIST)

*Stub: the README had no note for this exchange. The facts below come from the README tier table (as it stood at `9b75ff2`) and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table at `9b75ff2`): implemented
- Fetcher: `XISTFetcher`
- Source: <https://www.borsaistanbul.com/files/equity-market-2026-holiday-schedule.pdf>
- Source column (README tier table at `9b75ff2`): borsaistanbul.com equity-market holiday PDF (one PDF per market segment; Turkish closures only); the tier table also points to `BLOCKED.md`
- Verified live 2026-10-01 (per the docstring): Borsa Istanbul publishes one PDF per market segment and only the equity PDF is used. Known limitation from the docstring: single-year PDF, year-specific URL, the same annual-update pattern as XDFM, XWBO and XBUD. The URL is assembled from two adjacent string literals, so `tools/check_stale_year_urls.py` does not scan it.
