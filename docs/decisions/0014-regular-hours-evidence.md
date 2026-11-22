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

**Additional sessions (session 4b2).** A session the exchange itself calls
additional, morning or evening (MOEX's "утренняя (доп.) сессия" and
"вечерняя (доп.) сессия") is not regular, even where the main book trades
in it; where modelled it is `pre_market` or `post_market`. When the main
book splits into securities admitted to such a session, which trade
continuously from it straight into the main session, and securities whose
day starts with the main session's own opening auction, `open` is the start
of continuous trading for the second group: it is the one start of the
regular session that does not depend on which securities the exchange
admits to the additional session, or on whether that session runs at all.
The evidence item names the group. Applied to XMOS: 10:00 until
2026-09-13, 09:10 from 2026-09-14 (shares not admitted to the morning
session); the admitted shares trade continuously from 07:00.

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
`reference_compared` exchange.

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

## Consequences

- `docs/facts.json` `exchanges_hours_verified` counts exchanges whose
  current entry (the one in force on `last_checked`) is `verified`; the
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
| XMOS | from 2013-09-02 | 10:00-18:50 | Main Trading Mode T+, shares not admitted to the morning session | closing_auction_end | verified | MOEX notice of 23 August 2013; MOEX Closing Auction page (start date 2 September 2013) |
| XMOS | from 2026-03-23 | 10:00-19:00 | as above | closing_auction_end | verified | MOEX notice of 11 February 2026 (closing auction 18:55-19:00 from 23 March) |
| XMOS | from 2026-09-14 | 09:10-19:00 | as above (opening auction 09:00-09:10) | closing_auction_end (18:59:30 on the page) | verified | MOEX notice of 14 August 2026; MOEX trading schedule page |
