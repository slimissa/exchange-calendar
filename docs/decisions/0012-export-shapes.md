# ADR 0012 — Export shapes (SQL, CSV, Parquet)

**Status:** Accepted
**Date:** 2026-10-05
**Amended:** 2026-10-16 - SQL dialect matrix and idempotency clarified. Idempotency is `DROP TABLE IF EXISTS`; the commented PostgreSQL `ON CONFLICT` block is for additive loading only.
**Amended:** 2026-10-17 - Phase B: `sessions` drops `ordinal`, the remaining column types and the `NOT NULL` rule are added to 2a, and the holiday overlap guard is restored.
**Amended:** 2026-10-17 - No CHECK on `name`; the ASCII assertion is limited to `code`, `mic` and `country_code`; `status` and `level` sizes are set.
**Amended:** 2026-10-18 - CSV shape confirmed (five files, one dialect, formula guard); counts in Context, section 3 and section 7 refreshed to v2.16.1.
**Depends on:** ADR 0011 (snapshots are validators, not vendored data)

## Context

v3.0.0 projects `calendar.json` into three tabular exports: SQL, CSV
and Parquet. Four sessions will build them. Without a locked shape,
each session answers the same questions ad hoc and the formats
diverge, which is the failure the cross-language fixture exists to
prevent for the wrappers.

Measured on `calendar.json` v2.16.1 (74 exchanges):

| Collection | Rows |
|------------|------|
| exchanges | 74 |
| sessions | 166 |
| holidays, explicit | 3,894 |
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
- `predicted` is present on 285 explicit entries: `true` on 227, `false`
  on 58. The 227 `true` entries are exactly those carrying a
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

Normalised tables, not nested JSON columns. Amended after checking the
repo: the text this replaces is quoted under "Changed from the
original" at the end of this section. Types and CHECKs are in 2a,
column order in 5.

**Primary keys.** A key is tightened to its natural key only where
`schema.json` guarantees uniqueness. Data that happens to be unique
today is not a guarantee. Where the schema gives none, the key carries
`seq`: a `SMALLINT NOT NULL` holding the 1-based position among rows
that share the natural key, in source order (almost always 1).

- `exchanges`: `code`; `mic` is `UNIQUE NOT NULL`. The generator
  asserts both are unique across files, because the schema describes
  one file at a time.
- `sessions`: `(exchange_code, type, seq)`. `sessions` is an unkeyed
  array with no `uniqueItems`, and ten exchanges carry two `auction`
  sessions, so `(exchange_code, type)` is not a key.
- `holidays`: `(exchange_code, date, origin, seq)`. `holidays.explicit`
  is an unkeyed array with no `uniqueItems`, and `holidays.generated`
  is not in `schema.json` at all; `build.py` writes it.
- `ad_hoc_closures`: `(exchange_code, date, seq)`. Unkeyed array, no
  `uniqueItems`. It has no rows today, so no data could justify a
  tighter key.
- `confidence`: `(exchange_code, year)`, no `seq`. The schema keys it
  by year (`propertyNames` pattern `^\d{4}$`), so the pair is unique
  by construction.

The generator checks every primary key before it writes any file and
exits non-zero on a violation. The database is never the first to
notice one, and nothing is deduplicated silently.

The original `holidays` key doubled as a guard against generated and
explicit rows on the same date. With `origin` in the key the guard is
gone: an overlap would load as two rows. The exporter therefore checks
for `(exchange_code, date)` overlaps between `holidays.explicit` and
`holidays.generated` and exits non-zero if any exist, which restores the
guard the original key provided. Today's overlap count is 0 (0 of 67
generated rows).

