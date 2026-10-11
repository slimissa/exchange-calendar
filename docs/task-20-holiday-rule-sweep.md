# Task 20: holiday-rule sweep

**Status:** in progress, started 2026-10-07. Updated as each cluster is resolved.
**Goal:** find real exchange closures that have no rule or entry in a `built`
exchange's source file, and add them with a citable source.
**Why this file exists:** the first pass produced a 122-candidate table that lived
only in a session transcript. This is the durable copy.

## Running status

| Cluster | Candidates | False closures found | State |
|---------|-----------|----------------------|-------|
| XICE | 4 | — (not run; tier 3 sources only) | **resolved 2026-10-07** (tier 3, corroborated; see `BLOCKED.md`) |
| XCOL | 19 | 21 entries (13 in 2026, 8 copied Poya dates in 2027) | **2026 resolved 2026-10-07** (13 candidates, tier 1 circular); 2025 (6 candidates), 2027 and Vesak week open, see `BLOCKED.md` |
| XGSE | 11 | 1 kind, 5 entries (Founders' Day on 4 August: 2026-08-04 removed 2026-10-07; 2025-08-04 and 2027 to 2029 removed 2026-10-11; 2025-08-04 and the 2027 to 2029 ones rest on the 2025 Act and the Ministry, not on a GSE list for the year) | **11 of 11 resolved** (5 on 2026-10-07; 3 on 2026-10-11; 3 on 2026-10-11 after the second pass: 2025-07-04 and 2026-01-09 added, 2025-07-01 a non-closure); 2026-01-09 is [Likely], see `BLOCKED.md` |
| XGSE 2027 to 2029 (open class) | 3 gaps: Republic Day, Eid dates, midweek-to-Friday moves | — (not run) | **open, deliberately not started.** Needs GSE's 2027 list and the Ministry's declarations, which do not exist yet; see `BLOCKED.md` "2027–2029 open class" |
| XBUE | 12 | — (not run) | untouched |
| XBUD | 4 | — (not run) | untouched |
| XBRV, XCAY, XDFM, XMOS, XRIS, XSHE, XSTC | 37 | — (not run) | untouched |
| XDUB, XLIT, XZAG | 5 | XDUB 5 kinds, 21 entries; XZAG 6 kinds, 10 entries; XLIT — (not run) | **all 5 resolved 2026-10-07**: XDUB 2 non-closures, XLIT 1 closure, XZAG 2 closures; XDUB file corrected against Euronext 2026-10-10 (4 rules removed, Labour Day added; 2027 to 2029 pattern-derived); XZAG file corrected against ZSE 2026-10-11 (9 kinds, 23 entries; 2028 and 2029 pattern-derived), see `BLOCKED.md` |
| XETR, XPAR, XMAD, XNYS, XNAS | 30 | XMAD 0 (checked; one missing closure found, Easter Monday); XETR, XPAR, XNYS, XNAS — (not run) | **30 confirmed non-closures 2026-10-07** (tier 1 for all five; 2025 US dates rest on the same fixed set), recorded in `BLOCKED.md`. One real closure found outside the list: XMAD Easter Monday, now a rule |

Recommended order: XICE, XCOL, XGSE, XBUE, XBUD, then the rest of the likely closures.

Reading the new column: a number is what the two-sided check found against the
exchange's own list, as kinds and as dated entries. `0` means the check was run and found
none. `—` means the two-sided check has not been run for that exchange, so its true count
is unknown, not zero.

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

## Two-sided check

For every exchange, compare the file against the exchange's own published list in **both
directions**. Missing closures and false closures both count. A public-holiday detector
finds only the first side, so its candidate list understates the work.

**Why.** The method above started from a candidate list and went looking for missing
closures. Checking against the exchange's own list found the opposite error as often as
the first: XCOL (21 wrong entries), XGSE (a wrong 2026 closure), XDUB (five kinds of false
closure) and XZAG (six kinds, including an invented "(observed)" substitute for every
weekend holiday). XMAD showed the first side from a different angle: Easter Monday is
not a Spanish public holiday, so the detector could not see that BME closes on it.

**Procedure, per exchange.**

1. Fetch the exchange's own list for every year it publishes. Record each URL and what
   came back, including failures.
2. List every closure on it. Compare with the file, year by year, in both directions.
3. *Missing:* on the exchange's list, absent from the file. Add it under the source rules
   below.
4. *False:* in the file, absent from the exchange's list, on a weekday the exchange
   trades. Remove it under the acceptance rule below.
5. Record kinds and dated entries separately. A rule that generates five years of
   entries is one kind and five entries. The stop condition counts kinds; the commit and
   this file report both, so a reviewer can see the size.

**Sources, by tier** (`CONTRIBUTING.md`, "The hierarchy"):

| Tier | Source | Use here |
|------|--------|----------|
| 1 | The exchange's own notice or list, or the decree that sets the holiday | Verifies an addition or a removal |
| 2 | A mirror of the exchange's notice, with issuer, dates and resume date visible, only when tier 1 is unreachable | Verifies, with the evidence `CONTRIBUTING.md` lists |
| 3 | Press, settlement calendars, aggregators, holiday libraries | Finds a candidate; never alone for an addition or a removal. Corroborated tier 3 follows `CONTRIBUTING.md` |
| 4 | A date derived from a rule or precedent, no notice yet | An addition enters with `predicted: true` and the `(predicted)` name suffix |

**What counts as a false closure.** Only something the file lists: a rule, or an explicit
entry. A closure the file merely omits is *missing*, not false, and is added, not
removed. The fix for a false closure is to remove what the file lists:

- If the file has no rules (XZAG), remove the explicit entries. XZAG's "(observed)"
  Labour Day, Christmas, St Stephen's, New Year's and Epiphany days were explicit
  entries. ZSE never moves a weekend holiday, so each was a non-closure listed as a
  closure, and removal was the whole fix. A test that fails on any "(observed)" or
  "(substitute)" entry pins the class.
- If a rule generates the false closure (XDUB's St Patrick's Day and June, August and
  October bank holidays), remove the rule **and** its explicit entries. The generator
  skips any date already explicit, so removing only the rule leaves the entries in
  place.
- If the false closure came from a copied date (XCOL repeated 2025's Poya days in 2026
  and 2027), remove it. Do not relabel it `predicted`: it was copied, not calculated.

**Acceptance rule for a removal.** The exchange's own published list must show the date
as a trading day, and the removal must cite a tier 1 or tier 2 source. The test that
accompanies it pins the trading day.

**Unpublished years.** When the exchange has not published a year, a removal for that
year is pattern-derived: it follows what the published years show. Record it as such in
that exchange's `BLOCKED.md` section, with the pattern and the years it rests on, and
say it should be re-checked when the list appears. Do not write it in the source file:
`schema.json` sets `additionalProperties: false`, so the file cannot carry prose, and
an absent entry has nowhere to carry a marker. A pattern-derived *addition* is a tier 4
entry and is marked in the file (`predicted`, with the name suffix).

**Implication for the clusters not yet touched.** XBUE (12), XBUD (4) and XBRV / XCAY /
XDFM / XMOS / XRIS / XSHE / XSTC (37) have candidate counts that are understated: the
detector could not find false closures, and four of the five exchanges checked so far
carried them. Every future cluster session must run the two-sided check against the
exchange's own list, not only work the candidate list. A `—` in the "False closures
found" column means that check has not been run.

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
| XGSE | GH | 11 | Likely closure | 5 resolved, 6 open | 2025-03-31 Public Holiday; 2025-04-01 Public Holiday; 2025-06-06 Eid-ul-Adha; 2025-07-01 Republic Day; 2025-07-04 Public Holiday; 2025-09-22 Public Holiday; 2026-01-09 Public Holiday; 2026-03-20 Eid-ul-Fitr; 2026-05-27 Eid-ul-Adha; 2026-07-01 Republic Day; 2026-07-03 Public Holiday |
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
| XDUB | IE | 2 | Non-closure | resolved 2026-10-07; file corrected 2026-10-10 | 2025-02-03 Saint Brigid's Day; 2026-02-02 Saint Brigid's Day |
| XMOS | RU | 2 | Likely closure | untouched | 2025-05-08 Day off (substituted from 02/23/2025); 2025-11-03 Day off (substituted from 11/01/2025) |
| XZAG | HR | 2 | Closure | resolved 2026-10-07; file corrected 2026-10-11 | 2025-11-18 Remembrance Day; 2026-11-18 Remembrance Day |
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
- 2026-10-07: XCOL source retrieval. cse.lk circulars page returned an empty
  JavaScript shell (circular 03-04-2026 not retrieved); the CDS "Holiday List 2026"
  page was retrieved and matches the 17 dates already in the file; the 2025 circular
  was not found by two searches. XCOL open items unchanged: 2025 (6 candidates),
  Vesak-week half holiday, four unverified 2027 entries. Next attempt needs a
  direct `cdn.cse.lk` PDF link for each circular.
- 2026-10-07: XGSE, first six confirmed closures added (2025-03-31, 2025-04-01,
  2025-06-06, 2026-03-20, 2026-03-23, 2026-05-27) and the stop condition fired.
  GSE's own 2026 list (tier 1) gave the closure rule and also showed a wrong
  entry (2026-08-04), now removed. Of the 11 candidates, 5 are resolved
  (03-31, 04-01, 06-06, 03-20, 05-27); 2026-03-23 was not on the candidate list.
  Open: 2025-07-01, 2025-07-04, 2025-09-22, 2026-01-09, 2026-07-01, 2026-07-03,
  plus the 2027 to 2029 Aug 4 entries. Remaining likely closures: 65 (70 minus
  XGSE's 5), plus XGSE's open items.
- Method note from XGSE: the exchange's own list contradicted the registry as well
  as extending it (a wrong 2026 closure), as with XCOL. A sweep that only looks for
  missing closures misses this class.
- 2026-10-07: the 30 likely non-closures (XETR 5, XPAR 11, XMAD 6, XNYS 4, XNAS 4) are
  confirmed non-closures against each exchange's own calendar (Deutsche Boerse, Euronext,
  BME instructions, NYSE, Nasdaq). None was a closure, so none became a rule. The note
  lives in `BLOCKED.md`, one section per exchange, because `schema.json` forbids a
  comment field (`additionalProperties: false`). Remaining likely closures: 65 (unchanged
  by this step). The check found a real closure the detector cannot see: BME closes on
  Easter Monday (instructions for 2022, 2024, 2025, 2026) and the file did not. Added as a
  rule; XMAD tests that asserted the opposite were rewritten.
- Method note: a closure that is not a public holiday (Easter Monday for Spain) is
  invisible to a public-holiday detector. The exchanges' own calendars are the check.
- 2026-10-07: the five unclear candidates are resolved against each exchange's own
  calendar. XDUB St Brigid's Day (2): non-closure (Euronext). XLIT All Souls' Day (1):
  closure (Nasdaq Baltic); two further 2026 closures added. XZAG Remembrance Day (2):
  closure (ZSE). Stop condition fired for XDUB and XZAG: each file differs from its
  exchange's list by more than three rules. Open: XDUB, false closures for St Patrick's
  Day and the June, August and October bank holidays (2025 to 2029), a false 2025-12-29
  "Christmas Day (substitute)", and a missing Labour Day; XZAG, missing Good Friday,
  Christmas Eve and New Year's Eve and a false 2026-10-08.
- Method note: the unclear candidates led to the exchange's own list, and that list
  showed more wrong closures than missing ones for XDUB. Third time (XCOL, XGSE, XDUB):
  checking a file against the exchange's calendar finds false closures the candidate
  detector cannot.
- 2026-10-10: XDUB closed against Euronext's own calendars (tier 1, 2025 and 2026; the
  page also lists 2020 to 2024). Removed the St Patrick's Day and the June, August and
  October bank holiday rules and the 2025-12-29 "Christmas Day (substitute)": Dublin
  trades on all of them. Added Labour Day (1 May, `fixed_date`). Kept 2026-12-28, which
  Euronext lists as closed (substitute for St Stephen's Day). 2027 to 2029 are
  pattern-derived from the published years, not tier 1; re-check when Euronext publishes.
  `calendar.json` and `checksums.json` are regenerated in the next full session.
- 2026-10-11: XZAG closed against ZSE's own lists (tier 1: 2025, 2026, 2027). Stop
  condition lifted. 9 kinds changed, 23 dated entries (7 kinds and 15 entries on the
  published years). Removed 6 kinds, 10 entries: Independence Day (5) and the
  "(observed)" Labour Day, Christmas, St Stephen's, New Year's and Epiphany days (5),
  because ZSE does not move a weekend holiday. Added 3 kinds, 13 entries: Good Friday,
  Christmas Eve, New Year's Eve. 2028 and 2029 are pattern-derived (8 entries); re-check
  when ZSE publishes. A test now fails on any "(observed)" or "(substitute)" entry.
- 2026-10-11: XGSE two-sided check against GSE's own 2025 and 2026 lists (tier 1) and the
  Interior Ministry's declarations. 3 kinds, 5 dated entries (limit 10 kinds, not
  reached). Added 2 kinds, 2 entries: 2025-09-22 (Sunday 21 September observed on the
  Monday, declared) and 2026-07-03 (Republic Day moved to Friday). Removed 1 kind, 3
  entries: Founders' Day on 4 August, 2027 to 2029, pattern-derived from GSE's 2026
  list. 2026-07-01 is a non-closure. Open: 2025-07-01, 2025-07-04, 2026-01-09 (GSE's list
  says 7 January, the Ministry declared 9 January), and 2027 to 2029 Republic Day, Eid
  and midweek-to-Friday shifts. Unlike ZSE, GSE's own rule observes weekend holidays on
  the next working day if declared, so the file's "(observed)" entries are predictions,
  not false closures. Remaining likely closures: 62 (65 minus the 3 XGSE candidates resolved today), plus open items.
