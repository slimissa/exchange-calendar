# Phase 4d backlog

Items the 4c backfills and the 4c-R1 to 4c-R5 rechecks found but did not
fix. They need a schema field, a tooling decision, or an exchange document
that could not be read. Each line names the session that found it. Nothing
here is scheduled; [README §25](../README.md#25-whats-next) lists the
trigger.

## Schema and tooling

- **`regular_hours.current()` returns a future-dated entry.** XPRA's undated
  sessions and the SQL export show 16:55 before the 2027-01-04 change takes
  effect, because "current" means the latest entry. (4c-R5)
- **Dated sessions.** A `sessions` entry cannot carry `effective_from`, so an
  undated session describes the latest dated `regular_hours` entry (repository
  rule). XPRA shows its 2027 regular session today. (4c-R5)
- **A field for unconfirmed hours.** `coverage.unconfirmed` holds dates whose
  status is in doubt. XPRA (2027-01-04), XBUD (2010-01-01) and XOSL
  (2012-08-06) reuse it, with an effective date, for an hours entry. XDUB
  (2019-02-04) did too until 4c8. (4c-R4, 4c-R5, 4c8)
- **Continuous-close field.** ADR 0013 stores the end of the closing auction;
  the end of continuous trading, which the reference libraries use, has no
  field. (4c-R3.5, ADR 0013)
- **Timed special sessions.** A `special_session` cannot carry a time, so
  KRX's CSAT day (10:00-16:30, 4c-R1) and NSE/BSE's Muhurat evening session
  (4c-R2) are not modelled.
- **Later close on a delayed-open day.** `delayed_open_time` exists, but a day
  that opens late *and* closes late (KRX CSAT day, closing 16:30) cannot be
  expressed. (4c-R1)
- **Sessions that follow another market's daylight saving time.** BVC
  (XBOG) moves its equity session with New York DST: press reports give
  8:30-15:00 Bogota while New York is on EDT and 9:30-16:00 while it is on
  EST, and exchange_calendars models it as 9:30-16:00 America/New_York. The
  registry's single 09:30-15:00 America/Bogota mixes the two (EST open, EDT
  close); it is kept, unconfirmed, until a timezone or seasonal-entry model
  exists and a BVC document is read. (4c10)
- **Seasonal closes.** The Santiago exchange (XSGO) closes equities at
  16:00 in the southern winter and 17:00 in summer (exchange_calendars'
  close_times; press; DCV 2014). `regular_hours` has no season, so the
  registry keeps one 09:30-16:00 entry, unconfirmed. (4c10)

## Data leads (no exchange document read yet)

- **XICE pre_market:** the Nasdaq Nordic Market Model row puts the pre-open
  at 09:00 CET standard, which is 08:00 Reykjavik; the registry has 09:00.
  (4c-R4)
- **XWAR post_market:** WATS trading at last ends 17:05; the registry's
  post-market ends 17:10. (4c-R4)
- **XWAR close before 2013-04-15:** broker reports of GPW Resolution 933/2010
  give a 17:20-17:30 closing call from 2011-01-03; the resolution was not
  found on gpw.pl. The registry keeps 17:00. (4c-R4)
- **XCSE and XICE closes before the current market model:** only Market
  Model 2026:03 was read. (4c-R4)
- **XLIM hours:** the registry has 09:00-13:30 plus a 13:30-14:30
  `lunch_break` session; exchange_calendars has 09:00-16:00 with no break,
  and press (Gestión, March 2025) reports a nuam proposal to change BVL's
  schedule. No BVL document could be read, so the ADR 0013 close is not
  established; `regular_hours` is one entry from 2010-01-01, unconfirmed.
  (4c10)
- **Browser-only exchange pages.** Pages that render their tables
  client-side need a connected browser; none was connected in 4c10:
  - **XKLS 16:50:** Bursa's trading-sessions page and trading manual refuse
    this sandbox; 16:50 (Closing, before Trading at Last 16:50-17:00) rests on
    a search snippet and broker republications, unconfirmed. (4c9, 4c10)
  - **XNZE 2026-2027 abbreviated days:** NZX's memo "NZX Market Holidays -
    2025/2027" lists them in an attachment that is robots-blocked
    (api.nzx.com), and the Hours & Boards table (13:00 closing auction) is
    client-rendered. The four dates are predicted early closes at 13:00,
    unconfirmed, `recheck_date` 2026-12-15. (4c10)
- **The 17 disputed days:** XBOM (8) and XNSE (9), held in `contradicted_by`
  (151fc60). The BSE and NSE notices for those days are the primary source.
  The other `contradicted_by` entries (XBUD 4, XMOS 16, XSHG 18) are tracked
  in each file's note.
