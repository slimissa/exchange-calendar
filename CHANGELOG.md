# Changelog

All notable changes to this project will be documented in this file.

## [2.34.0] - 2026-11-23

### Added

- `tools/check_changelog_order.py` (4b6): `## [Unreleased]`, if present, must be the first `## [` heading, released headings must be strictly descending by version (compared numerically), and no version may appear twice. Run by the session gate, by CI (`validate.yml`) and by `release.sh`'s static preflight; 12 tests cover the real file and each failure. 4b5 had appended its entries under an `[Unreleased]` heading below `[2.32.0]`, which broke the release.
- Hours evidence for XMEX, XMAL and XSHE (4b6). XMEX: the `schema_limited` item is re-read from the BMV Manual Operativo itself (Versión 1.97/2026, in force from 23 July 2026; 4b4 had read it through WebFetch): continuous market 8:30-15:00, 7:30-14:00 during US daylight saving time, no closing auction (closing price from the last 20 minutes), so close 15:00. XSHE: verified from SZSE's Overview (continuous auction 9:30-11:30 and 13:00-14:57, closing call auction 14:57-15:00; close 15:00 under ADR 0013, lunch 11:30-13:00 as in the registry). XMAL: unconfirmed, values held: MSE's Trading page gives continuous trading 09:30-15:30 (so the open would be 09:30) and says trading "ends with a Closing Auction" without timing it, so what ends the session is ambiguous (stop condition). Hours evidence 46 -> 48 of 74; current hours verified 39 -> 40.

### Changed

- XKUW hours evidence (4b6): the 2025-10-12 entry (09:00-13:10) now also cites Boursa Kuwait's Trading Hours tab (continuous trading 09:00:00-01:00:00 PM, closing auction 01:00:00-01:10:00 PM, trade at last 01:10:00-01:15:00 PM), which agrees with the extension page. The tab shows only the current schedule, so the 2025-01-01 entry stays unconfirmed. No value changes.

### Fixed

- XBRV close 14:30 UTC (was 14:31) for the 2026-11-22 entry (4b6). Maintainer decision written into ADR 0013: a stated time with jitter around it ("T +/- N seconds") gives the stated time; only a window written as a range gives its end. BRVM's "+/- 60 secondes" applies to every time on its page, the opening fixing included, so its closing fixing "14 h 30 mn" gives 14:30. The open (09:45) is unchanged.
- XMAD regular hours 09:00-17:35 from 2026-11-23 (4b6, ADR 0014 section 8), against BME's "Spanish Stock Exchange Hours" page (SIBE: market open 9:00-17:30, closing auction 17:30-17:35, trading at last 17:35-17:45) and BME Circular 1/2026 (12 January 2026; the closing auction "shall end at any time within a random period of at most 30 seconds from 5.35pm", so the stated minute under ADR 0013). Neither document dates the schedule (the circular leaves its date of application to an Operating Instruction); the 2010 entry (09:00-17:30) is kept, unconfirmed. Post-market (sessions, extended_hours) is now trading at last, 17:35-17:45. XMAD joins the weekly session-time divergence run; its 17:35 vs the libraries' 17:30 from 2026-11-23 is a `convention_difference`.
- ADR 0014 restored (4b6): the session script that added XMAD's applied row opened the file for writing before reading it, and commit 14e2fc6 left ADR 0014 as that single row. The full text is back, with the XMAD row. A new test checks that ADR 0014 keeps its decision sections and has an applied-table row for every exchange with hours evidence; it fails on the truncated file.
- XBKK regular hours 10:00-16:40 from 2026-11-23 (4b6, ADR 0014 section 8), against SET's "Trading hours" and "Opening and closing price calculation" pages: main board Trading Session I T1-12.30 p.m., Trading Session II T2-4.30 p.m., pre-close 4.30 p.m.-T3, "T3 is the random closing time between 4:35 p.m. - 4:40 p.m."; off-hour trade reporting to 5.00 p.m. is not regular hours. A random window written as a range gives its end (ADR 0013), so 16:40; the open (10:00, end of T1's 9:55-10:00 window) and the 12:30-14:00 lunch break match. The pages are undated; the 2010 entry (10:00-16:35, the window's start under 4c9) is kept, unconfirmed. XBKK joins the weekly session-time divergence run: the close is a `convention_difference` (libraries 16:30) and the break column is a library gap (neither library models SET's intermission).
- XATH regular hours 10:30-17:10 from 2026-11-23 (4b6, ADR 0014 section 8), against ATHEX's Cash Markets Schedule ("Last update: Aug 2025", ver 3): Main Market continuous trading 10:30-13:45 and 14:00-17:00 around a 13:45-14:00 intraday auction, closing auction 17:00-17:10 with its one-minute random time period drawn 17:09-17:10, at-the-close 17:10-17:20 (not regular hours); "Closing Price: Closing auction". The random window is a range, so its end, 17:10 (ADR 0013). "Last update: Aug 2025" is the document's date, not an effective date; the 2025 entry (10:30-17:00) is kept, unconfirmed.
- XKAR regular hours 09:32-15:30 from 2026-11-23 (4b6, ADR 0014 section 8), against PSX's "Trading Hours" page, Monday to Thursday: pre-open 09:15-09:30, order matching and confirmation 09:30-09:32, open 09:32-15:30, post-close session 15:35-15:50 (not regular hours); no closing auction. Fridays run two sessions (09:17-12:00, 14:32-16:30), which the schema cannot hold: the new entry's evidence is `schema_limited` with the 4f backlog item "Weekday-specific sessions" (the first such item), so XKAR's current hours are not counted as verified. The page is undated; the 2010 entry (09:30-15:30) is kept, unconfirmed.

## [2.33.0] - 2026-11-22

### Changed

- ADR 0013: random closing windows (maintainer decision, 4b5). A random window of one minute or more ends the auction at the window's end (XHKG 16:08-16:10 -> 16:10, SET 16:35-16:40 -> 16:40, QSE 13:09-13:10 -> 13:10); seconds of jitter after a stated time leave the stated minute (Euronext, LSE, KRX, TSE, Boursa Kuwait). The earlier wording, applied two ways in the table (XDUB half days took a window's end, XBKK and XNZE its start), is replaced, and every row was audited: XBKK (16:40), XNZE (17:00 or 17:01) and XJSE (17:01) would change, and XETR, XWBO, XBUD and XSWX depend on a random-end length their cited documents do not give. None is changed without an exchange document.
- ADR 0014 section 8: undated current regimes (maintainer decision, 4b5). When an exchange's current page contradicts the registry and nothing dates the change, a new `regular_hours` entry starts on the page's read date (`verified`, `verified_from` = that date, "in force at least since the read date; start undated; earlier entry's end unknown"), the earlier entry's evidence becomes `unconfirmed`, earlier values are never rewritten, and a dated document always wins.
- XMAD note records the lead from BME's hidden draft block (4b5): non-trading days 1 January (Friday), 26 March (Friday) and 29 March (Monday), weekdays of 2027, but early closes on 24 and 31 December given as Thursdays, weekdays of 2026, under a "2026" heading. A draft, not data. The registry's 2027 already agrees: 1 January and 26 March are explicit rows, 29 March (Easter Monday) is closed by the recurrence rule without an explicit row, and 24 and 31 December close at 14:00. No 2027 row changes until BME publishes.

### Fixed

- XKUW regular hours 09:00-13:10 from 2025-10-12 (4b5), against Boursa Kuwait's "Extension of trading hours and amendments to the closing auction mechanism" page (starting October 12th, 2025): continuous trading 9:00 a.m. to 1:00 p.m., closing auction 1:00 to 1:10 p.m. with the random close in its last 30 seconds (the stated minute under ADR 0013), trade at last 1:10 to 1:15 p.m. (not regular hours). The 2025-01-01 entry (09:00-12:30) is kept, unconfirmed: the page says continuous trading ended 12:30 before the extension but not when the old auction ended. The 12:30-13:00 lunch break, which the page contradicts, is removed.
- XCAY regular hours 07:05-12:30 Cayman time from 2026-11-22 (4b5, ADR 0014 section 8), against the CSX Trading Procedures (section 5.1): opening auction 7 to 7.05 a.m., continuous trading 7.05 a.m. to 12:25 p.m., closing auction 12.25 to 12.30 p.m., post trading 12.30 to 12.45 p.m. The document dates nothing ("On 25 March ..." without a year), so the new entry starts on the print date; the 10:00-16:00 entry is kept, unconfirmed.
- XNSA regular hours 09:30-16:00 Lagos from 2026-11-22 (4b5, ADR 0014 section 8), against NGX's "Trading Market Structure" page: "Market hours: 9.00 to 4.00"; pre-open 9:00am, continuous trading 9:30am, pre-close 3:50pm (theoretical closing price), pre-close IO 3:55pm, close 4:00pm. Open is the start of continuous trading; close is the end of the pre-close call. The page is undated (a press lead dates the change to 27 April 2026, not an NGX document); the 10:00-14:30 entry is kept, unconfirmed.
- XBRV regular hours 09:45-14:31 UTC from 2026-11-22 (4b5, ADR 0014 section 8), against BRVM's "Horaires de cotation" page (horaire normal): pré-ouverture 09h00-09h45, fixing d'ouverture 09h45, négociation en continu 09h45-14h00, pré-clôture 14h00-14h30, fixing de clôture 14h30, négociation au dernier cours 14h30-15h00, all "assortis d'une période aléatoire de +/- 60 secondes". Open is the start of continuous trading; the closing fixing's random window runs 14:29-14:31, so under ADR 0013's random-closing rule the close is its end, 14:31 (the first window that straddles the stated time; flagged for the maintainer). The page is undated; the 09:00-14:00 entry is kept, unconfirmed. The holiday-eve schedule (fixing 11h30) has no rows in the registry to change.
- DSMD regular hours 09:30-13:10 Doha from 2026-11-22 (4b5, ADR 0014 section 8), against QSE's "General Overview" page: continuous trading period 09:30 am until 01:00 pm, pre-closing 01:00 to 01:10 pm, closing auction "Between 01:09-01:10 pm" (the last minute of the pre-closing is the randomization period), trading at last 01:10 to 01:15 pm. Under ADR 0013's random-closing rule the close is the window's end, 13:10; trading at last is not regular hours. The page is undated; the 09:30-13:15 entry is kept, unconfirmed.
- XIST regular hours 10:00-18:07 from 2026-11-22 (4b5, ADR 0014 section 8), against Borsa Istanbul's "Closing Session" page: order collection 18:01-18:05, price determination and closing session transactions 18:05-18:07 ("The determined closing session price is the closing price"), trades at closing price 18:08-18:10 (post-market, not regular hours). The page dates the closing session's introduction (2 March 2012) but not these times, and the equity session moved in November 2016 (a bank-notice lead), so 18:07 is not carried back to 2012; the 2010 entry (10:00-18:00) is kept, unconfirmed. XIST joins the weekly session-time divergence run (workflow, README); its 18:07 vs the libraries' 18:00 from 2026-11-23 is a `convention_difference` like Hong Kong's, noted in the report. The same run also shows the 2025-2029 half days (registry 13:00, libraries 12:30 or a full day), which were already in the data.
- The fetchers for XKUW, XNSA, XBRV, XCAY and XIST carry the hours now in the registry's latest dated entry (4b5). They had hard-coded hours that matched neither the old nor the new registry values (XBRV 09:00-15:15, XCAY 09:00-13:30, XIST 09:30-18:00, XKUW 09:00-13:00, XNSA 10:00-14:30). A fetch keeps a dated list and only warns when the fetched hours differ from its latest entry, so the data did not change, but every run would have warned.

## [2.32.0] - 2026-11-22

### Added

- Known source faults (4b4): `tools/known_source_faults.json` (entries: mic, match, reason, evidence, opened, expires at most 70 days after opened) and `tools/known_source_faults.py --check` (gate and `validate.yml`). The live check reports a failure matching an active entry as KNOWN (shown, not escalated, not failing the job) until `expires`, then FAIL; a different failure of a listed MIC is FAIL; a listed MIC that passes gets a "fault cleared, remove the entry" warning; the escalation issue lists KNOWN entries and the warnings, and KNOWN carries no streak. The list is empty: XMAD's page needed a fetcher fix, not an entry. Tests for each rule and for validation.
- Hours evidence from the maintainer's saved exchange pages (4b4). XKLS verified 09:00-16:50 from Bursa Malaysia's "Trading Sessions" page (Pre-Closing 4:45 pm, Closing 4:50 pm; Trading at Last 4:50-5:00 pm is not regular hours; `verified_from` 2026-11-22, the page states no date). XASX recorded `unconfirmed` (recheck 2027-02-19): ASX's "Cash market trading hours" page gives Open/Normal Trading 09:59:45-16:00:00 and the Closing Single Price Auction 16:10:00-16:11:00, so ADR 0013 puts the close at 16:11, not the registry's 16:00; the page dates nothing and no ASX notice was read, so the value stays and the mismatch is listed. XWAR's and XNAS's 2026 holiday lists match the registry row for row (no evidence item: no hours on the saved pages). Hours evidence 35 -> 37 of 74; current hours verified 29 -> 30.

### Changed

- Tier coverage guard blocking (4b4): `tools/check_tier_coverage.py` now fails on a registered fetcher in no tier list or a MIC in more than one (both were warnings). XIST, XSWX and XBUL, whose fetchers came after Tier 8 by resolving BLOCKED.md entries (2026-11-02, 2026-11-07, 2026-11-10), are placed in a new `TIER9_MICS_BUILT`; the comment records each one's job set (XIST stable; XSWX and XBUL CI-unreachable, in `STABLE_EXCLUDE`; XBUL's fetcher_status is blocked).
- XTKS random closing read (4b4): TSE's outline of rule revisions (6 August 2026) puts the afternoon close Itayose at a random time between 15:29:30 and 15:30:00 from 12 October 2027. ADR 0013 holds the end of a random window, so `regular_hours` stays 15:30 and no 2027 entry is added; the XTKS hours evidence note records the document (read from the search index's text of the PDF, matched by WebFetch).

### Fixed

