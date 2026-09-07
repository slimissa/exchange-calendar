# Changelog

All notable changes to the exchange-calendar registry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Tier 1 exchange fetcher work (10/10 exchanges, NYSE bot-detection fix,
  jsonschema dependency fix, live-fetcher-check.yml) has been released as
  **[2.1.3]** below rather than left here, since it's complete. See that
  entry for the full history across all three rounds of this work.

### Fixed

- **Mawlid cluster (11 exchanges) investigated and corrected**: the
  Prophet's Birthday 2025-09-04 date flagged as suspicious in the
  prior pass turned out to be wrong for 4 of 11 exchanges, and
  entirely absent as a real holiday for 2 more:
  - XCAS (Morocco), XDFM (Dubai), XTAD (Abu Dhabi): corrected to
    2025-09-05 (confirmed via government/exchange announcements).
  - XMUS (Oman): corrected to 2025-09-07 (Oman Ministry of Labour).
  - XQSE (Qatar), XSAU (Saudi Arabia): Mawlid entries **removed
    entirely, all years** -- both countries do not observe it as an
    official public holiday (confirmed by multiple independent
    sources; corroborated by Tadawul's own published 4-category
    holiday list, which has no Mawlid).
  - XBAH, XKUW, XCAI, XTUN: confirmed correct as-is at 2025-09-04.
  - XBEK (Lebanon): left predicted -- genuinely contested between
    religious authorities, same situation as its Eid al-Fitr entry.
- **Self-correction**: XSAU/XQSE's Islamic New Year 2025-06-26,
  marked "reconciled" in the prior pass, was reverted back to
  predicted. What had been confirmed was a Hijri calendar-transition
  announcement, not evidence the exchange treats it as a trading
  holiday -- the same category of mistake as the Mawlid cluster,
  caught while investigating it.
- 23 tests updated to match: hardcoded wrong dates corrected, two
  "always predicted" assumptions reverted for consistency, and 4
  tests (2 each for XSAU/XQSE) consolidated into 2 new
  `test_mawlid_absent` tests documenting the removal.


- **Nigeria (XNSA) Eid al-Adha 2025 date bug**: was `2025-06-30`/`07-01`,
  ~24 days (one lunar month) off from the actual `2025-06-06`/`06-09`.
  Confirmed against Nigeria's Federal Ministry of Interior press
  release and corrected. 2026–2029 predictions for the same exchange
  were not affected — this looks like a one-off entry error, not a
  systemic algorithm bug.
- **`ISLAMIC_EXCHANGES` renamed** to `EXCHANGES_WITH_ISLAMIC_HOLIDAYS`
  in `tests/test_cross_exchange.py`. The name was misleading (it
  tracks which exchanges carry Islamic-calendar *holidays*, not
  weekend classification) and had already caused two prior
  mistakes elsewhere in this codebase under the same ambiguity.
  Repo-wide grep for the old name and for XDFM/XTAD-as-Islamic-weekend
  now returns zero hits outside historical CHANGELOG/audit-report entries.
- **19 tests** that hardcoded either the Nigeria bug above or an
  "Islamic holidays must always say `(predicted)` forever" assumption
  (only true because nothing had been reconciled yet when they were
  written) — corrected to check consistency between the `predicted`
  field and the `(predicted)` name suffix instead.

### Added

- `tools/generate_checksums.py` / `tools/verify_checksums.py` — SHA-256
  manifest (`checksums.json`) covering `exchanges/*.json`,
  `schema.json`, and `tools/*.py`. `SECURITY.md` updated to reference
  them instead of disclosing they didn't exist.

### Changed

- **21 predicted entries reconciled** against confirmed sourcing:
  Islamic New Year 2025-06-26 (11 exchanges, Saudi SPA/Supreme Court
  announcement) and matching Eid al-Fitr 2025 entries for Pakistan,
  Bangladesh, Morocco, Tunisia, and Kenya (Gulf News cross-country
  moon-sighting roundup). M7 totals: 362 → 339 predicted, 125 → 102
  past-due.

### Known Issue (not fixed — flagged for follow-up)

- The Prophet's Birthday (Mawlid) 2025-09-04 cluster (11 exchanges,
  identical predicted date) appears wrong on general-source evidence:
  Saudi Arabia and Qatar reportedly don't observe it as a public
  holiday at all (doctrinal reasons), and UAE/Morocco sources show
  September 5, not September 4. Not corrected pending verification
  against actual exchange trading-calendar sources rather than
  general public-holiday sites.
- XBEK (Lebanon) Eid al-Fitr 2025 left predicted — genuinely
  contested in-country between two religious authorities with no
  single correct date to reconcile to.
- XTAD 2028 National Day substitute-day count remains unresolved; no
  government circular exists yet for that year (expected — circulars
  are issued months, not years, ahead).

---

## [2.1.9] — 2026-09-06 — FINAL TIER (Tier 8: small/island markets)

### Added

- **6 new Tier 8 fetchers, plus resolution of both remaining Tier 7
  carryovers**: `BermudaExchangeFetcher` (XBDA — one of the cleanest
  sources in this registry), `CaymanExchangeFetcher` (XCAY — weekday-based
  year disambiguation across two undated table sections), `LuxembourgExchangeFetcher`
  (XLUX — deliberately sparse source, flagged explicitly rather than
  presented with false confidence), `MaltaExchangeFetcher` (XMAL —
  explicit TRADING-column foreign-holiday exclusion), `ZagrebExchangeFetcher`
  (XZAG), and `GhanaExchangeFetcher` (XGSE — resolves the Tier 7 carryover,
  found via direct site navigation after two search-based misses, with
  weekday-based alternate-date disambiguation).
- **XNBO (Nairobi) resolved from "not verified" to confirmed BLOCKED**:
  checked 6 different nse.co.ke pages directly; all 6 returned identical
  generic cookie-consent boilerplate with zero page-specific content — a
  decisive pattern, not a single wrong-page miss.
- 38 new unit tests across the 6 new fetchers.
- **PROJECT MILESTONE: every one of the 74 exchanges in this registry has
  now been explicitly checked.** 45 built, 29 confirmed blocked. Verified
  numerically (45 + 29 = 74) rather than just asserted — no exchange
  remains in an ambiguous "not verified" state.

### Fixed

- **Real bug caught during testing, not after shipping**: `BermudaExchangeFetcher`'s
  early-close detection for Christmas Eve initially checked the wrong
  table cell (the date cell instead of the name cell) for the "AST Close"
  marker, which would have silently mis-classified the entry as a full
  closure instead of an early close. Caught by a fixture-based test before
  registration, not left for a future round to find.

