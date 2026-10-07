# Schema freeze audit

**Audited:** 2026-10-05 at v2.13.0
**Figures re-measured:** 2026-10-07, working tree for v2.15.0, 74 exchanges
**Script:** `python3 tools/schema_audit.py` (exit 0 = no unexplained gaps)
**Purpose:** confirm the schema is what it should be before the v3.0.0
exports (ADR 0012) project `calendar.json` into SQL, CSV and Parquet.

The checklist and findings below were written at v2.13.0. Every number
is the one `tools/schema_audit.py` prints for the current tree. A number
that changed since the audit is noted in the finding it belongs to.

## Result

No unexplained gaps. The audit found three open items, a stale
`checksums.json` and five documentation gaps; all are resolved (v2.15.0, see Findings). A later pass found a fourth item, generated
holidays on closed days, also resolved in v2.15.0.

Current output, without the `INFO` lines:

```
source files validated: 74, schema errors: 0
built.exchange.country: populated 74/74
built.exchange.country_code: populated 74/74
populated (5): regular 74, pre_market 30, auction 22, post_market 29, lunch_break 11
reserved (1): ['halt']
records checked: 4109
entries: 97, covered files: 97, drifted: 0
0 gap(s), 0 known-open
```

## Checklist

| Check | Result |
|-------|--------|
| All 74 source files validate against `schema.json` | Pass, 0 errors |
| Every field populated on every exchange, or optional | Pass. Optional and partial: `extended_hours` 30/74, `confidence.note` 213/361, `early_close_time` 150/3,895, `delayed_open_time` 5/3,895, `predicted` 276/3,895, `weekend_exception` 2/3,895 |
| Enum values closed and documented | Pass. No data value outside any enum |
| Times `HH:MM`, dates `YYYY-MM-DD` and real dates | Pass, 4,109 records checked |
| Nested arrays have one shape the wrappers agree on | Pass for data and for all four wrappers (see finding 3 below) |
| `confidence`: year-string keys, `source`/`level`/`last_verified`, optional `note` | Pass, 361 entries |
| Sessions coverage | Five of six types populated, one reserved (`halt`). See below |
| `country` and `country_code` present in `calendar.json` | Pass, 74/74 (was 0/74 at audit time) |
| No generated holiday on the exchange's own weekend | Pass, 0 of 66 (was 215 of 267) |
| `checksums.json` covers exactly the collected files, no drift | Pass, 97 entries, 97 covered, 0 drifted |

## Findings

### Fixed in the audit commit

1. `docs/exchange_schema.md` called `sessions` optional. The schema
   requires it, with `minItems` 1, and all 74 exchanges have it.
2. The same document listed two session types. The schema has six.
   It now has a table of all six with populated counts.
3. The document had no `confidence` section. It does now.
4. The document did not list `country`, `country_code` or `sessions` as
   required, and said nothing about how `generation_range` bounds
   generated dates (see finding 2 below for what it says now).
5. Rust and Go comments described a session type `other`. It does not
   exist. Comments corrected, no behaviour change.

### Open at audit time, since resolved

1. **`country` and `country_code` were required by `schema.json` but
   absent from `calendar.json`** (0/74). Resolved in v2.15.0:
   `tools/build.py` now copies both. The wrappers ignore unknown fields;
   this was tested before the change by adding the field to a copy of
   `calendar.json` and re-running the four-wrapper check.
2. **XCAI generated 2029-10-05 past its `generation_range` end of
   2029-07-24.** Resolved in v2.15.0: the generator clips to the range
   exactly.
3. **Rust and Go `HolidayEntry` had no `predicted` or `weekend_exception`
   field**, so both dropped them on deserialization (276 entries carry
   `predicted`, 2 carry `weekend_exception`). Resolved in v2.15.0: both
   structs carry the fields. The Python wrapper keeps entries as raw
   dicts and the JavaScript wrapper returns them as stored, so both
   already carried them; the JavaScript typings now declare them. Four
   cross-language fixture queries pin it.
4. **Generated holidays on closed days**, found after the audit. 215 of
   267 generated dates fell on the exchange's own weekend: 208 from
   `fixed_date` rules, which never shift, and the rest from
   `fixed_with_weekend_adjustment` on Friday/Saturday-weekend exchanges.
   Resolved in v2.15.0: the generator uses each exchange's
   `weekend_days` and drops any generated weekend date, leaving 66
   generated entries. The same pass found XCAI's forward-to-Sunday
   observance wrong and replaced it with
   `fixed_with_thursday_observance`.

### Session type coverage

The schema enum has six types. Five are populated: `regular` 74,
`pre_market` 30, `post_market` 29, `auction` 22, `lunch_break` 11 (166
sessions). One is reserved and unused: `halt`.

An earlier version of this checklist expected "three populated types
plus three reserved". That count was wrong, not the data. No document
in the repository asserts it: `schema.json` and
`docs/exchange_schema.md` have always listed six types. The checklist
now states the measured count, and `tools/schema_audit.py` reprints it
on every run.

Other enum values with no data, all in the schema and documented as
reserved: holiday status `special_session`, confidence source
`predicted`, confidence level `low`. `ad_hoc_closures` has no records,
so its population is not measurable; the table ships empty (ADR 0012).

### Outside the checklist

`checksums.json` did not match the repository at the time of the audit:
14 of its 91 entries verified, 77 did not. Its last regeneration was
commit 4715843, and neither CI nor `scripts/release.sh` ran
`tools/verify_checksums.py`. Resolved in v2.15.0: regenerated, gated in
`validate.yml`, and checked by `tools/schema_audit.py`, which now fails
on a missing, extra or mismatched entry.
