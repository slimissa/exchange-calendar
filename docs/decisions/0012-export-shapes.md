# ADR 0012 — Export shapes (SQL, CSV, Parquet)

**Status:** Accepted
**Date:** 2026-10-05
**Depends on:** ADR 0011 (snapshots are validators, not vendored data)

## Context

v3.0.0 projects `calendar.json` into three tabular exports: SQL, CSV
and Parquet. Four sessions will build them. Without a locked shape,
each session answers the same questions ad hoc and the formats
diverge, which is the failure the cross-language fixture exists to
prevent for the wrappers.

Measured on `calendar.json` v2.13.0 (74 exchanges):

| Collection | Rows |
|------------|------|
| exchanges | 74 |
| sessions | 166 |
| holidays, explicit | 3,893 |
| holidays, generated | 67 |
| confidence (exchange, year) | 361 |
| ad_hoc_closures | 0 |

Everything below is small. Flattening cannot explode row counts: the
whole registry is about 4,600 rows.

Facts the decisions rest on, each checked against the data:

- All three wrappers (Python, Rust, Go) answer `is_holiday` from
  `explicit` plus `generated` together. Generated entries never
  overlap explicit ones (0 of 67) and carry no `source_url`.
- `extended_hours` and `regular_hours` are fully redundant with
  `sessions`: 0 mismatches across 74 exchanges.
- Ten exchanges carry two `auction` sessions, so `(exchange, type)`
  is not a key. Stored order is the only identity a session has.
- `predicted` is present on 275 explicit entries: `true` on 217, `false`
  on 58. The 217 `true` entries are exactly those carrying a
  "(predicted)" suffix in `name`.
- `calendar.json` has no country field. `tools/build.py` drops
  `country` and `country_code`, which the source schema requires.
- `tools/iso10383_snapshot.json` is a list of 2,883 MIC strings with no
  metadata; the ISO 3166 snapshot is a validation list as well.

## Decisions

### 1. One shape, three formats

All three exports use the same five tables with the same columns, in
the same order. CSV is one file per table, SQL is one `CREATE TABLE`
per table, Parquet is one file per table. No format gets nested
columns, structs or maps, and no format gets JSON-in-a-cell. A
consumer who learns one export knows all three.

Tables: `exchanges`, `sessions`, `holidays`, `ad_hoc_closures`,
`confidence`.

### 2. SQL

Normalised tables, not nested JSON columns.

- `exchanges` primary key `code`; `mic` is `UNIQUE NOT NULL`.
- `sessions` primary key `(exchange_code, ordinal)`. `ordinal` is the
  zero-based position in the stored array.
- `holidays` primary key `(exchange_code, date)`. The key doubles as a
  guard: if generated and explicit ever overlap, the export fails
  instead of emitting duplicates.
- `ad_hoc_closures` primary key `(exchange_code, date)`.
- `confidence` primary key `(exchange_code, year)`.
- Every child table has a foreign key `exchange_code` to
  `exchanges(code)` with `ON DELETE CASCADE`.

There are no foreign keys to ISO reference tables. The exports ship
no ISO tables, and the vendored snapshots are validators (ADR 0011):
a MIC foreign key would drag 2,883 rows in to constrain 74.
Instead: `mic` has `CHECK (mic ~ '^[A-Z0-9]{4}$')` and
`country_code` has `CHECK (country_code ~ '^[A-Z]{2}$')`. Membership
in ISO 10383 and ISO 3166 stays enforced by `check_mic_codes.py` and
`check_country_codes.py` at build time.

### 3. CSV

One row per exchange, one per session, one per holiday, one per
`(exchange, year)`. Not nested JSON strings, not semicolon-delimited
pairs: both defeat `GROUP BY` and force every consumer to write a
parser. UTF-8, no BOM, LF line endings, RFC 4180 quoting, header row
always present. Names contain commas (4) and non-ASCII characters
(25), so quoting and encoding are not optional.

### 4. Parquet

The same flattened tables, no structs or maps. Native nesting would
make Parquet the one format whose shape differs from the other two,
and at 4,600 rows it buys nothing. Dates use the Parquet `DATE`
logical type; every other column is a string, integer or boolean.

### 5. Column order

Semantic, not alphabetical, identical across formats. Key columns
first, then descriptive columns, then data.