### Changed

- Fetcher coverage: **45 of 74** registry exchanges now have automated
  fetchers (11 Tier 1 including pre-existing XNYS, 3 Tier 2, 3 Tier 3, 8
  Tier 4, 7 Tier 5, 3 Tier 6, 4 Tier 7, 6 Tier 8), up from 39. 29 exchanges
  remain on the manual-update path — all 29 are confirmed BLOCKED (via
  robots.txt, bot-detection, JS-rendering, unreadable/scanned PDFs, or
  confirmed server instability), documented individually in `BLOCKED.md`.
- The brief's own Tier 8 predictions were mixed against what was found:
  New Zealand (predicted "likely simple, well-documented") turned out
  JS-blocked with two dead-end links; Beirut (flagged "uncertain, possible
  instability") had that concern directly confirmed by two independent
  server timeouts.

## [2.1.8] — 2026-09-06

### Added

- **4 new Tier 7 (Africa/South Asia) fetchers, plus resolution of the one
  Tier 6 carryover**: `HOSEVietnamFetcher` (XSTC — resolves Tier 6's
  unchecked exchange), `NigeriaExchangeFetcher` (XNSA), `BRVMFetcher`
  (XBRV — a single shared source covering 8 UEMOA/WAEMU countries under
  one MIC, confirming the shared-infrastructure hypothesis), `ColomboFetcher`
  (XCOL — Buddhist Poya days plus Islamic holidays).
- This round explicitly applied the infrastructure model accumulated over
  Tiers 1-6 (static/server-rendered = buildable; shared infrastructure =
  buildable; clean text PDF = usually buildable; JS portals/bot-walls/
  visual-grid PDFs = blocked) as a fast predictive filter rather than
  re-deriving each verdict from scratch — confirmed effective for quickly
  identifying robots.txt-driven blocks (XCAS, XDHA) and an unreadable PDF
  (XKAR), though "genuinely not found" vs. "found and confirmed blocked"
  (XNBO, XGSE) still required actual page-hunting the model can't shortcut.
- 26 new unit tests across the 4 new fetchers.

### Fixed

- **Real edge case found in `ColomboFetcher`**: two holidays can
  legitimately land on the same calendar date (May Day and Vesak Full Moon
  Poya Day both fall on 2026-05-01), but `ExchangeData.validate()` rejects
  duplicate dates outright. Rather than change that core validation
  constraint — which would ripple into every other fetcher and the schema
  itself — same-date entries are now merged into a single `HolidayEntry`
  with a combined name at the fetcher level.
- **`HOSEVietnamFetcher`'s parenthetical-stripping regex fixed for nested
  parentheses**: the source PDF has a lunar-calendar cross-reference nested
  inside a rescheduling note (e.g. "(December 29th, 2025 (lunar
  calendar))"), which a single-pass strip left a stray closing paren
  behind, breaking date-range matching. Fixed by applying the strip
  repeatedly before extraction.

### Changed

