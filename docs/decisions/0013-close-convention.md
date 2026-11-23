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
closing auction**: the uncross time the exchange publishes, read under
the random-closing rule below. Trading at Last
and other post-close phases are not part of the regular session; where
modelled they are a `post_market` session.

A dated `regular_hours` list (`effective_from`) is used when the auction
end changed inside the registry window; a single object when it held
throughout.

### Random closing windows (maintainer decision, session 4b5)

This replaces the earlier wording ("the end of the window"), which the
table below applied two ways: XDUB half days took the end of a window,
XBKK and XNZE took its scheduled start.

- **A random window of one minute or more:** the close is the window's
  end. XHKG 16:08-16:10 -> 16:10; SET 16:35-16:40 -> 16:40; QSE
  13:09-13:10 -> 13:10; Euronext Dublin half days 12:28-12:30 -> 12:30.
- **Random jitter of seconds after a stated time:** the close is the
  stated minute. Euronext 17:35:00-17:35:30 -> 17:35; likewise LSE, KRX,
  TSE (15:29:30-15:30:00 from 2027-10-12 -> 15:30) and Boursa Kuwait's
  last 30 seconds of the closing auction.
- A window that ends on a second rather than a whole minute is recorded
  under ADR 0014 section 2 (the minute the exchange's own notice states,
  else the next whole minute).
- **A stated time with jitter around it ("T +/- N seconds"):** the close
  is the stated time T. Only a window written as a range (from-to) gives
  its end. Example: BRVM attaches "une période aléatoire de +/- 60
  secondes" to every time on its page, the opening fixing included; its
  closing fixing "14 h 30 mn" gives 14:30, not 14:31 (maintainer decision,
  session 4b6).

### Audit of the applied table against the random-closing rule (session 4b5)

Every row of "Applied in 4c-R3.5", "Already conforming" and "Exceptions
left in place" was re-read against the rule. Rows not listed here do not
change: their close is a fixed uncross time, the end of continuous
trading, or a seconds-long random end after the stated minute (Euronext
core and Lisbon 17:35, XDUB full day "17:30 Random", XOSL "16:25 Random",
XLIT, XTAL and XRIS 15:59:30-16:00:00, XZAG up to 15 seconds after 16:00,
XSAU within 30 seconds after 15:10), or a window that already ends at the
recorded close (XDUB half days 12:28-12:30, XHKG 16:08-16:10).

| Row | Recorded | Window as cited | Under the rule | Changed in 4b5 |
|-----|----------|-----------------|----------------|----------------|
| XBKK | 16:35 | "closing time randomly selected between 16:35 and 16:40" | 16:40 | No: no SET page attached (listed for 4b6) |
| XNZE | 17:00 | "random time between 16:59:30 and 17:00:30" (one minute) | the window's end, 17:00:30: 17:00 if NZX's own notice states that minute, else 17:01 (ADR 0014 section 2) | No: NZX's page refuses the fetcher and none was attached |
| XJSE | 17:00 | Market Notice 2719: "earliest close 17:00:00 with a random uncross to 17:01" (one minute) | 17:01 | No: no JSE document attached |
| XETR, XWBO, XBUD | 17:35, 17:35, 17:05 | Xetra-type random end after the stated time; the documents cited give no length | the stated minute if the random end is seconds; the window's end if it is a minute or more | No: length to be read from the trading-parameter documents |
| XSWX | 17:30 | SIX closing auction with a random end; length not cited | as for XETR | No: length to be read from SIX's trading provisions |

Applied in 4b5 (random-closing rule, exchange documents attached):