- `exchanges`: `code`, `name`, `mic`, `country_code`, `timezone`,
  `weekend_day_1`, `weekend_day_2`, `regular_open`, `regular_close`,
  `generation_start`, `generation_end`
- `sessions`: `exchange_code`, `ordinal`, `type`, `open`, `close`, `at`
- `holidays`: `exchange_code`, `date`, `name`, `status`, `origin`,
  `early_close_time`, `delayed_open_time`, `predicted`,
  `weekend_exception`, `source_url`
- `ad_hoc_closures`: `exchange_code`, `date`, `name`, `status`,
  `early_close_time`, `source_url`
- `confidence`: `exchange_code`, `year`, `level`, `source`,
  `last_verified`, `note`

`weekend_days` and `generation_range` are exactly two items by schema
(`minItems` = `maxItems` = 2), so they become two columns each,
lossless and in stored order. `extended_hours` is not exported: it is
a redundant projection of the `pre_market` and `post_market`
sessions. `regular_open` and `regular_close` stay on `exchanges`
because every wrapper exposes them.

Rows are sorted by `code`, then `ordinal`, `date` or `year`, so that
exports are byte-reproducible.

### 6. Dates and times

Dates are ISO 8601 `YYYY-MM-DD`. Times are text `HH:MM`, 24-hour, with
no seconds and no timezone suffix; the exchange's `timezone` column
carries the zone. SQL `TIME` is not used, because it would render
seconds. SQL and Parquet store dates as `DATE`; CSV writes them as
ISO text. `year` in `confidence` is an integer, converted from the
string key in `calendar.json`, matching the wrapper APIs.

### 7. Null handling

One rule for every format: an absent field is NULL in SQL and Parquet
and an empty, unquoted field in CSV. Empty strings are never emitted;
the data has none today and the exporters assert it, so CSV can tell
"absent" from "present". Arrays are never emitted, so "empty array"
does not arise: a collection with no members is zero rows.

Booleans are exported as stored: `true`, `false` or NULL. Today
`predicted` is `true` on 217 entries, `false` on 58 and absent on the
rest; `weekend_exception` is `true` on 2 and absent elsewhere. The
schema defines absent `predicted` as false, so consumers read NULL and
`false` alike. The exporters do not rewrite `false` to NULL or the
reverse.

Values are exported as stored, with no normalisation. In particular
`name` keeps its "(predicted)" suffix, and `predicted` is the stored
flag. The two agree on all 217 `true` entries today.

### 8. Generated holidays

The exports carry both. `holidays` holds explicit and generated rows
together, distinguished by `origin` (`explicit` or `generated`).
`source_url` is NULL for generated rows and non-NULL for explicit
ones. A generated date never falls on the exchange's own `weekend_days`
(v2.14.2): the generator drops weekend occurrences of `fixed_date`
rules and applies `fixed_with_weekend_adjustment` against the
exchange's real weekend, so every `origin = generated` row is a real
trading-day closure. Wrapper `is_holiday` is unaffected: it returns true
for any weekend date before reading holiday data. Before v2.14.2, 215 of 267 generated rows were
no-ops on closed days. Dropping generated rows would make every export answer
"is this date a holiday?" differently from every wrapper for the 20
exchanges that have them. Carrying them without `origin` would hide
which dates are verified.

## Prerequisite: `country_code`

The `exchanges` table needs `country_code`, which `calendar.json` did
not carry through v2.13.0: `tools/build.py` dropped `country` and
`country_code`, both required by the schema. Resolved in v2.14.0, which
copies both into every exchange record. The change is additive and the
wrappers ignore the new keys. `country` (the name) is not exported; it
is derivable from ISO 3166.

## Consequences

- The four export sessions implement a fixed spec. A shape question
  that comes up mid-session is a bug in this ADR, fixed here first.
- Five tables are more files than one nested document. That is the
  price of one shape across three formats.
- `ad_hoc_closures` is empty today. The table ships anyway, with its
  columns, so the shape does not change when the first entry arrives.
- `special_session` and `halt` are valid schema values with no data
  behind them. The exports accept them without special handling.

## Rejected alternatives

- Nested JSON columns in SQL: not queryable without dialect-specific
  JSON functions.
- Semicolon-delimited key-value cells in CSV: no escaping story.
- Native structs and maps in Parquet: breaks cross-format symmetry.
- A foreign key to an ISO 10383 table: see Decision 2.
- Alphabetical column order: separates `code` from `name`, and buries
  the key columns.