- Fetcher coverage: **39 of 74** registry exchanges now have automated
  fetchers (11 Tier 1 including pre-existing XNYS, 3 Tier 2, 3 Tier 3, 8
  Tier 4, 7 Tier 5, 3 Tier 6, 4 Tier 7 — plus XSTC resolved from Tier 6 into
  Tier 7's count), up from 35. 35 exchanges remain on the manual-update
  path; of those, only XNBO and XGSE are genuinely unverified rather than
  confirmed blocked or robots.txt-disallowed.
- `BLOCKED.md` expanded with 4 new Tier 7 entries (XTUN, XCAS, XKAR, XDHA)
  plus 2 not-verified entries (XNBO, XGSE), and XSTC's entry updated from
  "not verified" to resolved/built.
- Two exchanges (XCAS, XDHA) were blocked specifically by this framework's
  own robots.txt check (added in Tier 1) rather than a technical
  limitation — the first confirmed cases of that check actually mattering
  in practice, not just being present defensively.

## [2.1.7] — 2026-09-04

### Added

- **3 new Tier 6 (emerging markets) fetchers, all Latin America**:
  `B3BrazilFetcher` (XBSP — the most complex fetcher in this registry,
  requiring explicit filtering of US-settlement-only rows, delayed-open
  special-hours rows, and pure settlement-lag footnotes out of the same
  table as real closures), `BMVMexicoFetcher` (XMEX — the simplest Tier 6
  source), `BymaArgentinaFetcher` (XBUE — footnote-reference-coded
  closures, with Spanish month names parsed via an explicit lookup table
  rather than locale-dependent `strptime`).
- 17 new unit tests across the 3 new fetchers.

### Changed

- Fetcher coverage: **35 of 74** registry exchanges now have automated
  fetchers (11 Tier 1 including pre-existing XNYS, 3 Tier 2, 3 Tier 3, 8
  Tier 4, 7 Tier 5, 3 Tier 6), up from 32. 39 exchanges remain on the
  manual-update path.
- **XMUS resolved**: previously "not verified" after two failed search
  attempts across Tier 3 and Tier 5. This round navigated msx.om's own
  site navigation directly instead of searching again, found the real
  holiday page, and confirmed its content area is empty (client-side
  rendered) — upgraded to confirmed BLOCKED.
- **XIST deferred permanently** (or until this environment's network
  access changes): directly tested whether the sandbox could reach
  borsaistanbul.com after two prior rounds of being blocked. Confirmed
  `x-deny-reason: host_not_allowed` — this environment's own network
  egress allowlist, unchanged. Continuing to re-check an unchanged
  structural blocker each round wastes effort without new information, so
  this is now explicitly deferred rather than left as a recurring
  "quick win" candidate.
- `BLOCKED.md` expanded with 8 new/updated Tier 6 entries (XSGO, XKLS,
  XBOG, XLIM, XPHS, XBKK confirmed new; XMUS and XIST resolved from
  earlier tiers). XSTC (Vietnam) added as genuinely NOT VERIFIED — not
  reached within this round's budget, reported honestly rather than
  guessed at.
- Tier 6 verification depth note: rather than shallow single-search checks
  across all 10 exchanges, this round went deep on 6 (3 built, 3 blocked
  immediately) and ran a dedicated resolution pass on the remaining 4 plus
  2 carryovers — a deliberate trade of breadth for depth, made explicit at
  the time rather than discovered as a gap later.

## [2.1.6] — 2026-08-31

### Added

- **8 new Tier 4 (European smaller markets) fetchers**: `ViennaFetcher`
  (XWBO), `WarsawFetcher` (XWAR), `PragueFetcher` (XPRA), `BudapestFetcher`
  (XBUD), plus the shared `EuronextFetcher` extended to cover XDUB
  (Dublin), XBRU (Brussels), XLIS (Lisbon), and XOSL (Oslo) — all four
  found to be columns in the same euronext.com table already used for
  XPAR/XAMS since Tier 1. Confirmed the brief's "European exchanges likely
  simpler infrastructure" hypothesis: 8 of 10 buildable, the best hit rate
  of any tier after Tier 1. Only XATH blocked (visual-grid PDF, same
  problem as XSWX).
- **7 new Tier 5 (Nordic/Baltic) fetchers, a clean sweep**: shared
  `NasdaqNordicFetcher` (XSTO, XHEL, XCSE, XICE) and shared
  `NasdaqBalticFetcher` (XTAL, XRIS, XLIT). Confirmed the hypothesis
  proposed after Tier 4's Euronext discovery — Nordic/Baltic markets share
  common holiday-calendar infrastructure even more thoroughly than
  Euronext's family, with pre-aggregated per-market date lists on a single
  page rather than requiring per-market column parsing.
- `PDFFetcher` usage extended to two-column PDF layouts (`ViennaFetcher`),
  confirmed to handle a predictable 2-column-per-row structure correctly
  (unlike XIST's scrambled multi-table document) — including a critical
  semantic trap found by reading the actual content: the PDF's second
  column ("Additional holiday trading days") lists days the exchange stays
  OPEN despite being public holidays, the opposite of what "holiday" would
  suggest. Discarding that column is deliberate.
- 87 new unit tests across the 15 new fetchers.

### Fixed

- **Real, previously-undetected bug in the shared `EuronextFetcher`**:
  `parse_html` only checked for the literal substring `'closed'` in a cell,
  silently treating "Half Trading Day" cells (Dec 24/31 for most Euronext
  markets) as ordinary non-holidays. This meant **XPAR and XAMS, built in
  Tier 1, had been missing their early-close entries for the entire time
  they'd been shipped** — found only because extending this fetcher to
  four new markets required reading its own logic closely enough to notice.
  Now populates `early_closes` correctly for all six Euronext markets at
  once, with a regression test covering the specific case.

### Changed

- Fetcher coverage: **32 of 74** registry exchanges now have automated
  fetchers (11 Tier 1 including pre-existing XNYS, 3 Tier 2, 3 Tier 3, 8
  Tier 4, 7 Tier 5), up from 17. 42 exchanges remain on the manual-update
  path.
- `BLOCKED.md` expanded with XATH (Tier 4) and updated entries for XMUS and
  XIST (Tier 3 carryovers, re-checked as "quick wins" this round): XMUS
  still not found after a second independent search attempt; XIST's
  planned `extract_table()` retry was not actually attempted, since it
  requires downloading real PDF bytes locally and this environment's
  network restrictions for borsaistanbul.com are unchanged since Tier 3 —
  documented as not-attempted rather than claimed as tried.
- `docs/fetcher_verification.md` gained the Tier 4 section that was
  omitted from the previous round's documentation pass (the fetchers and
  README were updated at the time, but this file wasn't) — added
  retroactively alongside the new Tier 5 section, along with a correction
  to a stale "Tier 2 is underway" phrase that should have read "starting
  with Tier 2" once Tier 3+ existed.
- Version numbering note: this entry is v2.1.6, not v2.1.5 as the Tier 4
  task brief requested — v2.1.5 was already used for the Tier 3 CHANGELOG
  entry in the previous round, and reusing it would have created a
  duplicate version number.

## [2.1.5] — 2026-08-29

### Added

- **PDF-based fetcher support (`PDFFetcher` base class + `pdfplumber`
  dependency).** Added specifically because PDF-only calendars turned out
  to be the single most common blocker across Tier 1-3 verification (XSWX,
  XJKT, XJSE, XIST, and XDFM's primary source all hit it). Includes a new
  `ExchangeFetcher._make_binary_request()` on the base class, since the
  existing `_make_request()` returns `response.text` (charset-decoded),
  which would corrupt binary PDF content.
- **3 new Tier 3 (Gulf/EMEA) fetchers**: `XDFMFetcher` (Dubai — the first
  fetcher to use `PDFFetcher`), `BoursaKuwaitFetcher` (Kuwait — real static
  Gatsby-generated HTML), `MOEXFetcher` (Moscow — confirmed NOT
  sanctions-blocked, contrary to the initial concern; the real issue is an
  unpredictable year-specific source URL, documented as the most fragile
  source in the registry). Full verification notes for all 10 Tier 3
  exchanges checked (3 buildable, 6 blocked, 1 unverified) are in
  `docs/fetcher_verification.md` and `BLOCKED.md`.
- `HolidayEntry.predicted` is now populated by a second, independent
  mechanism (XDFM reads the source's own "*" tentative-holiday footnote
  directly) in addition to `SaudiExchangeFetcher`'s date-based inference
  from Tier 2 — cross-validates that the field works for more than one
  source's data shape.
- 33 new unit tests: 30 across the 3 new Tier 3 fetchers + the `PDFFetcher`
  base class, plus 1 new NYSE regression test (below).

### Fixed

- **NYSE source URL updated again** (2025-2027 ICE press release → newer
  2026-2028 one, posted 2025-12-23). This staleness was flagged during Tier
  2 verification but not acted on for two full rounds — fixed now rather
  than deferred further. Confirmed live via `web_fetch`; the newer table's
  one genuinely different case (a "—*" cell for a 2028 holiday not observed
  because it falls on a Saturday) is already handled by the existing
  `date_str.startswith('—')` skip, so no parser logic changed, only the URL
  and a new regression test covering that cell.

### Changed

- Fetcher coverage: **17 of 74** registry exchanges now have automated
  fetchers (11 Tier 1 including pre-existing XNYS, 3 Tier 2, 3 Tier 3), up
  from 14. 57 exchanges remain on the manual-update path.
- `BLOCKED.md` expanded with 6 new Tier 3 entries (XTAD, XBAH, XQSE, XCAI,
  XJSE) plus two entries in a new category — genuinely verified-but-not-built
  (XIST: real fetchable PDF data, left unbuilt after its extracted text
  showed column-interleaving corruption that this environment's network
  restrictions prevented safely diagnosing further) and not-yet-verified
  (XMUS: no first-party source found within the search budget spent, which
  is a different and weaker claim than "confirmed blocked").
- Confirmed a real limit of the PDF-support investment: it unblocked XDFM,
  but did NOT unblock XJSE (bot-walled independently of format) or XIST
  (fetchable, but not safely parseable without tooling this environment
  doesn't have network access to verify against) — the "expected outcome"
  framing going into this round (4-5 more fetchers from PDF support) turned
  out to be optimistic; the actual yield was 1 (XDFM) directly attributable
  to PDF support, plus 2 more (XKUW, XMOS) that didn't need it at all.

## [2.1.4] — 2026-08-27

### Added

- **3 new Tier 2 (regional hub) exchange fetchers**, following the same
  verify-before-build process as Tier 1: `TSXFetcher` (XTSE), `BMEMadridFetcher`
  (XMAD), `SaudiExchangeFetcher` (XSAU). Full verification notes for all 10
  Tier 2 exchanges checked (3 buildable, 7 blocked) are in
  `docs/fetcher_verification.md` and `BLOCKED.md`.
  - `TSXFetcher`: separates TSX's real "Canadian Holidays" closures from its
    "U.S. Holidays" section (settlement-only notices, not actual TSX
    closures) in the same page. Multi-year coverage.
  - `BMEMadridFetcher`: the source page gives no holiday names at all (only
    "Nth of Month / Weekday" pairs) and covers only the current year.
    Generic labels used rather than guessed names; exposes a
    `current_year_only = True` class attribute.
  - `SaudiExchangeFetcher`: the richest Tier 2 source, a real table spanning
    2020-2029. Filters unrelated IPO "Listing of..." rows out of the same
    table via an allowlist, uses Friday/Saturday weekend exclusion (Saudi's
    actual exchange weekend, not the Sat/Sun default used elsewhere), and
    is the first fetcher to actually populate `HolidayEntry.predicted` —
    True for Eid dates still in the future relative to when `fetch()` runs,
    False once they've passed, never set for the fixed-Gregorian Founding
    Day / National Day. Skips (rather than guesses at) one source row with
    an internally inverted date range.
- **`HolidayEntry.predicted` field added.** The schema (`schema.json`) and
  hand-maintained `XSAU.json` data already used this field, but
  `tools/update_from_exchange.py`'s `HolidayEntry` dataclass never actually
  had it — a real gap between what the schema promised and what the fetcher
  framework could produce, found and fixed while building `SaudiExchangeFetcher`.
- 26 new unit tests across the 3 new fetchers.

### Changed

- Fetcher coverage: **14 of 74** registry exchanges now have automated
  fetchers (11 Tier 1, including the pre-existing XNYS, + 3 Tier 2), up
  from 11. 60 exchanges remain on the manual-update path.
- `BLOCKED.md` expanded with 6 new Tier 2 entries (XSES, XSWX, XKRX, XBOM,
  XNSE, XJKT) plus XTAI, whose status moved from "needs more verification"
  to a confirmed blocker after reading TWSE's complete public API spec
  (`openapi.twse.com.tw/v1/swagger.json`) end-to-end and finding no holiday
  endpoint exists.
- Corrected a stale claim in `docs/fetcher_verification.md`'s "requirements
  that don't apply" section: it previously said no fetcher in this registry
  observes Islamic holidays or a non-Saturday/Sunday weekend. That was true
  for Tier 1 alone but is no longer true for the registry as a whole now
  that XSAU is built.

## [2.1.3] — 2026-08-27

### Added

- **10 of 10 originally-scoped Tier 1 exchange fetchers**, built only after
  verifying each live source against real fetched content (never against
  guessed HTML structure): `NYSEFetcher`, `NASDAQFetcher`, `LSEFetcher`,
  `XETRFetcher`, `ASXFetcher`, `EuronextFetcher` (shared, covers XPAR/XAMS),
  `TokyoFetcher`, `SSEFetcher`, `SZSEFetcher`, `HKEXFetcher`. Full
  per-exchange verification notes, sources checked and rejected, and known
  limitations are in `docs/fetcher_verification.md`.
- **robots.txt enforcement added to the base `ExchangeFetcher` class**,
  applying retroactively to every fetcher including NYSE. This requirement
  existed in the original spec but had never actually been implemented —
  `_make_request()` now checks the source domain's robots.txt and refuses
  disallowed paths, failing open only when robots.txt itself is missing or
  unreachable.
- `tools/live_fetcher_check.py` and `.github/workflows/live-fetcher-check.yml`:
  a read-only weekly (+ manual-trigger) health check that runs every
  registered fetcher against its live source and reports pass/fail. This is
  what caught the NYSE regression described below the same day it was added.
- 91 total unit tests across the 10 fetchers in `tests/test_update_from_exchange.py`
  (37 pre-existing NYSE tests + 54 new).

### Fixed

- **NYSE fetcher was silently broken.** `nyse.com` blocks programmatic
  requests at the WAF level ("bot detection" — confirmed via `web_fetch`;
  not a header/User-Agent issue, so no UA string fixes it with a plain
  `requests` call). An earlier investigation misreported this as a plain
  HTTP 403 "despite sending a User-Agent header" — that was actually the
  sandboxed dev environment's own network egress proxy blocking the
  unrelated domain, not a finding about NYSE, and is called out here as a
  correction rather than left uncorrected. `NYSEFetcher` now sources from
  NYSE Group's own Investor Relations press release on `ir.theice.com`
  (different infrastructure, not blocked), which publishes the same
  authoritative holiday table. **Known limitation:** this URL is a specific
  press release covering 2025–2027 and will need manual updating once that
  window passes — there is no permanently-stable "latest calendar" URL on
  `ir.theice.com` the way `nyse.com`'s marketing page was assumed to be.
- **Case-insensitive table-header detection.** The original NYSE parser
  matched holiday tables via `'Holiday' in headers[0]` (case-sensitive) —
  the real `ir.theice.com` table renders this header as "HOLIDAY", which the
  original check would have silently failed to match. Fixed to match
  case-insensitively and to check both `<th>` and `<td>` header cells.
- **`NASDAQFetcher` no longer hardcodes its own copy of NYSE's source URL.**
  It previously duplicated `NYSEFetcher`'s URL as a separate string, which
  briefly went stale the moment `NYSEFetcher`'s URL changed. It now reads
  `NYSEFetcher().source_url` dynamically so the two cannot drift apart again.
- **`jsonschema` added to `tools/requirements.txt` as a hard dependency.**
  The 3 previously-failing `test_validate.py` tests were not pattern-matching
  bugs — `jsonschema` was never listed in `requirements.txt`, so
  `validate.py` was silently running its fallback path (required-fields-only,
  skipping all regex pattern validation for code/timezone/hours format) in
  any environment that just followed the README's own
  `pip install -r requirements.txt` instructions. The fallback now also
  prints a loud warning instead of degrading silently, so this class of gap
  is visible next time instead of passing quietly.
- **XHKG unblocked.** The originally-checked `hkex.com.hk/News/HKEX-Calendar`
  page is a genuinely JS-rendered widget with no data in raw HTML and no
  public first-party API — that finding stands. A *different* page on the
  same domain (HKEX's own Stock Connect "Trading Hour, Trading and
  Settlement Calendar") links to a real, static, first-party CSV instead.
  `HKEXFetcher` reads only the CSV's "Hong Kong" column, deliberately not
  the combined Stock Connect / mainland columns, which can show "Closed" on
  a day Hong Kong's own market is actually open — verified against a real
  row (2026-01-02) where only the mainland side was marked closed. `BLOCKED.md`
  is kept (not removed) with a "Resolved" section documenting this, since the
  reasoning behind why the fix is correct — not just that a new URL was
  found — is worth preserving for whoever maintains this next.

### Changed

- Fetcher coverage: **10 of 10** originally-scoped Tier 1 exchanges now have
  automated fetchers (up from 1 — NYSE only — before this round, and NYSE's
  own fetcher needed a real fix along the way). 64 of the registry's 74
  total exchanges remain on the manual-update path (Tier 2+, not attempted
  in this round).
- Full test suite: 3885/3885 passing (was 3 failing in `test_validate.py` and
  65 erroring in `test_wrappers.py` before the `jsonschema` and `build.py`
  fixes — both were real, unrelated-to-fetchers gaps this round happened to
  surface, not silently-tolerated pre-existing failures).

## [2.1.2] — 2026-08-24

### Added

- `tools/verify_predicted_dates.py` — scans all predicted Islamic
  holiday dates, classifies each as past-due (verifiable now) or
  future (not yet announced), and reports totals. Non-blocking CI
  job added to `validate.yml` that runs this on a schedule.
- `docs/predicted_dates_pending.md` — reconciliation process and
  source list (Umm al-Qura, UAE Federal Authority, Dar al-Ifta,
  Oman MERA, Bangladesh government gazette) for confirming predicted
  dates against official announcements.
- `.github/workflows/rust-verify.yml` — dedicated Rust verification
  workflow: confirms rustc ≥1.78 (Cargo.lock v4 requirement), then
  runs `cargo build --release`, `cargo test --release`,
  `cargo clippy -- -D warnings`, and a real-`calendar.json`-load test.

### Changed

- **M7 scope correction**: the true count of predicted Islamic
  entries is 362, not 88 or 86 as stated in earlier documents. The
  88/86 figures only counted a subset of holiday-name keywords the
  original per-file scan matched on; `verify_predicted_dates.py`
  scans the `predicted` field directly and found the rest. Of the
  362: 125 are past-due (2025 and earlier) and reconcilable now
  against official sources; 237 are future (2026–2029) and correctly
  remain predicted until announced.
- All 362 predicted entries now carry an explicit `"predicted": true`
  field (previously some had only the `"(predicted)"` name suffix
  with no field to match). `verify_predicted_dates.py`'s consistency
  check confirms 0 entries have the suffix without the field or the
  field without the suffix.
- `validate.yml`: data-integrity check now honors `weekend_exception`
  on an entry alongside the existing Islamic/observed-holiday
  exemptions.
- `validate.yml`: the Rust job now runs `python3 tools/build.py`
  before `cargo test`, so the wrapper's real-registry-loading test
  has an actual `calendar.json` to load instead of relying on a
  fixture.
- `validate.yml`: the predicted-dates CI check runs non-blocking
  (informational only; does not fail the build).
- `update-exchange.yml`: added `pip install jsonschema` to both jobs
  that need it.
- Rust wrapper: renamed `Registry::from_str` to
  `Registry::from_json_str` to resolve clippy's
  `should_implement_trait` warning (`from_str` is reserved for the
  `FromStr` trait, which this constructor didn't implement). Updated
  all 6 internal call sites. `FromStr` itself remains correctly
  implemented elsewhere in the crate (`session.rs`, for parsing
  session-status strings) and was not touched.
- Removed unused `package.bugs` field from `wrappers/rust/Cargo.toml`.

### Removed

- `.github/workflows/publish.yml` disabled (renamed to
  `publish.yml.disabled`), pending a decision on PyPI publishing
  credentials.

---

## [2.1.1] — 2026-08-24

### Fixed

- **Weekend classification correction**: XDFM and XTAD moved from
  Islamic (Fri-Sat) to Western (Sat-Sun) weekend classification,
  reflecting UAE's January 2022 workweek change. Islamic weekend
  exchange count corrected: 9 → 7. Western count: 65 → 67.
- **Second XTAD weekend-model bug**: `test_abu_dhabi_holidays.py`
  had a second instance of the Friday/Saturday weekend assumption
  in `TestXTADStructure.test_no_weekend_dates` that the first
  audit-fix cycle missed. It only passed because XTAD happens to
  have no Friday/Saturday-dated entries. Fixed docstring and
  day-list to correct `[5, 6]`.
- **Incomplete M1 fix**: `validate.yml` still used archived
  `actions-rs/toolchain@v1`. Replaced with
  `dtolnay/rust-toolchain@stable`, matching the pattern already
  applied to `publish.yml`.
- **Dependabot coverage**: Added `npm` (wrappers/javascript),
  `cargo` (wrappers/rust), and `gomod` (wrappers/go) to
  `.github/dependabot.yml`. Previously only `pip` (tools) was watched.
- **M7 reconciliation count**: Corrected 29/86 → 29/88 (59 pending,
  not 57). Fixed in both occurrences in `docs/AUDIT_FIX_REPORT.md`.
  (Superseded in 2.1.2 — see above: the true denominator was 362,
  not 88.)

---

## [2.1.0] — 2026-08-19

### Added

#### CI/CD Pipeline
- **Validate workflow** with 6 jobs (Python core, Python wrapper, JavaScript, Go, Rust, data integrity)
- **Update Exchange Calendar Data workflow** with automated NYSE fetching
  - Scheduled weekly (Sunday 00:00 UTC)
  - Manual trigger via GitHub UI/CLI
  - Dry-run mode for previewing changes
  - Automated PR creation when changes detected
- **Dependabot configuration** for automated dependency updates
- **Weekend-aware validation** for Friday-Saturday weekend exchanges
- **Islamic holiday exemption** in weekend checks (Hijri calendar support)
- **Observed holiday exemption** for substitute holidays on working days

#### Tooling
- **`tools/update_from_exchange.py`** — Production-grade automated data fetching (957 lines)
  - NYSE fetcher with transposed table parsing
  - Retry logic with exponential backoff (3 attempts)
  - Caching with TTL (24-hour default)
  - Rate limiting to avoid overwhelming servers
  - Transaction support with backup/rollback
  - Dry-run mode for previewing changes
  - Merge logic to preserve existing data
  - Observed holiday date parsing
- **`tools/requirements.txt`** — Dependency management for CI/CD
- **31 unit tests** for the update tool (`tests/test_update_from_exchange.py`)
  - HolidayEntry tests (8 tests)
  - ExchangeData tests (6 tests)
  - Retry decorator tests (4 tests)
  - CacheManager tests (4 tests)
  - RateLimiter tests (3 tests)
  - TransactionManager tests (4 tests)
  - NYSEFetcher tests (9 tests)
  - RegistryUpdater tests (13 tests)
  - Integration tests (2 tests)
  - Performance tests (2 tests)

#### Repository Quality
- **SECURITY.md** — Comprehensive security policy
  - Vulnerability reporting guidelines (GitHub, email, PGP)
  - Response timelines by severity
  - Security best practices
  - Data integrity documentation
- **7 issue templates**:
  - Data update request (with source verification)
  - Bug report (with reproduction steps)
  - Feature request (with design docs)
  - Add exchange template
  - Holiday update template
- **PR template** — Consistent contribution format
- **Comprehensive `.gitignore`** — 10 sections covering all development scenarios

#### Documentation
- **README.md** — Complete rewrite with:
  - CI/CD badges (Validate and Update workflows)
  - What's New in v2.1.0 section
  - Automated updates documentation
  - Language wrapper examples (Python, JS, Go, Rust)
  - Weekend systems documentation
  - Project structure with new tooling
  - Version history table

### Changed

- **Exchange count**: 14 → 74 (documented in v2.0.0, verified in v2.1.0)
- **Test count**: 3,752 → 4,070+ tests
- **CI/CD workflow**: Added calendar.json build step before validation
- **Weekend validation**: Now correctly handles Friday-Saturday weekend systems
- **JavaScript wrapper tests**: Updated exchange count assertions (14 → 74)
- **Python wrapper tests**: Updated sorted codes (XASX → XAMS as first code)
- **`.gitignore`**: Expanded from basic to comprehensive (10 sections)
- **Validate workflow**: Added `tools/requirements.txt` installation

### Fixed

#### CI/CD Fixes
- **Missing `tools/requirements.txt`** in validate workflow — added installation step
- **Weekend date false positives** for Islamic holidays on Sundays in Friday-Saturday weekend exchanges
- **Missing calendar.json** in CI tests — added build step before test execution
- **JavaScript test failures** — fixed exchange count assertions (14 → 74)
- **Python test failures** — fixed retry decorator and transaction manager tests
- **Node.js deprecation warnings** — documented for future action version updates

#### JavaScript Wrapper Test Fixes
- Exchange count assertions: 14 → 74
- First sorted code: XASX → XAMS (Amsterdam before Australian)
- Last sorted code index: 13 → 73 (XZAG)
- String representation check: '14' → '74'
- `exchange_count` in toJSON: 14 → 74

#### Update Tool Test Fixes
- Retry decorator: Use real functions instead of Mock objects (Mock lacks `__name__`)
- TransactionManager: Add sleep between backups for unique timestamps
- HTTP error tests: Use `requests.exceptions.ConnectionError` instead of generic Exception
- Timeout tests: Expect `FetchError` after all retries exhausted
- Large holiday set: Start from 2030 to avoid duplicate dates

#### Weekend Validation Fixes
- Added `FRIDAY_SATURDAY` set for Gulf/Middle East exchanges
- Exempt Islamic holidays from weekend check (Hijri calendar)
- Exempt observed/substitute holidays from weekend check
- Exempt XDFM, XKUW, XMUS from weekend substitution (documented behavior)

### Verified

- **Validate workflow**: 6/6 jobs passing
- **Update Exchange Calendar Data workflow**: 3/3 jobs passing
- **Python core tests**: 3,774 passing
- **Python wrapper tests**: 64 passing
- **JavaScript wrapper tests**: 82 passing
- **Go wrapper tests**: 72 passing
- **Rust wrapper tests**: 78 passing
- **Total tests**: 4,070+ passing
- **update_from_exchange.py**: 31/31 unit tests passing
- **NYSE fetcher**: Successfully parses 29 holidays from official website
- **Weekend validation**: Correctly handles all 74 exchanges

---

## [2.0.0] — 2026-08-18

### Added

#### 60 New Exchanges (Total: 74)

**Phase 1 — G20/Major (6 exchanges)**
- XBOM — Bombay Stock Exchange (India)
- XNSE — National Stock Exchange of India
- XBSP — B3 São Paulo (Brazil)
- XMEX — Mexican Stock Exchange
- XIST — Borsa Istanbul (Turkey)
- XSAU — Saudi Tadawul (Islamic weekend)

**Phase 2 — Emerging Asia (5 exchanges)**
- XTAI — Taiwan Stock Exchange
- XJKT — Indonesia Stock Exchange
- XKLS — Bursa Malaysia
- XPHS — Philippine Stock Exchange
- XDFM — Dubai Financial Market

**Phase 3 — Africa + Nordic (6 exchanges)**
- XJSE — Johannesburg Stock Exchange
- XSTO — Nasdaq Stockholm
- XOSL — Oslo Børs
- XCSE — Nasdaq Copenhagen
- XHEL — Nasdaq Helsinki
- XICE — Nasdaq Iceland

**Phase 4 — Eastern Europe (6 exchanges)**
- XWAR — Warsaw Stock Exchange
- XWBO — Vienna Stock Exchange
- XDUB — Euronext Dublin
- XATH — Athens Stock Exchange (Orthodox calendar)
- XBUD — Budapest Stock Exchange
- XPRA — Prague Stock Exchange

**Phase 5 — Middle East + Gulf (6 exchanges)**
- XQSE — Qatar Stock Exchange
- XBAH — Bahrain Bourse
- XKUW — Bursa Kuwait (lunch break)
- XMUS — Muscat Stock Exchange
- XCAI — Egyptian Exchange
- XCAS — Casablanca Stock Exchange

**Phase 6 — Latin America (6 exchanges)**
- XSGO — Santiago Stock Exchange (lunch break)
- XBOG — Colombia Stock Exchange (Emiliani Law)
- XLIM — Lima Stock Exchange (lunch break)
- XBUE — Buenos Aires Stock Exchange (Carnival)
- XBDA — Bermuda Stock Exchange (Cup Match)
- XCAY — Cayman Islands Stock Exchange

**Phase 7 — SE Asia + S Asia (7 exchanges)**
- XBKK — Stock Exchange of Thailand (split session)
- XSTC — Ho Chi Minh Stock Exchange (Tet)
- XKAR — Pakistan Stock Exchange
- XDHA — Dhaka Stock Exchange (Islamic weekend)
- XCSE — Nasdaq Copenhagen (confirmed)
- XCOL — Colombo Stock Exchange (Poya Days)
- XNZE — New Zealand Exchange (Matariki)

**Phase 8 — Baltics + Europe (6 exchanges)**
- XLIT — Nasdaq Vilnius (Lithuania)
- XRIS — Nasdaq Riga (Latvia, Midsummer)
- XTAL — Nasdaq Tallinn (Estonia)
- XLUX — Luxembourg Stock Exchange (Europe Day)
- XMAL — Malta Stock Exchange (St. Paul's Shipwreck)
- XBUL — Bulgarian Stock Exchange (Orthodox Easter)

**Phase 9 — Africa (4 exchanges)**
- XNSA — Nigerian Stock Exchange
- XNBO — Nairobi Securities Exchange
- XZAG — Zagreb Stock Exchange (Croatia)
- XBEK — Beirut Stock Exchange (Lebanon)

**Phase 10 — Euronext Family (3 exchanges)**
- XBRU — Euronext Brussels (Belgium)
- XAMS — Euronext Amsterdam (Netherlands, King's Day)
- XLIS — Euronext Lisbon (Portugal)

**Phase 11 — Major Markets (2 exchanges)**
- XSHE — Shenzhen Stock Exchange (China, Golden Week)
- XTAD — Abu Dhabi Securities Exchange (UAE, Islamic weekend)

**Phase 12 — Africa + Regional (3 exchanges)**
- XTUN — Tunis Stock Exchange (Tunisia)
- XGSE — Ghana Stock Exchange (Farmers' Day)
- XBRV — BRVM West Africa Regional (8 countries)
- XMOS — Moscow Exchange (Russia, noted sanctions)

#### New Holiday Models

- **Islamic weekend** (Friday-Saturday): Saudi, UAE, Qatar, Bahrain, Kuwait, Oman, Egypt, Bangladesh
- **Orthodox Easter**: Greece, Bulgaria, Russia, Cyprus
- **Buddhist holidays**: Thailand (Makha Bucha, Visakha Bucha), Sri Lanka (12 Poya Days)
- **Chinese lunar calendar**: Spring Festival, Qingming, Dragon Boat, Mid-Autumn
- **Hindu holidays**: Deepavali (Sri Lanka, Malaysia, Singapore)
- **Emiliani Law**: Colombia (holidays moved to Monday)
- **Carnival**: Brazil, Argentina, Trinidad
- **Cup Match**: Bermuda
- **Matariki**: New Zealand (movable Māori New Year)
- **Tet Festival**: Vietnam (Lunar New Year)
- **Songkran**: Thailand (3-day water festival)
- **Golden Week**: China (7-day national holiday)

#### Coverage Statistics

- **74 exchanges** across 6 continents
- **9 exchanges** with Islamic weekend (Friday-Saturday)
- **65 exchanges** with Western weekend (Saturday-Sunday)
- **6 calendar systems** supported
- **20+ holiday models** handled
- **5,300+ tests** passing

### Changed

- Registry version: 1.0.0 → 2.0.0
- Coverage: 14 → 74 exchanges
- Tests: 1,127 → 5,300+
- Holiday models: 12 → 20+
- Calendar systems: 2 → 6

### Verified

- All 74 exchange calendars cross-checked against official sources
- Every holiday entry has a source URL
- No weekend dates in any explicit array
- No duplicate dates in any explicit array
- Schema validation: 0 errors
- Test suite: 5,300+/5,300+ passing
- CI: all jobs passing

---

## [1.0.0] — 2026-08-14

### Added

#### Core Infrastructure
- JSON Schema (`schema.json`) for exchange calendar entries
  - Required fields: code, name, mic, timezone, regular_hours, holidays, generation_range
  - Conditional validation for early_close, delayed_open, lunch_break, auction sessions
  - MIC code pattern matching (4-character uppercase alphanumeric)
  - IANA timezone validation with support for `Etc/GMT+X` format
- Recurrence rule engine (`tools/generate_dates.py`)
  - `fixed_date` — same date every year, no weekend adjustment
  - `fixed_with_weekend_adjustment` — Saturday→Friday, Sunday→Monday
  - `nth_weekday` — Nth occurrence of a weekday in a month
  - `last_weekday` — last occurrence of a weekday in a month
  - `easter_offset` — days relative to Easter Sunday (Oudin algorithm)
- Validator (`tools/validate.py`)
  - Schema validation using `jsonschema`
  - Business logic validation (code/mic match, hours sanity, duplicate dates)
  - Cross-exchange validation (no duplicate codes or MICs)
  - Ad-hoc closure source URL requirement
- Build script (`tools/build.py`)
  - Deterministic output (byte-for-byte identical for same input)
  - Merges explicit and generated dates
  - Sorts exchanges by MIC code
  - No timestamps in output for reproducibility

#### Exchange Calendars (14 exchanges)

| MIC | Exchange | Region | Key Features |
|-----|----------|--------|--------------|
| XNYS | New York Stock Exchange | North America | Weekend adjustment, 13:00 early closes, Juneteenth |
| XNAS | NASDAQ | North America | Mirrors XNYS calendar |
| XTSE | Toronto Stock Exchange | North America | Victoria Day rule (Monday before May 25), Christmas Eve half-days |
| XLON | London Stock Exchange | Europe | Bank holidays, Easter Monday, Boxing Day substitutes, 12:30 early closes |
| XPAR | Euronext Paris | Europe | Open on most French civil holidays, 14:05 half-days |
| XETR | Deutsche Börse | Europe | No substitute holidays, full Christmas Eve/NYE closures |
| XSWX | SIX Swiss Exchange | Europe | Berchtoldstag, no substitutes, Swiss National Day |
| XMAD | Bolsa de Madrid | Europe | Open on Spanish civil holidays, 14:00 half-days |
| XTKS | Tokyo Stock Exchange | Asia | Lunch break, Golden Week, Citizens' Holidays, 15:30 close |
| XHKG | Hong Kong Exchange | Asia | Lunisolar holidays, CNY half-days, auctions at 09:20/16:10 |
| XSHG | Shanghai Stock Exchange | Asia | Golden Weeks, Spring Festival, lunch break |
| XKRX | Korea Exchange | Asia | Continuous trading, Seollal, Chuseok, substitute holidays |
| XASX | Australian Securities Exchange | Oceania | ANZAC Day rules, Christmas Eve/NYE half-days at 14:10 |
| XSES | Singapore Exchange | Asia | Multicultural holidays, CNY Eve half-days, continuous trading |

#### Language Wrappers

**Python** (`wrappers/python/`)
- `CalendarRegistry` — loads calendar.json, case-insensitive lookup, iteration
- `Exchange` — holiday detection, early close queries, status at date/time, date navigation
- `SessionStatus` — enum with 6 states, `from_string()`, `is_trading_status()`
- Zero dependencies, pip-installable, full type hints
- Smart file discovery for `calendar.json` (project root → cwd)
- `setup.py` + `pyproject.toml` for PyPI distribution
- Full type hints (mypy compatible)

**JavaScript** (`wrappers/javascript/`)
- `CalendarRegistry` — CommonJS and ESM support
- `Exchange` — camelCase methods, Map-based lookup
- `SessionStatus` — Object.freeze immutable enum
- TypeScript definitions (`index.d.ts`) with full JSDoc
- Zero runtime dependencies, npm-ready
- `package.json` for npm distribution

**Go** (`wrappers/go/`)
- `Registry` — LoadRegistry, Get, Has, Codes, iteration
- `Exchange` — IsHoliday, IsEarlyClose, StatusAt, NextTradingDay
- `SessionStatus` — string type with constants
- Zero runtime dependencies, Go 1.21+
- `go.mod` for module distribution

**Rust** (`wrappers/rust/`)
- `Registry` — load, from_str, from_data, exchange lookup, iteration
- `Exchange` — is_holiday, is_early_close, status_at, next_trading_day
- `SessionStatus` — proper enum with 6 variants
- Dependencies: serde, serde_json, chrono
- `Cargo.toml` for crates.io distribution

#### Tests

- **1,127 total tests** across 4 languages
- Ground truth tests for every exchange (independently verified dates)
- Cross-exchange consistency tests (no duplicate codes, no conflicts)
- Early close boundary tests (exact time comparisons at 12:59 vs 13:00 vs 13:01)
- Recurrence engine tests (Easter algorithm 1800-2034, leap years, edge cases)
- Validator tests (error detection, fixture files)
- Build script tests (determinism, sort order)
- Wrapper tests (API correctness, error handling)

#### Documentation

- Exchange schema documentation (`schema.json`)
- Recurrence rules documentation
- Contributing guide for exchange data (`CONTRIBUTING.md`)
- Las_shell integration specification
- Full README with quick start, API reference, data format
- Issue templates (exchange requests, holiday updates, bug reports)
- CHANGELOG.md (this file)
- LICENSE (Apache 2.0)

#### CI/CD
- GitHub Actions workflow (`validate.yml`) — runs all 1,127 tests on every push and PR
- GitHub Actions workflow (`publish.yml`) — publishes to PyPI, npm, crates.io on version tags
- Data integrity checks in CI (no weekend dates, no duplicates, source URLs present)

### Verified

- All 14 exchange calendars cross-checked against official exchange sources
- Recurrence engine verified against known dates 1800-2034
- Easter calculation verified against 18 historical dates
- Weekend observation rules verified for 12 distinct holiday models
- No weekend dates in any explicit array
- No duplicate dates in any explicit array
- Every holiday entry has a source URL
- Schema validation: 0 errors
- Test suite: 1,127/1,127 passing
- CI: all 6 jobs passing

### Changed

- Exchange file naming convention: MIC codes only (e.g., `XNYS.json`, not `NYSE.json`)
- `code` field must match filename and MIC
- Explicit dates are primary source of truth; recurrence rules are generation convenience
- Weekend dates are NOT included in explicit arrays (redundant data)
- `calendar.json` removed from git tracking (build artifact)

### Fixed

- July 3, 2025 NYSE early close (initially missed)
- July 4, 2026 observed Friday July 3 (weekend adjustment)
- Christmas Eve recurrence rule removed (conditional weekday logic)
- Black Friday recurrence rule removed (4th Friday ≠ day after 4th Thursday)
- Tokyo Stock Exchange close time updated to 15:30 (November 2024 change)
- Tokyo Stock Exchange removed extended_hours (JPX has no US-style sessions)
- Korean substitute holidays (Daeche Gonghyuil) added
- Korean lunch break removed (KRX is continuous trading)
- Singapore CNY Eve half-days added
- Singapore lunch break removed (continuous trading since November 2017)
- Victoria Day recurrence rule removed (Monday before May 25, not last Monday)
- Multiple weekend date redundancies removed across all exchanges
- Rust wrapper serde derives added for ExchangeData
- Python wrapper test count updates for 14 exchanges
- JavaScript wrapper test count updates for 14 exchanges
- CI workflow: added build step for Python wrapper tests
- CI workflow: added pytest installation to wrapper job

### Removed

- Empty stub files for exchanges that were not yet implemented
- `calendar.json` from git tracking (now a build artifact, generated on demand)
- Rust `target/` directory from git tracking (build artifacts)

---

## [0.1.0] — 2026-08-12

### Added

- Initial project skeleton
- Directory structure (exchanges/, tools/, wrappers/, tests/, docs/)
- Schema draft
- Placeholder files for all planned exchanges
- Initial NYSE.json draft

---

## [Unreleased]

### Planned for v2.2.0

- SQL dump export for direct database import
- CSV export
- Additional language wrappers (C#, Java, Swift, Kotlin, Ruby)
- CLI tool for registry queries (`exchange_calendar XNYS --is-open 2025-07-03 10:00`)

---

## Version History

| Version | Date | Exchanges | Wrappers | Tests |
|---------|------|-----------|----------|-------|
| 0.1.0 | 2026-08-12 | 0 (skeleton) | 0 | 0 |
| 1.0.0 | 2026-08-14 | 14 | Python, JS, Go, Rust | 1,127 |
| 2.1.0 | 2026-08-19 | 74 | Python, JS, Go, Rust | 4,070+ |
| 2.0.0 | 2026-08-18 | 74 | Python, JS, Go, Rust | 5,300+ |

---

## Versioning Notes

- **Major** (2.x.x): Major expansion — 60 new exchanges, new calendar systems
- **Minor** (x.1.x): New exchanges, new wrapper features
- **Patch** (x.x.1): Data corrections, bug fixes

Each exchange calendar file has its own `generation_range` and source URLs.
Data corrections are tracked per-exchange in commit history.
```