**Foreign keys.** Every child table carries a constraint such as
`CONSTRAINT fk_sessions_exchange FOREIGN KEY (exchange_code) REFERENCES
exchanges (code) ON DELETE NO ACTION ON UPDATE NO ACTION` (named `fk_`,
the table name, `_exchange`), identical in all four dialects. `NO
ACTION` because deleting an exchange must not silently remove its
history, and a code change is a migration, not an
update. Not `DEFERRABLE`: the load order is acyclic and MySQL has no
deferrable constraints. The child `exchange_code` has exactly the type
and length of `exchanges.code`, or MySQL rejects the key. Every
primary key that includes `exchange_code` leads with it, which
satisfies InnoDB's foreign-key index requirement.

SQLite checks foreign keys only when `PRAGMA foreign_keys` is on. The
setting is per connection, off by default, and a no-op inside a
transaction (verified on SQLite 3.45.1). The SQLite file sets it
before any `BEGIN`. Tests assert that the file leaves it on and set it
on any connection they open themselves, or an orphan-insert test
passes and hides the bug.

There are no foreign keys to ISO reference tables. The exports ship
no ISO tables, and the vendored snapshots are validators (ADR 0011):
a MIC foreign key would drag 2,883 rows in to constrain 74.
Membership in ISO 10383 and ISO 3166 stays enforced by
`check_mic_codes.py` and `check_country_codes.py` at build time.

**Idempotency.** Each file is `DROP TABLE IF EXISTS` for the children
and then the parent, `CREATE TABLE` for the parent and then the
children, then one `INSERT` per row, parent first, with no conflict
clause. A conflict clause would leave stale rows from an older version
in place, and `CREATE TABLE IF NOT EXISTS` would keep an old table
shape that the new `INSERT` no longer fits. Every header states the
limit: "Drops and recreates these five tables. Not safe if other
tables reference them." The PostgreSQL file carries a commented
`ON CONFLICT` block, one example per table with that table's own
primary key as the target. It is for additive loading only, and stale
rows persist.

**Transactions.** The SQLite, PostgreSQL and MySQL files wrap the
`INSERT` block in `BEGIN` or `START TRANSACTION` and `COMMIT`; MySQL
starts the wrapper after the `CREATE` statements because its DDL
commits implicitly. The ANSI file has no wrapper, because no keyword
is valid across the engines it targets. The live total is about 4,560
rows (74 exchanges, 166 sessions, 3,961 holidays, 361 confidence, 0
closures), against 302 in the sibling iso4217 exports. Autocommit per
`INSERT` dominates the load time at that size, and a failure part way
through the file would leave partial tables. This is a difference of
size from the sibling, not a departure from its pattern.

**Prerequisite.** No `.gitattributes` exists at `a1b166d`, so `*.sql`
files have no line-ending rule. Adding one is a prerequisite for the
SQL exporter.

**Changed from the original** (text at `a1b166d`, replaced above):

