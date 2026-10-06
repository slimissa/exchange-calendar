# Schema freeze audit

**Date:** 2026-10-05
**Registry:** v2.13.0, 74 exchanges
**Script:** `python3 tools/schema_audit.py` (exit 0 = no unexplained gaps)
**Purpose:** confirm the schema is what it should be before the v3.0.0
exports (ADR 0012) project `calendar.json` into SQL, CSV and Parquet.

## Result

No unexplained gaps. Three known-open items, none blocking the exports
once the first is done. Four documentation gaps were found and fixed.

## Checklist

| Check | Result |
|-------|--------|
| All 74 source files validate against `schema.json` | Pass, 0 errors |
| Every field populated on every exchange, or optional | Pass. Optional and partial: `extended_hours` 30/74, `confidence.note` 213/361, `early_close_time` 150/3901 |
| Enum values closed and documented | Pass. No data value outside any enum |
| Times `HH:MM`, dates `YYYY-MM-DD` and real dates | Pass, 4,317 records checked |
| Nested arrays have one shape the wrappers agree on | Pass for data. See wrapper note below |
| `confidence`: year-string keys, `source`/`level`/`last_verified`, optional `note` | Pass, 361 entries |
| Sessions coverage | See below: not three plus three |

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

1. **`country` and `country_code` are required by `schema.json` but
   absent from `calendar.json`** (0/74). `tools/build.py` does not copy
   them. ADR 0012 needs `country_code` in the exports, so this must land
   before the first exporter, as its own release. The wrappers ignore
   unknown fields; this was tested by adding the field to a copy of
   `calendar.json` and re-running the four-wrapper check.
2. **XCAI generates 2029-10-05 past its `generation_range` end of
   2029-07-24.** Recurrence rules expand by year. This is now documented.
   Clipping would remove a correct holiday date, so it needs an owner
   decision, not an audit edit.
3. **Rust and Go `HolidayEntry` have no `predicted` or
   `weekend_exception` field.** They deserialise leniently and drop
   them. The Python wrapper keeps entries as raw dicts, so the keys
   survive there; the JavaScript typings (`index.d.ts`) omit both
   fields, and I did not check its runtime. The
   exports read `calendar.json` directly, so ADR 0012 is unaffected, but
   a Rust or Go consumer cannot see which dates are predicted (275
   entries carry the flag). Not fixed here: adding fields changes public
   struct literals in both wrappers.

### Divergence from the checklist's premise

The checklist says "three populated session types plus three
reserved". The data has **five** populated types (`regular` 74,
`pre_market` 30, `post_market` 29, `auction` 22, `lunch_break` 11) and
**one** reserved (`halt`). Other enum values with no data: holiday
status `special_session`, confidence source `predicted`, confidence
level `low`. All are in the schema and documented as reserved.

### Outside the checklist

`checksums.json` does not match the repository at HEAD: 14 of its 91
entries verify, 77 do not. Its last regeneration was commit 4715843,
and neither CI nor `scripts/release.sh` runs
`tools/verify_checksums.py`. I did not regenerate it, since that
would rewrite 97 hashes inside an audit commit. It needs its own fix.
Adding `tools/schema_audit.py` also adds one file the manifest will
cover once it is regenerated.