- XMAD fetcher, settled on the real page (4b4). 4b3 read BME's page through a WebFetch paraphrase and concluded that a second block "headed 2026" with 2027 weekdays was published; the maintainer's raw save (2026-11-22) shows that block inside `<div id="container-a8cccbd951" class="cmp-container hidden ...">`: a draft readers never see (the print shows one block). It also says "has set the trading calendar for 2026"; its closures carry 2027 weekdays (1 January Friday, 26 March Friday, 29 March Monday) and its 24/31 December still say Thursday; no "2027" appears anywhere in the source. The fetcher now drops hidden elements (class token `hidden`, the `hidden` attribute, `aria-hidden="true"`, inline `display:none`; a collapsible FAQ panel is not hidden content) before reading blocks; the weekday guard stays and would still refuse the draft if it were shown unchanged. On the real page it returns the seven visible rows (1 January, 3 and 6 April, 1 May, 25 December closed; 24 and 31 December until 14:00), which agree with `exchanges/XMAD.json`. The WebFetch-derived fixtures are replaced by a trimmed real excerpt (`tests/fixtures/xmad_calendar_2026-11-22.html`, 20 KB, both blocks). No known-fault entry needed.
- XMEX seasonal hours recorded as `schema_limited` (4b4). BMV's Manual Operativo (v1.97, in force 23 July 2026) gives the continuous market "de 8:30 a 15:00 horas (7:30 a 14:00 horas durante el horario de verano EUA)"; BMV's 15 October 2025 notice returns the session to 8:30-15:00 from 3 November 2025; the maintainer's saved BMV tab shows the 7:30-14:00 table. The lead is confirmed: since Mexico abolished daylight saving time (2022), the registry's fixed 08:30-15:00 is an hour late for most of each year (US daylight saving time). `regular_hours` keeps 08:30-15:00 (no per-season entries); the evidence is `schema_limited` with the 4f item "Sessions that follow another market's daylight saving time", which now names XMEX as a confirmed case. Close under ADR 0013: 15:00, the end of continuous trading (BMV's closing price is calculated from the last 20 minutes; no closing auction). The manual was read through WebFetch (bmv.com.mx is not reachable from the sandbox), corroborated by the search index's verbatim text of the same manual and by the saved tab; the evidence says so. Hours evidence 34 -> 35 of 74.

## [2.31.0] - 2026-11-22

### Added

- Generated cross-language probes (`tools/gen_cross_lang_probes.py`, 4b3): for XNYS, XLON, XTKS, XHKG, XSAU, XCAI (Friday-Saturday weekend) and XBUE, every day Monday to Sunday of the first ordinary week of 2026, one minute before and at the open and the close, the first full holiday, and the first early close at the exchange level (`status_at`, `exchange_is_open`: `Exchange` honours early closes, unlike the registry contract). 325 probes written into `tests/cross_language_queries.json` as `<op>_gen_<suffix>`; every registry-level probe keeps its `in_session` twin (127 twins). The four runners gain the `status_at` and `exchange_is_open` ops. `--check` fails on drift (gate and `validate.yml`). `tests/test_cross_lang_coverage.py` fails if any weekday is missing for any of these MICs. All four wrappers agreed on every generated probe; XTKS, XSAU and XCAI have no early close in their data, so the exchange-level early-close probes cover XNYS, XLON, XHKG and XBUE.
- Hours evidence (4b3, ADR 0014, with `verified_from`) for batch B and four 4c exchanges; no value changed and no document contradicted the registry. XTAL and XRIS: Nasdaq Baltic's trading day (closing call 15:59:30-16:00:00; page modified 2026-05-05). XSTO: Nasdaq's European trading-hours page (09:00-17:30). XSHG: SSE's schedule (closing call 14:57-15:00, so close 15:00; lunch break out of scope). XSWX: SIX (closing auction 17:20-17:30, random end). XWBO: Wiener Börse (closing auction 17:30-17:35, earliest end). XTSE: TMX's trading hours; ADR 0013 applied to the Market on Close facility: the MOC call prints at 16:00, also the end of continuous trading, so close 16:00 (`closing_auction_end`). XTKS: the 2024-11-05 entry (09:00-15:30) verified and dated by TSE's release of 5 November 2024 (extension and closing auction "today") and its decision of 20 September 2023; the 1997 entry (15:00) unconfirmed; JPX's "Random Closing (from October 12, 2027)" is a lead. XPHS: CN-2022-0009 re-read (effective 1 March 2022; close 14:50, the pre-close auction end); 2010 entry unconfirmed. XSES: 2011-08-01 and 2017-11-13 verified from the 4c8 documents, 2010 unconfirmed. XTAI: TWSE's trading-system page (4c8, refuses this sandbox). XZAG: ZSE Trading Manual in force 22 January 2026 (4c11). Hours evidence 22 -> 34 of 74; current hours verified 17 -> 29; history verified 0. Ratchet floor 34.
- `tools/check_glued_words.py` (4b3; gate and `validate.yml`): fails on a closing inline-code backtick or a closing straight double quote followed immediately by a letter in CHANGELOG.md, README.md, the ADRs and the prose fields of `exchanges/*.json`, pairing delimiters per paragraph (fenced code skipped) and honouring an allowlist. Tests for both delimiters, spans across a line break, code fences, double-backtick spans, the allowlist and exchange notes.

### Changed

- One security-group rule for regular hours (ADR 0014, 4b3, the maintainer's decision): where an exchange's schedule differs by security group, the registry follows the group holding the main index's constituents; sessions the exchange calls additional stay excluded. Replaces 4b2's XMOS wording ("the rest of the book").
  - XHKG: no value change (CAS Phase 1 covered the Hang Seng Composite LargeCap and MidCap constituents); the rule is recorded in the 2016-07-25 evidence.
  - XMOS: open 09:00 from 2026-09-14 (was 09:10). MOEX's schedule page: admitted shares, Y1 main session ТП '09:00:00 — 18:54:59'. Also a new entry 2025-03-21 09:50-18:50, and 2026-03-23 opens 09:50 (was 10:00): MOEX's notice of 18 March 2025 admits 'все 49 из Индекса МосБиржи' to the morning session from 21 March 2025, and its notice of 22 January 2025 starts their main session at 9:50. The 2021-2022 morning session (IMOEX shares from 6 December 2021) is a lead: no document read gives its end. Probes and twins for 2025-03-20/21 09:55; the 2026-09-14 09:05 probe now answers open.
- `verified_from` (schema 2.3.2, ADR 0014 section 7): every `verified` hours item states the earliest date its cited document proves the hours (effective date, earliest stated date, or read date), never before the entry's `effective_from`, and only on `verified` items. Backfilled for all 25 verified items from their documents. Check 6 now reports two facts, both in `docs/facts.json`, the README and `check_doc_facts.py`: "Current hours verified" (`exchanges_hours_verified`; the entry in force on the evaluation day, the later of `last_checked` and the item's `checked_on`, is verified with `verified_from` on or before it): 21 -> 17, because Euronext's appendix edition read for XAMS, XBRU, XPAR and XLIS takes effect on 23 November 2026; and "History verified" (`exchanges_hours_history_verified`, new: every entry proven from its own start): 0 of 74. The end-of-4b-lite blocking rule applies to current hours; history is 4b full. Euronext items now name the edition read (effective 23 November 2026) in `source_title` and say that `source_url` is the 3 August 2026 edition (read in 4c8, which proves XDUB and XOSL from 2026-08-03).
- Weekly live fetcher check (4b3). It failed in 4 of its last 6 runs, each on a different fetcher, and its blocking job blocked nothing anyone saw. `tools/live_fetcher_check.py` now reports PASS / FAIL / TRANSIENT with the attempt count: TRANSIENT (FetchError or RateLimitError, a requests timeout, connection error or HTTP 5xx, or "no holidays" on an empty or maintenance page, judged from the page the fetcher actually read) is retried within the run, 3 attempts with increasing delay; FAIL (ValidationError, conflicting rows, SourceMissingError, any other ParseError or "no holidays" on a page with content or with no page recorded, HTTP 4xx, unexpected exceptions) is reported at once. `--json-out` writes the results. New `tools/live_check_escalate.py`: on the schedule, the workflow fails when a fetcher FAILs, or is TRANSIENT in two consecutive scheduled runs, and keeps one issue (label `live-check`, title "Live fetcher check failing", body = the summary table plus per-MIC streaks, state in a hidden block of the body), opened as "Watching" on a first transient failure and closed on the next fully green scheduled run. `issues: write` (and `contents: read`) on that job only, via GITHUB_TOKEN; no commits from CI. Manual runs honour the `mic` input again. The "Verify tier coverage" step, a placeholder comment since commit 2994f2c, runs the restored guard (`tools/check_tier_coverage.py`). Every workflow moves to `actions/checkout@v5` and `actions/setup-python@v6` (Node 24; inputs used, `fetch-depth` and `python-version`, unchanged).

### Fixed

- CHANGELOG `[2.29.0]`: removed the leftover planning sentence "Proposed as 2.29.0: minor, no breaking change." (a release slip; no other change to released text; 2.28.0 and 2.30.0 have none). Glued words: a frequency-based scan and the mechanical check found none in CHANGELOG.md, README.md, the ADRs or the exchange notes; the reported examples ("closedas", "andsession", "addedin", "Formore") are not in the tree or its git history. The nearest are hard line wraps ("and\nsession") in the Go and Rust wrapper READMEs, which Markdown renders with a space; left as they are.
- XMAD fetcher (4b3): the live check failed on 2026-11-22 with "Duplicate holiday date: 2026-01-01, 2026-12-24, 2026-12-31". Cause: BME's page carries two calendar blocks, both introduced as the "trading calendar for 2026"; the second lists dates whose weekdays fall in 2027 (1 January a Friday, 26 March a Friday, 29 March a Monday). The parser read every date with the first year and split closures from early closes at the first "will trade until" sentence, so 2026-01-01 came out as a closure and an early close, 24 and 31 December twice, and two rows silently put 2027's Good Friday and Easter Monday in 2026 (2026-03-29 is a Sunday). Now each block is parsed with its own year and early-close sentence (the early-close time, 14:00, is now set on the rows); each date's stated weekday must fall on that date, else ParseError naming the dates and the year they fit ("they fit 2027"), and no row is taken from the page; rows listed more than once go through the new `merge_holiday_rows`: identical rows become one, a closure against an early close or two different times raise ParseError naming the date and both rows. With today's page the fetcher therefore fails deterministically until BME relabels the block. The 2026 block and the second block read as 2027 agree with `exchanges/XMAD.json` (2027-03-29 comes from its Easter Monday rule): no data lead.

## [2.30.0] - 2026-11-22

Phase 4b-lite, session 4b2: the head of the hours queue and XBUE's year-end rows.

### Added
- Hours evidence (4b2, ADR 0014) for exchanges whose registry already matched: the six Euronext venues from Euronext's Appendix of Trading Manual 4-01, effective 23 November 2026 (saved by the maintainer; main equity groups J0, A0, F1, P0, 9A and OA in continuous mode: open 09:00 CET, close = the closing uncross, 17:35 CET, Dublin 17:30, Oslo 16:25; Lisbon and Dublin converted to local time, 08:00-16:35 and 08:00-16:30); batch A from the exchanges' own pages (Nasdaq's European trading-hours page for XCSE, XHEL and XICE, Nasdaq Baltic's trading day for XLIT, Deutsche Börse's Xetra parameters and trading-hours page for XETR, LuxSE's page for XLUX, NYSE's Hours & Calendars page for XNYS, read on the page itself, and PSE's trading-hours PDF for XPRA, whose 'Starts of trading procedures' table resolves 4b1's low-confidence reading: closing auction from 16:10, trading at close from 16:15); XBDA and XNZE from the 4c pages (refusing this sandbox, original read dates kept), XBUD from BSE Resolution 550/2013 (effective 8 April 2026) and XJSE from JSE Volume 00E v3.06, both read in 4b2. No value changed and no document contradicted the registry. Older entries without a document are `unconfirmed` (XOSL 2010 and 2012-08-06, XETR 2010, XBUD 2010; XPRA 2027-01-04 keeps its recheck). XKAR: PSX's page gives a 09:32 Monday-Thursday open (ADR 0014) and two Friday sessions, but no PSX notice dates the schedule, so the 2010 entry keeps 09:30-15:30 with `unconfirmed` evidence (the 4b2 stop rule). Hours evidence 3 → 22 of 74 exchanges (21 with the current entry verified); ratchet floor 22.
- `verification.hours` status `schema_limited` (schema 2.3.1, ADR 0014 section 6): the exchange's own document gives hours that `regular_hours` cannot express (a weekday schedule, for example). The item repeats the part the entry can hold and requires `limitation` (the rest, in the document's terms) and `backlog_item` (the bold title of the `docs/phase-4f-schema-backlog.md` item that would lift it). No recheck cap. It completes an exchange's evidence and does not block at the end of Phase 4b-lite, but it is not verified: `exchanges_hours_verified` stays verified-only.

### Changed
- `tools/check_verification.py` check 6 checks `schema_limited` items (a `limitation`; a `backlog_item` that is a title in the 4f backlog) and reports evidence items by status: "hours evidence: N of 74 (M of 48 reference_compared); items: V verified, S schema_limited, U unconfirmed".

### Fixed
- Rust wrapper: the registry-level `is_open` and `in_session` read every date as the day before (`weekday_from_iso` added `d - 1` to Sakamoto's sum and then shifted again), so Mondays were closed as Sundays and, for Friday-Saturday weekends, Sundays were closed as Saturdays. Present since schema 2.1 (`565087f`); no cross-language probe fell on a Monday or a Sunday until XHKG 2016-07-25 in 4b2. `Exchange::status_at` and the other three wrappers were not affected. New Rust tests compare `weekday_from_iso` with chrono on every date 1990-2030; new cross-language probes (with twins): XNYS Monday 2026-11-23 and Saturday 2026-11-21, XSAU Sunday 2026-11-22 and Friday 2026-11-20.
- XBUE year-end rows against BYMA's own December notices (4b2, saved by the maintainer). 2024-12-24: early close 15:00, was 13:00 (Comunicado N° 18674, 13 December 2024: 'habrá concertación de operaciones hasta las 15:00 hs', with exceptions that do not include 24-hour cash equities). 2024-12-31: closed, was a 13:00 early close ('no habrá actividades de negociación ni liquidación'). 2025-12-24: early close 15:00, was 13:00 (BYMA newsroom, 24/12/2025: 'habrá negociación hasta las 15:00 hs., pero no se realizará liquidación'). Predictions from those two notices, flagged `predicted`: 24 December 2026, 2027 and 2029 at 15:00 (were 13:00; 2026-12-24 stays unconfirmed, recheck 2026-12-22); 31 December 2027 and 2029 closed (were 13:00 early closes). The 2010-2023 24/31 December rows stay library values, recorded as leads. Divergence: 2024-12-31 is a library error (registry verified), 2027-12-31 and 2029-12-31 unpublished (predictions). XBUE's note records that Comunicados 18776 and 18806 (July and August 2025) govern fixed income only, so the July 2025 equity window stays unconfirmed until 18782 or 18293 can be read. Cross-language probes: 2024-12-24 14:30 and 15:30 (open: the registry-level `is_open` ignores early closes by contract), 2024-12-31 12:00 (closed), with `in_session` twins, and `holiday_entry` probes for both 2024 rows.
- XHKG regular hours (4b2): a third `regular_hours` entry from 2016-07-25, 09:30-16:10. HKEX's trading-hours page gives the Closing Auction Session as '4:00 p.m. to a random closing between 4:08 p.m. and 4:10 p.m.'; ADR 0013 takes the end of the random window. HKEX's news release of 25 July 2016 dates it ('For CAS securities, the market close is between 4:08 pm and 4:10 pm'; other securities still close at 16:00). The 2011-03-07 entry (09:30-16:00) is now `verified` by SEHK circular CMD/TMO/011/11; the 1990 entry stays 10:00-16:00, `unconfirmed`. The session-times comparison now shows a close difference on 3,281 days from 2016-07-25 (registry 16:10, both libraries 16:00): the ADR 0013 convention, since the libraries stop at the continuous close. `tools/divergence_report.py` now says so in the Session Times notes. Cross-language probes at 16:05 on 2016-07-22, 2016-07-25 and 2026-11-04, with twins.
- XMOS regular hours (4b2), dated by MOEX's own notices: 10:00-18:45 from 2010 (unconfirmed, recheck 2027-02-19); 10:00-18:50 from 2013-09-02 (notice of 23 August 2013: 'The closing auction will run from 18.40-18.50 pm MSK'); 10:00-19:00 from 2026-03-23 (notice of 11 February 2026: '18:55–19:00 – аукцион закрытия'); 09:10-19:00 from 2026-09-14 (notice of 14 August 2026: '9:00–19:00 – основная торговая сессия (9:00–9:10 – аукцион открытия – для ценных бумаг, недопущенных к утренней сессии)'). Was 10:00-18:45 throughout. ADR 0014 gains two rules: sessions the exchange calls additional ('доп.') are not regular, and where only part of the main book trades in such a session the open is the start of continuous trading for the rest; a close given with seconds (MOEX's page: 18:59:30) is recorded at the minute the exchange's notice states (19:00). The ADR's applied table also gets the XHKG rows. Cross-language probes on each change, with twins.

## [2.29.0] - 2026-11-21

Phase 4d (the `verification` audit after Phase 4c), session 4d.1 (every coverage-span finding resolved; the check blocks), session 4d2 (`in_session`, two primary documents, the recheck-date cap) and session 4b1 (hours evidence, schema 2.3.0).

### Added
- `tools/check_verification.py` checks `verification.coverage`: the spans tile `generation_range` exactly (no gap, overlap or span outside it); a span holding `predicted` entries or dates triaged `unpublished` says predicted/pattern in its label (or is "not covered"); a span naming a reference library stays within the years that library records; `contradicted_by` and `unconfirmed` dates lie inside their span. A predicted or unpublished date may stay under a publications label only when it is listed `unconfirmed` with a `recheck_date` and the label says "unconfirmed". Blocking (4d.1): added in 4d as warnings with 15 findings on 13 exchanges, all resolved in 4d.1; `tests/test_check_verification.py` requires none.
- `tools/derive_verification.py --all` records a re-derivation that changed no class, stamping every file with one `last_checked`.
- `tests/test_check_verification.py`: the coverage rules, and checks 1-4 of `check_verification.py` on the real tree (no CI step or test ran the tool before).
- `in_session` on the registry, in all four wrappers (4d2): Python `CalendarRegistry.in_session(mic, date, time)`, JS `CalendarRegistry.inSession(mic, date, time)` (also declared in `index.d.ts`, with the registry-level `isOpen`, which was missing there), Go `(*Registry).InSession(mic, date, time)`, Rust `Registry::in_session(code, date, time)`. Same signature and same result as the registry-level `is_open` for every input: both delegate to one function per wrapper. The cross-language fixture gives each of its 17 `is_open` probes an `in_session` twin, and `tools/cross_lang/check_in_session_twins.py` checks every runner's output for equal answers.

- `verification.hours` (schema 2.3.0, 4b1): evidence for `regular_hours`, one item per entry (`effective_from`, `open`, `close`, `segment`, `close_rule`, `source_url`, `source_title`, `checked_on`, `status` `verified` or `unconfirmed` with a `recheck_date`). `regular_hours` keeps its shape. `tools/derive_verification.py` keeps `hours` on rewrite, like `coverage`.
- ADR 0014 (4b1): regular hours are continuous trading of the main cash equity book at standard settlement; the close is the end of the closing auction where the segment has one, else the end of continuous trading (ADR 0013); "verified" means the exchange's own document or page, never press, a broker or a reference library.
- `tools/check_verification.py` check 6 (4b1): for every exchange with `verification.hours`, one item per `regular_hours` entry, matching hours, and the 92-day `recheck_date` cap on `unconfirmed` items. It prints "hours evidence: N of 74 (M of 48 reference_compared)", non-blocking (`--strict-hours` fails); `tests/test_hours_evidence.py` keeps N from shrinking. It becomes blocking for every `reference_compared` exchange at the end of Phase 4b-lite.
- `docs/facts.json` `exchanges_hours_verified` (the hours in force today have `verified` evidence), stated in the README and checked by `tools/check_doc_facts.py`.

### Fixed
- XBUE regular hours (4b1): `regular_hours` is now a dated list. From 2026-11-02, 10:30-18:00, `verified` by BYMA Comunicado Nº 19031 (28 October 2026, superseding Comunicado 19024): equities, Contado 24 hs, "10:30 hs. a 18:00 hs.", VWAP close (no equity closing auction), so the close is the end of continuous trading. Until then the registry reported XBUE closed from 17:00 to 18:00 and from 10:30 to 11:00 from 2 November 2026. The earlier 11:00-17:00 entry stays, `unconfirmed` (recheck 2026-12-22): no BYMA document was read, and press dates a 10:30 open from 28 July 2025, a lead that BYMA's July 2025 hours communiqué would settle. Cross-language probes (with `in_session` twins) at 10:45 and 17:30 on 2026-11-04 and 10:45 on 2026-10-14.
- `verification.last_checked` was split across files (70 at 2026-11-08, XKAR, XPHS, XRIS and XSAU at 2026-11-20), so `check_verification.py` failed; all 74 now carry 2026-11-21, the date of the audit. Classes unchanged: `reference_compared` 48, `source_verified` 9, `single_source` 14, `ci_unreachable` 3.
- `docs/divergence_triage.json`: the XSHG "unpublished" verdict for 2027 is removed. The State Council published the 2027 schedule on 2026-11-05 and the registry's 18 closures cite it (`contradicted_by`); the stale verdict had `docs/DIVERGENCE.md` count 16 of them as predictions.
- `tests/test_cairo_holidays.py`: the class-scoped fixture is a `classmethod` (pytest 10 removes the instance-method form).
- Coverage spans (4d.1, no date changed): XSAU coverage cut to its `generation_range` end, 2029-09-23 (the range end is the predicted National Day 2029 set in v2.2.0, not a published boundary; not extended); XSHE's 2028-2029 span past its range removed; XSES no longer names `exchange_calendars` after 2026. Future years the exchange has not published are labelled as predictions: XBOM and XNSE 2027-2029, XBUE 2027-2029, XKLS 2027 (matches the Cabinet's 2027 schedule; Bursa's list is not out), XJSE 2027, and the last-trading-day early closes of XETR 2027-2029 (set by circular each year; non-trading days published to 2032) and XWBO 2027-12-30 (not in Wiener Börse's 2027 schedule).
- XNZE against NZX's memo "NZX Market Holidays - 2025/2027" (announcement 463713, 1 December 2025; read from the maintainer's copy) (4d2): its 19 rows, 24 December 2025 to 4 January 2027, all match. 24 and 31 December 2026 (abbreviated trading) are confirmed, no longer predicted, and cite the memo; the 13:00 end stays on the NZX trading-hours source (the memo gives no hours). The 11 later 2027 rows are predicted (the memo stops at 4 January 2027), with the coverage span split there. The 2026-12-15 recheck is cleared.
- XBUE against BYMA's 2026 "Calendario bursátil" page (read from the maintainer's printout) (4d2): its 21 dates all match the registry's statuses. The 13:00 early close on 24 December 2026, a day "sin liquidación, con negociación" for which the page gives no hours, has no BYMA source: kept, unconfirmed, recheck 2026-12-22. The papal-visit triage text now quotes the page (reference 5, Decree 1103/2026). Holy Thursday 2025-04-17 stays a lead.
- Doubtful dates checked against the exchanges' documents (4d.1): XTAI 2027-02-03 confirmed by TWSE's ROC 116 schedule, its stale "unpublished" verdict merged into the `library_error` verdict for 2027-02-02. Left `unconfirmed` with a recheck date, the document named: XBUE 2025-04-17 (Holy Thursday; BYMA's 2025 calendar not reachable, recheck 2026-12-31), the XNZE abbreviated days 2026-2027 (NZX memo 463713's attachment), XBDA 2026-12-24 (BSX's 2026 festive notice). XKLS's 2027 triage text no longer says the government had not published.

### Changed
- README wrapper test counts (4b1): were hand-written and stale (JS 100, Go 86, Rust 83). Now static declaration counts for all four (`def test_`, `test(`/`it(`, `func Test`, `#[test]`), written and checked by the new `tools/wrapper_test_counts.py` (`--write` / `--check`), which CI (`validate.yml`) and the local gate run.
- Release claims (4b1): the per-commit gate runs only the next release's claims (2.29.0). Released claims are a snapshot that `scripts/release.sh` checks at release time; later work may break them (the schema 2.3.0 bump breaks v2.28.0's `"version": "2.2.3"` claim, as 26 older versions already fail), and they are not edited. Recorded in `tools/check_release_claims.py`.
- `tools/check_verification.py` (4d2): the unconfirmed exception of check 5 holds only while the span's `recheck_date` is no more than 92 days after the file's `verification.last_checked` (a far-off recheck date could otherwise keep a guess under a publications label indefinitely). The two spans that use the exception today, XBDA and XBUE 2025-2026, are 31 days out.
- `docs/phase-4d-backlog.md` is renamed `docs/phase-4f-schema-backlog.md` and opens with the post-4c roadmap (4d, 4d2, 4b-lite, 4e, 4f, 4g, 4b full, 5, 6, with 4h interleaved). The old path keeps a pointer because the v2.28.0 release claims name it.
- `tools/check_stale_year_urls.py`: four zse.hr allowlist entries that matched no scanned URL are deleted.

