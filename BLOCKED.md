# Blocked / Not Automated

**Tier 1 update 2026-08-27: XHKG is no longer blocked.** See "Resolved"
section below.

**Tier 2 (regional hubs) update 2026-08-27:** 7 of 10 Tier 2 exchanges
checked are blocked (XSES, XSWX, XKRX, XBOM, XNSE, XJKT, XTAI). Only XTSE,
XMAD, and XSAU were buildable.

**Tier 3 (Gulf/EMEA) update 2026-08-29:** 6 of 10 confirmed blocked (XTAD,
XBAH, XQSE, XCAI, XJSE, XIST), 1 unverified (XMUS), 3 buildable (XDFM,
XKUW, XMOS).

**Tier 4 (European smaller markets) update 2026-08-31:** 8 of 10 buildable
(XWBO, XWAR, XPRA, XBUD, XDUB, XBRU, XLIS, XOSL — the last four via
extending the existing shared Euronext fetcher). Only 1 confirmed blocked
this round (XATH — same visual-grid-PDF problem as XSWX). This is by far
the best hit rate of any tier after Tier 1, supporting the hypothesis that
European exchanges lean toward simpler, more static infrastructure — though
XATH shows that's not universal even within Europe.

**Tier 5 (Nordic/Baltic) update 2026-08-31:** 7 of 7 buildable — a clean
sweep, via two shared fetchers (`NasdaqNordicFetcher` for XSTO/XHEL/XCSE/
XICE, `NasdaqBalticFetcher` for XTAL/XRIS/XLIT), confirming the "shared
infrastructure" hypothesis proposed after Tier 4's Euronext discovery. No
new blocks this round.

**Tier 6 (emerging markets) update 2026-09-04:** 3 of 10 buildable (XBSP,
XMEX, XBUE — Latin America, checked with real depth rather than shallow
coverage of all ten). 8 confirmed blocked after a full resolution pass
(XSGO, XKLS, XBOG, XLIM, XPHS, XBKK, plus XMUS and XIST carried over from
earlier tiers, resolved this round rather than left ambiguous). XSTC
(Vietnam) remains genuinely unchecked — reported honestly rather than
guessed at.

**Tier 7 (Africa/South Asia) update 2026-09-06:** applied the accumulated
infrastructure model (static/shared = buildable, JS/bot-wall/visual-PDF =
blocked) as a fast predictive filter. 4 of 9 buildable (XNSA, XBRV, XCOL,
plus XSTC resolved as a carryover from Tier 6). 4 confirmed blocked, 2 of
them by robots.txt (XCAS, XDHA — respected by design, not worked around),
1 by an unreadable PDF (XKAR), 1 by a JS-rendered page (XTUN). 2 remain
genuinely unverified (XNBO, XGSE) rather than forced to a verdict.

**Tier 8 (small/island markets) update 2026-09-06 — FINAL TIER:** 6 of 8
buildable (XBDA, XCAY, XLUX, XMAL, XZAG, plus XGSE resolving the Tier 7
carryover). 4 confirmed blocked (XBUL, XBEK, XNZE, and XNBO — the second
Tier 7 carryover, resolved decisively this round via a consistent JS-SPA
signature across 6 different pages rather than a single miss). Notably,
the brief's own predictions for this tier were mixed: New Zealand was
expected to be simple and turned out JS-blocked; Beirut was flagged as
uncertain due to instability and that concern was directly confirmed (2
independent server timeouts).

This file documents what was checked and why each verdict holds, since "we
found a different URL" or "it's blocked" is easy to state and easy to get
wrong without the reasoning behind it.

## XSES — Singapore Exchange (SGX)

- **Checked:** sgx.com/trading and related pages
- **Finding:** JS-rendered shell. No first-party equities holiday HTML or
  CSV/JSON found — only a derivatives-specific trading circular PDF (a
  different market segment than the equities calendar this registry needs)
  and third-party aggregators, which are not authoritative.
- **Verdict:** BLOCKED.

## XSWX — SIX Swiss Exchange

- **Checked:** six-group.com/en/market-data/news-tools/trading-currency-holiday-calendar.html
- **Finding:** the page itself is real and static, but its only calendar
  data is a PDF -- a visual calendar grid with no per-day text labels
  identifying which holiday falls on which greyed-out date. Parsing this
  reliably would require either OCR or a pixel-level heuristic against
  cell shading, neither of which this project's text-based framework does
  (or should attempt to guess at).
