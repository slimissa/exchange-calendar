# ADR 0016 — Predicted entries

**Status:** Accepted
**Date:** 2026-11-28
**Decided by:** the maintainer (rulings R1-R14 of 2026-11-28, on the session 4e1 findings; recorded in session 4e2)

## Context

Phase 4e ("predictions", `docs/phase-4f-schema-backlog.md`, roadmap item 2)
had no written scope. Session 4e1 read the repository at v2.41.0 and found
that the word "predicted" carried four meanings, the data followed none of
them consistently, and three lifecycle rules contradicted each other.

Four meanings of "predicted":

- `schema.json:204`, field `predicted`: "True when this date is a
  calculated/estimated moon-sighting-dependent date (e.g. Islamic-calendar
  holidays) that has not yet been confirmed by an official announcement".
- `CONTRIBUTING.md:329`, evidence tier 4: "A date derived from a rule or
  from a precedent, with no notice yet | Enter with `predicted: true` and
  the `(predicted)` name suffix; cite the precedent".
- `tools/derive_confidence.py:27`: the year-level confidence note is
  "predicted" for every year after the current one.
- `README.md:650`, triage verdict `unpublished`: "the registry value is a
  prediction"; `docs/VERIFICATION_CONTRACT.md:30`: "values for years the
  exchange has not published are predictions".

