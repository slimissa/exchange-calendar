# Phase 4f schema backlog

Renamed from `docs/phase-4d-backlog.md` in Phase 4d (the old path keeps a
pointer, because the v2.28.0 release claims name it). Phase 4d became the
verification audit; the schema and API items below go to 4f (schema v3).

## Roadmap after Phase 4c (maintainer decision)

- **4d**: audit `verification` against Phase 4c; coverage spans checkable; housekeeping.
- **4d2**: `in_session` alias in the four wrappers; the `is_open` 3.0.0 meaning change documented (no run-time warning, for parity and to spare per-minute callers).
- **4b-lite**: current regular hours verified against each exchange's own page (ADR 0013, ADR 0014), evidence in `verification.hours` (schema 2.3.0, since 4b1; `schema_limited` for hours the schema cannot express since 2.3.1, 4b2). `check_verification.py` check 6 reports it non-blocking during 4b-lite and **turns blocking for every `reference_compared` exchange at the end of 4b-lite**; `schema_limited` items do not block (ADR 0014 section 6).
- **4e**: predictions.
- **4f**: schema v3 / API (major 3.0.0); this file's "Schema and tooling" items.
- **4g**: consumer alignment (QLF, DeBou) and a CLI.
- **4b full**: session-time verification.
- **5**: verification contract.
- **6**: publication.
- **4h**: the 23 exchanges without a reference library ("Phase 4h" below); interleaved from 4e on, finished before 6.
- **December rechecks** (8-14 Dec, 18-22 Dec): separate sessions, fixed in the calendar.

## Backlog

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
  XMEX is a confirmed case (4b4): BMV's Manual Operativo (v1.97, in force
  23 July 2026) gives 8:30-15:00 and "7:30 a 14:00 horas durante el horario
  de verano EUA"; its hours evidence is `schema_limited` with this item as
  `backlog_item`.
- **Seasonal closes.** The Santiago exchange (XSGO) closes equities at
  16:00 in the southern winter and 17:00 in summer (exchange_calendars'
  close_times; press; DCV 2014). `regular_hours` has no season, so the
  registry keeps one 09:30-16:00 entry, unconfirmed. (4c10)

- **Weekday-specific sessions.** PSX (XKAR) runs two Friday sessions
  (09:17-12:00 and 14:32-16:30, post-close 16:35-16:50) against one
  Monday-Thursday session; `sessions` and `regular_hours` have no weekday.
  (4c13) Hours evidence for such an entry is `schema_limited` with
  `backlog_item: "Weekday-specific sessions"` (ADR 0014 section 6, 4b2);
  lifting this item means migrating those items.
- **Seasonal (Ramadan) hours.** PSX (XKAR) and the Saudi Exchange (XSAU)
  publish Ramadan schedules each year; there is no seasonal or dated-range
  session entry. (4c13)
- **Half days as early closes.** PSE (XPHS) half days (for example 24 and
  31 December 2021 under CN-2021-0063) are not modelled; the 2010-2022 PSE
  schedule history is not built either. (4c12, 4c13)
- **Dated weekend.** The Saudi weekend moved from Thursday-Friday to
  Friday-Saturday in 2013; `weekend_days` has no `effective_from`. Needed only
  if XSAU 2010-2020 is backfilled (Phase 4h). (4c13)
- **Continuous close (ADR 0013).** See the continuous-close field above:
  4c13's XSAU (15:00 continuous, 15:10 auction end) and XPHS (14:45 / 14:50)
  are two more cases.
- **API: split registry `is_open`** into `is_open` (regular session) and
  `in_session` (any interval). The alias exists since 4d2 (2.29.0): Python
  `in_session`, JS `inSession`, Go `InSession`, Rust `in_session`, each
  delegating to the same function as the registry-level `is_open`, with a
  cross-language twin for every `is_open` probe. 3.0.0 only flips the meaning
  of the registry-level `is_open` to regular hours (what the exchange-level
  `is_open` returns today); `in_session` keeps the any-session meaning. The
  deprecation is documented (README, wrapper READMEs, CHANGELOG), not emitted.
  Until 3.0.0 both registry calls follow the (b1) contract settled in
  4c-final-1: any pre_market/regular/post_market interval,
  `early_close_time` ignored, `lunch_break` spanned, ad hoc rows closing the
  day only when `closed`. (4c13, 4c-final, 4c-final-1, 4d2)
- **`lunch_break` after the regular close:** XKUW (09:00-12:30, break
  12:30-13:00), XLIM (09:00-13:30, break 13:30-14:30) and XSTC (09:00-11:30,
  break 11:30-13:00) have a `lunch_break` session with no trading interval
  after it, so the session data does not describe an afternoon session (or
  the "break" is not one). No exchange document read; data unchanged.
  (4c-final-1)

## Phase 4h (backfill without a reference library)

No reference library covers these, so a 2010-2024 backfill must come from
the exchange's own archives, by hand. Their `generation_range` starts
2025-01-01 (README, Known limitations):

- DSMD, XATH, XBAH, XBEY, XBRV, XBSP, XBUL, XCAI, XCAS, XCAY, XCOL, XDFM,
  XDHA, XGSE, XJKT, XKUW, XMAL, XMUS, XNAI, XNSA, XSTC, XTAD, XTUN (23).
- XSAU 2010-2020: exchange_calendars starts XSAU in 2021; 2010-2020 also
  crosses the 2013 weekend change (dated weekend, above).

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