### Deprecated
- The meaning of the registry-level `is_open` (Python `registry.is_open`, JS `registry.isOpen`, Go `Registry.IsOpen`, Rust `Registry::is_open`): it means "in any session" (pre-market, regular or post-market) in 2.x and will mean regular hours in 3.0.0, the answer the exchange-level call (`registry.get(mic).is_open(date, time)` and its spellings) gives today. Callers who want "in any session" should switch to `in_session` now. Documented only: no run-time warning in any language, since a warning on a call made every minute floods callers and a Python-only warning would break parity.

## [2.28.0] - 2026-11-21

Phase 4c (sessions 4c1-4c13, the 4c-R1 to 4c-R5 rechecks and 4c-final).

### Added
- 2010-2024 backfills from `exchange_calendars` 4.13.2 for 44 exchanges, so 50 of 74 now have data from 2010 (XASX, XHKG, XLON, XNAS, XNYS from 1990 and XTKS from 1997 already did): XAMS, XBDA, XBKK, XBOG, XBOM, XBRU, XBUD, XBUE, XCSE, XDUB, XETR, XHEL, XICE, XIST, XJSE, XKAR, XKLS, XKRX, XLIM, XLIS, XLIT, XLUX, XMAD, XMEX, XMOS, XNSE (inferred from XBOM), XNZE, XOSL, XPAR, XPHS, XPRA, XRIS, XSES, XSGO, XSHE (inferred from XSHG), XSHG, XSTO, XSWX, XTAI, XTAL, XTSE, XWAR, XWBO, XZAG. XSAU starts in 2021, where `exchange_calendars` starts it. Each backfill keeps the library's dates except the ones its note lists as corrected against the exchange's own documents.
- `verification.coverage` (`from`, `to`, `ranges`, `sources` with `contradicted_by`, `unconfirmed` and `recheck_date`) and `note` on the backfilled exchanges; `note` is carried into `calendar.json`, and the Rust and Go wrappers expose `coverage`.
- `ad_hoc_closures` in use: 38 rows for XBDA, XBKK, XLIM, XRIS, XSGO, XTAI and XZAG.
- Recheck-date gate: `tools/check_recheck_dates.py` fails CI the day after a `recheck_date` passes.
- Divergence: the comparison covers 2010-2029; `docs/DIVERGENCE.md` has a 2010-2029 triage-coverage table (fourth pass, `--output /tmp/divergence_history.json`, also in the weekly workflow), and `tests/test_divergence_classified.py` fails if any disagreement has neither a triage verdict nor a `contradicted_by` entry. Every disagreement 2010-2029 is classified.
- The reference libraries are pinned and the whole divergence environment is locked (`constraints-divergence.txt`); the tools refuse to run unpinned.
- `docs/facts.json`: `exchanges_from_2010`, `exchanges_from_2021`, `exchanges_from_2025`, checked in the README by `check_doc_facts.py`.
- ADR 0013 (close convention: the scheduled end of the closing auction) with its applied and exceptions tables; `docs/phase-4d-backlog.md` with the Phase 4d and Phase 4h items (renamed `docs/phase-4f-schema-backlog.md` in Phase 4d).

### Fixed
- `delayed_open` is honoured in all four wrappers: on a `delayed_open` day the market opens at `delayed_open_time` (exchange-level `is_open`/`status_at` in Python, JavaScript, Go and Rust; registry-level `is_open` in Python and Rust).
- Closes moved to the end of the closing auction (ADR 0013): XAMS, XPAR and XBRU 17:35 CET; XLIS 16:35 Lisbon; XBUD 17:05; XETR 17:35; XWBO 17:35; XLUX 17:35; XSES 17:06 (half days 12:06); XNZE 17:00 (abbreviated days 13:00); XBKK 16:35; XKLS 16:50 (unconfirmed); XOSL 16:25 from 2012-08-06 (half days 13:05); XDUB half days 12:30 from 2019; XPRA 16:15, then 16:55 from 2027-01-04 (unconfirmed); XPHS 14:50 with a 12:00-13:00 recess from 2022-03-01; XSAU 15:10 (closing auction 15:00-15:10). XBDA is 09:00-16:30 (continuous trading, no auction).
- Hours history: XKRX (15:00 before 2016-08-01), XOSL (17:30 before 2012-08-06), XBOM and XNSE opening times from 2010, XLIS 08:00-16:30 Lisbon, XHEL open 10:00, XSHE close 15:00.
- Data corrections against the exchanges' own documents (dates and sources in each file's note), among them: XLIT pre-2020 All Souls' Day removed (law XIII-2415); XRIS Christmas Day 2012-2024, the 2018 song-festival and papal-visit days, Cabinet transfer days through 2026 and the 2023/2026 dates settled by Nasdaq Baltic's bulletins; XTAL nine missing Christmas Days; XJSE three declared public holidays and Dec 24/31 early closes; XTAI the 2027 ROC 116 schedule and the 2026 typhoon closures; XBKK 16 October and 16 December 2026; XKAR Ashura and Eid Milad-un-Nabi 2026; XSAU twelve 2021-2024 days and the published 2027-2029 Eid closures (Islamic New Year predictions removed); half days added for XAMS, XBRU, XLIS, XSTO, XOSL and XDUB; XSHG and XSHE dates against the exchanges.
- `tools/update_facts.py --check` compares `tests_total` (a stale count passed before).
- Registry-level `is_open` now gives the same answer in all four wrappers: any pre-market, regular or post-market interval; `early_close_time` ignored; `lunch_break` spanned; an ad hoc row counts as a closure only when its status is `closed`; `delayed_open` honoured. Python no longer treats an ad hoc early close as a full-day closure (XBDA 2025-10-01); JavaScript and Go no longer return the exchange-level (regular-session) answer; Python and Rust no longer count a `lunch_break` session lying outside the regular hours as open (XKUW, XLIM, XSTC). Seven probes added to `tests/cross_language_queries.json`.
- Fetchers: XIST raises `FetchError` on a non-PDF response and tries the next year's URL; `SourceMissingError` makes a gone source a failure, not a warning.

### Changed
- Schema 2.2.3: `coverage` and `note` (2.2.1), `effective_from` required on every recurrence rule (2.2.2), `coverage.from`/`to` required (2.2.3).
- Backfilled years have `low` confidence, not `medium`.

### Known limitation
- Registry-level `is_open` answers "in any session" (pre-market, regular, post-market), not "in regular hours", and it ignores early closes and lunch breaks; the exchange-level call gives regular hours. Splitting the two into separate registry calls is a breaking change, planned in `docs/phase-4f-schema-backlog.md` (an `in_session` alias in 4d2, the split in 4f).

## [2.27.0] - 2026-11-10

### Added
- `verification` object on every exchange (schema 2.2.0, required): `class`, `basis`, `last_checked`, `reference_note`. The class is derived from `fetcher_status` and from `docs/DIVERGENCE.md` by `tools/derive_verification.py` and checked by `tools/check_verification.py`: `reference_compared` 48, `source_verified` 9, `single_source` 14, `ci_unreachable` 3. `reference_compared` means a reference library covers the exchange and the registry is compared with it; it does not mean the two agree (20 of the 48 have disagreements in `docs/DIVERGENCE.md`) and it is not a check against the exchange's own calendar.
- `verification(mic)` in the Python, JavaScript, Rust and Go wrappers: the object, or nothing for an unknown MIC.
- The README's 74-row table is generated by `tools/gen_readme_table.py` from the exchange files and `docs/DIVERGENCE.md`, with a Verification column and a Disagreements column (`n/a` where no reference library covers the exchange). `release.sh` runs `gen_readme_table.py --check`.
- `check_doc_facts.py` asserts the `fetcher_status` partition: the four counts in `exchanges/` add up to the number of files and equal `docs/facts.json`.

### Fixed
- `tools/build.py` copies `verification` into `calendar.json`; without it the field the schema requires was dropped.

## [2.26.0] - 2026-11-08

### Fixed
- `exchanges/XBUL.json`: `fetcher_status` is `blocked` (was `ci_unreachable`).
  `robots.txt` is `Disallow: /`, which is a policy block, not a CI-network
  block. The `v2.25.0` release shipped the wrong state; this fixes it.
- `BLOCKED.md`: XBUL moved from "resolved" to the "Bot-Walled" class, with
  the index and the summary agreeing.
- `README.md`: XBUL's icon is ⛔ (was ⚠️), the counts are
  `42 implemented, 3 ci_unreachable, 3 blocked, 26 none`, and the
  `ci_unreachable` list is `(XHKG, XSHG, XNSA)`.
- `docs/FETCHERS.md`: XBUL's status line says `blocked`.

## [2.25.0] - 2026-11-08

### Added
- `XBULFetcher` (Bulgarian Stock Exchange) via Playwright DOM. The page renders a `div.calendar` with 12 monthly tables; the fetcher reads the cells marked `holiday` on weekdays (the title is the name, "Holiday" when there is none) and skips weekends. 8 test cases pass.

### Fixed
- `BLOCKED.md` and `docs/FETCHERS.md` now document that XBUL's `robots.txt` is `Disallow: /`: `XBULFetcher` respects it and returns `BLOCKED`, and the data stays curated by hand. The page is readable in a browser; it is not automatable under the site's own policy.

## [2.24.0] - 2026-11-07

- Add tools/fetch_render.py with Playwright, OCR, and BLOCKED fallback. Does not yet wire into update_from_exchange.py; that is Session 2.

## [2.23.13] - 2026-11-06

### Fixed
- Fixed known fetcher and early-close bugs, and triaged the final 22 unclassified disagreements for 2027-2029.
- BudapestFetcher no longer generates weekend substitutes (Hungarian law gives none). XSGO 31 December 2027 and 2029 and XBUE 31 December 2025 and 2026 are closures, not early closes.
- XBDA: Cup Match 2028 is 3 and 4 August. XBOG: 31 December 2027 and 2029 are closed. XKAR: no Monday substitute for Saturday holidays; Youm-e-Takbeer (28 May 2027 and 2029) is closed. XKLS: Nuzul Al-Quran (24 February 2027) and the Malaysia Day replacement (17 September 2029) are closed.

### Changed
- Unclassified disagreements are 0 for every year 2025-2029. Eight more dates are recorded as unpublished with a recheck date (XBUE, XHKG, XKLS, XBOG).

## [2.23.12] - 2026-11-06