What the data does (exchanges/*.json at v2.41.0):

- 296 entries in 29 exchanges carry `predicted: true`, every one with the
  " (predicted)" name suffix; 103 carry an explicit `predicted: false`.
- Only XKAR (14 entries) records a moon-sighting basis. Rule and precedent
  projections (XETR, XWBO, XJSE, XBDA, XBUE, XSES, the Euronext and Nasdaq
  Nordic half days, XTAI, XNZE, XZAG) carry the flag too; 14 exchanges (191
  entries) record no basis.
- Some predictions carry no flag: `BLOCKED.md:1322-1323` (XGSE observed
  days) "They are predictions and are not marked `predicted` in the file";
  the XSAU note keeps Founding Day and National Day 2027-2029 "predicted
  from the standing rules" without the field.
- The same kind of value is recorded two ways: XBDA and XBUE 2026-12-24 are
  `predicted` and listed `unconfirmed`; XETR and XWBO 2026-12-30 and XJSE
  2026-12-24 and 2026-12-31 are only listed `unconfirmed`.

Three lifecycle rules:

- `docs/predicted_dates_pending.md:21-29`: confirmed, set `predicted:
  false`; different, "Correct the date" in place.
- `tools/validate.py:385-387`: "Either confirm the date (remove predicted)
  or remove the entry."
- `BLOCKED.md:1741`: "Entries were removed rather than left marked
  `predicted`."
- ADR 0014 section 8 ("an earlier entry's values are never rewritten",
  `docs/decisions/0014-regular-hours-evidence.md:206`) covers
  `regular_hours` only; it was never a rule for holiday entries.

The gate also had a date it could not pass: `tools/validate.py` M7
(`check_past_due_predictions`) and `tests/test_no_stale_predictions.py`
fail as soon as a predicted date is earlier than today, so XBDA and XBUE
2026-12-24 would turn the gate red on 2026-12-25 whether or not their
recheck was on schedule. `tools/check_recheck_dates.py`, which fails an
overdue recheck date, ran in CI only, not in `tools/local_gate.sh`.

## Decision

The rules keep the maintainer's numbering.

### R1. Meaning

`predicted: true` means the entry's date or time was derived from a rule or
a precedent, and no exchange notice for that year has been read
(`CONTRIBUTING.md:329`). The schema description's moon-sighting wording
(`schema.json:204`), the year-level confidence note
(`tools/derive_confidence.py:27`) and the triage verdict `unpublished`
(`README.md:650`, `docs/VERIFICATION_CONTRACT.md:30`) are not this flag.
Their wording is aligned in session 4e3, not here.

### R2. Independence

`predicted` records how a value was produced; `verified` or `unconfirmed`
records the evidence. Both may be set together. Invariant: an entry with
`predicted: true` is never `verified`.

In 2.x a holiday entry has no `verified` field. Its evidence is the
coverage span that holds its date: a date listed in the span's
`unconfirmed` is held on doubt; any other date is backed by the span's
source. Check 5b already requires a span holding a predicted date to say
so in its label (predict, pattern or estimat) or to hold the date on doubt,
so a predicted entry cannot sit under a label that claims the exchange's
notice.

### R3. Every prediction carries the flag

Every entry that is a prediction under R1 carries `predicted: true`. The
data is brought into line in session 4e4 (for example XSAU Founding Day
and National Day 2027-2029, and the XGSE observed days of
`BLOCKED.md:1322`).

### R4. Predicted trading days

A predicted trading day has no entry to carry the flag (for example XBUE
Holy Thursday 2027-2029). In 2.x it is stated in the coverage span's label.
A structured form is a 4f backlog item.

### R5. Lifecycle

When an exchange notice for the year is read, or the date passes:

- (a) the notice confirms the entry: set `predicted: false` and cite the
  notice;
- (b) the notice gives another date or time: correct the entry in place and
  cite the notice;
- (c) the notice shows a trading day: remove the entry, and cite the notice
  in the coverage note and in CHANGELOG;
- (d) the date passes with no notice read: the entry keeps `predicted:
  true` and must be held on doubt. Held on doubt is check 5b's existing
  condition (`tools/check_verification.py`, 4d.1 and 4d2): the date is
  listed in its coverage span's `unconfirmed`, the span's label says
  "unconfirmed", and the span's `recheck_date` is at most 92 days after
  `verification.last_checked`. In addition the `recheck_date` is no later
  than the entry's date plus 30 days.

The gate accepts a past-due predicted entry only while it is held on doubt
and its `recheck_date` has not passed (the recheck date itself still
passes, as in `tools/check_recheck_dates.py`). Otherwise the gate is red.
An exchange without coverage spans cannot hold an entry on doubt, so a
past-due predicted entry there is red, as before this ADR.

ADR 0014 section 8 does not apply to holiday entries: it covers
`regular_hours` only.

### R6. Explicit `predicted: false`

An explicit `predicted: false` stays. It means "entered from a notice that
was read". It is not normalised to an absent field.

### R7. The name suffix

The " (predicted)" name suffix stays in 2.x: `tools/validate.py` M6 keeps
requiring it on every `predicted: true` entry and refusing it on
`predicted: false`. It is retired in v3 (Phase 4f).

### R8. No per-entry basis in 4e

Phase 4e records no basis per entry. A basis field is a 4f item. Entries
with no stated basis are not researched for one.

### R9. Year-level confidence

The confidence `note: "predicted"` and the reserved `source: "predicted"`
keep their values in 2.x. They are year-level statements, not the entry
flag. Renaming them is a 4f item.

### R10. Retired tool, and a warning instead

`tools/verify_predicted_dates.py` and `docs/predicted_dates_pending.md` are
retired. `tools/validate.py` M7 instead warns when a predicted entry's
date is 14 days away or less (the horizon of ADR 0015 section 5). The
warning does not change the exit code.

### R11. Schema in 2.x

In 2.x only schema description text may change (2.3.2 to 2.3.3, in session
4e3). No field or enum changes before Phase 4f.

### R12. Wrapper API

Exposing "predicted" through the wrapper API is a 4f item. The four
wrappers keep passing the stored field through as they do today.

### R13. Stale counts and examples

The stale counts and examples found by 4e1 (README's 226 flagged entries
against 296 in the data, the XSAU example, the XNZE rows in the 4f backlog
and in ADR 0013, the triage's 213 days against 198 dates) are fixed in
session 4e3, which also adds a predicted count to `docs/facts.json`,
checked by `tools/check_doc_facts.py`.

### R14. Recheck dates in the gate

`tools/check_recheck_dates.py` runs in `tools/local_gate.sh`. An overdue
`recheck_date` turns the gate red.

## Consequences

- A predicted entry whose date has passed no longer turns the gate red by
  date alone. It stays green only while it is held on doubt with a recheck
  date that has not passed and lies at most 30 days after the entry's date.
  When that recheck date passes, both M7 and `check_recheck_dates.py` are
  red until R5 (a), (b) or (c) is applied, or the hold is renewed within
  the 30-day cap.
- A predicted entry due within 14 days prints a warning in the gate, so a
  recheck is visible before the date arrives.
- With R14, every `recheck_date` in the data is a date on which the gate
  turns red. Recheck dates are chosen with that in mind.
- The flag, the suffix, the confidence wording and the wrapper API keep
  their 2.x shapes; every change of shape waits for Phase 4f, so data is
  written once in the v3 shape.
- ADR 0013, ADR 0014 and ADR 0015 are unchanged.

## Applied (filled as Phase 4e proceeds)

| MIC | added | expires | why |
|---|---|---|---|

## 4f backlog

Added to `docs/phase-4f-schema-backlog.md` by session 4e2:

- R4: a structured form for predicted trading days.
- R7: retire the " (predicted)" name suffix in v3.
- R8: a per-entry basis field for predicted entries.
- R9: rename the year-level confidence note "predicted" and the reserved
  confidence source "predicted".
- R12: expose "predicted" through the wrapper API.
