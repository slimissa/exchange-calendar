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
- **The 17 disputed days:** XBOM (8) and XNSE (9), held in `contradicted_by`
  (151fc60). The BSE and NSE notices for those days are the primary source.
  The other `contradicted_by` entries (XBUD 4, XMOS 16, XSHG 18) are tracked
  in each file's note.
