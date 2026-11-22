# ADR 0014 — Regular hours: segment, close rule, evidence

**Status:** Accepted
**Date:** 2026-11-21
**Decided by:** the CTO (Phase 4b-lite brief, session 4b1; section 6 added in session 4b2)

## Context

Holidays carry evidence (coverage spans, `contradicted_by`, `unconfirmed`,
triage); session times carried none. `regular_hours` was hand-entered, and
the registry-level `is_open` / `in_session` and the exchange-level
`is_open` are only as good as it. Phase 4d showed that a holiday audit
cannot catch wrong hours: every XBUE 2026 holiday matched BYMA's calendar
while its hours (11:00-17:00) were wrong.

## Decision

### 1. Which segment is "regular"

`regular_hours` describes **continuous trading of the exchange's main cash
equity order book at the standard settlement cycle** (the segment where
ordinary shares trade for regular settlement: T+1 or T+2). Not other
asset classes (fixed income, derivatives, repo), not same-day or
immediate-settlement books, not negotiated/bilateral segments, not
auction-only segments.

- `open` is the start of continuous trading. A pre-opening or opening
  auction before it is not part of the regular session; where modelled it
  is an `auction` or `pre_market` session.
- `close` follows the close rule below.
- Post-close phases (Trading at Last, trading at the closing price, run-off)
  are not regular; where modelled they are `post_market` (ADR 0013).

When an exchange runs several equity books with different hours, the
evidence item names the segment it used, in the exchange's own words.