- 2026-10-11 (second pass): XGSE open items. 2 kinds added, 1 removed, 3 dated entries
  (limit 10 kinds, not reached). Added 2025-07-04 (Republic Day moved to Friday) and
  2026-01-09 (Constitution Day moved to Friday); removed 2026-01-07. 2025-07-01 is a
  non-closure. 2026-01-09 is [Likely]: GSE's own list still prints 7 January, and no GSE
  notice or daily report for 7 or 9 January was reachable. GSE's reported session numbers
  show exactly one closed weekday between 2 and 12 January. The 2027 to 2029 class
  (Republic Day, Eid dates, midweek-to-Friday moves) is tracked as its own row, not
  filled: it needs publications that do not exist yet. Remaining likely closures: 62
  (65 minus the 3 XGSE candidates resolved on the first pass), 59 after this one.
- 2026-10-11 (correction): XGSE 2025-08-04 removed. The first pass kept it because it is on
  GSE's 2025 list; that list predates the 2025 Act and is stale (it also misses the 4 July
  Republic Day). The Interior Ministry stated on 31 July 2025 that 4 August 2025 is not a
  public holiday. [Likely]: no GSE daily report for that day was reachable. 1 kind, 1
  entry. This also changes the basis for the 2027 to 2029 Aug 4 removals: the Act, not
  only the pattern of the 2026 list.
