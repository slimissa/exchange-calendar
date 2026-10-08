# Blocked / Not Automated

> **A finding in this file is a snapshot, not a permanent fact.**
> Every entry carries a `Last verified:` date. Sources change: a WAF
> is added or removed, a URL rotates, a PDF gains a text layer, a
> page is redesigned. Re-test before trusting an entry, especially
> one that has not been re-checked in six months.
>
> Four entries demonstrate the pattern. **XKRX** was RESOLVED on
> 2026-09-19 and BLOCKED again on 2026-10-01 (HTTP 200, HTML 403
> body). **XIST** was BLOCKED on 2026-09-04 with a note describing
> "four market-segment tables in one PDF with a US-holiday template
> error"; re-testing showed the site publishes four separate PDFs
> and the equity PDF contains only Turkish closures. **XBUD**
> blocked at v2.9.1 with in-window removals that resolved to a
> parser gap for Hungarian substitute Mondays. **XPHS** was
> marked RESOLVED on 2026-09-19 on the strength of a network-path probe;
> re-testing on 2026-10-04 found that robots.txt disallows the same
> path, and the verdict was corrected to BLOCKED (robots.txt).


**Summary of all 74 registry exchanges.** One row per exchange in
`exchanges/`; the sections below give the evidence for every row not
marked `built`.

- **built** — a calendar exists and no unresolved block is recorded.
  Four of these (XBUD, XDFM, XGSE, XSTC) have a section below because a
  fetcher exists and its health or one date needs tracking.
- **blocked** — the source cannot be fetched automatically (bot wall,
  dead URL, robots.txt, visual-grid PDF, no endpoint). The calendar
  itself is maintained by hand.
- **CI-unreachable** — reachable from a residential IP but not from CI;
  not a permanent block.
- **resolved** — was blocked, no longer is.

| Code | Exchange | State |
|------|----------|-------|
| DSMD | Qatar Stock Exchange | blocked |
| XAMS | Euronext Amsterdam | built |
| XASX | Australian Securities Exchange | built |
| XATH | Athens Stock Exchange | blocked |
| XBAH | Bahrain Bourse | blocked |
| XBDA | Bermuda Stock Exchange | built |
| XBEY | Beirut Stock Exchange | blocked |
| XBKK | Stock Exchange of Thailand | blocked |
| XBOG | Colombia Stock Exchange | blocked |
| XBOM | Bombay Stock Exchange | blocked |
| XBRU | Euronext Brussels | built |
| XBRV | BRVM (West Africa Regional Stock Exchange) | built |
| XBSP | B3 (São Paulo Stock Exchange) | built |
| XBUD | Budapest Stock Exchange | built |
| XBUE | Buenos Aires Stock Exchange | built |
| XBUL | Bulgarian Stock Exchange | blocked |
| XCAI | Egyptian Exchange | blocked |
| XCAS | Casablanca Stock Exchange | blocked |
| XCAY | Cayman Islands Stock Exchange | built |
| XCOL | Colombo Stock Exchange | built |
| XCSE | Nasdaq Copenhagen | built |
| XDFM | Dubai Financial Market | built |
| XDHA | Dhaka Stock Exchange | blocked |
| XDUB | Euronext Dublin | built |
| XETR | Deutsche Börse | built |
| XGSE | Ghana Stock Exchange | built |
| XHEL | Nasdaq Helsinki | built |
| XHKG | Hong Kong Exchange | resolved |
| XICE | Nasdaq Iceland | built |
| XIST | Borsa Istanbul | resolved |
| XJKT | Indonesia Stock Exchange | blocked |
| XJSE | Johannesburg Stock Exchange | blocked |
| XKAR | Pakistan Stock Exchange | blocked |
| XKLS | Bursa Malaysia | blocked |
| XKRX | Korea Exchange | blocked |
| XKUW | Bursa Kuwait | blocked |
| XLIM | Lima Stock Exchange | blocked |
| XLIS | Euronext Lisbon | built |
| XLIT | Nasdaq Vilnius | built |
| XLON | London Stock Exchange | built |
| XLUX | Luxembourg Stock Exchange | built |
| XMAD | Bolsa de Madrid | built |
| XMAL | Malta Stock Exchange | built |
| XMEX | Mexican Stock Exchange | built |
| XMOS | Moscow Exchange | built |
| XMUS | Muscat Stock Exchange | blocked |
| XNAI | Nairobi Securities Exchange | blocked |
| XNAS | NASDAQ | built |
| XNSA | Nigerian Stock Exchange | CI-unreachable |
| XNSE | National Stock Exchange of India | blocked |
| XNYS | New York Stock Exchange | built |
| XNZE | New Zealand Exchange | blocked |
| XOSL | Oslo Børs | built |
| XPAR | Euronext Paris | built |
| XPHS | Philippine Stock Exchange | blocked |
| XPRA | Prague Stock Exchange | built |
| XRIS | Nasdaq Riga | built |
| XSAU | Saudi Stock Exchange (Tadawul) | blocked |
| XSES | Singapore Exchange | blocked |
| XSGO | Santiago Stock Exchange | blocked |
| XSHE | Shenzhen Stock Exchange | built |
| XSHG | Shanghai Stock Exchange | CI-unreachable |
| XSTC | Ho Chi Minh Stock Exchange | built |
| XSTO | Nasdaq Stockholm | built |
| XSWX | SIX Swiss Exchange | blocked |
| XTAD | Abu Dhabi Securities Exchange | blocked |
| XTAI | Taiwan Stock Exchange | blocked |
| XTAL | Nasdaq Tallinn | built |
| XTKS | Tokyo Stock Exchange | built |
| XTSE | Toronto Stock Exchange | built |
| XTUN | Tunis Stock Exchange | blocked |
| XWAR | Warsaw Stock Exchange | built |
| XWBO | Vienna Stock Exchange | built |
| XZAG | Zagreb Stock Exchange | built |

**Last-verified dates.** Each section below carries a **Last verified**
line recording the date its verdict was last actually checked (fetched,
re-tested, or re-derived against a live source) — not merely the date
the section's prose was last edited for wording. It's added by whoever
does that verification work, drawn from the check itself (a live fetch,
a re-run of `live_fetcher_check.py`, a documented re-derivation) rather
than guessed. It should be updated any time a verdict is re-checked,
whether the verdict changes or not — a re-check that confirms the
existing verdict still bumps the date; a section that is only reworded
without re-testing the underlying source should not.