- **Verdict:** BLOCKED.

## XKRX — Korea Exchange (KRX)

- **Checked:** global.krx.co.kr's "Market Closing(Holiday)" page
- **Finding:** confirmed JS/AJAX-driven data grid — a year dropdown
  (2016-2026) and a "Search"/"Download" button, but zero holiday rows in
  the raw HTML. No underlying public API endpoint was found within the time
  spent looking.
- **Verdict:** BLOCKED.

## XBOM — BSE India (Bombay Stock Exchange)

- **Checked:** bseindia.com/static/markets/marketinfo/listholi.aspx (the
  page referenced by other open-source market-calendar projects, e.g.
  `pandas_market_calendars`)
- **Finding:** the page is real and known to have a parseable structure
  historically, but direct `web_fetch` access returned "Site blocked the
  request (bot detection)" on both the `www.` and `beta.` subdomains.
  Undocumented "hidden" API endpoints exist (per third-party blog posts
  reverse-engineering bseindia.com's frontend calls) but were not used —
  they aren't officially documented, could change or be revoked without
  notice, and reverse-engineering internal endpoints crosses into a
  different risk category than parsing a published page.
- **Verdict:** BLOCKED.

## XNSE — National Stock Exchange of India (NSE)

- **Checked:** nseindia.com/resources/exchange-communication-holidays
- **Finding:** the page itself loads (not bot-blocked), but the actual
  holiday table is populated via JS/AJAX behind "Select Product" and
  "Year" dropdowns -- the static HTML contains only a single hardcoded
  note about one specific 2026 date, not the table. NSE is also widely
  documented (across multiple open-source projects) as requiring a
  session-cookie handshake before its internal APIs will respond to plain
  HTTP requests, which this framework's `requests`-based approach doesn't
  perform.
- **Verdict:** BLOCKED.

## XJKT — Indonesia Stock Exchange (IDX)

- **Checked:** idx.co.id's official static PDF announcement
  ("Peng-00171 Libur Bursa 2026")
- **Finding:** a real, first-party, government-adjacent PDF exists and is
  linked from IDX's own site — but the direct fetch request itself was
  bot-blocked, and even if it weren't, PDF parsing is out of scope for this
  `BeautifulSoup`-based HTML framework (same reasoning as XSWX).
- **Verdict:** BLOCKED.

## XTAI — Taiwan Stock Exchange (TWSE)

- **Checked:** twse.com.tw/en/trading/holiday.html (JS-rendered, confirmed
  no data in raw HTML) AND `openapi.twse.com.tw/v1` — TWSE's real, public,
  documented OpenAPI, fetched its full `swagger.json` spec directly and
  reviewed every listed endpoint (company governance, financials, indices,
  securities-firm data, trading reports, etc).
- **Finding:** **no holiday or trading-calendar endpoint exists in the
  public API.** Third-party MCP-server projects claiming "market calendar"
  support most likely scrape the same JS-rendered page rather than using a
  documented API endpoint, since none exists.
- **Verdict:** BLOCKED — this one moved from "needs more verification" to a
  confirmed blocker, not a resolved build.

## Resolved: XHKG — Hong Kong Exchanges and Clearing (HKEX)

- **Originally blocked on:** `https://www.hkex.com.hk/News/HKEX-Calendar?sc_lang=en`
  — confirmed JS-rendered widget, no holiday data in raw HTML, no first-party
  JSON API found (only paid third-party scraper wrappers, rejected as not
  authoritative).
- **Resolution:** a *different* page on the same domain — HKEX's own "Trading
  Hour, Trading and Settlement Calendar" page for Stock Connect — links
  directly to real, static CSV files (e.g.
  `.../2026-Calendar_csv_e.csv`), verified live and fetchable, not
  JS-rendered, not bot-walled.
- **Important nuance, not a footnote:** this CSV is the *Stock Connect*
  trading calendar, which combines Hong Kong, Shanghai & Shenzhen, and
  Northbound/Southbound trading status in one file. Stock Connect can show
  "Closed" on a day when Hong Kong's own market is actually open (e.g. when
  only the mainland side is on holiday). `HKEXFetcher` reads ONLY the "Hong
  Kong" column, not the Stock Connect / mainland columns — verified against
  a real fetched row where the "Hong Kong" column was blank while "Shanghai &
  Shenzhen" said "Holiday" (2026-01-02, the day after New Year's, a
  mainland-only closure). Reading the wrong column would have silently
  produced a mainland calendar mislabeled as XHKG's own.
