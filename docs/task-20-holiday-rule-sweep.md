# Task 20: holiday-rule sweep

**Status:** in progress, started 2026-10-07. Updated as each cluster is resolved.
**Goal:** find real exchange closures that have no rule or entry in a `built`
exchange's source file, and add them with a citable source.
**Why this file exists:** the first pass produced a 122-candidate table that lived
only in a session transcript. This is the durable copy.

## Running status

| Cluster | Candidates | State |
|---------|-----------|-------|
| XICE | 4 | **resolved 2026-10-07** (tier 3, corroborated; see `BLOCKED.md`) |
| XCOL | 19 | **2026 resolved 2026-10-07** (13 candidates, tier 1 circular); 2025 (6 candidates), 2027 and Vesak week open, see `BLOCKED.md` |
| XGSE | 11 | untouched |
| XBUE | 12 | untouched |
| XBUD | 4 | untouched |
| XBRV, XCAY, XDFM, XMOS, XRIS, XSHE, XSTC | 37 | untouched |
| XDUB, XLIT, XZAG | 5 | untouched, unclear |
| XETR, XPAR, XMAD, XNYS, XNAS | 30 | untouched, need a "trades on this holiday" comment each, not a rule |

Recommended order: XICE, XCOL, XGSE, XBUE, XBUD, then the rest of the likely closures.

## Method and its limits

- Scope: the 40 exchanges marked `built` in `BLOCKED.md`, years 2025 and 2026.
- Detector: the `holidays` PyPI package, one `country_holidays(country_code)` per
  exchange. A candidate is a public holiday on a weekday (by the exchange's own
  `weekend_days`) that is neither explicit nor generated in `calendar.json`.
- **A public holiday is not an exchange closure.** Exchanges trade on some public
  holidays (Euronext on Bastille Day, NYSE on Columbus Day) and close on days that are
  not public holidays. Every row below is a candidate, not a gap.
- **The `confidence` notes cannot be used.** They hold only the word "predicted"
  (213 entries) and no holiday names, so the repo has no per-exchange name list to
  compare against.
- The detector cannot find a closure that is neither a public holiday nor already in
  the data. June 30 Revolution Day (XCAI) was found by hand, not by this method.