**Tier 2 (regional hubs) update 2026-08-27:** 7 of 10 Tier 2 exchanges
checked are blocked (XSES, XSWX, XKRX, XBOM, XNSE, XJKT, XTAI). Only XTSE,
XMAD, and XSAU were buildable.

**Tier 3 (Gulf/EMEA) update 2026-08-29:** 6 of 10 confirmed blocked (XTAD,
XBAH, DSMD, XCAI, XJSE, XIST), 1 unverified (XMUS), 3 buildable (XDFM,
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
1 by an unreadable PDF (XKAR), 1 by an empty page response (XTUN;
originally recorded as JS-rendered, see its section). 2 remain
genuinely unverified (XNAI, XGSE) rather than forced to a verdict.

**Tier 8 (small/island markets) update 2026-09-06 — FINAL TIER:** 5 of
the 8 Tier 8 exchanges were buildable (XBDA, XCAY, XLUX, XMAL, XZAG); 3
were confirmed blocked (XBUL, XBEY, XNZE). Two Tier 7 carryovers were also
resolved in this round: XGSE (built) and XNAI (confirmed blocked).
Combined count for the round: 6 built, 4 blocked. Notably, the brief's
own predictions for this tier were mixed: New Zealand was expected to be
simple and turned out JS-blocked; Beirut was flagged as uncertain due to
instability and that concern was directly confirmed (2 independent server
timeouts).

This file documents what was checked and why each verdict holds, since "we
found a different URL" or "it's blocked" is easy to state and easy to get
wrong without the reasoning behind it.

## XSES — Singapore Exchange (SGX)

**Last verified:** 2026-09-19

- **Checked:** sgx.com/trading and related pages
- **Finding:** JS-rendered shell. No first-party equities holiday HTML or
  CSV/JSON found — only a derivatives-specific trading circular PDF (a
  different market segment than the equities calendar this registry needs)
  and third-party aggregators, which are not authoritative.
- **Finding (2026-09-19):** Playwright Chromium receives HTTP 403 from both
  www.sgx.com/trading/trading-hours (308 bytes) and sgx.com/trading (294
  bytes); Akamai present in the network log. The block is at HTTP level,
  before any rendering; a headless browser does not bypass it.
- **Verdict:** BLOCKED (other: Akamai, HTTP 403).

## XSWX — SIX Swiss Exchange

**Last verified:** 2026-08-27

- **Checked:** six-group.com/en/market-data/news-tools/trading-currency-holiday-calendar.html
- **Finding:** the page itself is real and static, but its only calendar
  data is a PDF -- a visual calendar grid with no per-day text labels
  identifying which holiday falls on which greyed-out date. Parsing this
  reliably would require either OCR or a pixel-level heuristic against
  cell shading, neither of which this project's text-based framework does
  (or should attempt to guess at).
- **Verdict:** BLOCKED.

## XKRX — Korea Exchange (KRX)

**Last verified:** 2026-09-19

- **Checked:** global.krx.co.kr's "Market Closing(Holiday)" page
- **Finding:** confirmed JS/AJAX-driven data grid — a year dropdown
  (2016-2026) and a "Search"/"Download" button, but zero holiday rows in
  the raw HTML. No underlying public API endpoint was found within the time
  spent looking.
- **Finding (2026-09-19):** Both global.krx.co.kr candidates (the
  GLB0501110000.jsp page and the site root) timed out at 30 s in Playwright
  Chromium, with no HTTP status and no anti-bot service identified. The
  JS/AJAX data-grid finding above was not re-tested, so it stands.
- **Finding (2026-09-19, retest):** Retest with a 30 s wait and XHR logging
  found a JSON endpoint: POST
  https://global.krx.co.kr/contents/GLB/99/GLB99000001.jspx returns JSON whose
  block1[] rows carry calnd_dd and holdy_eng_nm for 2026, and plain requests
  (no browser) reaches it. This confirms the JS/AJAX data-grid finding above
  and supersedes the sweep timeout.
- **Finding (2026-10-01, regression):** the JSON endpoint now returns
  an HTML body whose title is "403 Page" (622 bytes, HTTP status 200).
  No `name="code"` token appears in the response. Attempted with both
  the registry's default UA and a full Chrome UA header set; both
  receive the same 403 body. The 2026-09-19 retest that reported
  "plain requests reach it" no longer holds from this environment.
- **Verdict:** BLOCKED (regressed). The endpoint exists and serves the
  same JSON shape when reached from a browser session, but a
  client-side WAF blocks non-browser requests from this vantage point.
  No fetcher can be written until either (a) the WAF rule is
  identified and the correct header set is faked, or (b) the source
  publishes an alternate endpoint. Re-test if the WAF configuration
  changes.

- **See:** docs/decisions/0009-playwright-fetcher-category.md for the decision that governs this class of block.

- **See:** docs/decisions/0010-render-mode.md for the render-mode decision that governs this block.

- **Finding (2026-10-04, ADR 0010):** marked permanent-block. Three
  browser mechanisms tested across v2.10.0 and v2.12.x — headless
  Chromium, headful via Xvfb — both fail with a server-side redirect
  to `COM/403.html`. Real Chrome untested but the delta is smaller
  than the headless-to-headful delta, which also failed. See
  `docs/decisions/0010-render-mode.md`.

## XATH — Athens Exchange

**Last verified:** 2026-10-04

- **Finding (2026-10-04, v2.12.3 reconnaissance):** athexgroup.gr
  redirects its trading-hours and calendar pages to
  `athens.euronext.com`, which returns 404 for the paths previously
  recorded here. Athens is a Euronext member (since 2023) but is NOT
  a column on the shared holidays page at
  `euronext.com/en/trading/trading-hours-holidays` — that table covers
  Amsterdam, Brussels, Dublin, Lisbon, Milan, Oslo, Paris only.
- **Finding (2026-10-04):** Athens publishes its calendar as a
  downloadable PDF from
  `athens.euronext.com/en/trade/trading-model/calendar`. The 2026
  PDF (Greek, `Euronext_Athens_Ημερολόγιο_Συναλλαγών_2026_v01.pdf`)
  and the 2025 PDF (English, `Trading_Calendar_2025_EN.pdf`) both
  extract as **visual calendar grids** — month names, weekday
  abbreviations, day numbers. Holidays are highlighted by cell fill
  color, not text. `pdfplumber.extract_text()` returns 2751 and
  1557 characters respectively, none of them holiday names or
  "Closed" markers. Extraction yields day numbers only.
- **Verdict:** BLOCKED (visual-grid PDF). This is the first
  confirmed member of the class ADR 0009 named. Parsing would
  require color/fill detection on the PDF cells, which is outside
  the current fetcher framework's scope. Permanent block.

## XBOM — BSE India (Bombay Stock Exchange)

**Last verified:** 2026-09-19

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
- **Finding (2026-09-19):** Playwright Chromium receives HTTP 403 from both
  bseindia.com URLs (331 and 327 bytes); Akamai present in the network log.
  The "holiday" match in the 403 body is the requested URL echoed back, not
  calendar content. Headless browser does not bypass.
- **Verdict:** BLOCKED (other: Akamai, HTTP 403).

## XNSE — National Stock Exchange of India (NSE)

**Last verified:** 2026-09-19

- **Checked:** nseindia.com/resources/exchange-communication-holidays
- **Finding:** the page itself loads (not bot-blocked), but the actual
  holiday table is populated via JS/AJAX behind "Select Product" and
  "Year" dropdowns -- the static HTML contains only a single hardcoded
  note about one specific 2026 date, not the table. NSE is also widely
  documented (across multiple open-source projects) as requiring a
  session-cookie handshake before its internal APIs will respond to plain
  HTTP requests, which this framework's `requests`-based approach doesn't
  perform.
- **Finding (2026-09-19):** Playwright Chromium receives HTTP 403 from both
  www.nseindia.com and nseindia.com (335 and 331 bytes); Akamai present in the
  network log. This differs from the 2026-08-27 note that the page loaded; the
  "holiday" matches are the requested URL echoed in the 403 body. Headless
  browser does not bypass.
- **Verdict:** BLOCKED (other: Akamai, HTTP 403).

## XJKT — Indonesia Stock Exchange (IDX)

**Last verified:** 2026-09-19

- **Checked:** idx.co.id's official static PDF announcement
  ("Peng-00171 Libur Bursa 2026")
- **Finding:** a real, first-party, government-adjacent PDF exists and is
  linked from IDX's own site — but the direct fetch request itself was
  bot-blocked, and even if it weren't, PDF parsing is out of scope for this
  `BeautifulSoup`-based HTML framework (same reasoning as XSWX).
- **Finding (2026-09-19):** Playwright Chromium receives HTTP 503 (1,240
  bytes) from www.idx.co.id/en/idx-trading-holidays and HTTP 403 (4,839 bytes)
  from idx.co.id; Cloudflare present in the network log. Headless browser does
  not bypass.
- **Verdict:** BLOCKED (Cloudflare, HTTP 503/403).

## XTAI — Taiwan Stock Exchange (TWSE)

**Last verified:** 2026-09-19

- **Checked:** twse.com.tw/en/trading/holiday.html (JS-rendered, confirmed
  no data in raw HTML) AND `openapi.twse.com.tw/v1` — TWSE's real, public,
  documented OpenAPI, fetched its full `swagger.json` spec directly and
  reviewed every listed endpoint (company governance, financials, indices,
  securities-firm data, trading reports, etc).
- **Finding:** **no holiday or trading-calendar endpoint exists in the
  public API.** Third-party MCP-server projects claiming "market calendar"
  support most likely scrape the same JS-rendered page rather than using a
  documented API endpoint, since none exists.
- **Finding (2026-09-19):** www.twse.com.tw/en/page/trading/exchange.html
  returns HTTP 200 but redirects to /page-not-found.html (698 bytes, no
  calendar terms), so that registry URL is dead. The Checked page was only
  tried at the apex twse.com.tw, which fails DNS (ERR_NAME_NOT_RESOLVED); the
  www variant was not tested. The no-API finding above is unaffected.
- **Verdict:** BLOCKED (dead URL: registry source_url redirects to page-not-found) —
  earlier note: this one moved from "needs more verification" to a confirmed
  blocker, not a resolved build.

## Resolved: XHKG — Hong Kong Exchanges and Clearing (HKEX)

**Last verified:** 2026-08-27

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

**Last verified:** 2026-09-19

- **Checked:** adx.ae/about-adx/media/adx-events-calendar
- **Finding:** confirmed Next.js JS-rendered SPA — the raw HTML contains
  only "Loading component..." placeholders, no static holiday data.
- **Finding (2026-09-19):** adx.ae/about-adx/media/adx-events-calendar returns
  HTTP 200 (241,246 bytes in the sweep, 240,197 in the probe, 101,032 bytes
  visible text) with no calendar terms in visible text; the sweep's raw
  "holiday" match is not in visible text. www.adx.ae/trading-calendar timed
  out at 30 s. Cloudflare and reCAPTCHA appear in the network log, but the
  same URL returned HTTP 403 in an earlier spike run, so Cloudflare behaviour
  is inconsistent. This is consistent with the placeholder finding above.
- **Finding (2026-09-19, retest):** The _next/data JSON files contain
  no holiday keys, so no holiday endpoint was found. The tool's
  recaptcha-challenge marker on the second URL matches ordinary reCAPTCHA form
  widgets and is not treated as a block.
- **Verdict:** BLOCKED (no holiday endpoint: _next/data files have no holiday keys).

## XBAH — Bahrain Bourse

**Last verified:** 2026-08-29

- **Checked:** bahrainbourse.com's "Official Holidays" page (real SharePoint
  site, not JS-rendered overall)