- **Known limitation carried forward:** like NYSE/SSE/SZSE, this CSV's URL is
  year-specific (`{year}-Calendar_csv_e.csv`) and not guaranteed stable
  forever. `fetch()` tries the current year and next year automatically
  (HKEX has historically published next year's file in December), but the
  URL template will eventually need a manual update if HKEX changes the
  naming convention.
- **Specific holiday names not available:** unlike the other 9 fetchers, this
  source doesn't name the holiday (e.g. "Lunar New Year" vs "National Day")
  — only "Holiday" or "Half Day" per date. `HKEXFetcher` labels entries
  generically ("Hong Kong Public Holiday" / "Hong Kong Half Trading Day")
  rather than inventing a name the source doesn't provide.

## XTAD — Abu Dhabi Securities Exchange (ADX)

- **Checked:** adx.ae/about-adx/media/adx-events-calendar
- **Finding:** confirmed Next.js JS-rendered SPA — the raw HTML contains
  only "Loading component..." placeholders, no static holiday data.
- **Verdict:** BLOCKED.

## XBAH — Bahrain Bourse

- **Checked:** bahrainbourse.com's "Official Holidays" page (real SharePoint
  site, not JS-rendered overall)
- **Finding:** the site itself is real and static, but this specific page's
  content area is empty in the raw HTML — populated by a client-side
  SharePoint webpart. Bahrain Bourse otherwise only announces holidays
  individually via one-off "Market Message" news posts, not a structured
  calendar.
- **Verdict:** BLOCKED.

## XQSE — Qatar Exchange

- **Checked:** qe.com.qa/qse-calendar
- **Finding:** confirmed JS/AJAX-driven Liferay portal widget ("Events for
  [Month]"), empty table in raw HTML. This is a general corporate-events
  calendar, not specifically a holiday calendar, and is dynamic regardless.
- **Verdict:** BLOCKED.

## XCAI — Egyptian Exchange (EGX)

- **Checked:** egx.com.eg/en/Trading_Calendar.aspx
- **Finding:** real, static, first-party HTML — but the page only serves
  **2019** holiday data, six years stale as of verification. Likely an
  ASP.NET WebForms postback-gated year selector (not a simple GET query
  parameter), which a plain `requests`-based fetcher can't drive without
  reverse-engineering the postback/viewstate mechanism. Building against
  stale data would be actively worse than no fetcher at all.
- **Verdict:** BLOCKED (data staleness, not inaccessibility).

## XJSE — Johannesburg Stock Exchange (JSE)

- **Checked:** jse.co.za and clientportal.jse.co.za Market Notice PDFs
- **Finding:** expected to be one of the simpler Tier 3 sources (well
  documented, stable South African public holidays); instead, JSE only
  publishes its holiday calendar as PDF Market Notices, and even after
  adding `PDFFetcher` support to the framework, the PDF itself returned
  "Site blocked the request (bot detection)" on direct fetch. PDF-text
  extraction doesn't help if the file can't be fetched at all.
- **Verdict:** BLOCKED. Confirms that "PDF-only" and "bot-walled" are
  independent problems — fixing one doesn't guarantee fixing the other.

## XIST — Borsa Istanbul

- **Checked:** the real 2026 holiday-schedule PDF, linked from
  borsaistanbul.com's official-holidays page — fetched successfully (not
  bot-walled, unlike XJSE).
- **Finding:** the data is real, but the document is a genuinely hard case:
  four different market-segment tables in one PDF (Debt Securities, Precious
  Metals, Gold & Silver Fixing, Equity, Derivatives), of which only the
  "APPENDIX-3: Equity Market" table is the correct source for actual BIST
  equity closures — the first table (labeled "Debt Securities Market")
  contains what is very obviously a copy-paste template error, listing US
  market holidays (Martin Luther King Day, July 4th, Thanksgiving) instead
  of Turkish ones. On top of that, the extracted text for the Equity Market
  appendix itself already showed dates out of chronological order (e.g.
  "May 29 Friday, May 30 Saturday, May 28 Thursday") -- a strong signal that
  pdfplumber's plain text extraction is interleaving this PDF's multi-column
  layout incorrectly.
