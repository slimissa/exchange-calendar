# ADR 0014 — Regular hours: segment, close rule, evidence

**Status:** Accepted
**Date:** 2026-11-21
**Decided by:** the CTO (Phase 4b-lite brief, session 4b1)

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

### 2. Close rule (ADR 0013)

- The segment has a closing auction: `close` is the end of the closing
  auction (the published uncross time, or the end of a random window).
  `close_rule: "closing_auction_end"`.
- The segment has no closing auction (a VWAP or last-trade close, or
  continuous trading to the end): `close` is the end of continuous
  trading. `close_rule: "continuous_end"`. This is the rule already applied
  to XKAR and XBDA in ADR 0013.

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
| `status` | `verified` or `unconfirmed` |
| `recheck_date` | Required when `unconfirmed` |
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

## Consequences

- `docs/facts.json` `exchanges_hours_verified` counts exchanges whose
  current entry (the one in force on `last_checked`) is `verified`; the
  README states it.
- Wrappers do not read `verification.hours` yet (unknown keys are ignored
  by all four); exposing it is a 4f question.
- Pre/post-market, auctions and lunch breaks are out of scope until 4b full.

## Applied (filled as 4b-lite proceeds)

None yet: rows are added here as exchanges get `verification.hours`,
with the columns Exchange, Entry, Hours, Segment, Close rule, Status,
Source.