- XKUW: 13:10 from 2025-10-12 (Boursa Kuwait: closing auction 13:00-13:10, random close in the last 30 seconds -> the stated minute).
- XMAD: 17:35 from 2026-11-23 (BME Circular 1/2026: closing auction 17:30-17:35, "shall end at any time within a random period of at most 30 seconds from 5.35pm" -> the stated minute; 4b6).
- XBRV: 14:30 UTC from 2026-11-22 (BRVM: closing fixing "14 h 30 mn" with "une période aléatoire de +/- 60 secondes", a stated time with jitter -> the stated time; 4b5 recorded 14:31 as the end of a two-minute window, corrected in 4b6).

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
| XOSL half days 2023-2027 | 13:00 | 13:05 Oslo (2023, 2024, 2026 in 4c-R5; 2025, 2027 in 4c8; 2028-2029 predicted by rule) | Euronext's Oslo Børs half-day schedules (euronext.com media 7620, 10309, 12510, 14571, 16430): call 13:00-13:05, uncrossing 13:05, Trading At Last 13:05-13:10 |
| XOSL full day | 16:30 | 16:25 Oslo from 2012-08-06 (4c8; 2012-08-06 to 2026-08-02 unconfirmed) | Euronext's Appendix to Instructions 4-01/4-03 (effective 2026-08-03): Oslo equities continuous to 16:20, closing uncross '16:25 Random', Trading at Last 16:25-16:30 |
| XBUD | 17:00 | 17:05 Budapest (4c-R4), 2010-2029 | BSE Resolution 550/2013 (Xetra trading parameters): continuous until 17:00, closing auction call 17:00-17:05, price determination 17:05 + random end; versions effective 2015-02-27, 2018-01-02 and 2026-04-08. 2010 to 2015-02-26 unconfirmed (4c-R5) |
| XBUD 2019-11-29 | full day | early close 14:05 (4c-R4) | BSE CEO Resolution 387/2019: closing call 14:00-14:05, price determination 14:05 |
| XETR | 17:30 | 17:35 Frankfurt (4c8), 2010-2029; 2010-01-01 to 2025-11-30 unconfirmed | Deutsche Börse, Xetra trading parameters as of 2025-12-01: closing auction call 17:30, closing auction price 17:35; the auction schedule says auctions have a random end and the stated times are the earliest ends |
| XETR last trading day | 14:00 (exchange_calendars) | early close 14:05 (4c8): 2025-12-30 confirmed; 2026-12-30 unconfirmed (recheck 2026-12-15); 2027-2029 predicted | Deutsche Börse, Final trading session 2025: closing auction call from 14:00, earliest price determination 14:05. The 2010-2024 backfill keeps 14:00 (see exceptions) |
| XSES | 17:00 | 17:06 Singapore (4c8), 2010-2029; 2010-01-01 to 2011-07-31 unconfirmed | SGX-ST Regulatory Notice 8.2.1: Pre-Close 17:00 to 17:04-05 (random), Non-Cancel to 17:06; para 3.6(a): the Closing Routine ends at 17:06. 4c9 confirmed 17:06 is fixed, not the end of a random window |
| XSES half days | 12:30 | 12:06 Singapore: 2025-2027 (4c8), 2028-2029 predicted (4c9) | same notice: half-day Pre-Close 12:00 to 12:04-05, Closing Routine ends at 12:06; SGX-ST rule amendments of 2017-11-13 moved it from 12:30-12:36 |
| XWBO | 17:30 | 17:35 Vienna (4c8), 2010-2029; 2010-01-01 unconfirmed | Wiener Börse trading hours: equity closing auction 17:30-17:35 ("earliest end"), trade at close 17:35-17:45 |
| XWBO last trading day | none for 2025-2029 | early close 14:20 (4c8, derived): 2025-12-30; 2026-12-30 unconfirmed (recheck 2026-12-15); 2027-2029 predicted | Wiener Börse news, 30 December 2025: closing auction starts at 14:15; 14:20 adds the 5-minute auction of the trading-hours page, so the end time is derived, not stated |
| XJSE early closes | none | 12:00 Johannesburg on 24 and 31 December (4c8) | JSE Service Hotline 130/2025: closing auction call 11:50-12:00, close of trading 12:00 |
| XNZE | 16:45 | 17:00 Auckland (4c9; re-read in 4c10), 2010-2029; 2010-01-01 unconfirmed | NZX, Anatomy of a trading day: Pre-Close from 16:45, closing auction at a random time between 16:59:30 and 17:00:30, Adjust to 17:30; the random window is ignored and 17:00 is its scheduled time |
| XNZE abbreviated days | none for 2025-2029 | 13:00 Auckland (4c9, 4c10): 2025-12-24 and 2025-12-31 (dates confirmed, time unconfirmed); 2026-2029 predicted (2026-2027 unconfirmed, recheck 2026-12-15) | NZX notices of 2024-12-11 and 2025-12-02: abbreviated hours "closing at 1.30pm", the session end (an upper bound, like 17:30 on a normal day). The 13:00 closing auction (Pre-Close 12:45-13:00) is from NZX's Hours & Boards table, read only as a search snippet |
| XKLS | 17:00 | 16:50 Kuala Lumpur (4c9), 2010-2029; unconfirmed (4c10: Bursa's own page still not read) | Bursa Malaysia equities trading-sessions page, read only as a search snippet: Pre-Closing 16:45, Closing 16:50, Trading at Last 16:50-17:00; Bursa's pages refuse this sandbox and only broker republications were found in 4c10 |
| XBKK | 16:30 | 16:35 Bangkok (4c9), 2010-2029 | SET, opening/closing price calculation: pre-close from 16:30, closing time randomly selected between 16:35 and 16:40; the scheduled close is the start of the random window |
| XLUX | 17:30 | 17:35 Luxembourg (4c9), 2010-2029 | LuxSE trading-hours page: continuous trading 09:00-17:30, closing call 17:30-17:35, trading at last 17:35-17:40 (exchange_calendars has 17:40) |

Already conforming: XSTO (17:30 / 13:00), XHEL (18:30), XDUB full day
(16:30; confirmed in 4c8 by Euronext's Appendix to Instructions 4-01/4-03: Dublin
equities close call 17:28-17:30 CET, uncross '17:30 Random' = 16:30 Dublin) and half days 2022+ (12:30), Euronext core half days (14:05 CET),
XSWX (17:30). Confirmed and kept in 4c8: XTAI (13:30; TWSE trading-system
page, closing call 13:25-13:30 and closing match at 13:30; the 13:33 closing
delay applies only to flagged securities) and XJSE (17:00; JSE Volume 00E
closing auction call 16:50-17:00, Market Notice 2719 earliest close 17:00:00
with a random uncross to 17:01). Confirmed in 4c-R4 against the exchange's own document:
XCSE (17:00; Nasdaq Nordic Market Model 2026:03, closing uncross 17:00),
XICE (15:30 Reykjavik; same model, closing uncross 16:30 CET standard),
XWAR (17:00 from 2026-10-05; GPW WATS Detailed Exchange Trading Rules,
closing auction 16:50-17:00) and XPRA (16:15 until 2027-01-03; PSE
Trading-hours.pdf, closing auction 16:10-16:15). Confirmed in 4c9: XLIT (16:00; Nasdaq Baltic
trading-day structure, closing call 15:59:30-16:00:00 with a random uncross,
so the scheduled close is 16:00). Confirmed in 4c11-4c13 (value unchanged): XTAL
and XRIS (16:00; the same Nasdaq Baltic structure; one dated entry from
2010-01-01, unconfirmed for 2010), XZAG (16:00; ZSE Trading Manual of
2026-01-14, closing auction 15:55-16:00 with a random end up to 15 seconds
later) and XKAR (15:30; PSX trading-hours page, Monday-Thursday continuous
trading to 15:30 and no closing auction; one dated entry from 2010-01-01,
unconfirmed).

## Exceptions left in place

| Exchange | Value kept | Why |
|----------|------------|-----|
| XOSL half days 2011-2022 | 13:00 (unconfirmed) | No readable Euronext schedule (Oslo joined Euronext in 2019; 2022's PDF is binary). Narrowed in 4c-R5 and 4c8: 2023-2027 are 13:05 and 2028-2029 are predicted at 13:05 (see the applied table). |
| XDUB half days 2010-2018 | 12:28 | ISE Xetra (Deutsche Börse) era, before Euronext Dublin moved to Euronext's Optiq on 2019-02-04 (Euronext press release of that date); no half-day schedule found. |
| XWAR before 2013-04-15 | 17:00 | Warset era. Broker reports of GPW Resolution 933/2010 give a 17:20-17:30 closing call from 2011-01-03, but the resolution was not found on gpw.pl. The UTP era (2013-04-15 to 2026-10-02) has the WATS schedule only in republished GPW announcements. |
| XPRA from 2027-01-04 | 16:55 (unconfirmed, recheck 2027-01-04) | PSE's notice of 2026-07-31 confirms the date and the 17:00 end of day; the phase schedule is an image that could not be read, and 16:55 comes from a press transcription. |
| XBUD 2010 to 2015-02-26 | 17:05 (unconfirmed) | No BSE trading-parameter document found before the 550/2013 schedule effective 2015-02-27. |
| XETR last trading day 2010-2024 | 14:00 (exchange_calendars) | 4c8 backfill; the end of continuous trading, not the auction end. No Deutsche Börse final-session notice before 2025 was read. |
| XLIM | 13:30 (unconfirmed) | No BVL document read; exchange_calendars has 09:00-16:00 with no break and press reports a schedule proposal (4c10). |
| XSGO early closes 2010-2024 | 13:30 (exchange_calendars) | 4c10 backfill; Bolsa de Santiago's closing-auction schedule for those years was not read (convention difference against the registry's 2025 13:00 early closes). |
| XWBO last trading day 2017-2024 | 14:15 (exchange_calendars) | 4c8 backfill; the start of the shortened closing auction. The Wiener Börse notices actually seen cover 2018-2024 (corrected in 4c10; this row said 2017-2024) and give the same 14:15 start, so ADR 0013 would give 14:20; 2017 rests on exchange_calendars alone. Not changed. |
| XNZE abbreviated days 2011-2024 | 12:45 (exchange_calendars) | 4c9 backfill; the end of continuous trading. ADR 0013 would give 13:00 (the convention applied from 2025). exchange_calendars has no 2010 abbreviated days. |
| XKLS half days 2010-2024 | 12:30 (exchange_calendars) | 4c9 backfill; the end of Trading at Last. Bursa's own half-day notices (e.g. Chinese New Year 2015) give Closing 12:20, so ADR 0013 would give 12:20. |
| XPHS full day | 15:00 (continuous) | 14:50 Manila from 2022-03-01 (4c13); 2010 entry unchanged, unconfirmed | PSE CN-2022-0009 (effective 1 March 2022): pre-close 14:45-14:50, run-off/trading at last 14:50-15:00 (post_market), recess 12:00-13:00 |
| XSAU full day | 15:00 | 15:10 Riyadh (4c13), from 2021-01-01, unconfirmed before 2026-11-20 | Saudi Exchange trading cycle and times page (read 2026-11-20; no effective date): market open 10:00-15:00, closing auction 15:00-15:10, trade at last 15:10-15:20 (post_market); close randomised within 30 seconds after 15:10, ignored |
| XBDA | 16:00 | 16:30 Atlantic (4c11), from 2010-01-01, unconfirmed | BSX trading page: 'Trading Hours are Monday through Friday 9:00 a.m. - 4:30 p.m.'; continuous trading after an 08:30-09:00 price discovery, no closing auction, so the close is the end of continuous trading (press dates the 16:30 close from 2016-09-28; BSX's announcement not read) |

Each exception is also in the exchange's `note`. Exchanges not yet
rechecked (4c-R4, 4c-R5 and the non-backfilled exchanges) are brought to
this rule as they are rechecked.

## Phase 4d plan

Add a second field for the end of continuous trading (for example
`regular_hours.continuous_close` and `continuous_close_time` on a half
day), so both times are available, the libraries' convention can be
compared directly, and `convention_difference` stops being needed for
these cases. Schema change, so a schema version bump.