**Security groups (session 4b3; replaces 4b2's "additional sessions"
wording).** When an exchange's schedule differs by security group, the
registry follows the group that holds the constituents of the exchange's
main index, as the exchange's own document identifies them. Sessions the
exchange calls additional, morning or evening (MOEX's "утренняя (доп.)
сессия" and "вечерняя (доп.) сессия") stay outside regular hours even for
that group; where modelled they are `pre_market` or `post_market`. Reason:
one principle for every split. 4b2 had followed different groups at two
exchanges: HKEX's Closing Auction Session (index constituents) and MOEX's
shares without a morning session (not the index). The index group is also
the one the registry's users trade. Where the index's constituents fall
into more than one group, the rule does not decide and the entry is
`unconfirmed`. The evidence item names the group and cites the document
placing the index in it.

Applied: XHKG closes at 16:10 from 2016-07-25 (CAS Phase 1 covered the
Hang Seng Composite LargeCap and MidCap constituents). XMOS opens at 09:50
from 2025-03-21 (MOEX notice of 18 March 2025: all 49 MOEX Index shares
admitted to the morning session; the admitted shares' main session
starts at 9:50 with its trading period) and at 09:00 from 2026-09-14
(schedule page: admitted shares, main session ТП "09:00:00 — 18:54:59").
The morning session (06:50-09:00) stays excluded. MOEX's 2021-2022
morning session (also IMOEX shares, from 6 December 2021) is a lead: no
MOEX document read gives its end.

### 2. Close rule (ADR 0013)

- The segment has a closing auction: `close` is the end of the closing
  auction (the published uncross time, or the end of a random window).
  `close_rule: "closing_auction_end"`.
- The segment has no closing auction (a VWAP or last-trade close, or
  continuous trading to the end): `close` is the end of continuous
  trading. `close_rule: "continuous_end"`. This is the rule already applied
  to XKAR and XBDA in ADR 0013.
- Times are HH:MM. A close the exchange gives with seconds is recorded at
  the minute its own notice states (MOEX: schedule page 18:59:30, notice
  "18:55–19:00 – аукцион закрытия", recorded 19:00); with no such notice,
  at the next whole minute, since a query at HH:MM means HH:MM:00 and is
  still inside the auction.

### 3. What "verified" means

An hours entry is `verified` only when **the exchange's own document or
page** gives those hours for that segment: a circular, communique, rulebook,
trading-parameters document, the exchange's trading-hours page, or a
documentation site the exchange operates and signs. It is cited with its
URL and title, and was read by the session or saved by the maintainer
(the 4c rules).

Never verified by: press articles, broker pages, data vendors, the
reference libraries (exchange_calendars, pandas_market_calendars), a
sibling market's rules, or a public-holiday law. These are leads.

An entry without such a document is `unconfirmed`. It keeps its value (no
change to `regular_hours` without the exchange's word), carries a
`recheck_date` no more than 92 days after `verification.last_checked`
(the cap of check 5), and its `note` names the lead and the document that
would settle it.

### 4. Where the evidence lives

`verification.hours`, an array with **one item per `regular_hours` entry**
(schema 2.3.0). `regular_hours` keeps its shape: one object, or a dated
list (`effective_from`) when the hours changed inside the registry window
(wrappers parse it as such). Each item records:

| Field | Meaning |
|-------|---------|
| `effective_from` | The `effective_from` of the entry it backs; for a single undated object, `generation_range[0]` |
| `open`, `close` | The hours it backs; must equal the entry's |
| `segment` | The segment, in the exchange's words |
| `close_rule` | `closing_auction_end` or `continuous_end` |
| `source_url`, `source_title` | The document (for `unconfirmed`, the best lead) |
| `checked_on` | When it was read |
| `status` | `verified`, `schema_limited` (schema 2.3.1, section 6) or `unconfirmed` |
| `recheck_date` | Required when `unconfirmed` |
| `limitation`, `backlog_item` | Required when `schema_limited` (section 6) |
| `note` | Optional: the quoted line, the lead, what would settle it |

`tools/check_verification.py` check 6 tests it for every exchange that has
`verification.hours`: one item per entry, no item without an entry, equal
`open`/`close`, `recheck_date` on `unconfirmed` items within the 92-day
cap. `tools/derive_verification.py` keeps `hours` on rewrite, like
`coverage`.

### 5. Ratchet

4b1 reports check 6 ("hours evidence: N of 74 (M of 48
reference_compared)") without enforcing it; a test keeps N from shrinking.
At the end of Phase 4b-lite check 6 becomes blocking for every
`reference_compared` exchange, for current hours (section 7, 4b3).

### 6. Hours the schema cannot express (`schema_limited`, session 4b2)

Some exchanges publish hours that `regular_hours` cannot hold: a weekday
schedule (PSX, XKAR: two Friday sessions against one Monday-Thursday
session), a seasonal schedule. Neither `verified` (the entry does not say
what the exchange says) nor `unconfirmed` (nothing is in doubt, and no
recheck will settle it) fits.

- `status: "schema_limited"` (schema 2.3.1) means: the exchange's own
  document was read (same standard as `verified`, section 3), `open` and
  `close` repeat the part `regular_hours` can express, and the rest is
  stated in `limitation`, in the document's terms.
- `backlog_item` names the item of `docs/phase-4f-schema-backlog.md` (its
  bold title) whose schema change would lift the limitation. Check 6 fails
  an item whose `backlog_item` is not a title there, so removing the
  backlog item without migrating the evidence is caught.
- No recheck cap: the item is settled until the schema changes.
  `recheck_date` is optional and not capped.
- Counting: a `schema_limited` item is evidence, not verification. It
  completes an exchange's evidence (it counts toward "hours evidence: N of
  74") and **does not block** at the end of Phase 4b-lite. It does **not**
  count as verified: `exchanges_hours_verified` and the README count stay
  verified-only. Check 6 reports items as "V verified, S schema_limited, U
  unconfirmed".
- The entry's value still follows the exchange: a `schema_limited` entry
  holds the hours the exchange gives for the days it can describe, never a
  compromise between two schedules.

### 7. What the evidence proves: `verified_from`, current and history (session 4b3)

4b2 marked an entry `verified` when a document read in 2026 gave its hours,
even where the entry started in 2010: for 17 exchanges the evidence said
more than the document proved.

- A `verified` item carries `verified_from` (schema 2.3.2): the earliest
  date its cited document proves those hours. That is the document's
  effective date, or the earliest date it states (a release date, a
  version date, a page's last-modified date), or the read date when it
  states none. It is never before the entry's `effective_from`; it may be
  after `checked_on` when the document read takes effect later (Euronext's
  appendix edition effective 23 November 2026, read on 22 November).
  Entries are not split to make history look verified.
- **Current hours verified** (`docs/facts.json` `exchanges_hours_verified`):
  the entry in force on the evaluation day has a `verified` item with
  `verified_from` on or before that day. The evaluation day is the later of
  `verification.last_checked` and the item's `checked_on`: a document read
  on a day proves that day's hours, and `last_checked` can lag behind the
  read. Both are recorded dates, so the fact does not move with the clock.
- **History verified** (`exchanges_hours_history_verified`): every entry has
  a `verified` item with `verified_from` equal to its `effective_from`.
- The end-of-4b-lite blocking rule (section 5) applies to current hours.
  History is Phase 4b full.
- Check 6 prints both ("Current hours verified: N of 74", "History
  verified: M of 74"); the README states both and `tools/check_doc_facts.py`
  checks them.

## Consequences

- `docs/facts.json` `exchanges_hours_verified` counts exchanges whose
  current hours are verified (section 7: `verified_from` on or before the
  evaluation day; 4b2 counted the entry in force on `last_checked`); the
  README states it.
- Wrappers do not read `verification.hours` yet (unknown keys are ignored
  by all four); exposing it is a 4f question.
- Pre/post-market, auctions and lunch breaks are out of scope until 4b full.

## Applied (filled as 4b-lite proceeds)

| Exchange | Entry | Hours | Segment | Close rule | Status | Source |
|----------|-------|-------|---------|------------|--------|--------|
| XBUE | from 2010-01-01 | 11:00-17:00 | Renta Variable, standard settlement (period names not checked) | continuous_end | unconfirmed (recheck 2026-12-22) | No BYMA document read. Lead: La Nación, 18 July 2025, a 10:30 open from 2025-07-28; settled by BYMA's July 2025 hours communiqué |
| XBUE | from 2026-11-02 | 10:30-18:00 | Negociación Regular con modalidad de cierre VWAP Renta Variable - Contado 24 hs. | continuous_end (VWAP close, no equity closing auction) | verified | BYMA Comunicado Nº 19031, 28 October 2026, in force 2 November 2026 (supersedes 19024); BYMA Clearing's Cronograma diario v1.10 agrees on the 10:30 open |
| XHKG | from 1990-01-01 | 10:00-16:00 | Securities market continuous trading sessions (Main Board and GEM) | continuous_end | unconfirmed (recheck 2027-02-19) | HKEx consultation conclusions, November 2010, give these hours as of 2010 only (read through a search result) |
| XHKG | from 2011-03-07 | 09:30-16:00 | Morning Session, Afternoon Session | continuous_end (no closing auction until 2016-07-25) | verified | SEHK circular CMD/TMO/011/11, 3 March 2011 |
| XHKG | from 2016-07-25 | 09:30-16:10 | Continuous Trading Session followed by the Closing Auction Session (CAS securities) | closing_auction_end (random end 16:08-16:10) | verified | HKEX trading-hours page; HKEX news release of 25 July 2016 dates the CAS |
| XMOS | from 2010-01-01 | 10:00-18:45 | Main trading mode, Russian equities | continuous_end (post-trade auction, not a closing auction) | unconfirmed (recheck 2027-02-19) | MOEX notice of 23 August 2013 gives the 18:45 end of trading as of 2013 only |
| XMOS | from 2013-09-02 | 10:00-18:50 | Main Trading Mode T+, Y1 order book (no morning session for any share in most of this period) | closing_auction_end | verified | MOEX notice of 23 August 2013; MOEX Closing Auction page (start date 2 September 2013) |
| XMOS | from 2025-03-21 | 09:50-18:50 | Main Trading Mode T+, Y1, shares admitted to the morning session (all 49 MOEX Index shares) | closing_auction_end | verified | MOEX notices of 18 March 2025 (admission) and 22 January 2025 (09:50 main session for admitted shares) |
| XMOS | from 2026-03-23 | 09:50-19:00 | as above | closing_auction_end | verified | MOEX notice of 11 February 2026 (closing auction 18:55-19:00 from 23 March) |
| XMOS | from 2026-09-14 | 09:00-19:00 | as above (main session trading period from 09:00:00) | closing_auction_end (18:59:30 on the page) | verified | MOEX notice of 14 August 2026; MOEX trading schedule page |
| XAMS | from 2010-01-01 | 09:00-17:35 | Euronext Amsterdam regulated market, 'Equities AEX' (group J0), continuous mode C | closing_auction_end | verified | Euronext, Appendix of Trading Manual 4-01, effective 23 November 2026 (saved by the maintainer) |
| XBRU | from 2010-01-01 | 09:00-17:35 | Euronext Brussels regulated market, 'Equities BEL20' (group A0), continuous mode C | closing_auction_end | verified | Euronext, Appendix of Trading Manual 4-01, effective 23 November 2026 (saved by the maintainer) |
| XPAR | from 2010-01-01 | 09:00-17:35 | Euronext Paris regulated market, 'Equities CAC40 - Group 1' (group F1), continuous mode C | closing_auction_end | verified | Euronext, Appendix of Trading Manual 4-01, effective 23 November 2026 (saved by the maintainer) |
| XLIS | from 2010-01-01 | 08:00-16:35 | Euronext Lisbon regulated market, 'Equities PSI' (group P0), continuous mode C | closing_auction_end | verified | Euronext, Appendix of Trading Manual 4-01, effective 23 November 2026 (saved by the maintainer) |
| XDUB | from 2010-01-01 | 08:00-16:30 | Euronext Dublin regulated market, 'Shares - ISEQ 20 - XMSM' (group 9A), continuous mode C | closing_auction_end | verified | Euronext, Appendix of Trading Manual 4-01, effective 23 November 2026 (saved by the maintainer) |
| XOSL | from 2010-01-01 | 09:00-17:30 | Oslo Børs equities (period names not checked) | closing_auction_end | unconfirmed (recheck 2027-02-19) | Euronext/Oslo Børs |
| XOSL | from 2012-08-06 | 09:00-16:25 | Oslo Børs equities, continuous trading and closing auction | closing_auction_end | unconfirmed (recheck 2027-02-19) | Euronext/Oslo Børs |
| XOSL | from 2026-08-03 | 09:00-16:25 | Euronext Oslo Børs regulated market, 'Equities - OBX' (group OA), continuous mode C | closing_auction_end | verified | Euronext, Appendix of Trading Manual 4-01, effective 23 November 2026 (saved by the maintainer) |
| XCSE | from 2010-01-01 | 09:00-17:00 | Nasdaq Copenhagen equities, Main Market continuous trading | closing_auction_end | verified | Nasdaq, European Markets Trading Hours |
| XETR | from 2010-01-01 | 09:00-17:35 | Xetra, Continuous Trading with Auctions (equities) | closing_auction_end | unconfirmed (recheck 2027-02-19) | Deutsche Börse |
| XETR | from 2025-12-01 | 09:00-17:35 | Xetra, Continuous Trading with Auctions (equities) | closing_auction_end | verified | Deutsche Börse, Xetra trading parameters as of 1 December 2025 |
| XHEL | from 2010-01-01 | 10:00-18:30 | Nasdaq Helsinki equities, Main Market continuous trading | closing_auction_end | verified | Nasdaq, European Markets Trading Hours |
| XICE | from 2010-01-01 | 09:30-15:30 | Nasdaq Iceland equities, Main Market continuous trading | closing_auction_end | verified | Nasdaq, European Markets Trading Hours |
| XLIT | from 2010-01-01 | 10:00-16:00 | Nasdaq Baltic equities (Vilnius), continuous trading with opening and closing calls | closing_auction_end | verified | Nasdaq Baltic, Trading day |
| XLUX | from 2010-01-01 | 09:00-17:35 | LuxSE regulated market, continuous trading | closing_auction_end | verified | LuxSE, Opening hours, closing days and market status |
| XNYS | from 1990-01-01 | 09:30-16:00 | NYSE (Tape A) Core Trading Session | closing_auction_end | verified | NYSE, Hours & Calendars |
| XPRA | from 2010-01-01 | 09:00-16:15 | PSE shares, Prime and Standard (regulated), continuous trading (Xetra) | closing_auction_end | verified | PSE, Trading hours |
| XPRA | from 2027-01-04 | 09:00-16:55 | PSE shares, continuous trading (Xetra) | closing_auction_end | unconfirmed (recheck 2027-01-04) | PSE notice of 31 July 2026, extension of trading hours |
| XBDA | from 2010-01-01 | 09:00-16:30 | BSX equities, continuous trading | continuous_end | verified | BSX, Trading |
| XBUD | from 2010-01-01 | 09:00-17:05 | BSE equities (pre-Xetra MMTS era and Xetra's first months) | closing_auction_end | unconfirmed (recheck 2027-02-19) | BSE Resolution 550/2013 extract of 25 September 2017 |
| XBUD | from 2015-02-27 | 09:00-17:05 | BSE Equities Prime/Standard Market, Continuous Trading with Auctions (Xetra) | closing_auction_end | verified | BSE Resolution 550/2013 |
| XJSE | from 2010-01-01 | 09:00-17:00 | JSE equity market, Central Order Book, segment ZA01 (Top Companies), Normal Day | closing_auction_end | verified | JSE Specification Document, Volume 00E - Trading and Information Overview, Version 3.06, 23 July 2019 |
| XNZE | from 2010-01-01 | 10:00-17:00 | NZX Main Board, Normal Trading | closing_auction_end | verified | NZX, Anatomy of a trading day |
| XKAR | from 2010-01-01 | 09:30-15:30 | PSX Regular Market (Ready), Monday to Thursday | continuous_end | unconfirmed (recheck 2027-02-19) | PSX, Trading Hours |
| XTAL | from 2010-01-01 | 10:00-16:00 | Nasdaq Baltic equities (Tallinn), continuous trading with opening and closing calls | closing_auction_end | verified, verified_from 2026-05-05 | Nasdaq Baltic, Trading day |
| XRIS | from 2010-01-01 | 10:00-16:00 | Nasdaq Baltic equities (Riga), continuous trading with opening and closing calls | closing_auction_end | verified, verified_from 2026-05-05 | Nasdaq Baltic, Trading day |
| XSTO | from 2010-01-01 | 09:00-17:30 | Nasdaq Stockholm equities, Main Market continuous trading | closing_auction_end | verified, verified_from 2026-11-22 | Nasdaq, European Markets Trading Hours |
| XSHG | from 2010-01-01 | 09:30-15:00 | SSE Main Board stocks: continuous auction and closing call auction | closing_auction_end | verified, verified_from 2026-11-22 | SSE, Trading Schedule |
| XSWX | from 2010-01-01 | 09:00-17:30 | SIX Swiss Exchange, trading segments Shares and Investment Funds (incl. Blue Chip Shares) | closing_auction_end | verified, verified_from 2026-11-22 | SIX, Trading Hours |
| XWBO | from 2010-01-01 | 09:00-17:35 | Wiener Börse equities, prime market, Continuous Trading with Auctions | closing_auction_end | verified, verified_from 2026-11-22 | Wiener Börse, Trading hours |
| XTSE | from 2010-01-01 | 09:30-16:00 | Toronto Stock Exchange equities: continuous trading and the Market on Close (MOC) facility | closing_auction_end | verified, verified_from 2026-11-22 | TMX, Trading hours |
| XTKS | from 1997-01-01 | 09:00-15:00 | TSE cash equities (arrowhead), morning and afternoon sessions | continuous_end | unconfirmed (recheck 2027-02-19) | Tokyo Stock Exchange, 'Final Decision for Extension of Trading Hours', 20 September 2023 |
| XTKS | from 2024-11-05 | 09:00-15:30 | TSE cash equities (arrowhead): morning session, afternoon session ending with the Closing Auction | closing_auction_end | verified, verified_from 2024-11-05 | Tokyo Stock Exchange news release of 5 November 2024; TSE 'Final Decision for Extension of Trading Hours', 20 September 2023; JPX trading-hours page |
| XPHS | from 2010-01-01 | 09:30-15:00 | PSE equities (schedules before 1 March 2022) | continuous_end | unconfirmed (recheck 2027-02-19) | PSE |
| XPHS | from 2022-03-01 | 09:30-14:50 | PSE equities: market open to the pre-close (closing) auction | closing_auction_end | verified, verified_from 2022-03-01 | PSE notice CN-2022-0009, 17 February 2022 |
| XSES | from 2010-01-01 | 09:00-17:06 | SGX-ST securities market (before all-day trading) | closing_auction_end | unconfirmed (recheck 2027-02-19) | SGX |
| XSES | from 2011-08-01 | 09:00-17:06 | SGX-ST securities market, normal day: trading and the Closing Routine | closing_auction_end | verified, verified_from 2011-08-01 | SGX release 'SGX securities market trades all day from 1 August' |
| XSES | from 2017-11-13 | 09:00-17:06 | SGX-ST securities market, normal day: trading 09:00-12:00 and 13:00-17:00, Closing Routine | closing_auction_end | verified, verified_from 2017-11-13 | SGX-ST Regulatory Notice 8.2.1 |
| XTAI | from 2010-01-01 | 09:00-13:30 | TWSE securities market, matching and closing call auction | closing_auction_end | verified, verified_from 2026-11-20 | TWSE, trading system page |
| XZAG | from 2010-01-01 | 09:30-16:00 | ZSE Continuous Trading: opening auction, continuous trading, closing auction | closing_auction_end | verified, verified_from 2026-01-22 | ZSE Trading Manual of 14 January 2026, in force 22 January 2026 |