- **Finding:** the site itself is real and static, but this specific page's
  content area is empty in the raw HTML — populated by a client-side
  SharePoint webpart. Bahrain Bourse otherwise only announces holidays
  individually via one-off "Market Message" news posts, not a structured
  calendar.
- **Verdict:** BLOCKED.

## DSMD — Qatar Exchange

**Last verified:** 2026-09-19

- **Checked:** qe.com.qa/trading-calendar (original verdict 2026-08-27)
- **Finding (2026-09-17):** DNS no longer resolves for qe.com.qa —
  `Resolving timed out`. The 2026-08-27 verdict ("JS/AJAX-driven Liferay
  portal widget") assumed the domain was reachable; the domain appears
  to have moved or gone offline. Source URL cited by XQSE entries in
  the registry (`https://www.qe.com.qa/trading-calendar`) is dead.
- **Finding (2026-09-19):** www.qe.com.qa/trading-calendar returned HTTP 404
  (224,975 bytes, 108,797 bytes visible text, no calendar terms) in the
  2026-09-19 probe and timed out at 30 s (Cloudflare in the network log) in
  the sweep; apex qe.com.qa fails with ERR_CERT_COMMON_NAME_INVALID. The site
  answers, so the 2026-09-17 "DNS no longer resolves" finding does not hold
  from this network; the path is dead, not the domain. Also: 2 of the 36
  source_url citations in exchanges/DSMD.json point at www.ummulqura.org.sa,
  which is not a QSE source (the other 34 cite the dead qe.com.qa path).
  Fixing them is a separate task.
- **Verdict:** BLOCKED (dead URL: HTTP 404; site reachable).

## XCAI — Egyptian Exchange (EGX)

**Last verified:** 2026-10-07

- **Checked:** egx.com.eg/en/Trading_Calendar.aspx
- **Finding:** real, static, first-party HTML — but the page only serves
  **2019** holiday data, six years stale as of verification. Likely an
  ASP.NET WebForms postback-gated year selector (not a simple GET query
  parameter), which a plain `requests`-based fetcher can't drive without
  reverse-engineering the postback/viewstate mechanism. Building against
  stale data would be actively worse than no fetcher at all.
- **Verdict:** BLOCKED (data staleness, not inaccessibility).
- **Observance (2026-10-07):** the calendar is hand-maintained from EGX
  and government notices. National days use
  `fixed_with_thursday_observance` (see `docs/recurrence_rules.md`).
  Labour Day and Coptic Christmas use `fixed_date` plus explicit dates:
  both stay on their date midweek, and a Friday or Saturday date
  generates nothing because the real observance is set by notice.
  Sources: EGX notices via mondovisione.com (2025-07-24, 2025-07-03),
  Amwal Al Ghad (2025-04-24, 2025-10-09, 2022-01-06) and Arab Finance
  (2023-05-04); government decrees via cairo.gov.eg and arabfinance.com
  (2026-01-29, 2026-10-08, 2026-05-07). The EGX site itself could not be
  read from this environment, so each source is a mirror or press report
  of the notice, not the notice on egx.com.eg.
- **Citation tiers (`CONTRIBUTING.md`, "Citing Sources for Holiday Dates"):**
  2025-07-24 and 2025-07-03 are tier 2 (EGX notice reproduced on
  mondovisione.com). 2025-04-24, 2025-10-09, 2022-01-06 and 2023-05-04
  come from press reports quoting EGX (Amwal Al Ghad, Arab Finance): tier 3
  until the EGX disclosure is read. 2026-01-29, 2026-10-08 and 2026-05-07
  are tier 1 for the holiday (cabinet decree) and tier 3 for EGX's own
  closure. **Source needed for all of these:** the EGX disclosures on
  egx.com.eg, under its news and trading-calendar pages.
- **Coptic Christmas on a Friday (resolved 2026-10-07):** EGX and banks
  closed Thu 2022-01-06 for Fri 2022-01-07 and resumed Sun 2022-01-09
  (Amwal Al Ghad). The Saturday case went the other way: Sat 2023-01-07
  was observed Sun 2023-01-08 (Enterprise, quoting the EGX statement).
  The only Friday in range is 2028-01-07, entered as the predicted
  explicit date 2028-01-06. **Still open:** a decree can differ; the
  prediction is replaced when the cabinet decision is published.
- **Labour Day (2026-10-07, source check 2026-10-07):** it is moved by decree,
  not exempt. Mon 2023-05-01 was observed Thu 2023-05-04 (EGX disclosure of
  2023-05-02 via Arab Finance); Sat 2021-05-01 stayed on the Saturday; Fri
  2026-05-01 was replaced by Thu 2026-05-07 (PM decree, CBE notice).
  - **2026-05-07, EGX disclosure: not found.** `egx.com.eg/en/Trading_Calendar.aspx`
    was fetched and returned the 2019 table (cached copy). A search snippet of
    the live 2026 table shows nominal dates only, with Labor Day "May 01
    (Friday)" and "Date liable to change". What supports the entry: the PM decree
    (Arab Finance, cairo.gov.eg), the CBE bank-closure notice (Amwal Al Ghad)
    and one aggregator (market-holiday.com, "Labor Day (Obs)"). Tier: 1 for the
    holiday, 3 for EGX's closure. The entry stays. **Source needed:** the EGX
    disclosure for 2026-05-07 (query: the "Disclosures" or news list on
    egx.com.eg for 4 to 6 May 2026).
  - **2028-05-01 and 2029-05-01: option (b), predicted, nominal date.** Both
    entries are now `predicted: true` with the "(predicted)" suffix. A rule
    was not added because the precedents disagree: 2023 Monday went to the same
    week's Thursday, 2026 Friday went to the *following* week's Thursday, and the
    2026-09-30 report of the new Thursday policy says it excludes Labour Day. A
    shifted rule would only move a possible error to a different trading day.
    They are replaced when the cabinet decree is published (about a week
    before). **Source needed:** that decree and the EGX disclosure.
- **Extra evidence found 2026-10-07:** EGX's own 2019 calendar page notes
  "Holiday on 24/01/2019 instead of" Friday 25 January 2019, and "10/11/2019
  instead of" Saturday 9 November: a Friday holiday goes to the preceding
  Thursday and a Saturday one to the Sunday, in EGX's own words. A Global
  Exchanges repost of the EGX notice (globalexchanges.com, "EGX Publishes
  Holiday Notice") gives Thursday 2025-04-24 for Sinai Liberation Day and
  Thursday 2025-05-01 for Labour Day; it shows no notice date, so it stays
  tier 3.
- **June 30 Revolution Day (added 2026-10-07):** `fixed_with_thursday_observance`.
  EGX notice via mondovisione.com: Thu 2025-07-03 instead of Mon
  2025-06-30. Arab Finance (2026-06-25): EGX halted Thu 2026-07-02 instead
  of Tue 2026-06-30. Mubasher: the same move in 2020 (Tue 2020-06-30 to
  Thu 2020-07-02). In 2024 EGX closed on the Sunday itself, before the
  2025 policy, which is why the rule starts at 2025.

## XJSE — Johannesburg Stock Exchange (JSE)

**Last verified:** 2026-10-04

- **Checked:** jse.co.za and clientportal.jse.co.za Market Notice PDFs
- **Finding (2026-08-29):** expected to be one of the simpler Tier 3
  sources; instead, the PDF itself returned "Site blocked the request
  (bot detection)" on direct fetch.
- **Finding (2026-10-04, Playwright probe):** `page.goto` through
  headless Chromium returns HTTP 200 with the site's own HTML (402 KB),
  confirming Cloudflare's challenge is satisfied by a browser session.
  A one-level PDF scan from the homepage returned 137 links and one
  contact-list PDF. No holiday calendar URL surfaced.
- **Finding (2026-10-04, plain-HTTP re-probe, v2.12.5):** every URL
  returns 403 with the same 5017-byte Cloudflare challenge page:
  the homepage, `/robots.txt`, `/sitemap.xml`, `/sitemap_index.xml`,
  the four previously recorded paths, and fourteen additional
  candidates. `clientportal.jse.co.za` also returns 403 with a
  full Chrome UA and browser-like `Accept` headers. Nothing on the
  site is reachable from a plain HTTP client.
- **Verdict:** BLOCKED (permanent). The site is entirely behind
  Cloudflare for non-browser clients. The holiday calendar is
  published as a Market Notice PDF; no URL for it was enumerated by
  two discovery sessions (plain HTTP: fails at Cloudflare; one-level
  Playwright PDF scan: homepage loads, no PDF found).
- **Reopen condition:** a Playwright-driven **navigation walk** —
  following the site's own menu into the market notices or regulation
  section rather than scanning the homepage for direct PDF links.
  That is the one technique not yet tried. If it also fails, the
  source is documented as not publicly enumerable and the block is
  truly permanent.

- **See:** docs/decisions/0009-playwright-fetcher-category.md and
  docs/decisions/0010-render-mode.md for the decisions that govern
  this class of block.

## XICE — Nasdaq Iceland (built; rules added 2026-10-07)

**Last verified:** 2026-10-07

- **Added:** First Day of Summer (first Thursday after 18 April) and Commerce
  Day (first Monday in August), 2025 to 2029. The detector in
  `docs/task-20-holiday-rule-sweep.md` had flagged four missing dates.
- **Citation tier: 3, corroborated.** Nasdaq CSD Iceland's settlement calendar
  (states both rules and the closure) and LuxCSD's non-business-day lists for
  2025 and 2026 (name the four dates). Both are settlement calendars, not the
  exchange's own notice, so each is tier 3 under `CONTRIBUTING.md`. The
  exception in the tier 3 row applies: the two sources agree, and the Nasdaq CSD
  list matches every other date already in `exchanges/XICE.json`
  (Maundy Thursday, Good Friday, Easter Monday, Labour Day, Ascension, Whit
  Monday, 17 June, 24 to 26 December, 31 December).
- **Source needed:** the Nasdaq Nordic holiday schedule for Iceland (the
  existing `source_url` of the other entries is
  `nasdaqomxnordic.com/trading-hours`). Its holiday table did not render as
  text from this environment, and `nasdaq.com/european-market-activity/trading-hours`
  showed "Closed" cells without dates. Query: the Iceland column of "Exchange
  Holiday Schedule 2026".
- **Rule type:** First Day of Summer has no rule type (a Thursday in 19 to 25
  April), so it is explicit for all five years, as Victoria Day is for XTSE.
  Commerce Day has an `nth_weekday` rule and explicit entries.

## XIST — Borsa Istanbul

**Last verified:** 2026-10-01

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
- **Verdict (superseded 2026-10-01, see Resolution):** NOT BUILT. This is a genuine "verified accessible with real
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
- **Resolution 2026-10-01 (v2.9.0):** re-read the source with network
  access. The site publishes one PDF per market segment, not four tables
  in one file; the equity PDF is separate and lists only Turkish
  closures, so the US-holiday template error and the out-of-order dates
  described above did not apply to it. `XISTFetcher` was built on
  `pdfplumber.extract_text()` and registered, and `fetcher_manifest.json`
  carries its fetch. The 2026 confidence entry is `source: fetcher`,
  `level: high`, `last_verified: 2026-10-01`. The notes above are kept
  as history; the permanent deferral in the last bullet no longer holds.

## XMUS — Muscat Securities Market (MSX, formerly MSM)

**Last verified:** 2026-09-04

- **Checked:** searched for msx.om (the current domain, rebranded from
  msm.gov.om) holiday/trading-calendar pages
- **Finding:** no first-party holiday page was found within the search
  budget spent. This is NOT the same as "confirmed blocked" — it means the
  right page (if one exists) wasn't located, not that a located page failed
  verification.
- **Verdict (superseded 2026-09-04, see Resolved below):** NOT VERIFIED. Worth another, more targeted search pass in a
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

**Last verified:** 2026-09-19

- **Checked:** bolsadesantiago.com/mercado_horarios_feriados directly
- **Finding:** confirmed pure JS SPA shell (rebranded "SANTIAGOX") -- raw
  HTML contains only meta tags and a Google Tag Manager script, zero
  content.
- **Finding (2026-09-19):** www.bolsadesantiago.com/horarios returns HTTP 200
  with an 859-byte body; Cloudflare, hCaptcha and Perfdrive appear in the
  network log. The apex bolsadesantiago.com/mercado_horarios_feriados fails
  with ERR_CERT_COMMON_NAME_INVALID. Headless browser does not bypass; no
  CAPTCHA solving attempted.
- **Verdict:** BLOCKED (hCaptcha).

## XKLS — Bursa Malaysia

**Last verified:** 2026-09-04

- **Checked:** bursamalaysia.com/about_bursa/about_us/calendar directly
- **Finding:** confirmed bot-walled -- "Site blocked the request (bot
  detection)" on direct fetch.
- **Verdict:** BLOCKED.

## XBOG — Bolsa de Valores de Colombia (BVC)

**Last verified:** 2026-09-18

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
- **Re-checked 2026-09-17 (direct navigation, not search):** fetched
  `bvc.com.co`'s homepage directly. Unlike XMUS, there was no nav menu to
  follow -- the homepage itself is a Next.js client-side-rendered SPA shell,
  raw response containing only meta tags and a Google Tag Manager reference,
  zero server-rendered links or content. Same failure signature as XSGO and
  XLIM. Full evidence and a disclosed tooling limitation (this environment's
  sandbox cannot `curl` the domain directly; a different fetch tool with a
  broader network allowlist was used instead) in
  `docs/verifications/2026-09-17_xbog.md`.
- **Task 0, 2026-09-17: `exchanges/XBOG.json` audited and corrected.** The
  open issue above was investigated. Finding: the ~90 entries were
  hand-authored in a single 2026-08-18 commit, with no fetcher and no
  reachable page behind the `source_url` they all cited (confirmed above).
  Worse, independent of that citation problem, the data itself had real
  errors: three fixed, non-transferable holidays (Labour Day 2027, Christmas
  2027, New Year 2028) were wrongly Monday-shifted as if they were
  Emiliani-movable; three Emiliani-movable feast dates were shifted a week
  in the wrong direction (Saint Peter & Paul 2027, Ascension 2028, Corpus
  Christi 2028); and 2028's Corpus Christi / Sacred Heart were mislabeled
  and one was missing outright. Corrected all of these against an
  independently-implemented, Easter-date-validated reconstruction of
  Colombia's statutory holiday law (Ley 51 de 1983, "Ley Emiliani"),
  cross-checked against a reachable third-party source
  (rankia.co, matching all 18 of 2026's holidays exactly) and convergent
  Colombian press coverage of the 2025 official calendar. The 8
  Christmas-Eve/New-Year's-Eve early-close entries (claimed 11:30, never
  sourced) were removed rather than kept unverified -- one genuine piece of
  contrary evidence (a 2020 BVC announcement citing a different time) was
  found and no supporting evidence was. 95 entries -> 84. Full methodology,
  every diff, and the one real mistake I made and caught before committing
  (a first-pass fix that broke a genuine Colombian holiday-collision rule
  the original file had actually gotten right) are in
  `docs/verifications/2026-09-17_xbog_task0.md`.
- **Verdict: still BLOCKED for automated-fetcher purposes** — `bvc.com.co`
  is still unreachable, so there is still no `XBOGColombiaFetcher` and none
  is possible right now. But the manually-curated data in
  `exchanges/XBOG.json` is, as of 2026-09-17, verified as far as it's
  currently possible to verify it without a working first-party page --
  not merely "populated." Anyone re-blocking or re-populating this file
  in the future should read the Task 0 doc first; several of its findings
  (the fixed-vs-movable distinction, the 2025 collision rule) are easy to
  get wrong again from scratch.

## XLIM — Bolsa de Valores de Lima (BVL)

**Last verified:** 2026-09-19

- **Checked:** found the real page (bvl.com.pe/mercado/resumen-mercado/
  feriados-y-horarios-de-negociacion) and fetched it directly
- **Finding:** confirmed pure JS SPA shell -- raw HTML contains only meta
  tags and a Google Tag Manager script, same pattern as XSGO.
- **Finding (2026-09-19):** www.bvl.com.pe/calendario returns HTTP 200
  (149,967 bytes) with no calendar terms; Cloudflare and reCAPTCHA appear in
  the network log, and no challenge page was observed. The Checked page above
  was not successfully tested (apex bvl.com.pe fails DNS). reCAPTCHA presence
  alone does not show it gates the calendar.
- **Finding (2026-09-19, retest):** The only JSON endpoint flagged,
  stock-quote/home, is equities data, not holidays (a false positive of the
  tool's date+name key heuristic). The calendar page is an SPA and no holiday
  source is reachable in its network log.
- **Verdict:** BLOCKED (no holiday endpoint: SPA calendar page; the only JSON seen is equities data).

## XPHS — Philippine Stock Exchange (PSE)

**Last verified:** 2026-09-19

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
- **Finding (2026-09-19):** The sweep's pse.com.ph/trading-holidays/ returns
  HTTP 404 (156,901 bytes; Cloudflare and reCAPTCHA in the network log). The
  Checked page pse.com.ph/investing-at-pse/ loaded in an earlier Playwright
  run (HTTP 200, 528,057 bytes) with no Holiday/Eid/Ramadan/Arafat in visible
  text (the one raw hit was inside a <style> block); a retest timed out. The
  2026-09-04 finding above reported a "Holiday" column header in raw HTML,
  which this run did not reproduce.
- **Finding (2026-09-19, retest):** Retest found a JSON endpoint: POST
  https://www.pse.com.ph/wp-admin/admin-ajax.php returns JSON whose data[]
  entries carry cf:holiday_title, content (dates) and categories (years), and
  plain requests (no browser) reaches it. This is consistent with the
  2026-09-04 note of a table populated by AJAX, and supersedes the sweep's
  no-visible-content result.
- **Finding (2026-10-04):** an `XPHSFetcher` was attempted and reverted.
  The endpoint works from a plain HTTP client, but pse.com.ph's
  robots.txt disallows `/wp-admin/` for all User-agents, and the
  fetcher framework respects robots.txt (fail-closed when explicitly
  disallowed — the same reason XCAS and XDHA are blocked). The
  2026-09-19 note "plain requests (no browser) reaches it" was
  accurate about the *network path* but omitted the robots.txt check.
- **Verdict:** BLOCKED (robots.txt). Same class as XCAS and XDHA. Not
  worked around by design.

- **See:** docs/decisions/0009-playwright-fetcher-category.md for the decision that governs this class of block.

## XBKK — Stock Exchange of Thailand (SET)

**Last verified:** 2026-09-04

- **Finding (2026-10-04, v2.12.4 reconnaissance):** SET's current
  holiday page at `/en/about/event-calendar/holiday` links to two
  plain PDFs on `media.set.or.th` — not the AnyFlip flipbook the
  2026-09-04 note described. The site redesigned between the two
  observations.
- **Finding (2026-10-04):** the 2026 PDF (26 pages, 39725
  extractable characters) has a text layer, but the text is a
  **calendar grid**: month names in headers, day numbers in rows
  under a `SUNDAY MONDAY TUESDAY ...` column header, holiday names
  as separate text below each row. Nothing in the extracted text
  links a name to a date. `pdfplumber.extract_text()` returns the
  numerals and the labels as separate blocks; recovering the
  mapping requires word coordinates and column reconstruction,
  which `PDFFetcher` does not expose.
- **Verdict:** BLOCKED (visual-grid PDF). Second confirmed member
  of the class ADR 0009 named, alongside XATH. The source is not
  scanned, but its structure lives in cell position, not text.
  Reopening requires a grid-aware PDF parser that reads word
  coordinates — outside the framework's current scope. Permanent
  block.

## XSTC — Ho Chi Minh Stock Exchange (Vietnam)

**Last verified:** 2026-09-06

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

**Last verified:** 2026-09-06

Applied the accumulated 6-tier infrastructure model as a predictive filter
rather than deep-diving every exchange from scratch.

### XTUN — Bourse de Tunis (Tunisia)

**Last verified:** 2026-09-19

- **Checked:** bvmt.com.tn/fr/content/jours-feries-de-2026 directly
- **Finding:** confirmed JS-rendered -- the fetch tool itself reported "no
  readable text... rendered with JavaScript."
- **Finding (2026-09-19):** Both bvmt.com.tn candidates return HTTP 200 with a
  39-byte body after Playwright Chromium's 8 s wait; no anti-bot service in
  the network log and no calendar terms. The earlier "JS-rendered" observation
  is neither confirmed nor refuted by an empty response.
- **Finding (2026-09-19, retest):** With a 30 s wait and XHR logging,
  every URL tried returns a 39-byte body and no JSON endpoint appeared.
- **Verdict:** BLOCKED (empty response: 39-byte body on every URL tried).

### XCAS — Bourse de Casablanca (Morocco)

**Last verified:** 2026-09-06

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

**Last verified:** 2026-09-06

- **Checked:** psx.com.pk's official "HOLIDAY CALENDAR - 2026" PDF directly
- **Finding:** the PDF returned no extractable text at all -- almost
  certainly a scanned-image or otherwise non-text-based PDF, the same
  fundamental category as XSWX/XATH's visual-grid PDFs even though the
  failure mode looked different at the fetch-tool level.
- **Verdict:** BLOCKED.

### XDHA — Dhaka Stock Exchange

**Last verified:** 2026-09-06

- **Checked:** dsebd.org/hts.php ("Holidays and Trading Sessions") directly
  -- a real page confirmed to exist and to list "DSE will observe following
  Holidays during the Calendar Year 2026" in search results
- **Finding:** **robots.txt explicitly disallows automated access**, same
  as XCAS.
- **Verdict:** BLOCKED (by design, not by inability).

### XNAI — Nairobi Securities Exchange

**Last verified:** 2026-09-19

- **Checked:** nse.co.ke's investor-calendar mechanism, which turned out to
  be a directory of individual LISTED COMPANIES' corporate-events PDFs
  (dividends, AGMs), not the exchange's own trading-holiday calendar. The
  correct page was not located within this round's time budget.
- **Verdict (superseded 2026-09-06, see Resolved below):** NOT VERIFIED -- genuinely open, not guessed at. A more
  targeted search (or direct site-navigation, the approach that worked for
  XMUS in Tier 6) is the likely next step.
- **Resolved 2026-09-06 (Tier 8):** checked 6 different nse.co.ke pages
  directly (homepage, investor calendar, events, investor news, press
  releases, mobile trading) -- every single one returned identical generic
  cookie-consent boilerplate text with zero page-specific content. This
  consistent pattern across 6 independent URLs is a decisive signal (not a
  single wrong-page miss) that nse.co.ke is a JS-rendered SPA where only
  the cookie banner renders server-side.
- **Finding (2026-09-19):** www.nse.co.ke/trading-calendar and
  www.nse.co.ke/investor-relations/ both return HTTP 404 (174,568 and 174,596
  bytes; 96,178 bytes visible text on the second, no calendar terms).
  Cloudflare and reCAPTCHA appear in the network log but full pages are
  served, with no challenge page observed. The homepage returns 200 (334,434
  bytes) with a "holiday" match that was not inspected. The tested URLs are
  dead; the real calendar page, if any, was not located.
- **Verdict:** BLOCKED (dead URL: HTTP 404; calendar page not located).

### XGSE — Ghana Stock Exchange

**Last verified:** 2026-09-06

- **Checked:** gse.com.gh and gsewebportal.com; confirmed an "Events &
  Holidays" nav item exists but no direct URL with actual holiday data was
  located within this round's budget.
- **Verdict (superseded 2026-09-06, see Resolved below):** NOT VERIFIED -- same caveat as XNAI.
- **Resolved 2026-09-06 (Tier 8):** fetched gse.com.gh's homepage directly
  (not via search) and found the exact nav link ("Events & Holidays" ->
  `gse.com.gh/events/`) in the real, static WordPress site's menu. That
  page has a real, static holiday table with names, alternate-date rows
  disambiguated by weekday, and Islamic holidays footnoted as
  moon-sighting-dependent.
- **Verdict: BUILD.** Built as `GhanaExchangeFetcher`.

## Tier 8 (small/island markets) — 2026-09-06 — FINAL TIER

**Last verified:** 2026-09-17

**Tier 8 (small/island markets) update 2026-09-06 — FINAL TIER:** 5 of the
8 Tier 8 exchanges were buildable (XBDA, XCAY, XLUX, XMAL, XZAG); 3 were
confirmed blocked (XBUL, XBEY, XNZE). Two Tier 7 carryovers were also
resolved in this round: XGSE (built) and XNAI (confirmed blocked).
Combined count for the round: 6 built, 4 blocked.

### XBUL — Bulgarian Stock Exchange

**Last verified:** 2026-09-06

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

### XBEY — Beirut Stock Exchange (Bourse de Beyrouth)

**Last verified:** 2026-09-06

- **Checked:** bse.com.lb's official holidays page directly, twice
  (independent attempts)
- **Finding:** both attempts timed out (`Read timeout while fetching the
  URL`). This directly confirms the brief's own stated concern about this
  exchange specifically ("instability") -- not a speculative worry, an
  observed result.
- **Verdict:** BLOCKED.

### XNZE — New Zealand Exchange (NZX)

**Last verified:** 2026-09-06

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

## XKUW — Boursa Kuwait

**Last verified:** 2026-09-17

- **Checked:** boursakuwait.com.kw/en/securities/trading/market-holidays/
- **Finding:** HTTP 403 Forbidden from both GitHub Actions runners and
  residential IPs, with a browser User-Agent. The site's bot detection
  cannot be bypassed with header spoofing alone.
- **Verdict:** BLOCKED (HTTP 403 on 2026-09-17). One probe on one day;
  not shown to be permanent. `XKUW`'s fetcher stays registered and the
  informational job in `live-fetcher-check.yml` still exercises it.
  **Would unblock:** a 200 from `python tools/live_fetcher_check.py --only
  XKUW`. Only header changes are recorded as tried; a browser-grade
  render path (ADR 0009/0010) and a different egress have not been
  tried against this site. Until then the calendar is maintained by hand.

## XSAU — Saudi Exchange (Tadawul)

**Last verified:** 2026-09-17

- **Checked:** saudiexchange.sa/.../saudi-exchange-holiday-calendar
- **Finding:** HTTP 403 Forbidden from both GitHub Actions runners and
  residential IPs, with a browser User-Agent. Same pattern as XKUW.
- **Verdict:** BLOCKED (HTTP 403 on 2026-09-17). One probe on one day;
  not shown to be permanent. `SaudiExchangeFetcher` stays registered and
  the informational job in `live-fetcher-check.yml` still exercises it.
  **Would unblock:** a 200 from `python tools/live_fetcher_check.py --only
  XSAU`. Only header changes are recorded as tried (the fetcher already
  sends browser-like headers); a browser-grade render path (ADR 0009/0010)
  and a different egress have not been tried against this site. Until
  then the calendar is maintained by hand.

## XSHG — Shanghai Stock Exchange (CI-unreachable)

**Last verified:** 2026-09-17

- **Checked:** english.sse.com.cn/start/trading/schedule/
- **Finding:** HTTP 403 from GitHub Actions runners; HTTP 200 from
  residential IP with browser User-Agent. Same CDN IP-block pattern as
  XHKG. The source itself works.
- **Verdict:** CI-UNREACHABLE (not permanently blocked). No manual
  updates needed; works when run locally.

## XNSA — Nigerian Exchange Group (CI-unreachable)

**Last verified:** 2026-09-17

- **Checked:** ngxgroup.com/exchange/trade/becoming-an-investor/trading-holidays/
- **Finding:** fetches cleanly from residential IP (12 holidays, verified
  2026-09-17). Fails from GitHub Actions with `ParseError: No holidays
  found` — the page is behind Sucuri (`x-sucuri-id: 19017`), which serves
  a challenge body instead of the calendar to datacenter IP ranges.
- **Verdict:** CI-UNREACHABLE (not a parser bug, not permanently
  blocked). Works when run locally; only the scheduled CI check cannot
  reach it. A future maintainer seeing `ParseError` in a log should look
  here before touching `NigeriaExchangeFetcher`.

## XCOL — Colombo Stock Exchange (built; 2026 corrected 2026-10-07)

**Last verified:** 2026-10-07

- **2026 is now the exchange's own list.** CSE Circular No. 07-10-2025,
  "Colombo Stock Exchange Holidays for 2026" (22 October 2025), fetched from
  `cdn.cse.lk`: **tier 1**. All 17 closures on it are in the file, each with
  that URL as its source.
- **What was wrong.** Thirteen of the file's sixteen 2026 entries were not on
  the circular. Twelve were 2025's Poya dates repeated for 2026 (same month
  and day; Poya days move about eleven days a year) and one was an
  unsourced "Deepavali (observed)" on 2026-11-09. Fourteen closures on the
  circular were missing. All were fixed in one pass.
- **Open: Vesak week.** The circular lists an additional half holiday on
  Thu 2026-04-30 (in lieu of the day after Vesak Poya, which falls on a
  Saturday) and May Day on Fri 2026-05-01. CSE then issued Circular No.
  03-04-2026, "Holidays for 2026 - Amended" (20 April 2026), after the
  government moved the day after Vesak from 2 May to 31 May. Its text was
  not retrieved. **Source needed:** that circular, from the CSE circulars
  list on cse.lk. The half holiday has no entry until the hours are known.
- **Open: 2025.** The 2025 entries have not been checked against CSE's 2025
  circular. The detector flagged Duruthu Poya (file 2025-01-14, public
  holiday list 2025-01-13), Independence Day 2025-02-04, Maha Sivarathri
  2025-02-26, Eid al-Fitr 2025-03-31, Good Friday 2025-04-18 and Prophet's
  Birthday 2025-09-05. **Source needed:** the CSE circular of late 2024.
- **Open: 2027.** The 2027 Poya entries repeat 2025's dates in the same way
  and are almost certainly wrong. **Source needed:** the CSE circular for
  2027, normally issued in October. They stay until it exists.
- A calendar-aggregator page (calendarlabs.com) lists the same 2026 dates as
  the circular; it was not used as a source.

## XDFM — Dubai Financial Market (reconciled 2026-09-17)

**Last verified:** 2026-09-17

- **Checked:** dfm.ae annual holiday circular (original verdict 2026-08-29)
- **Finding (2026-09-17):** the year-specific circular PDF
  (`assets.dfm.ae/docs/.../circular-12-2025-trading-and-settlementholidays-...pdf`)
  returns 200 and parses cleanly with `pdfplumber`. Five past-due 2026
  entries (Eid al-Fitr, Eid al-Adha ×3, Prophet's Birthday) were
  confirmed and unmarked. One entry (Islamic New Year 2026-06-16) is
  not a DFM closure — removed. Three 2025 entries could not be
  confirmed because the circular covers 2026 only — removed.
- **Verdict:** RECONCILED for 2026. The 9 previously-predicted past-due
  entries are resolved. Fetcher remains active.

- **Finding (2026-10-03):** the DFM PDF omits 2026-12-01
  (Commemoration Day); the current file has it as a closure. The
  two sources disagree. The file is preserved; resolution needs a
  third source (prior-year DFM circular, or a UAE regulatory
  notice).
- **Status:** fetcher present, not authoritative for this date.
  The removal guard blocks refresh until the divergence is
  resolved.

## Past-due reconciliation — 2026-09-17

**Last verified:** 2026-09-17

Seven exchanges had their past-due predicted entries removed on
2026-09-17 because the source URLs cited in `exchanges/*.json` are
unreachable from any available IP (tests run from residential, browser
UA):

- **XCAS**: robots.txt disallows automated access
- **XDHA**: robots.txt disallows automated access
- **XKAR**: PDF has no extractable text (scanned image)
- **XKUW**: 403 from all IPs probed (see the XKUW section)
- **XBAH**: content area is a client-side SharePoint webpart

Entries were removed rather than left marked `predicted`. A `predicted`
entry with a past date is a silent-correctness bug — a caller reading
`is_holiday()` gets a confident answer for a date that was never
confirmed. Removing the entry makes the missing data explicit instead
of wrong.

- **Finding (2026-10-02):** the DFM PDF omits <date>. The current
  file has it as <name>. The two sources disagree; the file is
  preserved. Resolution requires a third source — DFM's own circular
  from the prior year, or a UAE regulatory notice.
- **Status:** fetcher present but not authoritative for this date.


## XBUD — Budapest Stock Exchange

**Last verified:** 2026-10-03

- **Finding (2026-10-03):** the BSE PDF resolution lists 12 trading
  holidays for 2026 but omits 2026-03-16 (National Day observed) and
  2026-12-28 (Boxing Day substitute). The current file carries both
  with `name` fields that say "(observed)" and "(substitute)". They
  are real closures under Hungarian labour law — March 15 and
  December 26, 2026 fall on a weekend and Hungarian law grants the
  Monday. The BSE resolution doesn't list them because the substitute
  is automatic.
- **Status:** fetcher present but incomplete. Resolution requires
  adding Hungarian observed-day logic to the parser. IMPLEMENTED
  at v2.9.3 (`BudapestFetcher._observed_substitutes`).