- **Verdict:** NOT BUILT. This is a genuine "verified accessible with real
  data" case that was deliberately left unbuilt rather than risk shipping a
  parser against text I could already see was corrupted. `pdfplumber`'s
  structured `extract_table()` method (rather than plain `extract_text()`)
  might handle the column layout correctly, but confirming that requires
  downloading and testing against the actual PDF bytes locally, which this
  environment's network restrictions block for borsaistanbul.com. A good
  candidate for a follow-up round with different tooling access, not a
  permanent blocker the way XJSE's bot-wall is.
- **Re-checked 2026-08-31 (Tier 5 "quick win" attempt):** still not built.
  The plan was to try `pdfplumber.extract_table()` in place of
  `extract_text()`, but that requires downloading the actual PDF bytes
  locally to run against — the same network restriction noted above still
  applies, unchanged since Tier 3. Rather than claim this was attempted, or
  guess at a parser without being able to verify it, this is left exactly
  where it was. Status unchanged, not because it wasn't worth trying again,
  but because nothing about the underlying blocker changed between rounds.
- **Re-checked 2026-09-04 (Tier 6 pre-check):** directly tested
  `requests.get()` against the PDF URL from the sandbox. Confirmed the
  block is `x-deny-reason: host_not_allowed` -- this environment's own
  network egress allowlist, not a response from borsaistanbul.com. This is
  a structural limitation of the current tooling, not something a retry or
  a different query will change. **Deferred permanently** (i.e. until this
  environment's network access changes) rather than re-checked again every
  round -- repeating an unchanged structural block each round wastes effort
  without producing new information.

## XMUS — Muscat Securities Market (MSX, formerly MSM)

- **Checked:** searched for msx.om (the current domain, rebranded from
  msm.gov.om) holiday/trading-calendar pages
- **Finding:** no first-party holiday page was found within the search
  budget spent. This is NOT the same as "confirmed blocked" — it means the
  right page (if one exists) wasn't located, not that a located page failed
  verification.
- **Verdict:** NOT VERIFIED. Worth another, more targeted search pass in a
  future round rather than being carried forward indefinitely as "blocked."
- **Re-checked 2026-08-31 (Tier 5 "quick win" attempt):** searched again
  with a second, differently-worded query. Same result: only third-party
  aggregators (TradingHours.com, MarketHours.io, calendarlabs,
  globalexchangesdirectory) turned up, no first-party msx.om page. Two
  independent search attempts across two rounds have now failed to locate
  one — this either doesn't exist as a scrapable HTML/PDF resource, or
  needs a research approach beyond keyword search (e.g. browsing msx.om's
  own site navigation directly) to find. Still NOT VERIFIED, but the
  confidence that a page is simply "out there, unfound" should be lower
  after two misses than after one.
- **Resolved 2026-09-04 (Tier 6 pre-check):** rather than search again, this
  time navigated msx.om's own site chrome directly -- fetched the
  homepage, found "Exchange Events/Holidays" in the actual left-nav menu,
  and followed it to `msx.om/exchange-holidays.aspx`. That page IS real and
  IS the correct page, but its content area under the "Exchange Holidays"
  heading is empty in the raw HTML response -- populated client-side, same
  pattern as XBAH's "Official Holidays" page. **Verdict upgraded from "not
  verified" to confirmed BLOCKED** -- the two prior search misses weren't a
  search-quality problem, they were correctly finding nothing indexed
  because the actual content isn't in static HTML at all.

## XSGO — Santiago Stock Exchange (Bolsa de Santiago)

- **Checked:** bolsadesantiago.com/mercado_horarios_feriados directly
- **Finding:** confirmed pure JS SPA shell (rebranded "SANTIAGOX") -- raw
  HTML contains only meta tags and a Google Tag Manager script, zero
  content.
- **Verdict:** BLOCKED.

## XKLS — Bursa Malaysia

- **Checked:** bursamalaysia.com/about_bursa/about_us/calendar directly
- **Finding:** confirmed bot-walled -- "Site blocked the request (bot
  detection)" on direct fetch.
- **Verdict:** BLOCKED.

## XBOG — Bolsa de Valores de Colombia (BVC)

