# Fetcher notes

Per-exchange notes for the 46 fetchers registered in `tools/update_from_exchange.py`, moved out of `README.md` in Phase 1a. The 29 sections that existed as README notes are copied verbatim, so each still describes its source as it was at `9b75ff2`. Five fetchers had no README note (XETR, XASX, XTKS, XPRA, XIST) and have a short stub, placed after the notes. The 28 exchanges that are blocked and have no fetcher are not here; they are in [`BLOCKED.md`](../BLOCKED.md). Status per exchange is in the tier tables in [`README.md`](../README.md).

**Anchors.** Every MIC has an anchor in lowercase, placed above its section: link to `FETCHERS.md#xpar`, not to a heading. Heading text may change; the MIC anchors are the stable reference. Three families also have a name anchor: `#euronext-family`, `#nasdaq-nordic`, `#nasdaq-baltic`.

## Expiring sources

Sources that will stop being current on a known trigger, or that already depend on a manual annual update. Triggers come from the README notes and the fetcher docstrings; where only a docstring says it, the row says so. "URL gate" refers to `ALLOWLIST` in `tools/check_stale_year_urls.py`: until the listed date the gate tolerates the stale URL, and after it the CI step fails.

| Exchange | Source | Expiry / trigger | Action needed |
|---|---|---|---|
| [XNYS](#xnys) (XNAS follows) | ir.theice.com press release covering 2026 to 2028 | ICE posts a new release every year or two, at an unpredictable URL (note). The fetcher docstring dates the two latest releases 2024-11-08 and 2025-12-23, so the next is plausible in Nov-Dec 2026 (inferred, not announced). The URL gate starts flagging this URL on 2029-01-01 | Replace `NYSEFetcher.source_url` when the new release appears |
| [XDFM](#xdfm) | DFM circular PDF for 2026 (opaque circular ID and `sfvrsn` hash) | DFM issues the 2027 circular. URL gate: allowlisted until 2027-06-01 (the same URL is cited by 5 entries in `XDFM.json`) | Update `XDFMFetcher.source_url`; decide how the 2026-dated JSON entries cite the circular |
| [XWBO](#xwbo) | wienerborse.at PDF `stock-exchange-holidays-2026-en.pdf` | Single-year, year-specific URL (docstring; not stated in the README note). URL gate: allowlisted until 2027-03-31 | Update `source_url` when the 2027 PDF is published |
| [XBUD](#xbud) | bse.hu resolution `trading-holidays-2026` | Single-year, year-specific URL (docstring; not stated in the README note). URL gate: allowlisted until 2027-03-31 | Update `source_url` when the next resolution is published |
| [XZAG](#xzag) | zse.hr news post `trading-calendar-in-2026/3260` | Single-year source (note), news-post ID not predictable. URL gate: allowlisted until 2027-03-31. BLOCKED.md lists zse.hr/en/non-trading-days/110 as a stable page with the 2026 and 2027 lists (see D7) | Update `source_url`, or switch to the stable page |
| [XIST](#xist) | borsaistanbul.com `equity-market-2026-holiday-schedule.pdf` | Single-year, year-specific URL (docstring). Invisible to the URL gate; covered only by the freshness check in `fetcher_manifest.json` (`max_age_days` 400) | Update `source_url` when the 2027 PDF is published |
| [XHKG](#xhkg) | HKEX Stock Connect CSV, URL template `{year}-Calendar_csv_e.csv` | The note says the fetcher tries the current and the next year, and the template may need updating if HKEX changes its naming. The URL gate skips template URLs (warning only) | Confirm the 2027 CSV resolves once published; edit `BASE_PAGE_TEMPLATE` only if the naming changes |
| [XMOS](#xmos) | moex.com news post (year-specific ID, no predictable pattern) | Each new year's schedule is a new post. No year token, so the URL gate cannot see it | Find the new post each year and update `source_url` |
| [XMAD](#xmad), [XKUW](#xkuw), [XMEX](#xmex) | Respective exchange pages, `current_year_only = True` | The page shows only the current year, so there is no forward coverage; the page changes each January. XKUW is also blocked (see D2) | Annual refresh |
| [XBDA](#xbda) | bsx.com trading-hours-and-holidays page | The note records a table covering 2024 to 2027 | Look for a 2028 table during 2027 |
| [XTSE](#xtse), [XSAU](#xsau) | tsx.com holiday page; Saudi Exchange table | Point-in-time claims: XTSE "2025 and 2026 both present at verification time"; XSAU "table spanning 2020 to 2029" (moot while XSAU is blocked) | Re-verify before relying on the year range |
| [XDFM](#xdfm), XCAI, [XMAD](#xmad) | 8 `source_url` fields in `exchanges/*.json` (XDFM x5, XCAI x2, XMAD x1) that cite 2026 documents | URL gate: allowlisted until 2027-06-01 | Re-source, or teach the gate that an entry dated 2026 may cite a 2026 document |

Three notes that go stale for other reasons are tracked under Discrepancies instead: XSHG/XSHE (D15), XNSA (D4), XLUX (D13).

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
and isn't blocked. **Updated again 2026-08-29** to the newer 2026-2028
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
since NASDAQ and NYSE observe an identical US equity holiday calendar. Every
mirrored entry carries a `note` field documenting this.

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
**As of verification, neither page had published 2026 Golden Week dates yet**
— both fetchers read whatever year sections exist on the page rather than
hardcoding a year, so they'll pick up new years automatically once published,
but don't assume current-year coverage without checking the returned dates.

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
"Nth of Month / Weekday" pairs — and only publishes the current year, no
multi-year table. `BMEMadridFetcher` uses generic labels ("BME Non-Trading
Day") rather than guessing real names, and exposes a
`current_year_only = True` class attribute so callers know not to expect
forward coverage the way NYSE/XETR/XSAU provide.

<a id="xsau"></a>
## Saudi Arabia (XSAU)

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
issues its 2027 circular.

<a id="xkuw"></a>
## Kuwait (XKUW)

**XKUW note:** boursakuwait.com.kw is Gatsby-generated (built at compile
time), so its holiday table is present in the raw static HTML despite the
site otherwise looking like a JS app. Single-year only, same
`current_year_only` pattern as XMAD.

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
government announcement). Showing 2024 data at verification time — treated
as "not yet updated" rather than a structural blocker, since it's a plain
table with no evidence of the postback-gating that made XCAI's staleness
permanent.

<a id="xbrv"></a>
## BRVM (XBRV)

**XBRV note (8 UEMOA countries):** a single shared page and fetcher covers
Benin, Burkina Faso, Guinea-Bissau, Cote d'Ivoire, Mali, Niger, Senegal,
and Togo under one MIC — the hypothesized shared-infrastructure pattern,
confirmed. Islamic holidays footnoted `(*)` by BRVM itself, mapped to
`predicted=True`.

<a id="xcol"></a>
## Sri Lanka (XCOL)

**XCOL note (Sri Lanka):** includes both Buddhist Poya (full-moon) holidays
(not predicted — computable, not sighting-dependent) and Islamic holidays
(predicted). Found a real edge case: two holidays can share a date (May Day
and Vesak Poya both fall on 2026-05-01) — since `ExchangeData.validate()`
rejects duplicate dates, same-date entries are merged into one with a
combined name rather than changing that core validation rule.

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

**XLUX note (Luxembourg):** real but deliberately sparse — only one
closure (Christmas Day) was confirmed present for 2026. This may
accurately reflect LuxSE's calendar (primarily a listing venue, not a
high-volume equity market) or may omit client-side-rendered entries. Every
entry carries an explicit `note` flagging this as not confirmed complete,
rather than presenting it with the same confidence as richer sources.

<a id="xmal"></a>
## Malta (XMAL)

**XMAL note (Malta):** an explicit "TRADING" column distinguishes real MSE
closures from foreign-holiday settlement-only notices ("US Holiday" / "UK
Holiday") — the same foreign-holiday-exclusion pattern already seen in
XTSE and XBSP.

<a id="xzag"></a>
## Zagreb (XZAG)

**XZAG note (Zagreb):** real, clean, single-year source with real names.

<a id="xetr"></a>
## Xetra (XETR)

*Stub: the README had no note for this exchange. The facts below come from the README tier table and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table): implemented
- Fetcher: `XETRFetcher`
- Source: <https://www.cashmarket.deutsche-boerse.com/cash-en/trading/trading-calendar-and-trading-hours>
- Tier table source column: cashmarket.deutsche-boerse.com
- Verified live 2026-08-26 (per the docstring): a server-rendered HTML table with one row per holiday name and one column per year (2026 to 2032). The fetcher extracts every `Mon DD, YYYY` date in a row, computes the weekday itself and drops Saturdays and Sundays, so it does not depend on cell styling.

<a id="xasx"></a>
## ASX (XASX)

*Stub: the README had no note for this exchange. The facts below come from the README tier table and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table): implemented
- Fetcher: `ASXFetcher`
- Source: <https://www.asx.com.au/markets/market-resources/trading-hours-calendar/cash-market-trading-hours/trading-calendar>
- Tier table source column: asx.com.au
- Verified live 2026-08-26 (per the docstring): server-rendered HTML. The page carries two tables (2026 and 2027), each with its own `Dates for <year>` header, and the fetcher reads the year per table. The Trading Day column maps `CLOSED` to a closure and `CLOSE EARLY` to an early close.

<a id="xtks"></a>
## Tokyo (XTKS)

*Stub: the README had no note for this exchange. The facts below come from the README tier table and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table): implemented
- Fetcher: `TokyoFetcher`
- Source: <https://www.jpx.co.jp/english/corporate/about-jpx/calendar/index.html>
- Tier table source column: jpx.co.jp (English-language table)
- Verified live 2026-08-26 (per the docstring): a server-rendered English table under per-year headings, with dates written like `Jan. 1 (Thu.)`. The year comes from the nearest preceding heading.

<a id="xpra"></a>
## Prague (XPRA)

*Stub: the README had no note for this exchange. The facts below come from the README tier table and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table): implemented
- Fetcher: `PragueFetcher`
- Source: <https://www.pse.cz/en/trading/trading-information/trading-calendar>
- Tier table source column: pse.cz
- Verified live 2026-08-31 (per the docstring): static HTML with real holiday names, grouped under `YYYY Non-business days` headings, with 2025 and 2026 both present at verification time.

<a id="xist"></a>
## Borsa Istanbul (XIST)

*Stub: the README had no note for this exchange. The facts below come from the README tier table and the fetcher class docstring in `tools/update_from_exchange.py`; nothing was re-verified when this file was created.*

- Status (README tier table): implemented
- Fetcher: `XISTFetcher`
- Source: <https://www.borsaistanbul.com/files/equity-market-2026-holiday-schedule.pdf>
- Tier table source column: borsaistanbul.com equity-market holiday PDF (one PDF per market segment; Turkish closures only); the tier table also points to `BLOCKED.md`
- Verified live 2026-10-01 (per the docstring): Borsa Istanbul publishes one PDF per market segment and only the equity PDF is used. Known limitation from the docstring: single-year PDF, year-specific URL, the same annual-update pattern as XDFM, XWBO and XBUD. The URL is assembled from two adjacent string literals, so `tools/check_stale_year_urls.py` does not scan it.

## Discrepancies

To be resolved in Phase 1a, Session 4. The notes above were moved verbatim from the README, so each one still says what it said at `9b75ff2`. This table lists where a note, the README tier tables, BLOCKED.md and the data files disagree. README line numbers refer to `README.md` at `9b75ff2` (`git show 9b75ff2:README.md`); BLOCKED.md line numbers refer to the current file.

| # | Exchange | Disagreement | Evidence |
|---|---|---|---|
| D1 | [XSAU](#xsau) | The tier table says blocked (403 from all IPs) and two README header lines say "permanently blocked". The note presents a working fetcher ("richest Tier 2 source", a 2020 to 2029 table). BLOCKED.md says 403 from CI and from a residential IP on 2026-09-17, and "not shown to be permanent". | README 6, 217, 241, 394-407; BLOCKED.md 95, 1240 |
| D2 | [XKUW](#xkuw) | Same pattern as D1. The note says the table is present in the static HTML; BLOCKED.md says 403 everywhere. "Permanently" is stronger than one probe on one day. | README 255, 418-421; BLOCKED.md 73, 1224 |
| D3 | [XHKG](#xhkg) | The tier table says CI-unreachable. BLOCKED.md lists it as `resolved` and its section does not mention CI. The note is silent on CI. `docs/DRIFT.md` records this as intentional. BLOCKED.md's XSHG section refers to the same CDN IP-block pattern as XHKG. | README 233, 371-379; BLOCKED.md 65, 462, 1256; docs/DRIFT.md |
| D4 | [XNSA](#xnsa) | The note explains the problem as the page showing 2024 data. BLOCKED.md says the page fetches cleanly from a residential IP (12 holidays, 2026-09-17) and CI fails on a Sucuri challenge, not a parser bug. BLOCKED.md also names it "Nigerian Stock Exchange". | README 310, 493-498; BLOCKED.md 86, 1267 |
| D5 | [XDFM](#xdfm) | The tier table says implemented and the note reads healthy. BLOCKED.md says the PDF omits 2026-12-01, the data file keeps it, and the removal guard blocks refresh until the divergence is resolved. | README 254, 409-416; BLOCKED.md 1394 |
| D6 | [XICE](#nasdaq-nordic) | The Nordic note says the Nasdaq page gives date lists per market directly in the page text. BLOCKED.md says that page showed `Closed` cells without dates (the Iceland query), and names nasdaqomxnordic.com/trading-hours as the existing XICE source; the code uses nasdaq.com/european-market-activity/trading-hours. | README 454-461; BLOCKED.md 662; tools/update_from_exchange.py 2672 |
| D7 | [XZAG](#xzag) | The note says single-year source. BLOCKED.md says ZSE publishes 2025 (its own 2025 post), 2026 and 2027 (zse.hr/en/non-trading-days/110) lists. The fetcher still uses the 2026-stamped news post. | README 541; BLOCKED.md 1461; tools/update_from_exchange.py 5746 |
| D8 | [XMAD](#xmad) | The note says the site only publishes the current year. BLOCKED.md uses the BME operational instructions for the 2025 and 2026 calendars on bolsasymercados.es as its tier-1 source and cites earlier ones back to 2022, so multi-year publications exist. | README 387-392; BLOCKED.md 235 |
| D9 | [XNYS](#xnys) | The note says nyse.com blocks programmatic requests. BLOCKED.md cites nyse.com/trade/hours-calendars as the tier-1 source for the 2026 list. | README 335-347; BLOCKED.md 265 |
| D10 | [XNAS](#xnas) | The note says the nasdaq.com trading calendar is client-rendered. BLOCKED.md uses nasdaq.com/market-activity/stock-market-holiday-schedule as the tier-1 source for 2026. | README 349-356; BLOCKED.md 255 |
| D11 | [XCOL](#xcol) | The note says Poya holidays are computable, not predicted, and that May Day and Vesak merge into one combined name. BLOCKED.md says Poya days move about eleven days a year (twelve 2026 entries had been 2025 dates repeated), that the Government moved the day after Vesak, and lists an open Vesak-week item; `XCOL.json` reads only "May Day" on 2026-05-01. | README 506-511; BLOCKED.md 1281; exchanges/XCOL.json |
| D12 | README tier tables | A "(28 exchanges) blocked" row sits below tier tables that already list all 30 blocked rows individually (28 without a fetcher plus XSAU and XKUW). BLOCKED.md counts 30 blocked. | README 333; BLOCKED.md summary table |
| D13 | [XLUX](#xlux) | The note says only Christmas Day is confirmed for 2026 and that every entry carries a `note`. `XLUX.json` has 10 closures in 2026 and no `note` key on any entry. | README 529-534; exchanges/XLUX.json |
| D14 | [XNAS](#xnas) | The note says every mirrored entry carries a `note` field. `XNAS.json` entries have none, and `schema.json` forbids it on explicit holiday entries (`note` exists only on confidence entries). | README 349-356; exchanges/XNAS.json; schema.json; BLOCKED.md 255 |
| D15 | [XSHG, XSHE](#xshg) | The note says neither page had published 2026 Golden Week dates. Both data files carry October 2026 Golden Week closures. | README 363-369; exchanges/XSHG.json, XSHE.json |