- Regex CHECKs. Original: "Instead: `mic` has `CHECK (mic ~
  '^[A-Z0-9]{4}$')` and `country_code` has `CHECK (country_code ~
  '^[A-Z]{2}$')`." Dropped in every dialect, see 2a. The membership
  sentence that followed it is unchanged.
- Table list. Unchanged: section 1 of the original lists five tables
  (`exchanges`, `sessions`, `holidays`, `ad_hoc_closures`,
  `confidence`) and the amendment keeps the same five.
- Keys. Original: "`sessions` primary key `(exchange_code,
  ordinal)`. `ordinal` is the zero-based position in the stored
  array." Now `(exchange_code, type, seq)`; `ordinal` is dropped as a
  column (Phase B, below). Original: "`holidays`
  primary key `(exchange_code, date)`. The key doubles as a guard: if
  generated and explicit ever overlap, the export fails instead of
  emitting duplicates." Now `(exchange_code, date, origin, seq)`; the
  key no longer carries the guard and an exporter check restores it
  (see the overlap note above). Original:
  "`ad_hoc_closures` primary key `(exchange_code, date)`." Now
  `(exchange_code, date, seq)`. `exchanges` and `confidence` keys are
  unchanged. Why: a key is tightened only where the schema guarantees
  uniqueness, and for these three tables it does not.
- Foreign keys. Original: "Every child table has a foreign key
  `exchange_code` to `exchanges(code)` with `ON DELETE CASCADE`." Now
  `ON DELETE NO ACTION ON UPDATE NO ACTION`, so removing an exchange
  cannot silently delete its history.
- Column lists (5). Original `sessions`: "`exchange_code`, `ordinal`,
  `type`, `open`, `close`, `at`". Original `holidays`:
  "`exchange_code`, `date`, `name`, `status`, `origin`,
  `early_close_time`, `delayed_open_time`, `predicted`,
  `weekend_exception`, `source_url`". Original `ad_hoc_closures`:
  "`exchange_code`, `date`, `name`, `status`, `early_close_time`,
  `source_url`". `holidays` and `ad_hoc_closures` gain `seq` and nothing
  else changes; `sessions` gains `seq` and, in Phase B, loses `ordinal`.

Further changes (Phase B, replacing text at `cca603c`):

- `ordinal` dropped. It is the zero-based array position in the JSON, a
  serialization artifact, and `seq` disambiguates the same rows, so
  keeping both is redundant. This supersedes the Phase A text that kept
  `ordinal` as a plain column.
- Sort order. Original: "Rows are sorted by `code`, then `ordinal`,
  `date` or `year`, so that exports are byte-reproducible." Now `type`
  replaces `ordinal`, and ties break by `seq`. `type` is the next key
  column of the `sessions` primary key; the effect is that sessions sort
  by type name instead of array position.
- Overlap guard. Supersedes the Phase A sentence that left a generated
  and explicit overlap undecided: an overlap is now an error.
- Matrix. The `source` row said no CHECK; `confidence.source` is a closed
  enum and now carries C2. The "not decided here" list is replaced by
  the second table and the rules after it.

Further changes (Phase B, second pass, replacing text at `3735b3c`):

- `name`. The previous text left it open, with a proposed
  `VARCHAR(255)` and C1 `LENGTH(c) BETWEEN 3 AND 255`. Now `VARCHAR(255)`,
  `TEXT` in SQLite, with no CHECK, for all three tables that have it.
  Why: the schema's `minLength` counts characters, no dialect has a
  portable character-count function, and non-ASCII names exist.
- ASCII assertion. The previous C1 text said it covered "these
  columns". It now names `code`, `mic` and `country_code`, the only
  C1 columns.
- `status` and `level`. `VARCHAR(n)` became `VARCHAR(16)` and
  `VARCHAR(8)`; both are closed enums well inside those bounds.

### 2a. SQL types and CHECKs

This is the only place the per-dialect types and CHECKs are written.
Identifiers are unquoted. Check constraints are named `chk_`, the table
name, `_`, the column name and an optional kind suffix (for example
`chk_holidays_status`); foreign keys are named as in section 2. Unquoted `date`, `year`,
`level`, `open`, `close`, `at` and `type` were executed on SQLite
3.45.1 only; the other engines are unverified.

| Field | ANSI / PostgreSQL / MySQL | SQLite STRICT | CHECK | Exact? |
|---|---|---|---|---|
| code | `VARCHAR(n)` | `TEXT` | C1 | length yes; pattern dropped |
| mic | `CHAR(4)` | `TEXT` | C1 (=4) | length yes; pattern dropped |
| country_code | `CHAR(2)` | `TEXT` | C1 (=2) | length yes; pattern dropped |
| date | `DATE` | `TEXT` | C4 (SQLite only) | yes |
| time | `VARCHAR(5)` | `TEXT` | C5, all four | approximate |
| year | `SMALLINT` | `INTEGER` | C3 if the schema bounds it | yes |
| origin | `VARCHAR(n)` | `TEXT` | C2 | yes |
| status | `VARCHAR(16)` | `TEXT` | C2 | yes |
| level | `VARCHAR(8)` | `TEXT` | C2 | yes |
| source (confidence) | `VARCHAR(32)` | `TEXT` | C2: `IN ('fetcher','manual','predicted')` | yes |

`n` is the `maxLength` in `schema.json`. The schema declares no
`maxLength` on any field, so the exporter sets an explicit bound per
column and the generator fails above it. It never truncates.

The CHECK forms, with `c` standing for the column:

- C1: `LENGTH(c) BETWEEN lo AND hi`. MySQL's `LENGTH` counts bytes, so
  the generator asserts `isascii()` on `code`, `mic` and `country_code`,
  the only columns that carry C1 and whose schema patterns
  (`^[A-Z0-9]{4}$`, `^[A-Z]{2}$`) allow only ASCII, which makes bytes
  equal characters.
- C2: `c IN (...)`, with the exact literals from the schema. Closed
  enums at `a1b166d`: `holidays.status` is `closed`, `early_close`,
  `delayed_open`, `special_session`; `ad_hoc_closures.status` is
  `closed`, `early_close`; `confidence.level` is `high`, `medium`,
  `low`. `origin` is not in the schema; its two values are `explicit`
  and `generated` (section 8).
- C3: `c BETWEEN lo AND hi`, or `c >= lo` where only a lower bound
  applies. `schema.json` gives no bounds for the year, so the check is
  not emitted until it does.
- C4: `c GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(c)
  = c`. SQLite's `date()` normalises `2026-02-30` to `2026-03-02`
  (verified on 3.45.1), so the equality rejects it. The exporter tests
  that insert.
- C5: `LENGTH(c)=5 AND SUBSTR(c,3,1)=':' AND SUBSTR(c,1,2) BETWEEN '00'
  AND '23' AND SUBSTR(c,4,2) BETWEEN '00' AND '59'`. It does not
  reject a non-digit second character such as `1a:30`; the schema's
  time pattern does. All 731 time values in `calendar.json` at
  `a1b166d` pass it, and none is `24:00`.

Pattern CHECKs on `code`, `mic` and `country_code` are dropped in every
dialect. They cannot be written exactly in ANSI or SQLite, and
PostgreSQL's `~` and MySQL's `REGEXP` would make the files differ by
capability instead of syntax; MySQL 8 (ICU) and MariaDB (PCRE) regex
semantics differ as well. The cost is that a lowercase code passes the
database, but `validate.py` and the generator's assertions reject it
first.

Dates and times. ANSI, PostgreSQL and MySQL use `DATE`. SQLite STRICT
accepts only `INT`, `INTEGER`, `REAL`, `TEXT`, `BLOB` and `ANY`
(`DATE` fails with "unknown datatype", verified), so dates are `TEXT`
holding ISO-8601, C4 replaces the type check, and tests compare
strings. Date literals are plain `'YYYY-MM-DD'` in all four files; a
`DATE '...'` literal is a syntax error in SQLite. Times are text in
every dialect (section 6).

Dialect differences:

- MySQL: `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin`.
  The default collation is case-insensitive and would loosen key and
  foreign-key matching compared with the other three files. The header
  says MySQL 8.0.16 or later, because earlier 8.0 parses `CHECK` and
  ignores it.
- SQLite: `STRICT`, `TEXT` for dates and fixed-width fields, `PRAGMA
  foreign_keys=ON` before any `BEGIN`, and C4.
- PostgreSQL: the commented `ON CONFLICT` block (section 2).
- ANSI: the baseline, with no wrapper and no dialect extras.

Columns beyond the first matrix (Phase B):

| Column | ANSI / PostgreSQL / MySQL | SQLite STRICT | CHECK |
|---|---|---|---|
| name | `VARCHAR(255)` | `TEXT` | none |
| timezone | `VARCHAR(64)` | `TEXT` | none |
| weekend_day_1, weekend_day_2 | `SMALLINT` | `INTEGER` | C3: `BETWEEN 0 AND 6` |
| source_url | `VARCHAR(2048)` | `TEXT` | none |
| note | `VARCHAR(4096)` | `TEXT` | none |
| sessions.type | `VARCHAR(16)` | `TEXT` | C2: `IN ('regular','pre_market','post_market','lunch_break','auction','halt')` |
| predicted, weekend_exception | `SMALLINT` | `INTEGER` | C2: `IN (0, 1)` |
| seq | `SMALLINT NOT NULL` | `INTEGER NOT NULL` | C3: `>= 1` |
| origin | `VARCHAR(16)` | `TEXT` | C2: `IN ('explicit','generated')` |

The `origin` row replaces the `VARCHAR(n)` entry in the first matrix.

Booleans (`predicted`, `weekend_exception`) are `SMALLINT` with
`CHECK IN (0, 1)` in all four dialects, not a native `BOOLEAN`. SQLite
STRICT has no `BOOLEAN` (verified), and MySQL's `BOOLEAN` is
`TINYINT(1)`. Consistency across the four files wins over native types.
Section 7 still applies: a stored `true`, `false` or absent value
becomes 1, 0 or NULL.

Nullability. A column is `NOT NULL` if and only if its field is in the
`required` array of `schema.json` for that record type. `seq` and
`origin` are `NOT NULL` by definition, because the exporter adds them.
Primary key columns are `NOT NULL` through the key itself.

No CHECK on `name` (`exchanges`, `holidays`, `ad_hoc_closures`): the
schema's `minLength` counts characters, and no dialect has a portable
character-count function. SQLite has no `CHAR_LENGTH` and MySQL's
`LENGTH` counts bytes, so a length check on text that can be non-ASCII
(three exchange names and 25 holiday names are at `cca603c`) would not
mean the same thing in every file. `validate.py` enforces `minLength`
at build time.

### 3. CSV

One row per exchange, one per session, one per holiday, one per
`(exchange, year)`. Not nested JSON strings, not semicolon-delimited
pairs: both defeat `GROUP BY` and force every consumer to write a
parser. UTF-8, no BOM, LF line endings, RFC 4180 quoting, header row
always present. Names contain commas (4, all holiday names) and
non-ASCII characters (28: 3 exchange names and 25 holiday names), so
quoting and encoding are not optional.

**Files.** Five files at the repository root, one per table:
`exchange_calendar.exchanges.csv`, `exchange_calendar.sessions.csv`,
`exchange_calendar.holidays.csv`, `exchange_calendar.ad_hoc_closures.csv`
and `exchange_calendar.confidence.csv`. The header row is that table's
column list from section 5, with the same names in the same order.
`sessions` and `confidence` are files of their own and nothing is nested
into `exchanges`. `holidays` carries explicit and generated rows
together, told apart by `origin` (section 8). The `ad_hoc_closures` file
is a header row and no records while the table is empty.

**One dialect.** Comma-delimited, UTF-8 without a BOM. There is no
Excel, European or tab-separated variant, unlike the sibling iso4217
export, which ships four dialect variants of its one table. This ADR
is the contract; a BOM variant would be a new decision if consumers
ask for one. Excel on Windows guesses the code page of a file with no
BOM, so the 28 non-ASCII names need an explicit UTF-8 import there, or
pandas or Sheets.

**Quoting and line endings.** Minimal quoting: a field is quoted if and
only if it contains a comma, a double quote, CR or LF, and a double
quote inside a quoted field is doubled. Every record ends with LF,
including the last, so the file ends with one newline and has no blank
trailing line. An absent value is an empty, unquoted field and booleans
are `true` or `false` (section 7); dates and times are the text of
section 6; `year`, `seq` and the weekend days are plain integers.

**Formula guard.** A spreadsheet runs a cell that starts with `=`, `+`,
`-` or `@`. No field does today. The exporter exits 2, before writing
any file, if the text of any field in any table starts with one of
those four characters.

**Command line.** The same as the SQL exporter: `--registry` (`-r`),
`--stdout` and `--check`, with `--table` in place of `--dialect`. The
value is `exchanges`, `sessions`, `holidays`, `ad_hoc_closures`,
`confidence` or `all`, and `all` is the default; `--stdout` needs one
table. `--check` regenerates into a temporary directory and compares
bytes. Exit codes: 0 success or match, 1 mismatch, 2 fatal (bad input
or a failed guard), 3 a committed file is missing.

**Prerequisite.** `.gitattributes` has a rule for `*.sql` and none for
`*.csv`. It needs `*.csv text eol=lf` before the exporter ships, or a
Windows checkout rewrites line endings and `--check` fails.

### 4. Parquet

The same flattened tables, no structs or maps. Native nesting would
make Parquet the one format whose shape differs from the other two,
and at 4,600 rows it buys nothing. Dates use the Parquet `DATE`
logical type; every other column is a string, integer or boolean.

### 5. Column order

Semantic, not alphabetical, identical across formats. Key columns
first, then descriptive columns, then data. In CSV each list below is
the header row of that table's file (section 3).

- `exchanges`: `code`, `name`, `mic`, `country_code`, `timezone`,
  `weekend_day_1`, `weekend_day_2`, `regular_open`, `regular_close`,
  `generation_start`, `generation_end`
- `sessions`: `exchange_code`, `type`, `seq`, `open`, `close`, `at`
- `holidays`: `exchange_code`, `date`, `name`, `status`, `origin`,
  `seq`, `early_close_time`, `delayed_open_time`, `predicted`,
  `weekend_exception`, `source_url`
- `ad_hoc_closures`: `exchange_code`, `date`, `seq`, `name`,
  `status`, `early_close_time`, `source_url`
- `confidence`: `exchange_code`, `year`, `level`, `source`,
  `last_verified`, `note`

`seq` (section 2) sits right after the last column of its table's
natural key. Types and CHECKs for every column are in 2a, not here.

`weekend_days` and `generation_range` are exactly two items by schema
(`minItems` = `maxItems` = 2), so they become two columns each,
lossless and in stored order. `extended_hours` is not exported: it is
a redundant projection of the `pre_market` and `post_market`
sessions. `regular_open` and `regular_close` stay on `exchanges`
because every wrapper exposes them.

Rows are sorted by `code`, then `type`, `date` or `year`, so that
exports are byte-reproducible. Ties break by `seq`.

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
`predicted` is `true` on 227 entries, `false` on 58 and absent on the
rest; `weekend_exception` is `true` on 2 and absent elsewhere. The
schema defines absent `predicted` as false, so consumers read NULL and
`false` alike. The exporters do not rewrite `false` to NULL or the
reverse.

Values are exported as stored, with no normalisation. In particular
`name` keeps its "(predicted)" suffix, and `predicted` is the stored
flag. The two agree on all 227 `true` entries today.

### 8. Generated holidays

The exports carry both. `holidays` holds explicit and generated rows
together, distinguished by `origin` (`explicit` or `generated`).
`source_url` is NULL for generated rows and non-NULL for explicit
ones. A generated date never falls on the exchange's own `weekend_days`
(v2.15.0): the generator drops weekend occurrences of `fixed_date`
rules and applies `fixed_with_weekend_adjustment` against the
exchange's real weekend, so every `origin = generated` row is a real
trading-day closure. Wrapper `is_holiday` is unaffected: it returns true
for any weekend date before reading holiday data. Before v2.15.0, 215 of 267 generated rows were
no-ops on closed days. Dropping generated rows would make every export answer
"is this date a holiday?" differently from every wrapper for the 20
exchanges that have them. Carrying them without `origin` would hide
which dates are verified.

## Prerequisite: `country_code`

The `exchanges` table needs `country_code`, which `calendar.json` did
not carry through v2.13.0: `tools/build.py` dropped `country` and
`country_code`, both required by the schema. Resolved in v2.15.0, which
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