- **Checked:** two independent search attempts for a first-party bvc.com.co
  holiday/calendar page
- **Finding:** no first-party page found in either attempt -- only
  third-party aggregators and articles referencing "the BVC calendar"
  without linking a real source page. Note: "BVC" is also the ticker/
  abbreviation for the unrelated Caracas Stock Exchange (Bolsa de Valores
  de Caracas), which polluted several search results and made this harder
  to resolve than most.
- **Verdict:** BLOCKED (treated the same as two independent misses for
  XMUS were treated before its page was eventually found by browsing site
  navigation directly -- that approach wasn't attempted here due to time
  spent on the Caracas/Colombia naming collision).

## XLIM — Bolsa de Valores de Lima (BVL)

- **Checked:** found the real page (bvl.com.pe/mercado/resumen-mercado/
  feriados-y-horarios-de-negociacion) and fetched it directly
- **Finding:** confirmed pure JS SPA shell -- raw HTML contains only meta
  tags and a Google Tag Manager script, same pattern as XSGO.
- **Verdict:** BLOCKED.

## XPHS — Philippine Stock Exchange (PSE)

- **Checked:** found the real "Trading Hours & Holidays" section on
  pse.com.ph/investing-at-pse/ (an anchor-linked section, not a separate
  page -- the earlier attempt at edge.pse.com.ph/companyPage/
  marketCalendar.do had found a *different*, unrelated corporate-actions
  calendar by mistake)
- **Finding:** the "National & Special Holidays" table exists in the raw
  HTML with real column headers ("Date", "Holiday", "Year") but zero data
  rows, plus an unrendered template placeholder literally reading
  "hf:categories" in the header row -- confirming the table is populated
  by JavaScript/AJAX from a custom data source, not present in the static
  response.
- **Verdict:** BLOCKED.

## XBKK — Stock Exchange of Thailand (SET)

- **Checked:** SET's official holiday landing page (real, static, but
  itself contains no data, only links), its downloadable PDF calendar, and
  its "E-Calendar" HTML version
- **Finding:** both the PDF and the "E-Calendar" are AnyFlip flipbook
  publications (a page-flip magazine/catalog renderer) -- the E-Calendar's
  raw HTML confirmed this is paginated into per-page files
  (`files/basic-html/page1.html` through `page26.html`), the same
  render-as-image pattern that makes XSWX and XATH's PDFs unusable: no
  per-day text data extractable from a page-flip viewer.
- **Verdict:** BLOCKED.

## XSTC — Ho Chi Minh Stock Exchange (Vietnam)

- **Originally checked:** nothing in Tier 6. This exchange was in scope for
  Tier 6's resolution pass but was not reached before that round's time
  budget ran out.
- **Resolved 2026-09-06 (Tier 7):** searched for HOSE's official trading-
  holiday notice and found a real, clean, English-language, text-
  extractable PDF at `staticfile.hsx.vn`. Buildable. Built as
  `HOSEVietnamFetcher`. See `docs/fetcher_verification.md` for the parsing
  details (nested-parenthesis stripping, combined-event date pairs).
- **Verdict: BUILD** (no longer blocked/unverified).

## Tier 7 (Africa/South Asia) — 2026-09-06

Applied the accumulated 6-tier infrastructure model as a predictive filter
rather than deep-diving every exchange from scratch.

### XTUN — Bourse de Tunis (Tunisia)

- **Checked:** bvmt.com.tn/fr/content/jours-feries-de-2026 directly
- **Finding:** confirmed JS-rendered -- the fetch tool itself reported "no
  readable text... rendered with JavaScript."
- **Verdict:** BLOCKED.

### XCAS — Bourse de Casablanca (Morocco)

- **Checked:** casablanca-bourse.com/market-data/jours-feries directly
- **Finding:** the page is real and appears to have real structured content
  (fixed-date vs. mobile Hijri-date holiday sections, per the search
  snippet), but **robots.txt explicitly disallows automated access** --
  confirmed by the fetch tool itself refusing the request on that basis.
  This framework respects robots.txt by design (added in Tier 1); this is
  the first exchange blocked specifically by that check rather than by a
  technical limitation.
- **Verdict:** BLOCKED (by design, not by inability).

### XKAR — Pakistan Stock Exchange

