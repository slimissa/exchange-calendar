# Schema freeze audit

**Date:** 2026-10-05
**Registry:** v2.13.0, 74 exchanges
**Script:** `python3 tools/schema_audit.py` (exit 0 = no unexplained gaps)
**Purpose:** confirm the schema is what it should be before the v3.0.0
exports (ADR 0012) project `calendar.json` into SQL, CSV and Parquet.

## Result

No unexplained gaps. The three items first recorded as known-open are
all resolved (v2.14.0 and v2.14.1, see Findings), as is the stale
`checksums.json`. Five documentation gaps were found and fixed.

## Checklist

| Check | Result |
|-------|--------|
| All 74 source files validate against `schema.json` | Pass, 0 errors |
| Every field populated on every exchange, or optional | Pass. Optional and partial: `extended_hours` 30/74, `confidence.note` 213/361, `early_close_time` 150/3901 |
| Enum values closed and documented | Pass. No data value outside any enum |
| Times `HH:MM`, dates `YYYY-MM-DD` and real dates | Pass, 4,316 records checked |
| Nested arrays have one shape the wrappers agree on | Pass for data. See wrapper note below |
| `confidence`: year-string keys, `source`/`level`/`last_verified`, optional `note` | Pass, 361 entries |
| Sessions coverage | Five of six types populated, one reserved (`halt`). See below |

## Findings

### Fixed in this commit

1. `docs/exchange_schema.md` called `sessions` optional. The schema
   requires it, with `minItems` 1, and all 74 exchanges have it.
2. The same document listed two session types. The schema has six.
   It now has a table of all six with populated counts.
3. The document had no `confidence` section. It does now.
4. The document did not say `generation_range` is year-granular, and
   did not list `country`, `country_code` or `sessions` as required.
5. Rust and Go comments described a session type `other`. It does not
   exist. Comments corrected, no behaviour change.

### Known open

1. **`country` and `country_code` were required by `schema.json` but
   absent from `calendar.json`** (0/74). Resolved in v2.14.0. `tools/build.py` does not copy
   them. ADR 0012 needs `country_code` in the exports, so this must land
   before the first exporter, as its own release. The wrappers ignore
   unknown fields; this was tested by adding the field to a copy of
   `calendar.json` and re-running the four-wrapper check.
2. **XCAI generated 2029-10-05 past its `generation_range` end of
   2029-07-24.** Resolved in v2.14.1: the generator now clips to the
   range exactly.
3. **Resolved in v2.14.1: Rust and Go `HolidayEntry` had no `predicted` or
   `weekend_exception` field.** They deserialise leniently and drop
   them. The Python wrapper keeps entries as raw dicts, so the keys
   survive there; the JavaScript typings (`index.d.ts`) omit both
   fields, and I did not check its runtime. The
   exports read `calendar.json` directly, so ADR 0012 is unaffected, but
   a Rust or Go consumer cannot see which dates are predicted (275
   entries carry the flag). Not fixed here: adding fields changes public
   struct literals in both wrappers.

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
`predicted`, confidence level `low`.

### Outside the checklist

Resolved in v2.14.1. `checksums.json` did not match the repository at
the time of the audit: 14 of its 91 entries verified, 77 did not. Its last regeneration was commit 4715843,
and neither CI nor `scripts/release.sh` runs
`tools/verify_checksums.py`. I did not regenerate it, since that
would rewrite 97 hashes inside an audit commit. It needs its own fix.
Adding `tools/schema_audit.py` also adds one file the manifest will
cover once it is regenerated.