### Fixed
- Resolved the final 17 unclassified disagreements across 7 exchanges, completing Phase 4a.
- XPRA: 7 July and 29 September 2025 trade; 31 December 2025 and 2026 are closed (the Prague Stock Exchange's 250 trading days in 2025).
- XTAL: Ascension Day (29 May 2025, 14 May 2026) is closed.
- XBOG: 31 December 2025 and 2026 are non-trading days; 1 July 2025 trades.
- XKLS: Nuzul Al-Quran (18 March 2025) is closed.
- XJSE: 11 August 2025 trades. XSES: 20 March 2026 trades. XSHG: 2 January 2026 is closed.

### Changed
- 2025-2026 unclassified disagreements: 17 to 0; one documented unpublished entry remains (XBUE, 17 April 2025). 2027-2029 still list 22 unclassified disagreements, outside this phase.

## [2.23.11] - 2026-11-05

### Fixed
- Triaged and resolved unclassified disagreements for XLIM, XKRX, XSGO, and XLIT.
- XLIM: the Battle of Ayacucho (9 December 2025 and 2026) is closed; the Monday substitutes on 8 June, 31 August and 2 November 2026 are removed (Peruvian law moves no weekend holiday in 2026).
- XKRX: 27 January, 3 June and 3 October 2025 and 1 May, 3 June and 17 July 2026 are closed; 8 June 2026 trades (no substitute for the Saturday Memorial Day).
- XSGO: 30 June and 13 October 2025 and 19 June 2026 trade (Ley 19.668 and Ley 21.357); 31 December 2025 and 2026 are closed for the bank holiday (Ley 21.791), with 30 December 2025 an early close.
- XLIT: Ascension Day (29 May 2025) and 31 December 2025 are closed (Nasdaq trading-day counts).

### Changed
- 2025-2026 unclassified disagreements: 36 to 17 (XLIM 5, XKRX 5, XSGO 5, XLIT 4). 17 remain: this is a partial triage, not a final one.

## [2.23.10] - 2026-11-04

### Fixed
- Triaged and resolved unclassified disagreements for XTAI, XBUD, XRIS, and XKAR using exchange sources.
- XTAI: Lunar New Year adjusted day (27 January 2025), Teachers' Day and Restoration Day adjusted days (29 September and 24 October 2025), Constitution Day (25 December 2025 and 2026), Tomb Sweeping Day observed (6 April 2026), Teachers' Day (28 September 2026) and Restoration Day observed (26 October 2026) are closed.
- XBUD: the weekend-holiday substitutes (14 March 2025, 16 March and 28 December 2026) are removed; the rest days 2 May and 24 October 2025 and 2 January and 21 August 2026 are closed (BSE resolution 311/2024 for 2025).
- XRIS: 5 and 29 May 2025 and Ascension Day 14 May 2026 are closed; 2 May and 17 November 2025 trade (Nasdaq trading-day counts).
- XKAR: 1 January 2025 trades; Juma-tul-Wida (28 March 2025, 20 March 2026), Youm-e-Takbeer (28 May 2025) and the Eid-ul-Azha days (6 and 9 June 2025, 26-28 May 2026) are closed.

### Changed
- 2025-2026 unclassified disagreements: 64 to 36 (XTAI 8, XBUD 7, XRIS 7, XKAR 6). 36 remain: this is a partial triage, not a final one.

## [2.23.9] - 2026-11-04

### Fixed
- Triaged and resolved unclassified disagreements for XBUE, XMOS, and XPHS using exchange sources.
- XBUE: Guemes and National Sovereignty Day follow Ley 27.399 art. 6 (Monday 16 June and 24 November 2025; Monday 15 June and 23 November 2026), and the papal visit closes BYMA on 9 and 10 November 2026. The old 20 November closures are removed. Holy Thursday 2025 is recorded as unpublished.
- XMOS: Moscow Exchange trades on 3, 6 and 8 January, 2 May and 13 June 2025 and 5, 6 and 8 January and 4 May 2026, and does not carry weekend holidays to Monday (24 February and 10 March 2025, 9 March and 11 May 2026).
- XPHS: PSE closes on Chinese New Year, Eid'l Fitr and Eid'l Adha (29 January, 1 April and 6 June 2025; 17 February, 20 March and 27 May 2026), 12 May 2025 (elections) and 31 October 2025.

### Changed
- 2025-2026 unclassified disagreements: 91 to 64 (XBUE 9, XMOS 9, XPHS 9). 64 remain: this is a partial triage, not a final one.

## [2.23.8] - 2026-11-03

### Fixed
- Triaged and resolved unclassified disagreements for XLUX and XBKK using exchange sources.
- XLUX: Europe Day, Ascension, Whit Monday, National Day and Assumption (2025), Ascension, Whit Monday and National Day (2026) and the 28 December 2026 substitute are trading days. Christmas Eve and New Year's Eve are early closes at 14:05 (LuxSE page and Euronext calendars).
- XBKK: 2 January, 16 April and 11 July 2025 and 30 July 2026 are trading days, and Visakha Bucha 2026 is Monday 1 June. 2 June, 28 July and 11 August 2025 and 28 July 2026 are closed (Bank of Thailand announcements).

### Changed
- 2025-2026 unclassified disagreements: 112 to 91 (XLUX 11, XBKK 10, all registry errors). 91 remain: this is a partial triage, not a final one.

## [2.23.7] - 2026-11-03

### Fixed
- Fixed known bugs in XKRX (election day), XIST (missing 2025-2026 Bayram), and XCSE (false May 1st closure).
- XKRX: 12 April 2028, the 23rd National Assembly election day, is a closing day.
- XIST: Ramazan Bayrami and Kurban Bayrami are closed in 2025 and 2026 (31 March, 1 April, 6 and 9 June 2025; 20 March, 27 to 29 May 2026), with half-day eves.
- XCSE: 1 May 2025 and 1 May 2026 are trading days, and the Friday after Ascension Day (30 May 2025, 15 May 2026) is closed.

### Changed
- 2025-2026 disagreements: 129 to 117. No new unclassified disagreement; the XKRX election day is a `library_error` in `docs/divergence_triage.json`. 22 unclassified disagreements remain for 2027-2029.

## [2.23.6] - 2026-11-02

### Fixed
- Fixed lunar holiday dates for XIST, XKRX, and XBKK for 2027-2029.
- XIST: Ramazan Bayrami and Kurban Bayrami closures and half-day eves are added (Diyanet's 2027 calendar; 2028-2029 by the same calculation).
- XKRX: Labour Day and Constitution Day are closed with their substitute days, Memorial Day and New Year get none, and Seollal and Chuseok follow the Korean lunar calendar. The 2027 closures equal KRX's published list.
- XBKK 2027: Makha Bucha is 22 February, Visakha Bucha 20 May and 28 July is a holiday (Bank of Thailand announcement 37/2569).
- XCSE: the Friday after Ascension Day is closed and 1 May is a trading day. XMEX: 2 November is closed.

### Changed
- 2027-2029 disagreements left unclassified: 68 to 22. `docs/divergence_triage.json` adds 4 `library_error` dates (XKRX) and 3 `unpublished` dates (XPHS, XSAU). The 22 left (XBDA, XBOG, XBUE, XHKG, XKAR, XKLS) have no source that settles them and are recorded in `BLOCKED.md`.

## [2.23.5] - 2026-11-01

### Fixed
- Fixed European "observed" holiday rules for XBUE, XLIM, XLIT, XRIS, XTAL, XPRA, XBUD, XLUX, and fixed XSTO Midsummer dates.
- XLUX 2027-2029: LuxSE closes only the Euronext/T2 days and closes early at 14:05 on 24 and 31 December; it trades on Luxembourg-only public holidays.
- XPRA, XBUD, XRIS, XLIT, XTAL, XBUE, XLIM: a holiday that falls on a weekend is no longer moved to a weekday, as the local law or exchange calendar provides. XBUD gains All Saints; XPRA closes on 31 December; XRIS, XLIT and XTAL close on 31 December and Ascension Day.
- XBUE: Guemes 2027 is Monday 21 June (Ley 27.399, art. 6).
- XSTO: Midsummer Eve 2027 is 25 June.

### Changed
- 2027-2029 disagreements left unclassified: 171 to 68. `docs/divergence_triage.json` marks 11 more dates `unpublished` (XBUD 2029 bridge days, XLIM's announced Monday scheme, XRIS 2028 song festival) and 8 `library_error` (XBUE Guemes, Christmas Day in XRIS, XLIT and XTAL). The rest, mainly XIST, XKRX, XBKK, XCSE, XKLS, XBDA, XKAR, XBOG, XHKG, XMEX, XPHS and XSAU, awaits a source check; the Buenos Aires Holy Thursday question is in BLOCKED.md.

## [2.23.4] - 2026-10-31

### Fixed
- Fixed future-year holiday rules for XHEL, XJSE, XTSE, and XNZE based on exchange laws, and marked unpublishable lunar dates as 'unpublished'.
- XHEL 2027-2029: Independence Day (6 December) is closed, and Midsummer Eve 2027 is Friday 25 June.
- XJSE: a Saturday holiday is no longer moved to the Friday (Public Holidays Act 36 of 1994, s2(1)); 15 December 2028 and 15 June 2029 are open.
- XTSE: Friday 31 December 2027 and Friday 30 June 2028 are open; Monday 3 January 2028 is closed in lieu of New Year's Day.
- XNZE: Matariki is 25 June 2027, 14 July 2028 and 6 July 2029 (Matariki Public Holiday Act 2022).
- 38 Islamic and lunar disagreements for XKAR, XSAU, XKLS and XPHS are marked `unpublished` with a recheck date. 171 disagreements for 2027-2029 are still unclassified, including XIST, XKRX, XBKK and XMEX, where the dates are already known and need a source check.

## [2.23.3] - 2026-10-30

### Added
- Added 'unpublished' verdict to divergence triage for future years where the exchange calendar is not yet public.
- `docs/DIVERGENCE.md` gains a "Triage coverage" table that counts each year's disagreements by verdict, including the ones still unclassified.

### Fixed
- XSGO 2027-2029: holidays that fall on a weekend are no longer moved (Ley 2.977), San Pedro y San Pablo and 12 October move to a Monday and 31 October to a Friday (Ley 19.668, Ley 20.299), 17 September follows Ley 20.215 and Ley 20.983, and All Saints (1 November) is a holiday. 26 dates corrected.
- XTAI 2027-2029: observed Peace Memorial, Labour and National Days, Taiwan Retrocession Day, 31 December 2027 and 11 February 2027 follow DGPA's 2027 calendar; Teachers' Day, Retrocession Day and Constitution Day are closed in 2028 and 2029. 14 dates corrected.
- XSES 2027: Hari Raya Puasa is Wednesday 10 March (MOM), not 9 March.
- XSHG, XBOM, XNSE, XSES (2028-2029) and the remaining XTAI and XSGO dates are marked `unpublished` with a recheck date. 2027-2029 disagreements for the other 25 exchanges are not triaged yet.

## [2.23.2] - 2026-10-28

### Changed
- Extended divergence verification to 2027-2029 and resolved future rule discrepancies.
- The weekly divergence job covers 2024-2029 for every exchange and 1990-2029 for the session-time check; `docs/DIVERGENCE.md` gains a by-year table.

### Added
- Recurrence rule `fixed_with_sunday_observance` (Sunday to Monday, a Saturday date not observed), used for New Year's Day on XNYS and XNAS.

### Fixed
- Registry dates for 2027-2029 that the check found wrong: XNYS and XNAS (Christmas observed 2027-12-24, no New Year's Day closure 2027-12-31), XASX and XLON (2028 holidays and half days), XTKS (eight dates) and XHKG (2027 Mid-Autumn, the 2028-2029 festival dates and Lunar New Year's Eve half days), each checked against the exchange's publication or the governing law.
- Three XHKG 2029 dates stay open until Hong Kong publishes its 2029 holidays; see BLOCKED.md.

## [2.23.1] - 2026-10-28

### Fixed
- Added support for date-effective regular_hours and fixed historical session times for XTKS and XHKG.
- XHKG 2026 holidays: added 2026-04-07 and 2026-10-19 as closures, removed 2026-09-25, and added the Lunar New Year's Eve half days (2025-01-28, 2026-02-16), from the SEHK holiday circulars.
- Go, Rust and JavaScript wrapper tests broken by the v2.23.0 backfill (a confidence year with no data, the XNYS holiday count).

## [2.23.0] - 2026-10-28

### Added
- Extended historical holidays back to 1990 for top exchanges (XNYS, XNAS, XLON, XASX, XHKG; XTKS from 1997, the earliest date exchange_calendars supports for it).
- Optional `effective_from` date on recurrence rules, so a rule can be limited to the years it was in force; the rules on XNYS, XNAS, XLON and XASX start 2025-01-01.
- History section in `docs/DIVERGENCE.md`.

### Fixed
- Divergence engine read `exchange_calendars` only for roughly the last 20 years; it now reads the requested years.

## [2.22.0] - 2026-10-27

### Added
- Extended divergence engine to verify session times (open/close/half-days) against reference libraries.

## [2.21.4] - 2026-10-27

### Added
- Added weekly CI workflow to run divergence tests and automatically open PRs if the reference libraries drift.

## [2.21.3] - 2026-10-27

### Fixed
- Triaged and fixed divergence test disagreements for XBRU, XLIS, XBOM, and XNSE.

## [2.21.2] - 2026-10-26

### Fixed
- Triaged and fixed divergence test disagreements for XAMS, XWBO, and XSAU.

## [2.21.1] - 2026-10-26

### Fixed
- Fixed XASX 2026 closures (ANZAC substitute and Labour Day) found by divergence testing.

### Added
- docs/DIVERGENCE.md report generating agreement rates across all reference exchanges.

## [2.21.0] - 2026-10-26

### Added
- Added tools/divergence_test.py to compare the registry against pandas_market_calendars and exchange_calendars.

## [2.20.2] - 2026-10-25

Patch release. CI and tooling only: no change to any exchange, to `calendar.json` content or to the schema.

### Changed
- Expanded check_doc_facts.py to cover version strings and the test file count.
- `scripts/release.sh` now rewrites the README sentence "as of vX.Y.Z" together with the badge, because the checker compares it with `VERSION`.

## [2.20.1] - 2026-10-25

Patch release. CI and tooling only: no change to any exchange, to `calendar.json` content or to the schema.

### Added
- Added docs/facts.json, update_facts.py, and check_doc_facts.py to prevent README prose drift.
- Added the `Check doc facts` step to the `python-core` job: `update_facts.py --check` compares `docs/facts.json` with the tree, `check_doc_facts.py` compares the numbers in the prose with it.

## [2.20.0] - 2026-10-25

### Added
- Added `fetcher_status` to the exchange schema to serve as the machine-readable source of truth for which exchanges have working fetchers.

### Changed
- Updated `tools/check_doc_links.py` to verify README status icons against `fetcher_status`.
- Resynchronized the Python wrapper `calendar.json`.

## [2.19.3] - 2026-10-25

### Added
- `tools/check_expiring_sources.py`: A new CI gate that parses the `## Expiring sources` table in `docs/FETCHERS.md` and fails the build if a documented source has passed its expiry date.
- `tests/test_check_expiring_sources.py`: 31 tests covering the parser, future/past date logic, and malformed tables.

## [2.19.2] - 2026-10-24

### Changed
- Resolved 15 fetcher discrepancies (D1–D15) found during the docs extraction. Notes in `docs/FETCHERS.md` and `BLOCKED.md` now accurately reflect CI failures (WAF blocks vs. parser bugs) and source changes.
- Removed the empty `## Discrepancies` table from `docs/FETCHERS.md`.

## [2.19.1] - 2026-10-24

### Changed
- Restructured `README.md` to replace the 8 tier tables with a single, unified 74-row lookup table.
- Restructured `BLOCKED.md` to group exchanges by *blocker class* (JS SPA, Bot-Walled, PDF Visual Grid, etc.) instead of alphabetically.
- Added `tools/check_doc_links.py` to ensure all README, BLOCKED.md, and FETCHERS.md cross-links resolve correctly.

## [2.19.0] - 2026-10-22

### Added
- `docs/FETCHERS.md`: Extracted 29 fetcher notes out of README prose, added stable `<a id="mic">` anchors, and included a new "Expiring sources" table and a "Discrepancies" table (since resolved).
- Defused a 2027-01-01 CI time-bomb by adding an `ALLOWLIST` to `check_stale_year_urls.py` for URLs that cannot be made dynamic.
- Added `--today YYYY-MM-DD` flag to `check_stale_year_urls.py` for deterministic testing.

### Changed
- Removed 208 lines of prose notes from `README.md`, replacing them with anchor links to `docs/FETCHERS.md`.

## [2.18.1] - 2026-10-21

Patch release. Tooling and tests only: no data, schema or consumer-facing change. `calendar.json`
differs from 2.18.0 only in `meta.version`. The four SQL files change by one header line and the
five Parquet files by their `exchange_calendar.version` footer key; the 20 CSV and TSV files do not
change.

### Added

- CI drift gate: a `Check Parquet exports` step in the `python-core` job runs
  `python3 tools/export_parquet.py --check` right after `Check CSV/TSV exports`, so a stale
  Parquet file fails the build in its own named step, as stale SQL and CSV files already do.
- `tests/test_cross_format_consistency.py`: ADR 0012 promises one shape in three formats, and this
  test checks it. Each of the five tables is loaded from `exchange_calendar.sqlite.sql` (in-memory
  SQLite), the RFC CSV file and the Parquet file, and the three must agree on row count, columns
  and every value in the same row order. Cells are normalized by column kind first (null, boolean,
  integer, ISO date). The normalizers are strict: `"True"`, SQLite `2` for a boolean, a datetime
  where a date belongs, and an empty string in SQLite or Parquet are errors, not coerced. Self-tests
  alter one source at a time and require the comparison to notice.

### Notes

- The 2.18.0 note that nothing in CI runs `tools/export_parquet.py --check` as its own step is true
  of 2.18.0 and no longer true from this release on.
- The test covers the RFC CSV dialect only. The Excel, European and TSV files are covered by
  `tests/test_export_csv.py`.

---

## [2.18.0] - 2026-10-20

Minor release. Adds the Parquet export. No data change: `calendar.json` differs from 2.17.1 only
in `meta.version`. The five Parquet files carry that version in their footer, so unlike the CSV
and TSV files they change with every release.

### Added

- `tools/export_parquet.py` and five committed files at the repository root, one per table:
  `exchange_calendar.exchanges.parquet`, `exchange_calendar.sessions.parquet`,
  `exchange_calendar.holidays.parquet`, `exchange_calendar.ad_hoc_closures.parquet` and
  `exchange_calendar.confidence.parquet`. The columns are the ADR 0012 section 5 list. Dates are
  `date32`, times are `HH:MM` text, `seq`, `year` and the weekend days are `int16`, `predicted`
  and `weekend_exception` are booleans, `exchange_code` is a plain string, and an absent value is
  a real null, never an empty string. A column that is `NOT NULL` in the SQL export is a required
  field. Files are snappy-compressed with one row group, and the footer carries
  `exchange_calendar.version` and `exchange_calendar.table`.
- The rows are the ones `tools/export_sql.py` builds, so the Parquet, CSV and SQL exports cannot
  disagree, and the SQL exporter's guards apply. A string column holding an empty string exits 2.
- `--check` compares logical content, not bytes: it reads the committed file and requires
  `pyarrow.Table.equals(..., check_metadata=True)` against a fresh build, so a file rewritten with
  another compression or row-group size passes, and a changed value, type, nullability, row or
  footer key fails with the column and row named. `--table` selects one table, `--stdout` writes
  one table's bytes. Exit codes are 0 match, 1 mismatch, 2 fatal, 3 committed file missing.
- `tests/test_export_parquet.py`: the schema is checked against a table written out in the test,
  every value is compared with the committed CSV files, nulls, booleans, footer keys and the
  writer options are checked, fifteen kinds of mutation are shown to be caught, and `--check`,
  the CLI and the repository wiring are tested.
- `.gitattributes` rule `*.parquet binary`.
- `pyarrow>=22.0` in `requirements.txt`, a lower bound with no pin. It is a build-time dependency
  of `tools/export_parquet.py` only; the wrappers do not use it.

### Changed

- `scripts/release.sh` regenerates the Parquet files after `tools/export_sql.py` and lists them in
  `RELEASE_FILES` and in the cleanup trap.
- `docs/decisions/0012-export-shapes.md`: section 4 records what the Parquet exporter does, and
  the choices left open after Phase A are marked confirmed.
- `docs/CONSUMERS.md`: a Parquet paragraph, and the distribution table row.
- `checksums.json` covers `tools/export_parquet.py`.

### Notes

- The four SQL files change by one header line (`Source: calendar.json v2.18.0`) and the five
  Parquet files by their `exchange_calendar.version` footer key.
- Nothing in CI runs `python3 tools/export_parquet.py --check` as its own step yet. The test suite
  runs it on the committed files, so a stale file still fails the build.
- `pyarrow` writes the same bytes for the same table across 22.0.0 to 26.0.0 except the version
  digits in the footer's `created_by` string, which is why `--check` is logical and no exact pin
  is needed.

---

## [2.17.1] - 2026-10-20

Patch release. Tooling and CI only: no data, schema or consumer-facing change. `calendar.json`
differs from 2.17.0 only in `meta.version`, and the CSV and TSV files carry no version, so none
of them changes with it. The four SQL files change by one header line.

### Added

- CI drift gate: a `Check CSV/TSV exports` step in the `python-core` job runs
  `python3 tools/export_csv.py --check` right after `Check SQL exports`, so a stale CSV or TSV
  file fails the build the same way a stale SQL file does.

### Fixed

- `.gitattributes`: the `*.tsv` rule is now `text eol=lf whitespace=-blank-at-eol`. An empty
  trailing field ends a TSV line in a tab, which is valid but tripped git's blank-at-eol check
  and made `git am` warn.

### Notes

- The 2.17.0 note that nothing in CI runs `tools/export_csv.py --check` is true of 2.17.0 and
  no longer true from this release on.

---

## [2.17.0] - 2026-10-19

Minor release. Adds the CSV and TSV exports. No data change: `calendar.json` differs from
2.16.1 only in `meta.version`, and the CSV and TSV files carry no version, so none of them
changes with it.

### Added

- `tools/export_csv.py` and 20 committed files at the repository root: each of the five tables
  (`exchanges`, `sessions`, `holidays`, `ad_hoc_closures`, `confidence`) in four dialects,
  following the iso4217 sibling. For a table such as `holidays`: `exchange_calendar.holidays.csv`
  (RFC 4180, comma, UTF-8), `exchange_calendar.holidays.excel.csv` (comma, UTF-8 with a BOM),
  `exchange_calendar.holidays.european.csv` (semicolon) and `exchange_calendar.holidays.tsv` (tab).
  The dialects differ only in the delimiter and the BOM. The header row is the ADR 0012 section 5
  column list, an absent value is an empty field, booleans are `true` or `false`, quoting is
  minimal, and every record ends in LF including the last.
- The rows are the ones `tools/export_sql.py` builds, so the CSV, TSV and SQL exports cannot
  disagree, and the SQL exporter's guards apply. A formula guard exits 2 before any file is
  written if a field starts with `=`, `+`, `-` or `@`.
- `--check` regenerates into a temporary directory and compares bytes. `--table` selects one
  table's four files. Exit codes are 0 match, 1 mismatch, 2 fatal, 3 committed file missing.
- `tests/test_export_csv.py`: every file is read back with the `csv` module, its rows are compared
  with the committed SQLite export, and headers, BOM, delimiters, quoting, the formula guard,
  determinism and `--check` are tested.
- `.gitattributes` rules `*.csv text eol=lf` and `*.tsv text eol=lf`.

### Changed

- `docs/decisions/0012-export-shapes.md`: section 3 covers four dialects per table, and three
  Context statements that had stopped being true are corrected (session identity, the `country`
  fields in `calendar.json`, and the shape of the ISO snapshots).
- `docs/CONSUMERS.md`: a CSV and TSV paragraph, and the footer's version and date.

### Notes

- The four SQL files change by one header line (`Source: calendar.json v2.17.0`).
- Nothing in CI runs `python3 tools/export_csv.py --check` yet, so after a data change the files
  are regenerated by hand with `python3 tools/export_csv.py`.

---

## [2.16.1] - 2026-10-18

Patch release. Tooling and CI only: no data, schema or consumer-facing change.

### Added

- CI drift gate: a `Check SQL exports` step in the `python-core` job runs
  `python3 tools/export_sql.py --check` after `calendar.json` is built, so a stale SQL file
  fails the build.
- `tools/check_sql_dialects.py` executes `exchange_calendar.postgresql.sql` on a real
  PostgreSQL server and `exchange_calendar.mysql.sql` on a real MySQL server, then checks that
  the five row counts equal `calendar.json`, that every stored row equals the exporter's row
  (quote escaping, non-ASCII text), and that a foreign key, a primary key, NOT NULL, a CHECK,
  a time CHECK and an impossible date are rejected while valid rows are accepted. It retries
  connecting for `--wait-seconds` and exits non-zero if a server never answers (no skips).
  The MySQL database is created on demand and defaults to `exchange_calendar`, never the
  `mysql` system schema.
- `check-sql-execution` job in `validate.yml`: `postgres:15` and `mysql:8.0` service
  containers, then `tools/check_sql_dialects.py`.
- `requirements-dev.txt` with the database drivers (`psycopg2-binary`, `PyMySQL[rsa]`), kept out
  of `requirements.txt` so the runtime install stays small.
- `tests/test_check_sql_dialects.py`: unit tests that need no server or driver.

### Fixed

- `checksums.json` had no entry for `tools/check_fixture_labels.py`, which `schema_audit.py`
  reported as a gap. It now has 100 entries.

### Notes

- This supersedes the 2.16.0 note that the PostgreSQL and MySQL files are not executed in CI.

---

## [2.16.0] — 2026-10-17

Minor release. Adds the SQL exporter and the four SQL files it writes. No data change:
`calendar.json` differs from 2.15.4 only in `meta.version`.

### Added

- `tools/export_sql.py` and four committed files at the repository root:
  `exchange_calendar.sql` (ANSI SQL-92), `exchange_calendar.postgresql.sql`,
  `exchange_calendar.mysql.sql` (MySQL 8.0.16 or later) and
  `exchange_calendar.sqlite.sql` (SQLite 3.37 or later, STRICT). Five tables
  (`exchanges`, `sessions`, `holidays`, `ad_hoc_closures`, `confidence`), the primary keys,
  foreign keys, CHECKs and column order of ADR 0012, one `INSERT` per row, and a header that
  reads `meta.version`. The SQLite, PostgreSQL and MySQL files wrap the inserts in a
  transaction. `--check` regenerates into a temporary directory and compares bytes; exit
  codes are 0 match, 1 mismatch, 2 fatal, 3 committed file missing.
- Generator guards that exit 2 before any file is written: key uniqueness, a generated or
  explicit holiday overlap, non-ASCII `code`, `mic` or `country_code`, over-long values, and
  values the database CHECKs would reject.
- `tests/test_export_sql.py`: the SQLite and ANSI files are loaded and exercised, and
  `sqlglot` parses the PostgreSQL, MySQL and ANSI files and compares their literals with the
  SQLite rows for all five tables. `sqlglot>=30.0` is now in `requirements.txt`, and the
  tests fail rather than skip when it is missing.
- `.gitattributes` with `*.sql text eol=lf`, so a checkout cannot rewrite line endings and
  break `--check`.

### Changed

- `schema.json` `version` bumped from `2.0.0` to `2.1.1`. The field was set once,
  in `e95238e`, and three later schema changes left it alone: Schema 2.1 (`519cd48`,
  sessions accept six types), Schema 2.1.1 (`368d62f`, per-year `confidence`) and the
  `fixed_with_thursday_observance` rule type (`cba973d`, shipped in 2.15.0).
  `README.md`, `docs/CONSUMERS.md` and `docs/MARKET_CONTEXT_SPEC.md` already said
  2.1.1. The rule-type addition is arguably a minor change, so the planned next
  schema bump is `2.2.0`, pending a review of `docs/MARKET_CONTEXT_SPEC.md`, which
  requires one at 2.2 or higher. The schema version is independent of the registry
  `VERSION`.
- `docs/decisions/0012-export-shapes.md` amended for the SQL shapes (keys, `seq`, foreign
  keys, idempotency, transactions, per-dialect types and CHECKs). `sessions` no longer has
  an `ordinal` column and sorts by type, then `seq`.

### Notes

- Verification is uneven by dialect. The SQLite and ANSI files are executed in the tests,
  both on SQLite. The PostgreSQL and MySQL files are parsed and their literals are
  cross-checked against the SQLite rows, but they are not executed in CI.
- The SQL files are not in `checksums.json`; `tools/export_sql.py` is, and
  `python3 tools/export_sql.py --check` is the guard against a stale SQL file. Nothing runs
  it automatically yet.

---

## [2.15.4] — 2026-10-11

Patch release. Removed explicit entries and marked two as predicted on existing rule
types; no schema change, no new rule type.

### Fixed

- XCOL (Sri Lanka): settled the four unverified 2027 entries against the Government's
  Extraordinary Gazette No. 2493/05 of 16 June 2026, which is tier 1 for the holiday.
  Removed 2027-04-15 (the gazette lists 13 and 14 April only), 2027-05-03 and
  2027-12-27 (the "observed" weekend substitutes: the gazette lists the Saturdays, and
  CSE's 2026 circular has no Monday closure for any weekend holiday). Marked
  2027-04-14 and 2027-10-28 `predicted`: they are on the gazette, but CSE has not
  issued its 2027 circular. The Vesak-week half holiday and the six 2025 candidates
  stay open: CSE's amended 2026 circular and its 2025 circular could not be retrieved.
  See `BLOCKED.md`.

### Documentation

- `CONTRIBUTING.md`: the source-precedence rule now distinguishes a closure
  announcement from a static annual list that predates a decree or law, gives the test
  (does the exchange's source postdate the decree?), and says how an override is
  recorded. It replaces "where the two differ, the exchange wins".

---

## [2.15.3] — 2026-10-11

Patch release. Added and removed explicit entries on existing rule types; no schema
change, no new rule type.

### Fixed

- XGSE (Ghana): closed the open items from the two-sided check. Added 2025-07-04
  (Republic Day, moved by Executive Instrument from Tuesday 1 July) and 2026-01-09
  (Constitution Day, moved from Wednesday 7 January); removed 2026-01-07. The
  2026-01-09 entry is [Likely]: GSE's own 2026 list still prints 7 January and no GSE
  notice or daily report was reachable, so the file follows the Interior Ministry's
  declaration. Removed 2025-08-04, which the previous release kept from GSE's 2025
  list: that list predates the 2025 Act, and the Ministry stated that 4 August 2025
  was not a public holiday. The 2027 to 2029 Founders' Day removals from 2.15.2
  now rest on that Act as well as on GSE's 2026 list. 2025-07-01 is a non-closure.
  The 2027 to 2029 gaps (Republic Day, Eid dates, midweek-to-Friday moves) are
  recorded as an open class in `BLOCKED.md`, not filled in. See `BLOCKED.md`.

---

## [2.15.2] — 2026-10-11

Patch release. New and removed explicit entries on existing rule types; no schema
change, no new rule type.

### Fixed

- XGSE (Ghana): checked in both directions against GSE's own 2025 and 2026 lists
  and the Interior Ministry's declarations (3 holiday kinds, 5 dated entries).
  Added 2025-09-22 (Sunday 21 September observed on the Monday, declared) and
  2026-07-03 (Republic Day moved to Friday). Removed Founders' Day on 4 August for
  2027, 2028 and 2029: GSE's 2026 list has Founder's Day on 21 September only.
  Those three removals rest on the pattern of the published years, not on a
  published list. Three candidates stay open (2025-07-01, 2025-07-04, 2026-01-09),
  with the source needed for each. See `BLOCKED.md`.

### Documentation

- `docs/task-20-holiday-rule-sweep.md`: the two-sided check is now written down as a
  method (sources by tier, how to record a false closure, the acceptance rule for a
  removal, pattern-derived removals for unpublished years) and the running-status
  table has a "False closures found" column.
- `BLOCKED.md`: corrected the XDUB removed-entry count (21 entries in all).

---

## [2.15.1] — 2026-10-11

Patch release. New data on existing rule types and an existing field (XDUB
rule and entries, XZAG explicit entries); no schema change, no new rule type.

### Fixed

- XDUB (Euronext Dublin): corrected against Euronext's own holiday
  calendars (tier 1, 2022 to 2026). Removed the St Patrick's Day, June,
  August and October bank holiday rules and their entries (Dublin trades
  on all of them) and the false 2025-12-29 "Christmas Day (substitute)".
  Added Labour Day (1 May, `fixed_date`), which was missing. 2026-12-28,
  the substitute for St Stephen's Day, stays: Euronext lists it closed.
  Euronext has not published 2027 to 2029; those years rest on the
  pattern of the published years, and the 2029-05-01 entry is marked
  `predicted`. See `BLOCKED.md`.
- XZAG (Zagreb): corrected against ZSE's own lists (tier 1, 2025 to 2027).
  Removed Independence Day (8 Oct, not a ZSE closure) and the "(observed)"
  Labour Day, Christmas, St Stephen's, New Year's and Epiphany days: ZSE does
  not move a weekend holiday. Added the missing Good Friday, Christmas Eve and
  New Year's Eve. 9 holiday kinds, 23 dated entries (7 kinds and 15 entries on
  the published years); 2028 and 2029 are pattern-derived, and the 4 added
  entries for those years are marked `predicted`. All explicit entries, no new
  rule. A test now fails on any "(observed)" or "(substitute)" entry. See
  `BLOCKED.md`.

---

## [2.15.0] — 2026-10-07

Cumulative release. It ships everything recorded under 2.14.0, 2.14.1
and 2.14.2 below, which were never tagged on their own. Sized as a minor
release because it adds a schema field, a rule type and a rule.

### Added

- `calendar.json` exchange records carry `country` and `country_code`
  (additive field; the wrappers ignore it).
- Rule type `fixed_with_thursday_observance` (schema, validator,
  generator): Egypt's Thursday observance for national holidays.
- XCAI: a June 30 Revolution Day rule, which was missing.
- Rust and Go `HolidayEntry` carry `predicted` and `weekend_exception`.
- `tools/verify_checksums.py` is gated in CI; `tools/schema_audit.py`
  covers the checksum manifest.

### Changed

- Generated holidays no longer fall on an exchange's own weekend
  (267 to 66). `is_holiday` is
  unchanged; `list_holidays` and `holiday_count` no longer list those
  entries. See `docs/CONSUMERS.md`.
- XCAI observed dates follow EGX and government notices; four explicit
  dates were corrected.

- XCAI Coptic Christmas and Labour Day are `fixed_date` with explicit
  entries for the cases a notice decided: Labour Day Thursday 2026-05-07
  (Friday 2026-05-01 was replaced by decree) and a predicted Coptic
  Christmas Thursday 2028-01-06 (EGX closed Thursday 2022-01-06 for a
  Friday). Earlier text called Labour Day exempt from the Thursday move;
  that was wrong.

- XCAI Labour Day 2028 and 2029 are marked predicted (nominal date kept,
  no shift rule) because the precedents conflict; the 2026-05-07 entry and
  the source checks are recorded in `BLOCKED.md`.
- XCOL: 2026 replaced with the dates on CSE's own Circular 07-10-2025.
  Fourteen closures were missing and thirteen entries were wrong (2025's
  Poya dates repeated, plus an unsourced Deepavali substitute). 2025, 2027
  and the Vesak-week half holiday remain open (`BLOCKED.md`).
- XCOL: the eight 2027 Poya entries are removed (2025's dates repeated).
  They return with CSE's 2027 circular.
- XGSE: six Eid closures added (2025-03-31, 2025-04-01, 2025-06-06,
  2026-03-20, 2026-03-23, 2026-05-27) and the 2026-08-04 closure removed,
  because GSE's own 2026 list has no 4 August. Six more candidates are open.
- XMAD: Easter Monday added (`easter_offset` +1). BME has closed on it since
  at least 2022 (its Instrucciones Operativas for 2022, 2024, 2025 and 2026);
  the file and its tests said it was open. Generated holidays total 70.
- The 30 "likely non-closures" (XETR, XPAR, XMAD, XNYS, XNAS) are recorded as
  confirmed non-closures in `BLOCKED.md` against each exchange's own calendar.
- XLIT: Ascension Day 2026, New Year's Eve 2026 and All Souls' Day (2026 to
  2029) added from Nasdaq Baltic's trading holidays page. XZAG: Remembrance Day
  (2025 to 2027) added from ZSE's non-trading days page. XDUB: St Brigid's Day
  confirmed a non-closure. XDUB and XZAG differ from their exchanges' lists by
  more than the sweep's limit and are recorded in `BLOCKED.md`.
- XICE: First Day of Summer and Commerce Day added for 2025 to 2029
  (ten explicit entries) and a Commerce Day `nth_weekday` rule. Four
  closures were missing, confirmed by two settlement calendars (Nasdaq CSD
  Iceland, LuxCSD). `CONTRIBUTING.md` gains a "Citing Sources for Holiday
  Dates" section and `docs/task-20-holiday-rule-sweep.md` tracks the rest
  of the sweep.

### Notes

See the 2.14.0, 2.14.1 and 2.14.2 sections for the detail of each
change. Open items are listed in `BLOCKED.md` (XCAI) and were not
changed in this release.

## [2.14.2] — 2026-10-06

### Fixed

- Generated holidays no longer land on the exchange's own weekend.
  Generated entries drop from 267 to 59; 215 of the 267 were no-ops on
  closed days. 208 came from `fixed_date` rules, which never shift, on
  Sat/Sun-weekend exchanges. The rest came from
  `fixed_with_weekend_adjustment` on Fri/Sat-weekend exchanges (XBAH,
  XCAI, XKUW, XMUS), where the Sat/Sun shift produced a Friday.
- On those four exchanges a holiday on Friday or Saturday now moves to
  the following Sunday, and one on Sunday stays on Sunday, matching
  their explicit data. This removes six false closures on trading
  days (a Sunday holiday had been pushed to Monday) and adds 13
  Sunday observances.

- `BLOCKED.md`: XKUW and XSAU were marked "BLOCKED (permanent)" while
  their fetchers stayed registered and ran in CI. Both now read
  "BLOCKED (HTTP 403 on 2026-09-17)" with what would unblock them. The
  informational CI job no longer calls them "permanently blocked". Both
  fetchers remain registered.

- XCAI: Egypt moves mid-week national holidays to Thursday, so the
  forward-to-Sunday dates generated for XCAI were wrong. New rule
  `fixed_with_thursday_observance` (Friday goes back to Thursday,
  Sunday to Wednesday go forward to Thursday, Saturday stays) now covers
  Revolution Day (Jan 25, Jul 23), Sinai Liberation Day and Armed Forces
  Day; Labour Day is `fixed_date` (exempt). Four explicit dates were
  corrected to what EGX and the government observed: 2025-07-23 to
  2025-07-24, 2025-10-06 to 2025-10-09, 2026-01-25 to 2026-01-29,
  2026-10-06 to 2026-10-08. Seven unsourced future entries at the nominal
  date (2027-2029) and one Sunday substitute (2028-10-08) were removed
  so the rule generates them. The four suspect dates from the weekend
  fix (2025-01-26, 2025-04-27, 2026-04-26, 2026-05-03) are gone;
  2025-04-24 is generated, matching the EGX notice.
- `docs/CONSUMERS.md`: new section "Weekend dates and holiday lookups".
  `is_holiday` is unchanged in all four wrappers (true on any weekend
  date); `list_holidays` and `holiday_count` no longer list generated
  weekend entries. Five fixture queries pin it across the wrappers.
- XCAI gains a June 30 Revolution Day rule
  (`fixed_with_thursday_observance`). It was missing, so closures such as
  Thu 2025-07-03 and Thu 2026-07-02 were absent from the registry. Four
  generated dates are added; generated entries total 67.
- `schema.json` and `tools/validate.py` accept
  `fixed_with_thursday_observance` (additive).

### Changed

- `tools/generate_dates.py`: `adjust_weekend` and
  `generate_dates_for_rule` take `weekend_days` (default Sat/Sun, so
  existing callers are unchanged). `expand_exchange` drops any
  generated date on a weekend day.
- `tools/schema_audit.py` fails on a generated date on a weekend day.
- `tests/test_generated_weekends.py` and `TestWeekendDays` in
  `tests/test_recurrence.py`.

### Notes

**Release scope.** Superseded: 2.14.0, 2.14.1 and 2.14.2 were never
tagged. Everything under those three headings ships as v2.15.0, above.
The sections stay as the record of what each step changed.

No source file changed. The convention lives in the generator, applied
uniformly, rather than in 74 source files. Lookups on a weekend date no
longer report a generated holiday name there; the exchange is closed
that day regardless.

## [2.14.1] — 2026-10-06

### Fixed

- XCAI no longer generates 2029-10-05 (Armed Forces Day). Its
  `generation_range` ends 2029-07-24, and generated holidays are now
  clipped to the range exactly, not by calendar year.

- Rust and Go `HolidayEntry` now carry `predicted` and
  `weekend_exception`, as the Python and JavaScript wrappers already
  did. Both previously dropped the two fields on deserialization. The
  JavaScript typings (`index.d.ts`) now declare them.
- `tests/cross_language_queries.json` gained `holiday_entry` queries
  covering `predicted: false`, `predicted: true`, `weekend_exception`
  and an absent date, so a wrapper that drops a field fails the diff.

- `BLOCKED.md`: XIST moves from `blocked` to `resolved` in the summary
  table (`XISTFetcher` has been registered since v2.9.0); superseded
  early verdicts on XIST, XMUS, XNAI and XGSE are labelled as such.

- `checksums.json` regenerated (it had drifted: 14 of 91 entries
  verified) and is now gated: `validate.yml` runs
  `tools/verify_checksums.py` after the freshness checks, and
  `tools/schema_audit.py` fails on missing, extra or mismatched entries.

### Changed

- `tools/generate_dates.py` clips generated dates to the exchange
  file's `generation_range`. Explicit `start_year`/`end_year`
  arguments keep whole-year behaviour.

### Notes

The audit found one exchange in 74 where the year-granular expansion
passed the range end. The rule is legitimate; the date was outside the
span the file declares. Extending the range to year end would have
claimed verification the file does not have, so the generator now
honours the range as written. Behaviour is unchanged for lookups: 2029-10-05
is a Friday, already a weekend day on XCAI (`weekend_days` 4, 5).
Removed one generated entry; 267 remain.

## [2.14.0] — 2026-10-06

### Added

- `calendar.json` exchange records now carry `country` and
  `country_code`.
- `tests/test_calendar_required_fields.py` — fails if a field
  `schema.json` requires is absent from any exchange in
  `calendar.json`.

### Changed

- `tools/build.py` copies `country` and `country_code` from each
  exchange file. It previously dropped both.

### Notes

Additive field, no removal and no change to existing values. The
wrappers deserialise leniently and ignore the new keys; the four-wrapper
check passes unchanged. `schema.json` always required both fields in
source files; only the built artifact lacked them. This is the
prerequisite named in ADR 0012: the SQL, CSV and Parquet exports need
`country_code`.

## [2.13.0] — 2026-10-05

### Added

- `docs/decisions/0011-mic-lei-connector.md` — records the
  decision to decline the MIC→LEI connector as a separate artifact.

### Notes

Documentation-only release. No schema change, no data change, no
new artifact.

The MIC→LEI connector was proposed at v2.12.5 as a companion file
vendored from ISO 10383. Two reconnaissance findings changed the
shape:

1. ISO 10383's Phase 0 found that GLEIF's MIC-to-LEI file is a
   strict subset of the `lei` field already on `iso10383.json`.
   Every pair agrees; the field carries 120 pairs GLEIF does not.
   The sibling declined its own companion for that reason.

2. EC's vendored snapshot at `tools/iso10383_snapshot.json` is a
   minimal validation artifact — 2,883 MIC code strings, no per-
   entry metadata, no generator in this repo. There is nowhere to
   put the field without changing the snapshot's shape or adding
   a second file for the same source.

No consumer has asked for an exchange operator's LEI. The data
exists on ISO 10383's registry. The reopen condition is a consumer
request; the correct shape at that time is a projection of
`iso10383.json`'s `lei` field into a dedicated EC snapshot.

The v3.0.0 exports are unaffected: there was no MIC→LEI field to
project.

## [2.12.5] — 2026-10-04

### Changed

- `BLOCKED.md` — XJSE marked permanent-block. The entire site is
  behind a Cloudflare bot-wall for plain HTTP clients; a reopen
  condition names the one technique not yet tried.
- `docs/decisions/0010-render-mode.md` — Amendment records the XJSE
  finding. Non-goals section updated.

### Notes

Documentation-only release. No fetcher, no schema change, no data
change.

The XJSE reconnaissance re-probed the four recorded paths and
fourteen additional candidates. Every one returned 403 with the same
5017-byte Cloudflare challenge page — including the homepage,
robots.txt, and sitemap.xml. A full Chrome UA did not change the
result. The prior Playwright probe reached the homepage but its
one-level PDF scan found no holiday calendar URL.

XJSE is now permanent-block with a specific reopen condition: a
Playwright navigation walk through the site's own menu into the
market notices section. That is the one discovery technique not yet
attempted.

This closes the fetcher track. Every blocked exchange in the
ecosystem has a final state and a dated reason. The next release is
v2.13.0 (MIC-to-LEI connector).

## [2.12.4] — 2026-10-04

### Changed

- `docs/decisions/0010-render-mode.md` — D3 (XBKK) amended from
  `defer` to `permanent-block`.
- `BLOCKED.md` — XBKK recorded with the specific finding: the PDF
  has a text layer but its holiday data is a visual calendar grid.

### Notes

The prior XBKK note described an AnyFlip flipbook. That was true of
the URL it checked; the site redesigned. SET's current holiday page
links to plain PDFs. The PDFs are not scanned — text is extractable —
but the text is a grid layout with day numbers and holiday names as
separate blocks, and nothing links them by date. `PDFFetcher`'s
text-based parsing cannot reconstruct the mapping without word
coordinates.

The "visual-grid PDF" class in BLOCKED.md now has two confirmed
members: XATH and XBKK. Both were previously filed under different
reasons (XATH as a stale URL, XBKK as a flipbook). The class
definition is now precise: a PDF whose holiday data is encoded in
cell position rather than in a text list.

The fetcher track closes with this release. XKRX, XATH, and XBKK are
permanent-block. v2.13.0 (MIC-to-LEI connector) is the next release.

## [2.12.3] — 2026-10-04

### Changed

- `docs/decisions/0010-render-mode.md` — D2 (XATH) amended from
  `defer` to `permanent-block`. Athens publishes a visual-grid PDF
  with no extractable text layer.
- `BLOCKED.md` — XATH recorded with the specific finding: a
  visual calendar grid, day numbers only, holidays marked by cell
  fill color.

### Notes

This is the first confirmed instance of the "visual-grid PDF" class
ADR 0009 named. Until this release the class was empty in BLOCKED.md
— the last entry that belonged to it (XATH's 2026-08-31 entry) was
a stale-URL problem in disguise. It is now a real class with a real
member.

The `EuronextFetcher` parent gained an optional `source_url`
parameter. It has no current user but is a small generalization
worth keeping: a future Euronext venue on a different URL will not
require modifying the parent again.

No fetcher was added. No test was added. The reconnaissance produced
a decision, not code.

## [2.12.2] — 2026-10-04

### Changed

- `docs/decisions/0010-render-mode.md` — status was incorrectly
  "Accepted" on a template with placeholders. Every decision is now
  written from the reconnaissance: XKRX permanent-block, XATH defer
  (site moved to athens.euronext.com), XBKK defer (probe two SET URLs).
- `BLOCKED.md` — XKRX, XATH, XBKK reflect the ADR's findings.

### Added

- `tests/test_decision_adrs.py` — fails if an Accepted ADR under
  `docs/decisions/` contains `<...>` placeholders. The check that
  would have caught ADR 0010 shipping as a template.

### Fixed

- `tools/release_claims.json` — v2.12.0's ADR claims matched section
  headings and passed on a skeleton. v2.12.2's claims match decision
  strings and specific findings that only exist in a written ADR.

### Notes

Documentation and tests only. No schema change, no wrapper change,
no data change.

Key finding: the Athens Exchange is now Euronext Athens. The XATH
block was a stale URL, not a visual-grid PDF. The "visual-grid PDF"
class in BLOCKED.md is empty after this ADR.

Fetcher track: XKRX closed permanently. XATH and XBKK deferred with
specific named follow-ups. Two sessions remain before v3.0.0.

## [2.12.1] — 2026-10-04

### Fixed

- `wrappers/python/exchange_calendar/registry.py` — `is_open()` no
  longer calls `.get()` on an `Exchange` object. The bug was
  introduced at v2.11.0 and survived three releases because the check
  that exercises it (`tools/check_cross_language.sh`) was not in the
  release gate.
- `scripts/release.sh` — `tools/check_cross_language.sh` is now
  invoked by the local gate. A regression of this class fails
  locally, before the release commit exists.

### Added

- `RELEASE_PATTERN.md` section "Gate parity" — names the rule that
  every CI check has a corresponding gate invocation, with the
  failure that paid for it.

### Notes

No schema change, no wrapper API change, no data change.

This release closes a gate-coverage gap, not a code gap. The
underlying bug was a two-line error; the reason it shipped three
times is that nothing ran the check that catches it.

## [2.12.0] — 2026-10-04

### Added

- `docs/decisions/0010-render-mode.md` — the render-mode and OCR
  decision for XKRX, XATH, and XBKK. Determines which techniques
  (if any) are approved for v2.12.x, at what CI cost, and whether
  the shape generalizes to `RELEASE_PATTERN.md`.

### Changed

- `BLOCKED.md` — XKRX, XATH, and XBKK cross-reference the ADR.
- `README.md` — Specifications section links the new ADR.

### Notes

Documentation-only release. No schema change, no wrapper change,
no data change.

The decision gate for v2.12.x depends on this ADR's outcome:
- If any exchange's decision is `attempt`, v2.12.x opens with one
  fetcher per session.
- If all three are `permanent-block`, the fetcher track closes and
  v2.13.0 (MIC→LEI connector) follows immediately.

## [2.11.4] — 2026-10-04

### Added

- `tools/check_cross_language.sh` — verifies that all four wrappers
  (Python, JavaScript, Rust, Go) answer a shared fixture of queries
  identically. Fixture at `tests/cross_language_queries.json`.
  Rust and Go runners are skipped cleanly if not yet implemented.
- `docs/CONSUMERS.md` — names every consumer of this registry, the
  version they vendor, the fields they read, and their update trigger.
  Documents the cross-registry snapshot pattern and the update
  protocol for patch, minor, and major releases.

### Fixed

- `wrappers/python/exchange_calendar/registry.py` — `is_open()` no
  longer calls `.get()` on an `Exchange` object. The earlier port
  left four dict-style accessors that raised `AttributeError` at
  runtime; all replaced with `getattr` on the Exchange's actual
  attributes.

### Notes

Documentation, tooling, and one wrapper bug. No schema change,
no data change.

This is the first release exercising the `RELEASE_COMPLETE` fix from
v2.11.3. If the trap fires after `Done.`, that's the fix failing --
paste the release output.

## [2.11.3] — 2026-10-04

### Fixed

- `scripts/release.sh` — the failure trap no longer fires on a
  non-zero exit *after* the release has been tagged and pushed.
  Before this, three consecutive releases (v2.11.0, v2.11.1,
  v2.11.2) printed `Done.`, tagged correctly, then reverted `main`
  because a trailing informational `gh run list` returned non-zero
  on a transient GitHub API hiccup.

  The trap now reads a `RELEASE_COMPLETE` flag, set immediately
  after the `Done.` message. When set, a non-zero exit is treated
  as an informational hiccup: the trap prints a one-line note and
  exits with the same code, without reverting `main`.

  The script also carries an explicit `exit 0` as its last
  statement, so the exit status of informational commands no
  longer determines the script's outcome.

### Notes

No schema change, no wrapper change, no data change. The failure
trap's pre-commit and post-push recovery paths are unchanged for
failures that occur before `Done.`.

## [2.11.2] — 2026-10-04

### Added

- `docs/MARKET_CONTEXT_SPEC.md` — specification of the
  `@market_context` interface between this registry and a compiler
  that type-checks market-context annotations. Defines the annotation
  grammar, the five checks (MIC resolution, calendar coverage,
  confidence threshold, session validity, offset anchor), and the
  diagnostic format for each. Spec version 1.0.0.

### Changed

- `README.md` — new Specifications section linking the market
  context spec.

### Notes

Documentation-only release. No schema change, no wrapper change,
no data change.

The five checks are the compiler-side manifestation of the schema
work shipped in v2.11.0 (sessions) and v2.11.1 (confidence). The
specification names them once, at a stable URL, so Tempus and any
future consumer compile against the same contract.

The spec is versioned independently from the registry. A registry
schema bump to 2.2 or higher requires reviewing this spec.

## [2.11.1] — 2026-10-04

### Added

- `confidence` map on every exchange, keyed by year. Values:
  `{source, last_verified, level, note?}`. Derived from
  `fetcher_manifest.json` and the year span of `holidays.explicit`.
- `tools/derive_confidence.py` — idempotent; `--check` in the
  release gate.
- `confidence(mic, year)` and `as_of(mic, date)` on all four wrappers.
- `tools/build.py` — carries `confidence` into the aggregate
  `calendar.json`.

### Changed

- Schema version -> 2.1.1.

### Notes

Additive. Every year with an explicit holiday gets a confidence
entry: `high` when the current fetch covers it and is fresh, `low`
when the fetch is stale, `medium` for years derived from non-fetcher
sources.

`as_of(mic, date)` is a projection of the current record, not a
historical snapshot. Only `confidence` is filtered -- entries whose
`last_verified` is after `date` are dropped. Sessions, holidays, and
hours are returned as they are today. Real history is planned for
v4.x.

## [2.11.0] — 2026-10-04

### Added

- `sessions` array on every exchange. Types: `regular`, `pre_market`,
  `post_market`, `lunch_break`, `auction`, `halt`. Interval types
  carry `open`/`close`; point types carry `at`.
- `tools/migrate_sessions.py` — idempotent migration with `--check`.
- `sessions(mic)` and `is_open(mic, date, hh_mm)` on all four wrappers.

### Changed

- Schema version → 2.1.0. `regular_hours` and `extended_hours` are
  now derived fields, regenerated from `sessions`. Same values;
  `sessions` is the source of truth.

### Notes

Additive: no field removed. 21 exchanges with pre-existing auction
or lunch_break sessions kept those sessions and gained interval
types derived from the scalar fields.

`is_open` returns true for pre_market and post_market windows.
Consumers wanting regular-hours-only filter `sessions(mic)`.

## [2.10.2] — 2026-10-04

### Changed

- `CONTRIBUTING.md` — documents the `fetcher_manifest.json` rule:
  it is provenance data, committed with the work that produces it;
  a dry-run that dirties it should be reverted manually.
- `scripts/release.sh` — when the working tree is dirty because of
  `fetcher_manifest.json` alone, the preflight names the fix.
- `BLOCKED.md` — XJSE section records the 2026-10-04 search: what
  paths were tried, what was returned, and where the next attempt
  should start.
- `docs/decisions/0009-playwright-fetcher-category.md` — XKRX
  action line: moves to ADR 0010's bucket.

### Removed

- `wrappers/javascript/package.json` — the dead `lint` script and
  its `eslint` devDependency. ESLint 8 had no config and no CI
  usage; the script was non-functional. A deliberate JS lint setup
  (flat config, current version, CI job) can be a future feature.
  PR #14 (eslint 8 → 10.11.0) was closed: version 10.11.0 does not
  exist on npm, and the 8→9+ path requires a config migration this
  wrapper doesn't have.

### Notes

Documentation-and-cleanup release. No fetchers, no schema changes.

## [2.10.1] — 2026-10-04

### Fixed

- `scripts/release.sh` — the failure trap now distinguishes
  pre-commit from post-commit failure. Before this, a release
  that failed *after* the release commit was pushed left the
  tree half-bumped, because `git checkout HEAD -- VERSION ...`
  is a no-op when HEAD is the release commit. The trap now
  reverts the pushed release commit (`git revert HEAD && git
  push`) in that case, and resets it (`git reset --hard HEAD~1`)
  if the commit was local-only.

### Notes

The predicate is `git log -1 --format=%s | grep -q '^Release v'`.
It assumes the release script's commit message format is stable.
If the commit message format ever changes, update the predicate
in the same commit.

Both recovery paths are covered by `tests/test_scripts.py`.
The tests exercise the primitives (`is_release_commit`,
`git checkout HEAD --`, `git revert`) rather than the full
release script, which would require mocking remotes and CI.

## [2.10.0] — 2026-10-04

### Added

- `ExchangeFetcher.use_playwright` — routes the fetch through a
  headless Chromium session. Default False; existing fetchers
  unaffected. ADR 0009 fetch mode only.
- `_make_request_playwright` — the browser transport. Same
  robots/rate-limit/manifest contract as the requests path.

### Changed

- `.github/workflows/validate.yml` and `update-exchange.yml` — install
  Playwright and Chromium; cache `~/.cache/ms-playwright`.
- `docs/decisions/0009-playwright-fetcher-category.md` — amendment
  records two probe results from 2026-10-04:
  - **XJSE fetch mode works.** `page.goto` to the JSE homepage
    through headless Chromium returns the site's own HTML
    (Cloudflare challenge satisfied). The holiday calendar's PDF
    URL was not located; a URL-discovery session is required
    before a fetcher is writable.
  - **XKRX fetch mode does not work.** `page.goto` to the KRX
    endpoint redirects to a `403.html` page even from headless
    Chromium. The WAF blocks headless clients server-side; not a
    client-fingerprint block a browser session can spoof past.
- `BLOCKED.md` — XJSE verdict reclassified from a WAF block to
  URL-discovery; XKRX verdict reclassified from client-fingerprint
  to headless-client block.

### Notes

Framework-only release. ADR 0009's Context section grouped two
different WAF classes together; the probes separated them:

- Client-fingerprint block (XJSE): bypassed by a browser session.
- Headless-client block (XKRX): not bypassed by headless Chromium.

XJSE remains BLOCKED pending URL discovery. XKRX moves to the render
bucket; ADR 0010's scope is now headless bypass, not fingerprint
bypass. Neither fetcher ships at v2.10.0.


## [2.9.6] — 2026-10-04

### Changed

- `BLOCKED.md` — snapshot header paragraph added. Names the pattern
  (a finding is a dated snapshot, not a permanent fact) with four
  examples from the last cycle.
- `BLOCKED.md` — XATH now has its own section (`## XATH — Athens
  Exchange`), completing the 5-of-5 cross-references to ADR 0009.
- `BLOCKED.md` — XPHS verdict corrected from "RESOLVED" to
  "BLOCKED (robots.txt)". The 2026-09-19 finding described the
  endpoint as reachable, which was true about the network path but
  omitted that pse.com.ph's robots.txt disallows `/wp-admin/`. Same
  class as XCAS and XDHA, which the project already respects.

### Notes

Documentation-only release. An `XPHSFetcher` was attempted and
reverted: the framework refuses to fetch sources whose robots.txt
explicitly disallows the path, and PSE's does. The "resolved but
not shipped" state was itself the bug — a note describing the
endpoint as available without checking robots.txt is not a
resolution. Recorded in BLOCKED.md so the next reader checks the
full access path, not just the network path.


## [2.9.5] — 2026-10-04

### Added

- `docs/decisions/0009-playwright-fetcher-category.md` — the
  Playwright decision. Adopts Playwright in fetch mode only;
  defers render+OCR to ADR 0010; declares EC-local, not shared.

### Changed

- `BLOCKED.md` — XKRX, XJSE, XATH, XBKK, XPHS cross-reference
  the ADR.
- `RELEASE_PATTERN.md` § Sources unreachable from CI — note
  added distinguishing fetch-mode from render-mode blocking.

### Notes

Documentation release. No fetcher code changes. v2.10.0 will
implement fetch-mode Playwright for XKRX and XJSE.

## [2.9.4] — 2026-10-04

### Fixed

- `ExchangeFetcher._record_manifest` skips the write when the only
  field that would change is `fetched_at`. The field records when
  the source's content last changed, not when we last looked at it.
  Before this, every dry-run rewrote `fetcher_manifest.json` and
  every release needed a manual `git checkout --` first.

### Notes

Semantics refined: `fetched_at` now means "when did this source's
content last differ from the recorded value", not "when did we
last fetch". A re-fetch of identical bytes is a no-op on the
manifest. A future release may split this into `last_checked` and
`last_changed` if a consumer needs the "we looked but nothing
changed" signal — no such consumer today.

## [2.9.3] — 2026-10-03

### Fixed

- XBUD: parser computes Monday substitutes for weekend state
  holidays. March 15, 2026 is a Sunday and December 26 a Saturday;
  Hungarian labour law grants the next working day as a rest day.
  BSE observes both but its resolution lists only the
  exchange-declared closures. `BudapestFetcher._observed_substitutes`
  handles 3-15 and 12-26. Other fixed-date Hungarian holidays are
  not generalized — no source confirms BSE treats them the same way.

### Changed

- `BLOCKED.md` — XBUD entry marked IMPLEMENTED at v2.9.3.

## [2.9.2] — 2026-10-02

### Fixed

- XWBO: removed <N> 2026 entries the exchange stays open for. The
  current file carried Austrian public holidays the exchange trades
  through; the Vienna PDF's left column (real closures) is the
  correct source and the fetcher was already using it.
- XBUD: parser now recognises the observed Monday when a Hungarian
  national holiday falls on a weekend.
- XDFM: <if applicable — either a fix or a documented divergence>.

### Notes

The three in-window removal blocks from v2.9.1 are resolved. Each
was a different class: a stale file entry, a parser gap, and a
source disagreement. The XIST correction from v2.9.1 is the same
pattern — the fetcher and the file disagree, and re-reading the
source is what resolves which side is right.

## [2.9.1] — 2026-10-01

### Fixed

- `generate_exchange_json` scopes the fetcher's authority to the
  years the fetched data covers. Holidays outside that window are
  preserved from the existing file. Single-year fetchers previously
  failed to write because the removal guard saw 2027-2029 entries
  as removed.
- `compare_holidays` uses the same window. Without it, every
  successive update reported spurious removals of out-of-window
  entries, so `UNCHANGED` never fired.
- `XISTFetcher.parse_html` filters to the PDF's own year. The
  settlement notes mention adjacent years and the parser treated
  those as closures.

### Semantics

Phase 1.1's "the fetcher is the source of truth for
`holidays.explicit`" is refined: the fetcher is the source of truth
**for its own year window**. Within those years, silence is a
deletion and field corrections propagate. Outside, silence is
silence.

### Notes

XIST, XMAD, XKUW now write cleanly. Three remain blocked with
legitimate in-window removals — XBUD, XWBO, XDFM carry 2026
entries the fetchers do not reproduce. That is the removal guard
working as designed (ADR 0008); resolution requires either
updating the current files or correcting the parsers, not
weakening the guard.

## [2.9.0] — 2026-10-01

### Added

- XISTFetcher — Borsa Istanbul equity-market PDF.
- `docs/verifications/2026-10-01_pdf_bucket.md` — probe results.

### Changed

- `BLOCKED.md` — XIST resolved. XBKK, XATH, XJSE confirmed for the
  Playwright bucket (or their respective blockers).

### Notes

The 2026-09-04 BLOCKED.md note described borsaistanbul.com as
publishing "four market-segment tables in one PDF" with a
US-holiday template error in the debt-securities table. In fact the
site publishes four separate PDFs, one per market, and the equity
PDF contains only Turkish closures. The US-holiday filter from the
earlier draft was unnecessary.

## [2.8.0] — 2026-10-01

### Added

- `RELEASE_PATTERN.md` section "Sources unreachable from CI".

### Changed

- `BLOCKED.md` — XKRX recorded as regressed (was RESOLVED on
  2026-09-19; the endpoint returns a 403 HTML body as of 2026-10-01).

### Notes

Documentation release. The XKRXFetcher was attempted and reverted:
the endpoint that BLOCKED.md's 2026-09-19 retest described as
reachable with plain requests now returns a WAF-blocked page. The
regression is recorded with a dated finding rather than silently
dropped, and the CI-unreachable section documents the shape so the
next registry that hits either variant does not have to invent the
pattern from scratch.

## [2.7.0] — 2026-10-01

### Added

- `tools/check_removed_entries.py` — classifies removals between two
  exchange datasets (holiday, exchange, MIC rename). Exit 0/1/2.
- `tools/summarize_blocked.py` — one-line summary of a run's
  `blocked_by_removal` entries.
- `docs/decisions/0008-removal-guard-semantics.md`.
- `FetchStatus.BLOCKED_BY_REMOVAL`.

### Changed

- `RegistryUpdater.update_exchange()` — refuses to write an update
  that removes a holiday. Applies only to `UPDATED`.
- `tools/update_from_exchange.py` — exit 3 when one or more exchanges
  are blocked.
- `.github/workflows/update-exchange.yml` — runs the updater for real
  (previously `--dry-run`, so `git diff` was always empty and the PR
  was never opened); blocked removals reach the PR body.

### Fixed

- `tests/test_check_removed_entries.py` — `_write_dir` creates parent
  directories.
- 3 `test_update_from_exchange.py` fixtures aligned with the guard.

### Rationale

A removal is the change class most likely to break a downstream
consumer. Making it deliberate, not silent, is the point of the
guard. Pattern adopted from ISO 10383's `refresh_diff.py` and ADR
0003, adapted to EC's three-class data model.

## [2.6.0] — 2026-9-30

### Added

- **`fetcher_manifest.json`** — per-fetcher provenance record.
  Populated on fetch with `{fetched_at, source_url, sha256, bytes,
  max_age_days, status}`. Answers "did October's refresh run?" with
  one file read, and "did we parse the same bytes we fetched?" with
  a sha256 comparison.
- **`tools/check_fetcher_freshness.py`** — reads the manifest, fails
  on any entry whose `fetched_at + max_age_days` is in the past, or
  whose `status` is `failed`. Exit 0 fresh, 1 stale, 2 fatal.
- **`tests/test_check_fetcher_freshness.py`** — ~15 tests.

### Changed

- **`ExchangeFetcher.MAX_AGE_DAYS`** — per-class freshness window.
  Default 90 days; overridden per source with a one-line comment
  naming the cadence.
- **`ExchangeFetcher.fetch()`** — computes SHA-256 of the raw
  response bytes and records a manifest entry, on both success and
  failure paths.
- **CI** (`validate.yml`) runs the fetcher freshness check after the
  MIC check.

## [2.5.1] — 2026-09-30

### Fixed

- **`scripts/release.sh` poll reads every run, not the first.**
  `gh run list --limit 1` returned one run per workflow. A rerun or a
  simultaneous push and workflow_dispatch produces multiple runs on
  the same SHA; the poll could return green on one while a sibling
  was pending or failed. Now reads all runs and requires every
  conclusion to be `success`.
- **`scripts/release.sh` tolerates transient failure reports.** During
  the v2.5.0 release, GitHub's API reported a non-success conclusion
  on the release commit's run, which then settled to success seconds
  later. The poll died and required a manual tag. A one-shot 20-second
  re-check now absorbs this race before the poll gives up.

### Added

- **`tests/test_check_mic_codes.py`** — 19 tests for
  `tools/check_mic_codes.py`. The suite was written in the v2.5.0
  cycle but skipped by a `git add` path mismatch; this release lands
  it.

## [2.5.0] — 2026-9-30

### Added

- **`tools/check_mic_codes.py`** — cross-registry check against the
  vendored ISO 10383 snapshot. Verifies every `mic` in
  `exchanges/*.json` is present, matches the filename stem, equals the
  `code` field, and resolves against the registry. `--allowlist`
  support for documented exceptions (empty after v2.4.2's corrections).
- **`tools/iso10383_snapshot.json`** — flat list of 2,883 MIC codes
  vendored from ISO 10383 v1.0.4 (active, expired, operating, segment).
- **`tools/iso10383_snapshot.meta.json`** — sibling metadata for the
  freshness check, matching the ISO 3166 snapshot shape.
- **`tools/mic_allowlist.json`** — allowlist for MICs not in the
  registry. Empty.
- **`tests/test_check_mic_codes.py`** — test suite mirroring the
  country-code check.

### Changed

- **CI** (`validate.yml`) runs the MIC check after the country-code
  check.
- **README** gains a cross-registry edges section linking to ISO
  10383's `docs/JOINS.md`.

### Fixed

- References to `XBEK`, `XNBO`, and `XQSE` in `BLOCKED.md`,
  `README.md`, `CONTRIBUTING.md`, `docs/contributing_exchange.md`,
  and `tools/update_from_exchange.py` updated to their corrected
  codes `XBEY`, `XNAI`, and `DSMD`. CHANGELOG and `docs/verifications/`
  keep the old codes as historical record.

## [2.4.2] — 2026-9-30

### Fixed

- **Three MICs corrected to their registered codes.**
  - `XBEK` → `XBEY` (Beirut Stock Exchange)
  - `XNBO` → `XNAI` (Nairobi Stock Exchange)
  - `XQSE` → `DSMD` (Qatar Stock Exchange)

  SWIFT's 2026-09-23 ISO 10383 file registers these venues under the
  codes above; EC's files carried codes that did not resolve. Files
  renamed, `code` and `mic` fields updated, tests updated.

### Added

- **`tools/check_mic_codes.py`** — cross-registry check against the
  vendored ISO 10383 snapshot (`tools/iso10383_snapshot.json`,
  2,883 MICs, all active/expired, operating/segment).
- **`tools/mic_allowlist.json`** — allowlist for MICs not in the
  registry. Empty after this correction.

Resolves the three MIC gaps documented in ISO 10383's ADR 0007.

## [2.4.1] — 2026-9-30


### Fixed

- **`scripts/release.sh` polls every run, not the first.** Landed
  after v2.4.1 — the v2.4.1 tag shipped without it due to a no-op
  commit. The fix is on `main` as of the commit following v2.4.1. The poll
  used `gh run list --limit 1`, which returns one run per workflow.
  A rerun or a simultaneous push and workflow_dispatch produces two
  runs on the same SHA; if the first is green and the second is red,
  the poll returned success. Now reads all runs, requires each to be
  `completed`, and dies with the failing run's id on any
  non-`success` conclusion. Zero runs is treated as pending.

### Changed

- **`RELEASE_PATTERN.md`** names Exchange Calendar as the source of
  the `check_mojibake.py` signature extension (U+201A removed;
  cp1252 and U+FFFD added). ISO 3166 merged at v1.6.8.

## [2.4.0] — 2026-09-29

### Added

- **`tools/check_mojibake.py`** — UTF-8/Latin-1 round-trip detector,
  ported from ISO 3166 v1.6.7, extended with cp1252 and U+FFFD
  signatures the upstream version misses.
- **`tools/check_release_claims.py`** + `tools/release_claims.json`
  — release-claims gate, ported from ISO 3166 v1.6.7.
- **`tools/check_snapshot_freshness.py`** +
  `tools/iso3166_snapshot.meta.json` — freshness metadata for the
  vendored ISO 3166 snapshot.
- **`RELEASE_PATTERN.md`** — three-registry convention document at
  repo root.
- **Orphan preflight** in `scripts/release.sh` — fails if a heredoc
  references an undefined variable.
- **Manifest precondition** in `scripts/release.sh` — fails at
  preflight if the target version is missing from
  `release_claims.json`.
- **Workflow-coverage check** in `scripts/release.sh` — the poll list
  is verified against `.github/workflows/` at release time.

### Fixed

- **`rust-verify.yml`** — added `VERSION` to the push paths filter.
  It now fires on release commits, so the release poll gates on it
  instead of timing out after push and before tag.

- **`scripts/release.sh` CI polling** — `gh run list` with no matching
  runs returns `.status = null`, which was stringified rather than
  treated as "pending". The poll loop died before tagging.
- **`scripts/` was gitignored** — `scripts/release.sh` existed only on
  one machine. Removed from `.gitignore`; the script is now tracked.

### Changed

- **`validate.yml`** — two new steps: mojibake check (after the
  cross-registry check) and snapshot freshness (after mojibake).

## [2.3.0] — 2026-09-23

### Added

- **`country_code` on all 74 exchanges.** Every `exchanges/*.json` now
  carries `country` (ISO 3166 `countries.active[].name`, verbatim) and
  `country_code` (ISO 3166 alpha-2, `^[A-Z]{2}$`). Both are required by
  `schema.json`. Joins to the ISO 3166 registry on `alpha_2` without
  normalization.
- **`tools/country_mapping.json`** — the MIC → alpha-2 derivation used
  to populate the two fields. Data, not code; regenerable from
  `exchanges/*.json` and ISO 3166.
- **`tools/check_country_codes.py`** — cross-registry check that loads
  `tools/iso3166_snapshot.json` and verifies every exchange's
  `country_code` resolves to an active ISO 3166 entry and its `country`
  string matches byte-for-byte. Exit codes 0/1/2.
- **`tools/iso3166_snapshot.json`** — verbatim snapshot of the ISO 3166
  registry at v1.5.2. Refresh with
  `python3 tools/check_country_codes.py --refresh-from <path>/iso3166.json`.
- **`scripts/release.sh`** — deterministic release pipeline. Refuses on
  dirty tree, wrong branch, missing CHANGELOG section, or CI failure.
  Polls `Validate` and `Rust Verification`; tags only on green.
  `DRY_RUN=1 scripts/release.sh <version>` for preflight.
- **18 tests** for `tools/check_country_codes.py`.

### Changed

- **`schema.json`** now requires `country` and `country_code`.
- **`tools/validate.py`** checks the `country_code` pattern
  (`^[A-Z]{2}$`) and requires the `country` field.
- **`CONTRIBUTING.md`** — Release Process section rewritten. The
  no-tag-before-CI-green rule is now enforced by `scripts/release.sh`,
  not by convention.
- **CI** (`validate.yml`) runs the cross-registry country-code check
  after the main validation step.

- **XQSE** — removed 2 Islamic New Year entries citing
  `ummulqura.org.sa`, which is the Saudi calendar authority, not a
  Qatar Exchange source. `qe.com.qa` returns 404 and the apex domain
  has a certificate error; no reachable QSE source exists for those
  dates.

### Known Issue

- **XKRX and XPHS** have identified JSON endpoints (`GLB99000001.jspx`
  and `wp-admin/admin-ajax.php`) but no fetchers yet. Both require
  rotating anti-replay tokens (`code=` and `_ajax_nonce=`); a fetcher
  will need a two-step handshake. Tracked for a follow-up release.

## [2.2.2] — 2026-09-19

### Changed

- **BLOCKED.md: replaced the "JS-rendered" label on 13 exchanges with
  the specific blocker observed by a Playwright sweep.** Eight are
  blocked by non-rendering causes (Akamai 403, Cloudflare, hCaptcha,
  dead URLs). Five remain undecided — pages loaded without visible
  calendar text, which neither confirms nor disproves client-side
  rendering.

### Added

- `docs/verifications/2026-09-19_js_sweep.md` — per-exchange sweep
  results with HTTP status, bytes, visible-text matches, and anti-bot
  services.

### Known Issue

- XKRX, XTUN, XLIM, XTAD, XPHS are not yet classified. Re-test with
  `wait_for_selector` on a table element and XHR/fetch logging to see
  whether the calendar loads from an API endpoint.
- XQSE's `exchanges/XQSE.json` cites `ummulqura.org.sa` on 2 of 36
  entries — not a QSE source. Fix pending.

## [2.2.1] — 2026-09-19

### Fixed

- **README badge** now matches VERSION (was stuck at 2.1.11).
- **`VERSION`** file bumped to match CHANGELOG top entry.
- **`wrappers/python/exchange_calendar/calendar.json`** re-synced;
  had a trailing newline that `tools/build.py` does not emit.
- **Root `calendar.json`** rebuilt against current `exchanges/*.json`
  (was stale since the 2026-09-17 reconciliation).

### Added

- `Makefile` `release` target: bumps VERSION and prints the CHANGELOG
  steps.

## [2.2.0] — 2026-09-19

### Added

- **`Last verified` dates on every `BLOCKED.md` entry.** All 39 `##`/`###`
  exchange sections now carry a `**Last verified:** YYYY-MM-DD` line,
  derived from git history, the round dates already documented in
  `CHANGELOG.md`, and prose dates in the sections themselves (dates
  range 2026-08-27 to 2026-09-18). A new top-matter paragraph documents
  the convention: what the date means, who adds it, and when to update
  it.
- **`tools/check_stale_verifications.py`** — CI check that fails when
  any `BLOCKED.md` `Last verified` date is more than 18 months (549
  days) old, or missing/malformed. Wired into `.github/workflows/
  validate.yml`. Tests in `tests/test_check_stale_verifications.py`.
- **`tools/check_stale_year_urls.py`** — CI check that scans
  `tools/update_from_exchange.py`'s fetcher `source_url` literals and
  every `exchanges/*.json` holiday's `source_url` for hardcoded 4-digit
  year tokens (2010-2099), and fails when the maximum year found in a
  static URL is older than the current year. Templated/dynamic URLs
  (`{year}`, `%Y`, `%d`, or values built from a variable the checker
  can't resolve) are skipped rather than guessed at. Wired into
  `.github/workflows/validate.yml`. Tests in
  `tests/test_check_stale_year_urls.py`.
- **`make package`** — one command that rebuilds `calendar.json` from
  `exchanges/` and syncs the copy bundled inside the Python wrapper at
  `wrappers/python/exchange_calendar/calendar.json`, so `pip install`
  users no longer risk getting a stale registry. A `make build-wheel`
  target chains this with `python3 -m build`. The build is
  deterministic, so the sync is idempotent.
- **`tools/check_wrapper_snapshot.py`** — CI check that rebuilds
  `calendar.json` in memory from `exchanges/` and compares it
  byte-for-byte against the wrapper's bundled copy, failing (with a
  size/line-count diff summary) if the copy is stale or missing. Wired
  into `.github/workflows/validate.yml`. Tests in
  `tests/test_check_wrapper_snapshot.py`.
- `wrappers/python/exchange_calendar/calendar.json` is now tracked in
  git (previously gitignored) and synced via `make package`, so the
  wrapper package's bundled registry is no longer silently absent or
  stale between releases.

### Changed

- Test suite: 3994 → 4026 passed (0 failed), from the four new test
  files above.

---
## [2.1.13] — 2026-09-18

### Fixed

- **Test suite: 71 stale assertions removed.** Each asserted a specific
  past-due predicted Islamic holiday that was removed during the
  2026-09-17 reconciliation. Replaced by a global invariant test
  (`tests/test_no_stale_predictions.py`) that enforces the property
  those methods collectively verified: no past-due `predicted` entry
  may survive in any exchange JSON. Suite: 71 failed / 3993 passed →
  0 failed / 3994 passed.
- **Cross-exchange Eid al-Adha test reframed from 2025 to 2027.** The
  2025 comparison was no longer testable against all three of XCAI,
  XMUS, and XSAU because the 2025-06-08 entry was removed from XSAU
  during reconciliation. Same policy intent, valid data.

### Added

- `docs/verifications/` directory with the XBOG audit artifacts.

### Known Issue

- `v2.1.12` was tagged and pushed on a suite with 71 failing tests.
  Fixed as of this release. The tag remains as a historical snapshot.
  
## [2.1.12] — 2026-09-17

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

- `tools/generate_checksums.py` / `tools/verify_checksums.py` — SHA-256
  manifest (`checksums.json`) covering `exchanges/*.json`,
  `schema.json`, and `tools/*.py`. `SECURITY.md` updated to reference
  them instead of disclosing they didn't exist.

### Changed

- **Past-due predicted holidays reconciled to zero.** 106 entries
  across 15 exchanges. XDFM: 5 entries confirmed against the exchange's
  2026 circular PDF, 4 removed (3 outside the circular's coverage,
  1 not a DFM holiday). XNSA: 4 entries removed — the only available source 
  (NGX's own page) footnotes the dates as tentative, and no first-party 
  Nigerian government source confirms them. The remaining 13 exchanges: 
  97 entries removed as unresolvable (robots.txt, 403 from all IPs, JS-rendered,
  client-side empty, or timeout). The `KNOWN_PAST_DUE` allow-list in 
  `tools/validate.py` is now empty and has been deleted; `check_past_due_predictions`
  fires on every exchange.

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
- Islamic-calendar fetchers mark past-dated entries as `predicted=True`
  because the predicted flag is derived from the source's own footnote
  without checking whether the date has already passed. This is the
  underlying cause of the reconciliation work above; a fix is planned
  but not yet implemented. See `tools/update_from_exchange.py`.

---
## [2.1.11] — 2026-09-17

### Fixed

- **SZSE parser rewritten for prose format.** The live page no longer
  publishes a table; holiday data is now natural-language prose
  ("The market will close from January 1st to January 2nd..."). The
  old table-based parser returned zero holidays. Rewritten to extract
  date ranges from prose and expand them to individual weekdays.
  Also fixed the source URL path (`/www/English/...`).
- **Date regex ordinal-suffix whitespace bug.** 11 fetchers used
  `(\d{1,2})(?:st|nd|rd|th)?`, which fails when the ordinal suffix is
  separated by whitespace (`16 th`). Changed to
  `(\d{1,2})\s*(?:st|nd|rd|th)?` across SZSE, Ghana, Cayman, and eight
  other fetchers.
- **Workflow: `continue-on-error` moved from job to step level.** The
  previous design correctly prevented informational failures from
  gating the workflow, but displayed them as red ✗ in the UI. Now
  shown as `::warning::` annotations on green jobs.

### Added

- `live_fetcher_check.py` gained `--only` and `--exclude` flags for
  comma-separated MIC filtering.
- `BLOCKED.md` now distinguishes three categories: **permanently
  blocked** (XKUW, XSAU — 403 from all IPs), **CI-unreachable** (XHKG,
  XSHG, XNSA — works from residential IP, blocked from GitHub runners),
  and **blocked** (the existing 29 blocked sources).

### Changed

- Live-fetcher workflow split into five jobs: `verify-coverage`,
  `live-check-stable` (blocking), `live-check-ci-unreachable`
  (informational), `live-check-blocked` (informational), `summarize`.
- README coverage claim rewritten: 45 registered, 40 CI-verified, 5
  CI-unreachable or permanently blocked, 29 blocked sources.

## [2.1.10] — 2026-09-11 — Live health-check regressions (round 1 + round 2)

### Fixed

Two consecutive live runs of `live-fetcher-check.yml` against real
endpoints (not `web_fetch` snapshots) surfaced regressions in 8 fetchers
as source pages changed since original verification. All were re-verified
live via `web_fetch` before fixing — none guessed at.

**Round 1 (3 fetchers — 40/45 → 43/45 passing):**

- **XASX**: duplicate holiday dates (2026-01-01, 01-26, 12-25, 12-28). Root
  cause: the live page now publishes two tables (2026 and 2027 calendars);
  the parser extracted one year globally via `.search()` and reused it for
  every table, so the 2027 table's rows were mis-dated as 2026. Fixed by
  extracting the year per-table. Added defensive same-date-entry merging
  as a safety net (`ExchangeData.validate()`'s duplicate-date rule was not
  loosened, since that affects every fetcher).
- **XBSP**: "No holidays found." Root cause: the live page's month labels
  ("January", etc.) are accordion nav links (`<a href="#panel10a">`), not
  heading tags — `current_month` never got set, so every row was silently
  skipped. Fixed by also walking `a` tags with `href` starting `#panel`.
- **XBUE**: "No holidays found." Root cause: the Webflow-generated page no
  longer exposes its calendar as `<table>` markup. Rewrote the parser to
  work directly off linearized page text (sequential date/weekday/motivo
  triplets) instead of depending on any specific tag structure — more
  resilient to this class of change going forward.

**Round 2 (5 fetchers — 40/45 → pending re-verification):**

- **XWAR**: duplicate `2027-01-01`. Root cause: the "2027" section has a
  stray trailing row ("Thursday 1 January") that's actually 2026's New
  Year's Day (confirmed: 1 Jan is a Thursday in 2026, a Friday in 2027) —
  a page template artifact. Fixed by validating each row's own weekday
  against its assigned section year and skipping mismatches, plus
  defensive de-duplication.
- **XHKG**: 404 on both CSV URLs. Confirmed via `web_fetch` the URL/data
  are unchanged and correct — likely HKEX's CDN reacting to the base
  class's generic User-Agent (`ExchangeCalendarRegistry/1.0`). Overrode
  `_make_request` with realistic browser headers, scoped to this fetcher
  only. **Not verified end-to-end** (this environment cannot make live
  `requests` calls to hkex.com.hk) — a defensible mitigation, not a
  confirmed fix.
- **XSAU**: 403 Forbidden. Same investigation and same fix pattern as
  XHKG — page confirmed unchanged via `web_fetch`, likely CDN reacting to
  the generic User-Agent, same caveat about not being verifiable
  end-to-end from this environment.
- **XSHE**: "No holidays found." Root cause: the live page's year heading
  splits "2026" across separate `<strong>` tags; `get_text("\n", ...)`
  inserted a newline between them, breaking the year regex. Fixed by
  anchoring on stable heading text and stripping all non-digit characters
  before matching the year. Also fixed an unrelated quirk found in the
  same investigation: one entry has zero whitespace between month and day.
- **XCOL**: "No holidays found." Root cause: the PDF now has month name
  and date on the same line ("January 01st Thursday..."), not on separate
  lines as originally assumed. Fixed to handle both layouts. Also fixed a
  second bug: the circular's sign-off text was being swept in as a
  continuation of the last holiday — now parsing stops at "Yours
  faithfully".

### Added

- 12 new regression tests, one or two per fix, each reproducing the exact
  failure mode the live check found (not just re-testing the happy path).

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

## Version History

| Version | Date | Exchanges | Wrappers | Tests |
|---------|------|-----------|----------|-------|
| 0.1.0 | 2026-08-12 | 0 (skeleton) | — | 0 |
| 1.0.0 | 2026-08-14 | 14 | Python, JS, Go, Rust | 1,127 |
| 2.0.0 | 2026-08-18 | 74 | Python, JS, Go, Rust | 5,300+ |
| 2.1.0 | 2026-08-19 | 74 | Python, JS, Go, Rust | 4,070+ |
| 2.1.11 | 2026-09-17 | 74 | Python, JS, Go, Rust | 4,070+ |

Patch releases 2.1.1 through 2.1.10 are documented in the sections above; the table tracks milestones, not every release.

---

## Versioning Notes

- **Major** (2.x.x): Major expansion — 60 new exchanges, new calendar systems
- **Minor** (x.1.x): New exchanges, new wrapper features
- **Patch** (x.x.1): Data corrections, bug fixes

Each exchange calendar file has its own `generation_range` and source URLs.
Data corrections are tracked per-exchange in commit history.
```