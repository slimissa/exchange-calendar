# ADR 0013 — Close time = end of the closing auction

**Status:** Accepted
**Date:** 2026-11-20
**Decided by:** the maintainer (4c-R3 report, 4c-R3.5 brief)

## Context

The registry stores one close time per session: `regular_hours.close`
(and the regular entry of `sessions[]`) for a full day, and
`early_close_time` for a half day. Exchanges that run a closing auction
publish two candidate times: the end of continuous trading and the
closing auction's uncross. Until 4c-R3 the registry mixed them, sometimes
inside one file. Euronext Amsterdam, Brussels, Lisbon and Paris stored
17:30 CET (the end of continuous trading) for full days but 14:05 CET
(the end of the half-day auction) for half days. XOSL, XPRA and XSWX had
already been set to the auction end in 4c5, 4c7 and 4c-R1.

## Decision

`regular_hours.close` and `early_close_time` hold the **end of the
closing auction**: the uncross time the exchange publishes. Where the
uncross has a random end inside a window (Euronext Dublin's 12:28-12:30
on half days), the registry holds the end of the window. Trading at Last
and other post-close phases are not part of the regular session; where
modelled they are a `post_market` session.

A dated `regular_hours` list (`effective_from`) is used when the auction
end changed inside the registry window; a single object when it held
throughout.

## Why

The official closing price, the one indices, funds and benchmarks use,
is set by the closing auction. A consumer asking "when is the close" for
an exchange with a closing auction means that time. It is also the
time the exchange's own documents give as the close of the trading day.

## Consequences

- The reference libraries (exchange_calendars, pandas_market_calendars)
  generally use the end of continuous trading. Session-time comparisons
  (`divergence_test.py --mode sessions`) on these exchanges therefore
  differ by the length of the auction; those differences are classified
  `convention_difference`, not errors.
- A consumer that needs the end of continuous trading cannot derive it
  from the registry yet (see the Phase 4d plan).

## Applied in 4c-R3.5

| Exchange | Was | Now | Source |
|----------|-----|-----|--------|
| XAMS, XPAR, XBRU | 17:30 | 17:35 CET, 2010-2029 | Euronext announcement of 2007-02-16, effective 2007-02-19: pre-closing 17:30-17:35, closing auction at 17:35 CET; FESE trading-hours tables 2024 and 2026 |
| XLIS | 16:30 | 16:35 Lisbon (17:35 CET), 2010-2029 | as above |
| XPAR sessions | auction at 17:30, post_market 17:30-17:35 | auction at 17:35, post_market (Trading at Last) 17:35-17:40 | as above |
| XDUB half days 2019 | 12:28 | 12:30 Dublin (4c-R4; 4c-R3.5 had 13:05) | Euronext's trading hours & holidays page, "Calendar of business days 2019": Dublin equities close between 12:28 and 12:30 Dublin time. The October 2018 release's "by 14:05 CET" is an upper bound, not an auction end. |
| XDUB half days 2020-2021 | 12:28 | 12:30 Dublin | Euronext's 2020 and 2021 holiday calendars: Dublin equities close between 12:28 and 12:30 Dublin time |

Already conforming: XSTO (17:30 / 13:00), XHEL (18:30), XDUB full day
(16:30) and half days 2022+ (12:30), Euronext core half days (14:05 CET),
XPRA (16:15, then 16:55 from 2027-01-04), XSWX (17:30).

## Exceptions left in place

| Exchange | Value kept | Why |
|----------|------------|-----|
| XOSL full day | 16:30 | Secondary sources (FESE, brokers) give continuous to 16:20, closing auction 16:20-16:25, Trading at Last 16:25-16:30, which would make the auction end 16:25. Euronext's own cash trading-hours document (euronext.com media 1927) could not be read in 4c-R3.5. Rule: change only on the exchange's own document. |
| XOSL half days | 13:00 | Euronext's own 2024 half-day schedule gives the uncross at 13:05 (closed 13:10), but only for 2024; the 2025-2027 schedule PDFs could not be read and 2011-2023 have none. Changing one year would split the series. |
| XDUB half days 2010-2018 | 12:28 | ISE Xetra (Deutsche Börse) era, before Euronext Dublin moved to Euronext's Optiq on 2019-02-04 (Euronext press release of that date); no half-day schedule found. |

Each exception is also in the exchange's `note`. Exchanges not yet
rechecked (4c-R4, 4c-R5 and the non-backfilled exchanges) are brought to
this rule as they are rechecked.

## Phase 4d plan

Add a second field for the end of continuous trading (for example
`regular_hours.continuous_close` and `continuous_close_time` on a half
day), so both times are available, the libraries' convention can be
compared directly, and `convention_difference` stops being needed for
these cases. Schema change, so a schema version bump.