- Triage classes are my judgment from general knowledge of each exchange's calendar.
  Only XICE is confirmed against a source (Nasdaq CSD Iceland's settlement calendar
  and LuxCSD's non-business-day list, both tier 3 under `CONTRIBUTING.md` since they
  are settlement calendars, not the exchange's own notice).
- Correction to the first report: the table covers **20** exchanges, not 22, and the
  classes total 4 confirmed, 83 likely closures, 30 likely non-closures and 5 unclear.
  The first report said "about 100" and "36".
- Candidate names are English where the package supports it. Dates are the package's.

## Stop condition and why it still applies

The sweep stops and reports when a batch finds more than a handful of missing real
closures, because each one needs its own citable source (`CONTRIBUTING.md`, "Citing
Sources for Holiday Dates"), and adding many unsourced rules at once is how the XCAI
dates went wrong. The first pass hit it on XICE alone (4 closures). It still applies:
83 likely closures remained after XICE and 70 after XCOL 2026. A candidate with no citable source does not become a rule;
it stays open here with the source named.

## Candidate table (122 candidates, 20 exchanges)

| Exchange | Country | Count | Class | Status | Candidates (date, name) |
|----------|---------|-------|-------|--------|-------------------------|
| XCOL | LK | 19 | Likely closure | 2026 resolved; 2025 open | 2025-01-13 Duruthu Full Moon Poya Day; 2025-02-04 Independence Day; 2025-02-26 Maha Sivarathri Day; 2025-03-31 Eid al-Fitr; 2025-04-18 Good Friday; 2025-09-05 Prophet's Birthday; 2026-01-15 Tamil Thai Pongal Day; 2026-02-04 Independence Day; 2026-03-02 Medin Full Moon Poya Day; 2026-04-01 Bak Full Moon Poya Day; 2026-04-03 Good Friday; 2026-04-13 Day Before Sinhala and Tamil New Year; 2026-05-28 Eid al-Adha; 2026-06-29 Poson Full Moon Poya Day; 2026-07-29 Esala Full Moon Poya Day; 2026-08-26 Prophet's Birthday; 2026-08-27 Nikini Full Moon Poya Day; 2026-11-24 Il Full Moon Poya Day; 2026-12-23 Unduvap Full Moon Poya Day |
| XBUE | AR | 12 | Likely closure | untouched | 2025-04-17 Maundy Thursday; 2025-05-02 Bridge Public Holiday; 2025-06-16 Pass to the Immortality of General Don Martín Miguel de Güemes; 2025-08-15 Bridge Public Holiday; 2025-11-21 Bridge Public Holiday; 2025-11-24 National Sovereignty Day; 2026-03-23 Bridge Public Holiday; 2026-06-15 Pass to the Immortality of General Don Martín Miguel de Güemes; 2026-07-10 Bridge Public Holiday; 2026-11-09 Visit of His Holiness Pope Leo XIV; 2026-11-23 National Sovereignty Day; 2026-12-07 Bridge Public Holiday |
| XGSE | GH | 11 | Likely closure | untouched | 2025-03-31 Public Holiday; 2025-04-01 Public Holiday; 2025-06-06 Eid-ul-Adha; 2025-07-01 Republic Day; 2025-07-04 Public Holiday; 2025-09-22 Public Holiday; 2026-01-09 Public Holiday; 2026-03-20 Eid-ul-Fitr; 2026-05-27 Eid-ul-Adha; 2026-07-01 Republic Day; 2026-07-03 Public Holiday |
| XPAR | FR | 11 | Likely non-closure | untouched | 2025-05-08 Victory Day; 2025-05-29 Ascension Day; 2025-06-09 Pentecost Monday; 2025-07-14 National Day; 2025-08-15 Assumption Day; 2025-11-11 Armistice Day; 2026-05-08 Victory Day; 2026-05-14 Ascension Day; 2026-05-25 Pentecost Monday; 2026-07-14 National Day; 2026-11-11 Armistice Day |
| XBRV | CI | 10 | Likely closure | untouched | 2025-03-27 Day after Night of Power; 2025-03-31 Day after the Eid al-Fitr; 2025-06-06 Eid al-Adha; 2025-08-07 Independence Day; 2025-09-04 Day after Prophet's Birthday; 2026-03-16 Day after Night of Power; 2026-03-20 Eid al-Fitr; 2026-05-27 Eid al-Adha; 2026-08-07 Independence Day; 2026-08-25 Day after Prophet's Birthday |
| XDFM | AE | 8 | Likely closure | untouched | 2025-03-31 Eid al-Fitr Holiday; 2025-04-01 Eid al-Fitr Holiday; 2025-06-03 Day of Arafah; 2025-06-04 Eid al-Adha; 2025-06-05 Eid al-Adha Holiday; 2025-06-06 Eid al-Adha Holiday; 2026-05-26 Day of Arafah (estimated); 2026-06-16 Islamic New Year (estimated) |
| XCAY | KY | 6 | Likely closure | untouched | 2025-03-05 Ash Wednesday; 2025-04-30 General Election Day; 2025-05-05 Emancipation Day; 2025-06-23 King's Birthday; 2026-05-04 Emancipation Day; 2026-06-22 King's Birthday |
| XMAD | ES | 6 | Likely non-closure | untouched | 2025-01-06 Epiphany; 2025-08-15 Assumption Day; 2025-12-08 Immaculate Conception; 2026-01-06 Epiphany; 2026-10-12 National Day; 2026-12-08 Immaculate Conception |
| XETR | DE | 5 | Likely non-closure | untouched | 2025-05-29 Ascension Day; 2025-06-09 Pentecost Monday; 2025-10-03 German Unity Day; 2026-05-14 Ascension Day; 2026-05-25 Pentecost Monday |
| XRIS | LV | 5 | Likely closure | untouched | 2025-05-02 Day off (substituted from 05/10/2025); 2025-05-05 Restoration of Independence Day (observed); 2025-11-17 Day off (substituted from 11/08/2025); 2026-01-02 Day off (substituted from 01/17/2026); 2026-06-22 Day off (substituted from 06/27/2026) |
| XSTC | VN | 5 | Likely closure | untouched | 2025-05-02 Day off (substituted from 04/26/2025); 2025-09-01 National Day; 2026-08-31 Day off (substituted from 08/22/2026); 2026-09-01 National Day; 2026-11-24 Vietnam Cultural Day |
| XBUD | HU | 4 | Likely closure | untouched | 2025-05-02 Day off (substituted from 05/17/2025); 2025-10-24 Day off (substituted from 10/18/2025); 2026-01-02 Day off (substituted from 01/10/2026); 2026-08-21 Day off (substituted from 08/08/2026) |
| XICE | IS | 4 | Confirmed | resolved | 2025-04-24 First Day of Summer; 2025-08-04 Commerce Day; 2026-04-23 First Day of Summer; 2026-08-03 Commerce Day |
| XNAS | US | 4 | Likely non-closure | untouched | 2025-10-13 Columbus Day; 2025-11-11 Veterans Day; 2026-10-12 Columbus Day; 2026-11-11 Veterans Day |
| XNYS | US | 4 | Likely non-closure | untouched | 2025-10-13 Columbus Day; 2025-11-11 Veterans Day; 2026-10-12 Columbus Day; 2026-11-11 Veterans Day |
| XDUB | IE | 2 | Unclear | untouched | 2025-02-03 Saint Brigid's Day; 2026-02-02 Saint Brigid's Day |
| XMOS | RU | 2 | Likely closure | untouched | 2025-05-08 Day off (substituted from 02/23/2025); 2025-11-03 Day off (substituted from 11/01/2025) |
| XZAG | HR | 2 | Unclear | untouched | 2025-11-18 Remembrance Day; 2026-11-18 Remembrance Day |
| XLIT | LT | 1 | Unclear | untouched | 2026-11-02 All Souls' Day |
| XSHE | CN | 1 | Likely closure | untouched | 2026-01-02 Day off (substituted from 01/04/2026) |

Class totals: Confirmed 4, Likely closure 83, Likely non-closure 30, Unclear 5.

## Log

- 2026-10-07: table recorded. No cluster resolved.
- 2026-10-07: XICE resolved. 4 closures confirmed and added (First Day of Summer
  and Commerce Day, 2025 to 2029 as explicit entries; Commerce Day also a rule).
  Open items for XICE: 0. Remaining likely closures: 83 (XICE was in the confirmed class).
- 2026-10-07: XCOL 2026 resolved from CSE Circular 07-10-2025 (tier 1). Fourteen
  missing closures added and thirteen wrong entries removed; the 13 candidates dated
  2026 are resolved. XCOL still has 6 open candidates (all 2025), the 2027 entries
  (repeat 2025's Poya dates; wrong) and the Vesak-week half holiday. The stop
  condition fired here: XCOL alone exceeded six confirmed closures, so XGSE was not
  started. Remaining likely closures: 70 (83 minus XCOL's 13), plus XCOL's open items.
- Method note from XCOL: a candidate list from a public-holiday package is a worse
  tool than the exchange's own circular when one exists. The circular also found
  errors the detector could not (thirteen wrong entries, not just missing ones).
- 2026-10-07: XCOL 2027 Poya entries removed (8, copied from 2025 and wrong).
  Decision: remove, not "predicted" (they were copied, not calculated) and not
  computed (not citable to tier 1 or 2). Open until the 2027 circular exists.