- **Checked:** psx.com.pk's official "HOLIDAY CALENDAR - 2026" PDF directly
- **Finding:** the PDF returned no extractable text at all -- almost
  certainly a scanned-image or otherwise non-text-based PDF, the same
  fundamental category as XSWX/XATH's visual-grid PDFs even though the
  failure mode looked different at the fetch-tool level.
- **Verdict:** BLOCKED.

### XDHA — Dhaka Stock Exchange

- **Checked:** dsebd.org/hts.php ("Holidays and Trading Sessions") directly
  -- a real page confirmed to exist and to list "DSE will observe following
  Holidays during the Calendar Year 2026" in search results
- **Finding:** **robots.txt explicitly disallows automated access**, same
  as XCAS.
- **Verdict:** BLOCKED (by design, not by inability).

### XNBO — Nairobi Securities Exchange

- **Checked:** nse.co.ke's investor-calendar mechanism, which turned out to
  be a directory of individual LISTED COMPANIES' corporate-events PDFs
  (dividends, AGMs), not the exchange's own trading-holiday calendar. The
  correct page was not located within this round's time budget.
- **Verdict:** NOT VERIFIED -- genuinely open, not guessed at. A more
  targeted search (or direct site-navigation, the approach that worked for
  XMUS in Tier 6) is the likely next step.
- **Resolved 2026-09-06 (Tier 8):** checked 6 different nse.co.ke pages
  directly (homepage, investor calendar, events, investor news, press
  releases, mobile trading) -- every single one returned identical generic
  cookie-consent boilerplate text with zero page-specific content. This
  consistent pattern across 6 independent URLs is a decisive signal (not a
  single wrong-page miss) that nse.co.ke is a JS-rendered SPA where only
  the cookie banner renders server-side.
- **Verdict: BLOCKED** (confirmed, not left as "not verified").

### XGSE — Ghana Stock Exchange

- **Checked:** gse.com.gh and gsewebportal.com; confirmed an "Events &
  Holidays" nav item exists but no direct URL with actual holiday data was
  located within this round's budget.
- **Verdict:** NOT VERIFIED -- same caveat as XNBO.
- **Resolved 2026-09-06 (Tier 8):** fetched gse.com.gh's homepage directly
  (not via search) and found the exact nav link ("Events & Holidays" ->
  `gse.com.gh/events/`) in the real, static WordPress site's menu. That
  page has a real, static holiday table with names, alternate-date rows
  disambiguated by weekday, and Islamic holidays footnoted as
  moon-sighting-dependent.
- **Verdict: BUILD.** Built as `GhanaExchangeFetcher`.

## Tier 8 (small/island markets) — 2026-09-06 — FINAL TIER

### XBUL — Bulgarian Stock Exchange

- **Checked:** bse-sofia.bg's trading-calendar page directly (found via a
  targeted search after an initial generic search failed on an unrelated
  "BSE" naming collision)
- **Finding:** the page itself is real (a genuine dashboard with live
  market-data widgets, navigation, and rules links all present in the raw
  HTML), but the actual holiday calendar content was not present anywhere
  in the response -- only the surrounding page chrome and unrelated
  market-data widgets. This suggests the specific calendar widget is loaded
  dynamically within an otherwise mostly-static page.
- **Verdict:** BLOCKED.

### XBEK — Beirut Stock Exchange (Bourse de Beyrouth)

- **Checked:** bse.com.lb's official holidays page directly, twice
  (independent attempts)
- **Finding:** both attempts timed out (`Read timeout while fetching the
  URL`). This directly confirms the brief's own stated concern about this
  exchange specifically ("instability") -- not a speculative worry, an
  observed result.
- **Verdict:** BLOCKED.

### XNZE — New Zealand Exchange (NZX)

- **Checked:** the official NZX Market Holidays announcement page
  (nzx.com/announcements/443000), the PDF it references, and the
  trading-hours page mentioned in that PDF's own memo text
- **Finding:** all three failed differently. The announcement page's
  holiday content is a JS-loaded "Updating..." placeholder for an embedded
  attachment. The directly-referenced PDF URL 404'd. The trading-hours page
  URL from the memo's own text also 404'd. This directly contradicts the
  brief's assumption that New Zealand would be "likely simple" -- a good
  illustration that a well-documented, mature exchange doesn't necessarily
  mean an accessible one.
- **Verdict:** BLOCKED.
