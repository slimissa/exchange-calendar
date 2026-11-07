# Exchange Calendar Registry

**A versioned, schema-validated registry of trading calendars for 74 exchanges across 6 continents, with the evidence for each calendar kept next to it: a fetcher status per exchange, a confidence level per exchange-year, and a divergence report against two reference libraries.**

One JSON file per exchange is the source of truth. Everything else — `calendar.json`, SQL, CSV, TSV, Parquet, four language wrappers — is regenerated from it and re-checked on every push. The registry does not claim all 74 calendars are verified. It says which ones an independent reference covers, which it does not, and how many disagreements remain.

[![Validate](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml)
[![Update](https://github.com/slimissa/exchange-calendar/actions/workflows/update-exchange.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/update-exchange.yml)
[![Divergence](https://github.com/slimissa/exchange-calendar/actions/workflows/divergence.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/divergence.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Schema Version](https://img.shields.io/badge/schema-2.1.1-green.svg)](./schema.json)
[![Registry Version](https://img.shields.io/badge/registry-2.24.0-orange.svg)](./CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-5625-green.svg)](./tests/)
[![Exchanges](https://img.shields.io/badge/exchanges-74-blue.svg)](./exchanges/)
[![Fetchers](https://img.shields.io/badge/fetchers-41_CI--verified-green.svg)](./.github/workflows/live-fetcher-check.yml)
[![Blocked](https://img.shields.io/badge/blocked-30-lightgrey.svg)](./BLOCKED.md)

---

## Contents

1. [At a glance](#1-at-a-glance)
2. [Why this exists](#2-why-this-exists)
3. [Where to start](#3-where-to-start)
4. [Quick start](#4-quick-start)
5. [The data model: five layers](#5-the-data-model-five-layers)
6. [The registry file](#6-the-registry-file)
7. [The coverage boundary](#7-the-coverage-boundary)
8. [Sessions and holidays](#8-sessions-and-holidays)
9. [Flat exports: SQL, CSV, TSV, Parquet](#9-flat-exports-sql-csv-tsv-parquet)
10. [The Tier 3 execution gate](#10-the-tier-3-execution-gate)
11. [Divergence testing](#11-divergence-testing)
12. [Worked example: a year of one exchange](#12-worked-example-a-year-of-one-exchange)
13. [Examples](#13-examples)
14. [Command-line interface](#14-command-line-interface)
15. [Language wrappers](#15-language-wrappers)
16. [Validation](#16-validation)
17. [Continuous integration](#17-continuous-integration)
18. [Release pipeline](#18-release-pipeline)
19. [Versioning](#19-versioning)
20. [Project structure](#20-project-structure)
21. [Documentation index](#21-documentation-index)
22. [Contributing](#22-contributing)
23. [Known limitations](#23-known-limitations)
24. [Consumed by](#24-consumed-by)
25. [What's next](#25-whats-next)

Every number below comes from a one-line command in the audit that accompanies this README (`audit-readme.sh`, output in `SPEC.md`). If a number here disagrees with the tree, the tree wins; `tools/check_doc_facts.py` checks the counts it can.

---

## 1. At a glance

| | |
|---|---|
| **Exchanges** | 74, across 6 continents, one JSON file each in [`exchanges/`](./exchanges) |
| **Fetcher status** (`fetcher_status`) | 41 `implemented`, 3 `ci_unreachable`, 2 `blocked`, 28 `none`. 46 have a registered fetcher; 30 are listed in [`BLOCKED.md`](./BLOCKED.md) (the 28 with no fetcher plus the 2 `blocked`). |
| **Independent reference** | 50 exchanges are compared against at least one reference library; 24 have none ([`docs/DIVERGENCE.md`](./docs/DIVERGENCE.md)) |
| **The reference is thinner than it looks** | `pandas_market_calendars` serves 46 of the exchanges both libraries cover straight from `exchange_calendars`. For those, "two references" is one reference counted twice. |
| **Verification class as a field** | None. The registry has no `verification_class` field; the 50 / 24 split is derived from the divergence report, and [Section 7](#7-the-coverage-boundary) says how |
| **Per-year confidence** | 564 exchange-year rows: 560 `medium` (source `manual`), 4 `high` (source `fetcher`: XBUD, XDFM, XIST, XWBO for 2026) |
| **Divergence** | 62,738 trading days compared, 2024-2029; all available sources agree on 62,465 (99.6%). 273 disagreeing days remain, every one classified: 213 unpublished, 62 library error, 1 convention difference. Unclassified: 0. |
| **What 99.6% is not** | Agreement with a library is not agreement with the exchange. 213 of the 273 are future dates (2027-2029) the exchange has not published; the registry value there is a prediction. |
| **Registry errors found by the comparison** | 410 dates across 41 exchanges, recorded in `docs/divergence_triage.json` as `registry_error`, all fixed |
| **Coverage window** | `generation_range` runs 2025-01-01 to 2029-12-31 for 68 exchanges; 6 start earlier (XASX, XHKG, XLON, XNAS, XNYS from 1990; XTKS from 1997) |
| **Sessions in the data** | 74 `regular`, 30 `pre_market`, 29 `post_market`, 22 `auction`, 11 `lunch_break` |
| **Flat exports** | 29 files: 4 SQL (one per dialect, all five tables in each), 20 CSV/TSV (5 tables × 4 dialects), 5 Parquet (one per table) |
| **Wrappers** | 4: Python, JavaScript, Go, Rust. One shared fixture of 24 queries. |
| **Tests** | 5,625 in the root suite (includes the 95 Python wrapper tests); JavaScript 100 more; Go 86 and Rust 83 declarations, counted statically |
| **Release gate** | 18 local checks in `scripts/release.sh`, plus 3 static preflight checks |
| **Version** | 2.23.13 (schema 2.1.1) |
| **Sources** | Many: each exchange's own publication, one primary per exchange. This is a many-source registry, not a one-source registry like the ISO family. |
| **Runtime dependencies** | None. The JSON is the contract. Tool time: `jsonschema`, `pyarrow`, `sqlglot`, and the fetchers' own libraries. |
| **License** | Apache 2.0 |

The row to read twice is the third and fourth: **50 of 74 have an independent reference and 24 do not.** Of those 24, nine have a working CI fetcher against the exchange's own page, two have a fetcher that cannot run in CI, and thirteen have no fetcher at all. [Section 7](#7-the-coverage-boundary) has the table.

---

## 2. Why this exists

Every trading system, quant library and fintech app keeps its own exchange holiday list. They go out of date, they disagree, and some include national holidays the exchange does not observe. This registry is one versioned, schema-validated file set that any tool can depend on.

**Time is the join dimension.** Every fact table needs a trading calendar and none should own it. A fact table that carries only `(mic, date)` inherits from this registry whether the exchange was open, whether the session closed early, and how much evidence stands behind that answer, instead of copying holiday lists into every project.

**Correctness has a boundary, and the registry draws it.** A calendar is a claim, and most of what a calendar claims about is the future. The registry does not say "all 74 exchanges are verified". It says:

- For **50 of 74** exchanges an external reference library has the calendar, and the comparison for 2024-2029 is public in `docs/DIVERGENCE.md`. 30 of those 50 show no disagreement. The other 20 show 273 disagreeing days, each classified.
- For **24 of 74** no reference library knows the exchange. There the only checks are the exchange's own published pages (via a fetcher, for nine of them) or manual curation (for the rest).
- A reference library is not the exchange. The report says so itself: a disagreement does not say which side is right, and nothing in it has been checked against the exchange's calendar unless the triage entry says so.

A consumer who reads the registry should be able to see that boundary, not discover it later. The data carries `fetcher_status` per exchange and `confidence` per exchange-year; the divergence report carries the rest.

---

## 3. Where to start

| If you are... | Start with |
|---------------|------------|
| A programmer who wants a library | [Language wrappers](#15-language-wrappers) |
| A database engineer | [`exchange_calendar.postgresql.sql`](./exchange_calendar.postgresql.sql) and the other dialects; see [Flat exports](#9-flat-exports-sql-csv-tsv-parquet) |
| An analyst in Excel, Sheets, pandas or DuckDB | The CSV or Parquet files; see [Flat exports](#9-flat-exports-sql-csv-tsv-parquet) |
| A shell user | There is no `exchange-calendar` command; see [Command-line interface](#14-command-line-interface) for what exists |
| Asking "what does the registry know, and what can it prove?" | [The coverage boundary](#7-the-coverage-boundary), [`docs/DIVERGENCE.md`](./docs/DIVERGENCE.md) and [Known limitations](#23-known-limitations) |
| Asking "was XNYS open on 2030-01-01?" | It cannot say: `generation_range` ends 2029-12-31. See [The coverage boundary](#7-the-coverage-boundary) |
| Evaluating whether to trust a date | [`docs/DIVERGENCE.md`](./docs/DIVERGENCE.md), [`docs/FETCHERS.md`](./docs/FETCHERS.md), [`BLOCKED.md`](./BLOCKED.md) |
| Adding or fixing an exchange | [`CONTRIBUTING.md`](./CONTRIBUTING.md) and [`docs/contributing_exchange.md`](./docs/contributing_exchange.md) |
| Joining to MICs or country codes | [Consumed by](#24-consumed-by) and [`docs/CONSUMERS.md`](./docs/CONSUMERS.md) |
| Building a registry with the same release discipline | [`RELEASE_PATTERN.md`](./RELEASE_PATTERN.md) |

---

## 4. Quick start

Nothing is published to PyPI, npm, crates.io or a Go proxy: `.github/workflows/publish.yml.disabled` is disabled. Every path starts from a clone.

```bash
git clone https://github.com/slimissa/exchange-calendar.git
cd exchange-calendar
pip install -r requirements.txt
python3 tools/validate.py          # validate exchanges/*.json against schema.json
python3 tools/build.py             # rebuild calendar.json
```

### Python (3.8+ wrapper, no dependencies)

```bash
pip install ./wrappers/python
```

```python
from exchange_calendar import CalendarRegistry

reg = CalendarRegistry()                       # bundled calendar.json
xnys = reg.get("XNYS")

print(xnys.is_holiday("2026-07-03"))           # True  (Independence Day, observed)
print(xnys.early_close_time("2026-11-27"))     # 13:00
print(xnys.next_trading_day("2026-07-02"))     # 2026-07-06
print(reg.confidence("XNYS", 2026))            # {'last_verified': None, 'level': 'medium', 'source': 'manual'}
print(reg.confidence("XNYS", 2028)["note"])    # predicted
```

`confidence(mic, year)` is the verification signal the wrappers expose: a level, a source, a `last_verified` date and, for future years, a `note` of `predicted`. **No wrapper exposes the 50 / 24 reference split or the divergence verdict**, because neither is a field in the data ([Section 7](#7-the-coverage-boundary)).

### JavaScript (Node)

```javascript
const { CalendarRegistry } = require('./wrappers/javascript');
const reg = new CalendarRegistry();
const xlon = reg.get('XLON');
console.log(xlon.isOpen('2025-12-24', '12:00'));   // true  (before the 12:30 close)
console.log(reg.confidence('XLON', 2026));
```

### Rust (edition 2021)

```toml
[dependencies]
exchange-calendar-registry = { path = "wrappers/rust" }
```

```rust
use exchange_calendar::Registry;
```

### Go (1.21+)

```go
import exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"

registry, _ := exchangecalendar.LoadRegistry("calendar.json")
```

Each wrapper README has the full API, and the cross-language fixture pins the behaviour all four share ([Section 15](#15-language-wrappers)).

### Any SQL database

```bash
psql -f exchange_calendar.postgresql.sql              # PostgreSQL
mysql < exchange_calendar.mysql.sql                   # MySQL 8 / MariaDB
sqlite3 registry.db < exchange_calendar.sqlite.sql    # SQLite
psql -f exchange_calendar.sql                         # generic dialect
```

```sql
-- Closed days of one exchange in 2026, with the confidence recorded for that year.
SELECT e.mic, h.date, h.name, c.level, c.source
FROM exchanges e
JOIN holidays   h ON h.exchange_code = e.code
JOIN confidence c ON c.exchange_code = e.code
                 AND c.year = CAST(substr(h.date, 1, 4) AS INTEGER)
WHERE e.mic = 'XNYS' AND h.status = 'closed' AND h.date LIKE '2026-%';
```

(`CAST ... AS INTEGER` is the SQLite spelling; use the integer cast of your engine.)

### pandas

```python
import pandas as pd
h = pd.read_parquet("exchange_calendar.holidays.parquet")
c = pd.read_parquet("exchange_calendar.confidence.parquet")
print(c.groupby(["level", "source"]).size())
# level   source
# high    fetcher      4
# medium  manual     560
```

---

## 5. The data model: five layers

The registry is several files with different authority. There is no `docs/LAYERS.md` in this tree; this section is the layer model. Where a layer is not enforced by a tool, it says so.

| Layer | Name | Lives at | Committed | Authority |
|-------|------|----------|-----------|-----------|
| 0 | **Raw** | Each exchange's own publication (HTML, PDF, CSV) | No | Fetched on demand by `tools/update_from_exchange.py`; `fetcher_manifest.json` records hash and fetch date for four of them |
| 1 | **Curated** | [`exchanges/*.json`](./exchanges) | Yes | The registry. 74 files; single source of truth for everything below |
| 2 | **Bundled** | `calendar.json`, `wrappers/python/exchange_calendar/calendar.json`, `checksums.json` | Yes | Projections of Layer 1 consumed by the wrappers |
| 3 | **Derived** | 29 flat files at the repository root | Yes | Projections of `calendar.json`: 4 SQL, 20 CSV/TSV, 5 Parquet |
| 4 | **Reports** | `docs/DIVERGENCE.md`, `docs/FETCHERS.md`, `BLOCKED.md`, `docs/facts.json` | Yes | Evidence about Layer 1, not data. `DIVERGENCE.md` is generated; `FETCHERS.md` and `BLOCKED.md` are written by hand |

**Where the rule is enforced by a tool, not by convention:**

| Edge | Tool | Mode |
|------|------|------|
| Layer 0 → 1 | `tools/update_from_exchange.py` (one fetcher per exchange) | Opens a pull request; the updater calls `tools/check_removed_entries.py` to refuse silent deletions ([ADR 0008](./docs/decisions/0008-removal-guard-semantics.md)). That guard is not a separate CI or release-gate step |
| Layer 1 → 2 | `tools/build.py`, `make package` | Deterministic: sorted keys and exchanges, no timestamps. `tools/check_wrapper_snapshot.py` compares the Python wrapper's copy; `tools/generate_checksums.py` and `tools/verify_checksums.py` cover `checksums.json` |
| Layer 2 → 3 | `tools/export_sql.py`, `tools/export_csv.py`, `tools/export_parquet.py` | Each has `--check`; the Parquet check compares logical content, not bytes |
| Layer 3 consistency | `tests/test_cross_format_consistency.py` | Loads each table from SQLite, CSV and Parquet and requires identical values |
| Layer 3 execution | `tools/check_sql_dialects.py` | Runs the PostgreSQL and MySQL files on real servers ([Section 10](#10-the-tier-3-execution-gate)) |
| Layer 1 → 4 | `tools/divergence_test.py`, `tools/divergence_report.py` | Weekly workflow opens a pull request when the report changes |
| Layer 4 prose | `tools/update_facts.py --check`, `tools/check_doc_facts.py`, `tools/check_doc_links.py` | Counts in prose are compared with `docs/facts.json`; links and the 74-row table are resolved |

**Not enforced by a tool:**

- **Layer 0 is not reproducible.** Nothing in the tree stores the raw publications; the sources change, expire or sit behind a bot wall. Replaying history means checking out a tag.
- **Layer 1 → `exchanges/*.json` for 28 exchanges has no fetcher.** Their data is curated by hand against sources the notes in `BLOCKED.md` describe. No tool re-reads those sources.
- **The two vendored snapshots have no generator in the tree** (`tools/iso3166_snapshot.json`, `tools/iso10383_snapshot.json`). `docs/CONSUMERS.md` says "generator script (see `tools/`)"; there is none. They are checked for freshness, and their contents are checked by use, but they cannot be reproduced from a pinned upstream tag.
- **`docs/FETCHERS.md` and `BLOCKED.md` verdicts are hand-written.** `tools/check_stale_verifications.py` flags old `Last verified` dates; nothing re-tests the verdict itself.

---

## 6. The registry file

There are two shapes, and both are committed:

- [`exchanges/<MIC>.json`](./exchanges) — 74 files, one per exchange. The source of truth.
- [`calendar.json`](./calendar.json) — one file built from them: `{"exchanges": [...], "meta": {"exchange_count": 74, "version": "2.23.13"}}`. The wrappers and the flat exports read this file, not the 74.

### An exchange file

`exchanges/XNYS.json`, with the 315 `Historical Holiday` entries and the per-year `confidence` rows elided:

```json
{
  "code": "XNYS",
  "mic": "XNYS",
  "name": "New York Stock Exchange",
  "country": "United States of America",
  "country_code": "US",
  "timezone": "America/New_York",
  "weekend_days": [5, 6],
  "generation_range": ["1990-01-01", "2029-12-31"],
  "fetcher_status": "implemented",
  "regular_hours": { "open": "09:30", "close": "16:00" },
  "extended_hours": {
    "pre_market":  { "open": "04:00", "close": "09:30" },
    "after_hours": { "open": "16:00", "close": "20:00" }
  },
  "sessions": [
    { "type": "pre_market",  "open": "04:00", "close": "09:30" },
    { "type": "regular",     "open": "09:30", "close": "16:00" },
    { "type": "post_market", "open": "16:00", "close": "20:00" }
  ],
  "holidays": {
    "explicit": [
      { "date": "1990-01-01", "name": "Historical Holiday", "status": "closed",
        "source_url": "https://github.com/gerrymanoim/exchange_calendars" }
    ],
    "recurrence_rules": [
      { "name": "New Year's Day", "rule": "fixed_with_sunday_observance",
        "month": 1, "day": 1, "effective_from": "2025-01-01", "status": "closed",
        "source_url": "https://www.nyse.com/markets/hours-calendars" }
    ]
  },
  "ad_hoc_closures": [],
  "confidence": {
    "2026": { "level": "medium", "source": "manual", "last_verified": null },
    "2027": { "level": "medium", "source": "manual", "last_verified": null, "note": "predicted" }
  }
}
```

### An unusual exchange

`exchanges/XTKS.json` has a lunch break, an hours change inside its history, and the only `regular_hours` shape that is a list:

```json
"regular_hours": [
  { "open": "09:00", "close": "15:00", "effective_from": "1997-01-01" },
  { "open": "09:00", "close": "15:30", "effective_from": "2024-11-05" }
],
"sessions": [
  { "type": "regular",     "open": "09:00", "close": "15:30" },
  { "type": "lunch_break", "open": "11:30", "close": "12:30" }
],
"generation_range": ["1997-01-01", "2029-12-31"]
```

`exchanges/XSAU.json` shows the other unusual case: a Thursday-Friday weekend (`"weekend_days": [4, 5]`) and a predicted Islamic date, `{"date": "2027-03-09", "name": "Eid al-Fitr (predicted)", "predicted": true, "status": "closed"}`.

### Field reference

Counts are over the 74 exchange files. No top-level field is `null` in any file.

| Field | Present in | Meaning |
|-------|-----------:|---------|
| `code`, `mic` | 74 | Exchange code and ISO 10383 MIC. Joined to the ISO 10383 snapshot by `tools/check_mic_codes.py` |
| `name`, `country`, `country_code` | 74 | `country_code` joined to the ISO 3166 snapshot; `country` must equal ISO 3166's `name` |
| `timezone` | 74 | IANA time zone |
| `weekend_days` | 74 | Weekday numbers, Monday = 0. 67 exchanges use `[5, 6]`, 7 use `[4, 5]` |
| `generation_range` | 74 | `[start, end]`: the dates the registry is willing to answer for ([Section 7](#7-the-coverage-boundary)) |
| `fetcher_status` | 74 | `implemented`, `ci_unreachable`, `blocked` or `none` |
| `regular_hours` | 74 | An object, or a list of objects with `effective_from` |
| `sessions` | 74 | List of typed intervals; see [Enums](#enums) |
| `extended_hours` | 30 | Legacy pre- and post-market block, kept beside `sessions` |
| `holidays.explicit` | 74 | Dated entries: 6,290 in all (5,823 `closed`, 462 `early_close`, 5 `delayed_open`; 226 flagged `predicted`) |
| `holidays.recurrence_rules` | 74 | 318 rules in all; see [Enums](#enums) |
| `ad_hoc_closures` | 74 | One-off closures. **Empty in all 74 files today** (0 rows) |
| `confidence` | 74 | One row per year inside `generation_range`: 564 rows in all |

### `calendar.json`

`calendar.json` carries one object per exchange, plus a `meta` object with `exchange_count` and `version`. The build step (`tools/build.py`) is a projection with one change to `holidays`: the object holds `explicit` (6,290 entries in all) and `generated` (54 in all, dates `tools/generate_dates.py` derives from recurrence rules), and `recurrence_rules` itself is not carried. The wrappers and every export read this shape.

### Coverage

| `fetcher_status` | Exchanges | Verified how |
|------------------|----------:|--------------|
| `implemented` | 41 | A fetcher reads the exchange's own page or file; `live-fetcher-check.yml` runs the stable set weekly and blocks on failure |
| `ci_unreachable` | 3 | XHKG, XNSA, XSHG: a fetcher exists but the source is not reachable from CI |
| `blocked` | 2 | XKUW, XSAU: a fetcher exists; HTTP 403 on 2026-09-17 |
| `none` | 28 | No fetcher. Documented in `BLOCKED.md` |

### Enums

**`weekend_days`**: `[5, 6]` (Saturday-Sunday) or `[4, 5]` (Friday-Saturday: DSMD, XBAH, XCAI, XDHA, XKUW, XMUS, XSAU).

**`holidays.*[].status`**: `closed` (5,823), `early_close` (462), `delayed_open` (5).

**`sessions[].type`**: `regular`, `pre_market`, `post_market`, `auction`, `lunch_break`.

**`holidays.recurrence_rules[].rule`**: `fixed_date` (186), `easter_offset` (63), `fixed_with_weekend_adjustment` (26), `nth_weekday` (20), `fixed_with_sunday_observance` (13), `fixed_with_thursday_observance` (5), `last_weekday` (5). Rule semantics are in [`docs/recurrence_rules.md`](./docs/recurrence_rules.md).

**`confidence[year].level`**: `medium` (560) and `high` (4). **`.source`**: `manual` (560) and `fetcher` (4).

The field-level schema is [`schema.json`](./schema.json) (schema 2.1.1), documented in [`docs/exchange_schema.md`](./docs/exchange_schema.md). Design decisions are in [`docs/decisions/`](./docs/decisions).

---

## 7. The coverage boundary

This section is what the ISO registries do not need. They reproduce one source. This registry has 74.

### What exists in the data

- **`generation_range`** per exchange: the dates the registry answers for. The registry does not answer outside it.
- **`fetcher_status`** per exchange: whether a program re-reads the exchange's own publication.
- **`confidence`** per exchange-year: `medium` / `manual` for 560 rows; `high` / `fetcher` for 4 (XBUD, XDFM, XIST and XWBO for 2026). `last_verified` is `null` on the `medium` rows. Years after 2026 carry the note `predicted`.

### What does not exist in the data

There is **no `verification_class` field**, and no field says "this exchange has an independent reference". The split below is derived from `docs/DIVERGENCE.md` ("Exchanges with at least one reference library: 50; with none: 24") joined to `fetcher_status`. It is a reading of the report, not something a wrapper can return.

### The 50 and the 24

| | `implemented` | `ci_unreachable` | `blocked` | `none` | Total |
|---|---:|---:|---:|---:|---:|
| **Has a reference library** | 32 | 2 | 1 | 15 | **50** |
| **No reference library** | 9 | 1 | 1 | 13 | **24** |
| Total | 41 | 3 | 2 | 28 | 74 |

**The 24 with no reference library** (the report names them all): DSMD, XATH, XBAH, XBEY, XBRV, XBSP, XBUL, XCAI, XCAS, XCAY, XCOL, XDFM, XDHA, XGSE, XJKT, XKUW, XMAL, XMUS, XNAI, XNSA, XSHE, XSTC, XTAD, XTUN.

- **9 have a fetcher that runs in CI** against the exchange's own page: XBRV, XBSP, XCAY, XCOL, XDFM, XGSE, XMAL, XSHE, XSTC. For these the fetcher is the only independent check.
- **2 have a fetcher that cannot run in CI**: XNSA (`ci_unreachable`) and XKUW (`blocked`).
- **13 have no fetcher and no reference**: DSMD, XATH, XBAH, XBEY, XBUL, XCAI, XCAS, XDHA, XJKT, XMUS, XNAI, XTAD, XTUN. Their dates rest on manual curation against the sources `BLOCKED.md` records. Nothing re-reads them.

So "24 single-source" is true in one sense (no reference library), but only 9 of the 24 have a live check against the exchange. The other 15 have none that runs.

**The 50 with a reference library** are the rest: most of Europe, the Americas, and Asia-Pacific that `exchange_calendars` covers, plus XBOM, XNSE, XSES and XSHG (covered by `pandas_market_calendars` only) and XNAS and XSGO (covered by `exchange_calendars` only). Of the 50, 30 show no disagreement for 2024-2029 and 20 do. 15 of the 50 have no fetcher, so for them the reference library is the only independent check.

### What a reference match means

Two caveats govern how far "has a reference" can be read:

1. **The two libraries are mostly one.** `pandas_market_calendars` serves 46 of the exchanges that both libraries cover from `exchange_calendars`. Only XBOM and XNSE have a PMC-native implementation. For the rest, agreement of PMC and EC is not independent confirmation.
2. **A library is not the exchange.** The 99.6% figure counts days on which every available source agrees. It says nothing about which side is right when they differ, and it says nothing when both are wrong.

A third caveat concerns the **historical backfill**. Six exchanges carry `Historical Holiday` entries copied from `exchange_calendars` (XNYS 315, XNAS 315, XLON 287, XASX 273, XTKS 441, XHKG 497). Those entries are sourced from the library itself, and `docs/DIVERGENCE.md` compares only 2024-2029, so the pre-2024 part of those files has no independent check at all in this tree.

### The limit

A consumer querying a date can read the exchange's `fetcher_status` and the year's `confidence`, and can look the exchange up in the divergence report. A date for an exchange in the 24, or for any year after 2026, has no independent confirmation that this registry can show. For 2027-2029 the registry value is a prediction wherever the exchange has not published; 213 disagreeing days are recorded as `unpublished` with a `recheck_date` for that reason.

### The 74 exchanges

One row per exchange, from `exchanges/*.json`. The icon is `fetcher_status`: ✅ `implemented`, ⚠️ `ci_unreachable`, ⛔ `blocked` or `none`. `tools/check_doc_links.py` fails CI if this table disagrees with the JSON or with `BLOCKED.md`.

| Exchange | MIC | Status | Source | Notes |
|----------|-----|:------:|--------|-------|
| Qatar Exchange | DSMD | ⛔ | qe.com.qa | [BLOCKED.md#dsmd](BLOCKED.md#dsmd) |
| Euronext Amsterdam | XAMS | ✅ | euronext.com | [#xams](docs/FETCHERS.md#xams) |
| Australian Securities Exchange | XASX | ✅ | asx.com.au | [#xasx](docs/FETCHERS.md#xasx) |
| Athens Exchange | XATH | ⛔ | athens.euronext.com | [BLOCKED.md#xath](BLOCKED.md#xath) |
| Bahrain Bourse | XBAH | ⛔ | bahrainbourse.com | [BLOCKED.md#xbah](BLOCKED.md#xbah) |
| Bermuda Stock Exchange | XBDA | ✅ | bsx.com | [#xbda](docs/FETCHERS.md#xbda) |
| Beirut Stock Exchange | XBEY | ⛔ | bse.com.lb | [BLOCKED.md#xbey](BLOCKED.md#xbey) |
| Stock Exchange of Thailand | XBKK | ⛔ | set.or.th | [BLOCKED.md#xbkk](BLOCKED.md#xbkk) |
| Bolsa de Valores de Colombia | XBOG | ⛔ | bvc.com.co | [BLOCKED.md#xbog](BLOCKED.md#xbog) |
| BSE India | XBOM | ⛔ | bseindia.com | [BLOCKED.md#xbom](BLOCKED.md#xbom) |
| Euronext Brussels | XBRU | ✅ | euronext.com | [#xbru](docs/FETCHERS.md#xbru) |
| BRVM (8 UEMOA countries) | XBRV | ✅ | brvm.org | [#xbrv](docs/FETCHERS.md#xbrv) |
| B3 (Brazil) | XBSP | ✅ | b3.com.br | [#xbsp](docs/FETCHERS.md#xbsp) |
| Budapest Stock Exchange | XBUD | ✅ | bse.hu | [#xbud](docs/FETCHERS.md#xbud) |
| Bolsas y Mercados Argentinos | XBUE | ✅ | byma.com.ar | [#xbue](docs/FETCHERS.md#xbue) |
| Bulgarian Stock Exchange | XBUL | ⛔ | bse-sofia.bg | [BLOCKED.md#xbul](BLOCKED.md#xbul) |
| Egyptian Exchange | XCAI | ⛔ | egx.com.eg | [BLOCKED.md#xcai](BLOCKED.md#xcai) |
| Bourse de Casablanca | XCAS | ⛔ | casablanca-bourse.com | [BLOCKED.md#xcas](BLOCKED.md#xcas) |
| Cayman Islands Stock Exchange | XCAY | ✅ | csx.ky | [#xcay](docs/FETCHERS.md#xcay) |
| Colombo Stock Exchange | XCOL | ✅ | cdn.cse.lk | [#xcol](docs/FETCHERS.md#xcol) |
| Nasdaq Copenhagen | XCSE | ✅ | nasdaq.com | [#xcse](docs/FETCHERS.md#xcse) |
| Dubai Financial Market | XDFM | ✅ | assets.dfm.ae | [#xdfm](docs/FETCHERS.md#xdfm) |
| Dhaka Stock Exchange | XDHA | ⛔ | dsebd.org | [BLOCKED.md#xdha](BLOCKED.md#xdha) |
| Euronext Dublin | XDUB | ✅ | euronext.com | [#xdub](docs/FETCHERS.md#xdub) |
| Deutsche Boerse Xetra | XETR | ✅ | cashmarket.deutsche-boerse.com | [#xetr](docs/FETCHERS.md#xetr) |
| Ghana Stock Exchange | XGSE | ✅ | gse.com.gh | [#xgse](docs/FETCHERS.md#xgse) |
| Nasdaq Helsinki | XHEL | ✅ | nasdaq.com | [#xhel](docs/FETCHERS.md#xhel) |
| Hong Kong Exchange | XHKG | ⚠️ | hkex.com.hk | [#xhkg](docs/FETCHERS.md#xhkg), [BLOCKED.md#xhkg](BLOCKED.md#xhkg) |
| Nasdaq Iceland | XICE | ✅ | nasdaq.com | [#xice](docs/FETCHERS.md#xice) |
| Borsa Istanbul | XIST | ✅ | borsaistanbul.com | [#xist](docs/FETCHERS.md#xist) |
| Indonesia Stock Exchange | XJKT | ⛔ | idx.co.id | [BLOCKED.md#xjkt](BLOCKED.md#xjkt) |
| Johannesburg Stock Exchange | XJSE | ⛔ | jse.co.za | [BLOCKED.md#xjse](BLOCKED.md#xjse) |
| Pakistan Stock Exchange | XKAR | ⛔ | psx.com.pk | [BLOCKED.md#xkar](BLOCKED.md#xkar) |
| Bursa Malaysia | XKLS | ⛔ | bursamalaysia.com | [BLOCKED.md#xkls](BLOCKED.md#xkls) |
| Korea Exchange | XKRX | ⛔ | global.krx.co.kr | [BLOCKED.md#xkrx](BLOCKED.md#xkrx) |
| Boursa Kuwait | XKUW | ⛔ | boursakuwait.com.kw | [#xkuw](docs/FETCHERS.md#xkuw), [BLOCKED.md#xkuw](BLOCKED.md#xkuw) |
| Bolsa de Valores de Lima | XLIM | ⛔ | bvl.com.pe | [BLOCKED.md#xlim](BLOCKED.md#xlim) |
| Euronext Lisbon | XLIS | ✅ | euronext.com | [#xlis](docs/FETCHERS.md#xlis) |
| Nasdaq Vilnius | XLIT | ✅ | nasdaqbaltic.com | [#xlit](docs/FETCHERS.md#xlit) |
| London Stock Exchange | XLON | ✅ | gov.uk | [#xlon](docs/FETCHERS.md#xlon) |
| Luxembourg Stock Exchange | XLUX | ✅ | luxse.com | [#xlux](docs/FETCHERS.md#xlux) |
| BME (Bolsa de Madrid) | XMAD | ✅ | bolsasymercados.es | [#xmad](docs/FETCHERS.md#xmad) |
| Malta Stock Exchange | XMAL | ✅ | borzamalta.com.mt | [#xmal](docs/FETCHERS.md#xmal) |
| Bolsa Mexicana de Valores | XMEX | ✅ | bmv.com.mx | [#xmex](docs/FETCHERS.md#xmex) |
| Moscow Exchange | XMOS | ✅ | moex.com | [#xmos](docs/FETCHERS.md#xmos) |
| Muscat Securities Market | XMUS | ⛔ | msx.om | [BLOCKED.md#xmus](BLOCKED.md#xmus) |
| Nairobi Securities Exchange | XNAI | ⛔ | nse.co.ke | [BLOCKED.md#xnai](BLOCKED.md#xnai) |
| NASDAQ | XNAS | ✅ | ir.theice.com | [#xnas](docs/FETCHERS.md#xnas) |
| Nigerian Exchange Group | XNSA | ⚠️ | ngxgroup.com | [#xnsa](docs/FETCHERS.md#xnsa), [BLOCKED.md#xnsa](BLOCKED.md#xnsa) |
| NSE India | XNSE | ⛔ | nseindia.com | [BLOCKED.md#xnse](BLOCKED.md#xnse) |
| New York Stock Exchange | XNYS | ✅ | ir.theice.com | [#xnys](docs/FETCHERS.md#xnys) |
| New Zealand Exchange | XNZE | ⛔ | nzx.com | [BLOCKED.md#xnze](BLOCKED.md#xnze) |
| Oslo Bors (Euronext Oslo) | XOSL | ✅ | euronext.com | [#xosl](docs/FETCHERS.md#xosl) |
| Euronext Paris | XPAR | ✅ | euronext.com | [#xpar](docs/FETCHERS.md#xpar) |
| Philippine Stock Exchange | XPHS | ⛔ | pse.com.ph | [BLOCKED.md#xphs](BLOCKED.md#xphs) |
| Prague Stock Exchange | XPRA | ✅ | pse.cz | [#xpra](docs/FETCHERS.md#xpra) |
| Nasdaq Riga | XRIS | ✅ | nasdaqbaltic.com | [#xris](docs/FETCHERS.md#xris) |
| Saudi Exchange (Tadawul) | XSAU | ⛔ | saudiexchange.sa | [#xsau](docs/FETCHERS.md#xsau), [BLOCKED.md#xsau](BLOCKED.md#xsau) |
| Singapore Exchange | XSES | ⛔ | sgx.com | [BLOCKED.md#xses](BLOCKED.md#xses) |
| Santiago Stock Exchange | XSGO | ⛔ | bolsadesantiago.com | [BLOCKED.md#xsgo](BLOCKED.md#xsgo) |
| Shenzhen Stock Exchange | XSHE | ✅ | szse.cn | [#xshe](docs/FETCHERS.md#xshe) |
| Shanghai Stock Exchange | XSHG | ⚠️ | english.sse.com.cn | [#xshg](docs/FETCHERS.md#xshg), [BLOCKED.md#xshg](BLOCKED.md#xshg) |
| Ho Chi Minh Stock Exchange | XSTC | ✅ | staticfile.hsx.vn | [#xstc](docs/FETCHERS.md#xstc) |
| Nasdaq Stockholm | XSTO | ✅ | nasdaq.com | [#xsto](docs/FETCHERS.md#xsto) |
| SIX Swiss Exchange | XSWX | ✅ | six-group.com | [#xswx](docs/FETCHERS.md#xswx) |
| Abu Dhabi Securities Exchange | XTAD | ⛔ | adx.ae | [BLOCKED.md#xtad](BLOCKED.md#xtad) |
| Taiwan Stock Exchange | XTAI | ⛔ | twse.com.tw | [BLOCKED.md#xtai](BLOCKED.md#xtai) |
| Nasdaq Tallinn | XTAL | ✅ | nasdaqbaltic.com | [#xtal](docs/FETCHERS.md#xtal) |
| Tokyo Stock Exchange | XTKS | ✅ | jpx.co.jp | [#xtks](docs/FETCHERS.md#xtks) |
| Toronto Stock Exchange | XTSE | ✅ | tsx.com | [#xtse](docs/FETCHERS.md#xtse) |
| Bourse de Tunis | XTUN | ⛔ | bvmt.com.tn | [BLOCKED.md#xtun](BLOCKED.md#xtun) |
| Warsaw Stock Exchange | XWAR | ✅ | gpw.pl | [#xwar](docs/FETCHERS.md#xwar) |
| Vienna Stock Exchange | XWBO | ✅ | wienerborse.at | [#xwbo](docs/FETCHERS.md#xwbo) |
| Zagreb Stock Exchange | XZAG | ✅ | zse.hr | [#xzag](docs/FETCHERS.md#xzag) |

**47 of 74 registry exchanges have automated fetchers as of v2.24.0** — 42 verified against live sources from CI on every run, plus 5 documented as CI-unreachable (XHKG, XSHG, XNSA) or blocked, HTTP 403 on 2026-09-17 (XKUW, XSAU). The remaining 27 have no fetcher and are documented as blocked sources (29 exchanges are blocked in total, counting XKUW and XSAU) in [`BLOCKED.md`](./BLOCKED.md), with the reasoning for each verdict recorded per exchange. Per-exchange fetcher notes are in [`docs/FETCHERS.md`](./docs/FETCHERS.md).

---

## 8. Sessions and holidays

**Grain.** One file per exchange. Inside it, a day is identified by `(exchange, date)`. A *session* is one open interval of a trading day; an exchange has one `regular` session and optionally pre-market, post-market, auction and lunch-break sessions. Sessions describe the regular day. Which dates are not regular is described by holidays.

### `sessions`

```json
{ "type": "regular",     "open": "09:00", "close": "15:30" },
{ "type": "lunch_break", "open": "11:30", "close": "12:30" }
```

(XTKS.) 74 exchanges have a `regular` session; 30 have `pre_market`, 29 `post_market`, 22 `auction`, 11 `lunch_break`. Times are exchange-local `HH:MM`. `regular_hours` can be a list with `effective_from`, so a past change of hours (XTKS 2024-11-05, XHKG 2011) answers correctly by date.

### `holidays.explicit`

A dated entry. All 6,290 entries have `status` `closed`, `early_close` or `delayed_open`:

```json
{ "date": "2026-11-27", "name": "Day after Thanksgiving", "status": "early_close", "early_close_time": "13:00" }
```

That is the NYSE entry the wrapper reads: `early_close_time("2026-11-27")` returns `13:00`. A `delayed_open` entry (5 in the registry) carries `delayed_open_time`. An entry can carry `predicted: true` (226 do) and `weekend_exception` for the few days the exchange trades on its weekend.

### `holidays.recurrence_rules`

318 rules, which `tools/build.py` expands with `tools/generate_dates.py` into `holidays.generated` in `calendar.json` (54 entries in all; the exchanges' explicit lists already carry most dated entries inside `generation_range`, and the exporters refuse a date that is both explicit and generated). Example from XNYS:

```json
{ "name": "Martin Luther King Jr. Day", "rule": "nth_weekday",
  "month": 1, "n": 3, "weekday": "monday", "effective_from": "2025-01-01", "status": "closed" }
```

The seven rule types are listed in [Enums](#enums); semantics, including observance direction, are in [`docs/recurrence_rules.md`](./docs/recurrence_rules.md).

### `ad_hoc_closures`

A list of one-off closures (a storm, a national day of mourning). **It is empty in all 74 files**, so the `ad_hoc_closures` table in every export has 0 rows. The exporters insert a synthetic row only in tests, to prove the constraints accept one.

### Querying a day

`status_at(date, time)` returns a `SessionStatus` for a date and a local time; `is_holiday(date)` returns true for a date on the exchange's own `weekend_days` before any holiday data is read, so `is_holiday("2026-07-04")` on XNYS is `True` for a Saturday ([`docs/CONSUMERS.md`](./docs/CONSUMERS.md), "Weekend dates and holiday lookups"); `status_at` rules are in [`docs/status_at_semantics.md`](./docs/status_at_semantics.md). Semantics of how the registry updates a day are in [`docs/update_semantics.md`](./docs/update_semantics.md).

---

## 9. Flat exports: SQL, CSV, TSV, Parquet

All 29 flat files are regenerated from `calendar.json`, committed, and compared in CI. The layout is decided in [ADR 0012](./docs/decisions/0012-export-shapes.md). There are **five tables**: `exchanges`, `sessions`, `holidays`, `ad_hoc_closures` and `confidence`.

| Format | Files | Per file | Generator | `--check` |
|--------|------:|----------|-----------|-----------|
| SQL | 4 | all five tables | `tools/export_sql.py` | yes, in CI |
| CSV/TSV | 20 | one table, one dialect | `tools/export_csv.py` | yes, in CI |
| Parquet | 5 | one table | `tools/export_parquet.py` | yes, in CI (logical content) |

| Table | Rows | Columns |
|-------|-----:|--------:|
| `exchanges` | 74 | 11 |
| `sessions` | 166 | 6 |
| `holidays` | 6,344 | 11 |
| `ad_hoc_closures` | 0 | 7 |
| `confidence` | 564 | 6 |

(Parquet row and column counts.) `holidays` has 6,344 rows: 6,290 with `origin` `explicit` and 54 with `origin` `generated`, matching `calendar.json`.

### SQL

Four files, one per dialect, each self-contained and idempotent (`DROP TABLE IF EXISTS`, then create and insert):

| File | Target |
|------|--------|
| `exchange_calendar.sql` | Generic dialect |
| `exchange_calendar.postgresql.sql` | PostgreSQL |
| `exchange_calendar.mysql.sql` | MySQL 8 / MariaDB |
| `exchange_calendar.sqlite.sql` | SQLite |

PostgreSQL, MySQL and SQLite files wrap the load in a transaction. Booleans are `SMALLINT` with `CHECK IN (0, 1)`. The files carry the registry version in a header, so a version bump regenerates them (`release.sh` does this).

```sql
SELECT mic, regular_open, regular_close FROM exchanges WHERE country_code = 'JP';
```

### CSV and TSV

Twenty files named `exchange_calendar.<table>.<dialect>`, in four dialects per table:

| Suffix | Audience |
|--------|----------|
| `.csv` | Every CSV parser: RFC 4180, UTF-8 without BOM |
| `.excel.csv` | Excel on Windows: UTF-8 BOM |
| `.european.csv` | European Excel locales: semicolon-delimited |
| `.tsv` | Terminal, clipboard, Sheets: tab-separated |

LF line endings; a header row always. **Formula-injection guard:** the exporter exits 2, writing no file, if any field in any table begins with `=`, `+`, `-` or `@`.

### Parquet

One file per table: `exchange_calendar.<table>.parquet`. Typed columns; nulls are real nulls. The footer carries `exchange_calendar.version` and `exchange_calendar.table`, so a file received alone can be traced to its release.

```python
import pyarrow.parquet as pq
print(pq.read_table("exchange_calendar.confidence.parquet").schema.metadata[b"exchange_calendar.version"])
# b'2.23.13'
```

### Comparison semantics

`export_sql.py --check` and `export_csv.py --check` regenerate and compare text. `export_parquet.py --check` compares logical content (loading both tables and comparing), because equivalent Parquet files can differ in bytes.

### Cross-format consistency

[`tests/test_cross_format_consistency.py`](./tests/test_cross_format_consistency.py) loads each of the five tables from the SQLite file, the RFC CSV and the Parquet file, normalises each cell by column kind (null, bool, int, date, string) and requires identical columns, row counts and values in the same order. The normalisers are strict: a `True` where the format should say `true` is an error. Self-tests inside the file alter one source at a time and require the comparison to notice, so a pass means something. ISO 4217 and ISO 3166 have no equivalent: their exports are compared with their generators, not with each other.

---

## 10. The Tier 3 execution gate

Parsing a SQL file with a library shows the syntax is plausible. It does not show a database accepts it. `tools/check_sql_dialects.py` runs the PostgreSQL and MySQL files on real servers and reads back what the engines stored.

**What it does.** For each dialect, it loads the file into a disposable database, then checks:

1. the row counts of the five tables equal the counts derived from `calendar.json`;
2. every stored row equals the row the exporter derives from `calendar.json` (this covers quote escaping and non-ASCII text);
3. the engine enforces its constraints: a foreign key, a primary key, `NOT NULL`, a `CHECK`, a time `CHECK` and an invalid calendar date are all rejected, and a valid synthetic `ad_hoc_closures` row is accepted. Each probe runs in a transaction that is rolled back.

**Where it runs.** The `check-sql-execution` job in `validate.yml`, with `postgres:15` and `mysql:8.0` service containers (`MYSQL_DATABASE: exchange_calendar`), calling `python3 tools/check_sql_dialects.py --wait-seconds 120`. Connecting is retried because service containers start slowly.

**What it costs.** One extra job per push. It needs `psycopg2-binary` and `PyMySQL` (in `requirements-dev.txt`, not `requirements.txt`).

**Failure mode.** It fails if the connection cannot be made; it never skips. Each file DROPs and recreates the five tables, so the target must be disposable. Defaults point at the CI service containers (`postgresql://postgres:postgres@localhost:5432/postgres`, `mysql://root:root@127.0.0.1:3306/exchange_calendar`); the MySQL database is created if missing so the `mysql` system schema is never touched.

**What it does not do.** It is **not part of the release gate** in `scripts/release.sh`, which has no database. CI runs it on the release commit, and `release.sh` waits for `validate.yml`, so a tag still implies a green run. The SQLite and generic files are covered by `tests/test_export_sql.py` (sqlglot) and the cross-format test, not by a server.

---

## 11. Divergence testing

`tools/divergence_test.py` compares the registry with two reference libraries, and `tools/divergence_report.py` turns the output into [`docs/DIVERGENCE.md`](./docs/DIVERGENCE.md). Libraries and versions at v2.23.13: `exchange_calendars` 4.13.2 and `pandas_market_calendars` 5.6.0, both dev-only dependencies.

**What it compares.** For each exchange and year, the set of trading days. In the registry a trading day is a date that is not a `weekend_days` day and not a `closed` holiday or ad-hoc closure; `early_close` and `delayed_open` days are trading days, so half days are not disagreements. Only regular working days are compared: weekend dates are skipped for all three sources, because the libraries model one-off weekend sessions (Budget Day, Muhurat) that the registry does not. `--mode sessions` also compares open and close times, half days and the Tokyo lunch break; the weekly workflow runs it for six exchanges (XNYS, XNAS, XLON, XTKS, XASX, XHKG).

**What it reports at v2.23.13.**

- 62,738 trading days compared across 2024-2029; **62,465 (99.6%)** are days on which every available source agrees.
- 50 of 74 exchanges have at least one reference library; 24 have none; 30 of the 50 show no disagreement.
- 273 days still disagree: 22 in 2025, 18 in 2026, 66 in 2027, 85 in 2028, 82 in 2029.

**The two references are mostly one.** `pandas_market_calendars` serves 46 of the exchanges both libraries cover straight from `exchange_calendars`, so for those the "two libraries" are one source counted twice. PMC has its own implementation for XBOM and XNSE only. The report states this in its own header: "effectively the registry is being compared against one reference for the rest." Coverage is also uneven: XNAS and XSGO exist only in `exchange_calendars`; XBOM, XNSE, XSES and XSHG exist only in PMC (and `exchange_calendars` stops at 2026 for XBOM, XSES and XSHG).

**How disagreements are classified.** Every disagreeing date needs a verdict in [`docs/divergence_triage.json`](./docs/divergence_triage.json), which cites the exchange's own publication:

| Verdict | Meaning | Dates |
|---------|---------|------:|
| `registry_error` | The registry was wrong; fixed. The fixed dates no longer appear as disagreements | 410 (41 exchanges) |
| `library_error` | The registry matches the exchange; the libraries are wrong | 62 |
| `convention_difference` | Both defensible; sources use different conventions | 1 |
| `unpublished` | The exchange or government has not published that year; the registry value is a prediction; carries `recheck_date` | 213 |

Unclassified disagreements are 0 for every year 2025-2029.

**What this means.** The comparison found 410 registry errors, so the 100% rows in the summary are what remains after those fixes, not what the registry started with. Even NYSE had one: Christmas Day 2027 is observed on Friday 24 December and 2028 has no New Year's closure (fixed in 2.23.2). Of the 273 remaining days, 213 cannot be checked until the exchanges publish, and the report ends with that count.

**Not claimed.** The engine does not run against the exchange itself. A `library_error` verdict is a hand check against a published page, not a program. The engine covers 2024-2029; the 1990-2023 backfill for six exchanges is not compared (see [Section 7](#7-the-coverage-boundary)). `docs/DIVERGENCE.md` is regenerated every Monday 08:00 UTC by the Divergence workflow, which opens a pull request when it changes.

---

## 12. Worked example: a year of one exchange

A real session against the NYSE for 2026, run from the repository root against v2.23.13. Output is as printed, except that the holiday list is reflowed to one entry per line and the SQL query is abbreviated.

```text
$ python3 - <<'EOF'
import sys; sys.path.insert(0, "wrappers/python")
from exchange_calendar import CalendarRegistry
reg = CalendarRegistry(); x = reg.get("XNYS")
print(len(reg), "exchanges loaded")
print(x.is_holiday("2026-07-03"), x.is_early_close("2026-11-27"), x.early_close_time("2026-11-27"))
print(x.next_trading_day("2026-07-02"), x.status_at("2026-12-24", "12:59"))
print(reg.confidence("XNYS", 2026)); print(reg.confidence("XNYS", 2028))
EOF
74 exchanges loaded
True True 13:00
2026-07-06 early_close
{'last_verified': None, 'level': 'medium', 'source': 'manual'}
{'last_verified': None, 'level': 'medium', 'note': 'predicted', 'source': 'manual'}
```

2026-07-03 is a closure (Independence Day observed), 2026-11-27 closes at 13:00, and the next trading day after 2 July is Monday 6 July. The confidence for 2026 is `medium` / `manual`; 2028 carries the note `predicted`.

The year's holidays, from the wrapper:

```text
>>> [(h['date'], h['name'], h['status']) for h in x.list_holidays(2026)]
2026-01-01 New Year's Day closed
2026-01-19 Martin Luther King Jr. Day closed
2026-02-16 Presidents Day closed
2026-04-03 Good Friday closed
2026-05-25 Memorial Day closed
2026-06-19 Juneteenth National Independence Day closed
2026-07-03 Independence Day (observed) closed
2026-09-07 Labor Day closed
2026-11-26 Thanksgiving Day closed
2026-11-27 Day after Thanksgiving early_close
2026-12-24 Christmas Eve early_close
2026-12-25 Christmas Day closed
```

The same year from the Parquet file:

```text
>>> h = pd.read_parquet("exchange_calendar.holidays.parquet")
>>> x = h[(h.exchange_code == "XNYS") & h.date.astype(str).str.startswith("2026")]
>>> x.status.value_counts()
closed         10
early_close     2
>>> x[x.status == "early_close"][["date", "name", "early_close_time"]]
      date                   name early_close_time
2026-11-27 Day after Thanksgiving            13:00
2026-12-24          Christmas Eve            13:00
```

Ad-hoc closures for the year: there are none, in any exchange (`ad_hoc_closures` has 0 rows).

The verification class, from the data and the report:

```text
>>> c = pd.read_parquet("exchange_calendar.confidence.parquet")
>>> c[(c.exchange_code == "XNYS") & c.year.isin([2026, 2027])]
exchange_code  year  level source last_verified      note
         XNYS  2026 medium manual          None       NaN
         XNYS  2027 medium manual          None predicted
```

XNYS has `fetcher_status` `implemented` and a reference library. In `docs/DIVERGENCE.md`:

```text
| XNYS | 1506 | 1506 | 1506 | 0 | 100.0% |
```

Registry, PMC and EC each count 1,506 trading days over 2024-2029 and agree on all of them. The one triage entry for XNYS is the registry error above (2 dates, fixed in 2.23.2). The same query against the SQLite file, joined to the confidence table:

```text
>>> db.executescript(open("exchange_calendar.sqlite.sql").read())
>>> db.execute(<the Section 4 query, with h.date BETWEEN '2026-11-01' AND '2026-12-31'>).fetchall()
[('XNYS', '2026-11-26', 'Thanksgiving Day', 'closed', 'medium', 'manual'),
 ('XNYS', '2026-11-27', 'Day after Thanksgiving', 'early_close', 'medium', 'manual'),
 ('XNYS', '2026-12-24', 'Christmas Eve', 'early_close', 'medium', 'manual'),
 ('XNYS', '2026-12-25', 'Christmas Day', 'closed', 'medium', 'manual')]
```

What this example does not show: the same questions for an exchange in the 24. For XCAY, say, there is no row in the divergence table to join to (`No reference data`), and only the fetcher and the `confidence` row speak for the dates.

---

## 13. Examples

**There is no `examples/` directory in this tree.** The ISO 4217 and ISO 10383 registries each ship one runnable companion (`examples/stores-200`, `examples/orders-5k`); Exchange Calendar does not yet. [Section 12](#12-worked-example-a-year-of-one-exchange) is a reproducible session against the committed files, and the wrapper test suites and `tests/cross_language_queries.json` serve as executable examples of the API. A companion that joins a fact table to the calendar and shows what a missing or `predicted` day does to it is listed in [What's next](#25-whats-next).

---

## 14. Command-line interface

**There is no command-line interface for querying the registry.** No `bin/` directory, no console script in the Python wrapper, no `exchange-calendar` command. The ISO 4217, ISO 3166 and ISO 10383 registries each have one.

What exists are repository tools, run with `python3 tools/<name>.py`, none of which queries a date:

| Tool | Use |
|------|-----|
| `validate.py` | Validate `exchanges/*.json`. Exit 0 valid, 1 errors, 2 schema missing, 3 directory missing |
| `build.py` | Build `calendar.json` |
| `update_from_exchange.py` | Run fetchers: `--list-fetchers`, `--exchange XNYS`, `--all`, `--dry-run`, `--force` (bypass cache) |
| `divergence_test.py`, `divergence_report.py` | Divergence engine and report |
| `export_sql.py`, `export_csv.py`, `export_parquet.py` | Exporters, each with `--check` (`export_sql.py --help` lists its dialect option) |
| `check_*.py`, `verify_*.py` | The checks in [Section 16](#16-validation) |

To query a date from the shell today, use a wrapper (`python3 -c ...`) or the SQL and Parquet files. A CLI is in [What's next](#25-whats-next).

---

## 15. Language wrappers

Four wrappers, one contract.

| Language | Package | Source | Import | Tests |
|----------|---------|--------|--------|------:|
| Python | `exchange-calendar-registry` | [`wrappers/python`](./wrappers/python) | `from exchange_calendar import CalendarRegistry` | 95 (in the root suite, `tests/test_wrappers.py`) |
| JavaScript | `exchange-calendar-registry` | [`wrappers/javascript`](./wrappers/javascript) | `require('exchange-calendar-registry')` | 100 |
| Go | `github.com/slimissa/exchange-calendar/wrappers/go` | [`wrappers/go`](./wrappers/go) | `import exchangecalendar "..."` | 86 declarations |
| Rust | `exchange-calendar-registry` | [`wrappers/rust`](./wrappers/rust) | `use exchange_calendar::Registry;` | 83 declarations |

None is published ([Section 4](#4-quick-start)). The JavaScript and Python counts come from running the suites; Go and Rust are static counts of `func Test` and `#[test]`, because the audit environment had no `go` or `cargo`. The Python wrapper bundles `calendar.json` (`make package` keeps it current).

### One API, four spellings

| Operation | Python | JavaScript | Go | Rust |
|-----------|--------|------------|----|------|
| Load | `CalendarRegistry()` | `new CalendarRegistry()` | `LoadRegistry(path)` | `Registry` |
| Open at a time | `.is_open(date, time)` | `.isOpen(date, time)` | `IsOpen` | `.is_open` |
| Next trading day | `.next_trading_day(d)` | `.nextTradingDay(d)` | `NextTradingDay` | `.next_trading_day` |
| Confidence of a year | `.confidence(mic, year)` | `.confidence(mic, year)` | `Confidence` | `.confidence` |
| As of a date | `.as_of(mic, date)` | `.asOf(mic, date)` | `AsOf` | `.as_of` |

Method names for the less common operations are in each wrapper's README. A wrapper accepts `regular_hours` as an object or as a list with `effective_from`, so the shape change did not break callers.

### The shared fixture

[`tests/cross_language_queries.json`](./tests/cross_language_queries.json) holds 24 queries. `tools/check_cross_language.sh` runs the Python and JavaScript runners (`tools/cross_lang/`), the Rust runner (`wrappers/rust/examples/cross_lang.rs`) and the Go runner (`wrappers/go/cmd/cross_lang`), and diffs each against the Python output. A missing runner prints `SKIP` and does not fail the script; `tools/check_fixture_labels.py` fails first on duplicate labels. The release gate runs the script; in this audit environment the Go and Rust legs could not run.

### What the wrappers do not expose

No wrapper exposes the divergence verdict, `fetcher_status` or the reference split. They expose `confidence(mic, year)` and `as_of`. If you need the class of an answer, read `fetcher_status` from the JSON or Parquet and the divergence report.

---

## 16. Validation

Every check that runs in CI or the release gate, one row each.

| Check | What it catches | Runs in |
|-------|-----------------|---------|
| `tools/validate.py` | Schema, business-rule and cross-exchange errors in `exchanges/*.json` | CI, release gate |
| `tools/check_country_codes.py` | `country_code` not in the ISO 3166 snapshot, or `country` not equal to its `name` | CI, release gate |
| `tools/check_mic_codes.py` | `mic` not in the ISO 10383 snapshot | CI, release gate |
| `tools/check_snapshot_freshness.py` | A vendored snapshot past `review_by` (both are 2027-03-01) | CI (ISO 3166 step), release gate |
| `tools/check_release_claims.py` | A claim in `tools/release_claims.json` for this version that is false (12 for 2.23.13) | release gate |
| `tools/check_mojibake.py` | UTF-8 / Latin-1 corruption in text files | CI, release gate |
| `tools/check_stale_verifications.py` | Old `Last verified` dates in `BLOCKED.md` | CI, release gate |
| `tools/check_stale_year_urls.py` | A year-stamped source URL past its allowlist expiry | CI, release gate |
| `tools/check_expiring_sources.py` | A row of the `Expiring sources` table in `docs/FETCHERS.md` whose expiry has passed | CI only |
| `tools/check_doc_facts.py` | A number in the prose of 5 documents (26 claims) that differs from `docs/facts.json` | CI only |
| `tools/update_facts.py --check` | `docs/facts.json` out of step with the tree | CI only (through the facts step) |
| `tools/check_doc_links.py` | A broken link or anchor; the README's 74-row table disagreeing with `fetcher_status` or `BLOCKED.md` | CI, release gate |
| `tools/check_wrapper_snapshot.py` | The Python wrapper's `calendar.json` differing from the root file | CI, release gate |
| `tools/migrate_sessions.py --check` | `sessions` out of step with `regular_hours` / `extended_hours` | release gate |
| `tools/derive_confidence.py --check` | `confidence` out of step with its derivation | release gate |
| `tools/check_fetcher_freshness.py` | A fetched source older than its `max_age_days` in `fetcher_manifest.json` (four entries) | CI, release gate |
| `tools/verify_checksums.py` | `checksums.json` drifting from the files | CI |
| `tools/export_sql.py --check`, `export_csv.py --check`, `export_parquet.py --check` | A stale export | CI only |
| `tests/test_cross_format_consistency.py` | SQL, CSV and Parquet disagreeing | CI, release gate (pytest) |
| `tools/check_sql_dialects.py` | A SQL file a real PostgreSQL or MySQL rejects | CI only |
| `tools/check_cross_language.sh` | A wrapper answering the 24 fixture queries differently | release gate |
| `python3 -m pytest tests/` | 5,625 tests, including the 74 per-exchange holiday suites | CI, release gate |
| Wrapper suites (JavaScript, Go, Rust) | Each wrapper's own tests | CI, release gate |
| `tools/divergence_test.py` + `divergence_report.py` | Disagreement with reference libraries | Weekly workflow (opens a PR); `tests/test_divergence*.py` run in pytest |
| `tools/live_fetcher_check.py` | A fetcher failing against its live source | Weekly workflow |
| `tools/verify_predicted_dates.py --check` | Predicted Islamic dates past due | CI, non-blocking (`|| echo`) |
| Version consistency (CI job) | `VERSION`, `CHANGELOG.md` top entry, README badge and `build.py` output disagreeing | CI |
| Workflow coverage, orphan variables, manifest precondition | Static preflight of `release.sh` | release gate |
| Data-integrity job | Weekend dates in explicit arrays, duplicate dates, entries without a source URL | CI |

**What is not checked.** There is no `check_version_consistency.py`; the CI job checks three sites, not nine. No check re-tests a `BLOCKED.md` verdict. No check compares the 1990-2023 backfill with anything. The vendored snapshots have no reproduction check.

---

## 17. Continuous integration

Five active workflows in [`.github/workflows`](./.github/workflows) (a sixth, `publish.yml.disabled`, is not enumerated).

| Workflow | Runs on | Jobs | Guards |
|----------|---------|------|--------|
| **`validate.yml`** | push to `main`, pull requests to `main`, manual | 9: `python-core`, `python-wrapper`, `javascript`, `go`, `rust`, `data-integrity`, `verify-predicted-dates`, `version-consistency`, `check-sql-execution` | The data, the exports, the wrappers, the docs' counts and links |
| **`rust-verify.yml`** | push touching `wrappers/rust/**`, `schema.json`, `exchanges/**`, `tools/build.py` or `VERSION`; manual | 1 | The Rust wrapper on real `calendar.json`, with clippy |
| **`update-exchange.yml`** | Sundays 00:00 UTC; manual; push touching `exchanges/**` or the updater | 3: `validate`, `update`, `notify` | Fetches every fetcher and opens a pull request |
| **`live-fetcher-check.yml`** | Sundays 00:00 UTC; manual | 5: coverage verification, stable fetchers (blocking), CI-unreachable (informational), blocked (informational), summary | A fetcher breaking against its live source |
| **`divergence.yml`** | Mondays 08:00 UTC; manual | 1 | Regenerates `DIVERGENCE.md` and opens a pull request when it changes |

### CI versus the release gate

They differ, and the reasons are structural:

- **CI only:** `check_expiring_sources.py`, `check_doc_facts.py`, the three export `--check` modes, `check_sql_dialects.py`, `verify_checksums.py`. `release.sh` has no database and does not re-run the export checks; it regenerates SQL and Parquet and relies on the pytest run and on CI for the drift checks. The CSV and TSV files carry no version and are not regenerated at release.
- **Release gate only:** `migrate_sessions.py --check`, `derive_confidence.py --check`, `check_release_claims.py`, `check_cross_language.sh`.
- **The release waits for `validate.yml` and `rust-verify.yml`**, the two workflows that fire on a push to `main` (`POLLED_WORKFLOWS`). The release poll cannot see the other three, which are scheduled or path-limited.

---

## 18. Release pipeline

Releases are cut by [`scripts/release.sh`](./scripts/release.sh):

```bash
scripts/release.sh 2.23.14                # release
DRY_RUN=1 scripts/release.sh 2.23.14      # print every step; changes nothing
```

The dry run is an environment variable, not a flag. Steps:

0. **Static preflight (3 checks):** no orphan variables (`$CONSTANT` expanded but never assigned), every workflow that fires on a push to `main` is in `POLLED_WORKFLOWS`, and `tools/release_claims.json` has an entry for the version.
1. **Preconditions:** on `main`, clean tree, `HEAD` equals `origin/main`, `VERSION` differs from the target, `CHANGELOG.md` has a `## [<version>]` section.
2. **Version bump:** `VERSION`, the README badge, the README sentence "automated fetchers as of v2.24.0…", and the CHANGELOG top-entry check.
3. **Rebuild:** `tools/build.py`, `tools/export_sql.py`, `tools/export_parquet.py`, `make package`; both `calendar.json` copies are checked for `meta.version`.
4. **Local gate: 18 checks**, in order: `validate.py`, `check_country_codes.py`, `check_release_claims.py`, `check_mojibake.py`, `check_mic_codes.py`, `check_snapshot_freshness.py`, `check_stale_verifications.py`, `check_stale_year_urls.py`, `check_doc_links.py`, `check_wrapper_snapshot.py`, `check_cross_language.sh`, `migrate_sessions.py --check`, `derive_confidence.py --check`, `check_fetcher_freshness.py`, `pytest tests/`, the JavaScript suite (`npm ci && npm test`), `go test ./...`, `cargo test`.
5. **Commit and push** `Release v<version>`; on any failure after the bump, a trap restores the mutable files, and reverts a pushed release commit.
6. **Poll CI:** both polled workflows must succeed on the release SHA (15 s interval, 900 s timeout).
7. **Tag** `v<version>` with the CHANGELOG section as message, read back with `git for-each-ref` and compared; a mismatch stops before the push. Then push the tag.

**What this tree does not have:** a verification report per release (`docs/v<version>-verification.md` does not exist), and a recorded exit code per gate check. The tag and the CI run are the record. Tags are immutable ([`RELEASE_PATTERN.md`](./RELEASE_PATTERN.md)).

---

## 19. Versioning

One registry version, the Semantic Versioning of the **data** and tooling together, plus a separate schema version.

**Registry axis** — sites that carry the registry version:

| Site | How it stays right |
|------|--------------------|
| `VERSION` | Source of truth; written by `release.sh` |
| `CHANGELOG.md` top released heading | Written by hand before the release; the CI job and `release.sh` check it |
| README badge `registry-<version>-orange` | `release.sh` rewrites it; CI checks it |
| README "automated fetchers as of v2.24.0<version>" | `release.sh` rewrites it; `check_doc_facts.py` compares it with `VERSION` |
| `calendar.json` `meta.version` | `tools/build.py`; CI checks `build.py` output |
| `wrappers/python/exchange_calendar/calendar.json` | `make package`; `check_wrapper_snapshot.py` |
| Four SQL file headers | `export_sql.py`; `--check` fails if stale |
| Five Parquet footers `exchange_calendar.version` | `export_parquet.py`; `--check` fails if stale |

That is eight kinds of site, thirteen files. **There is no single consistency script**: the CI `version-consistency` job checks `VERSION` against the CHANGELOG, the README badge and `build.py` output; the others are checked by the tool that writes them. The wrapper package versions (`wrappers/javascript/package.json` is `1.0.0`) do **not** track the registry version. Go has no version site; the version is the git tag.

**Schema axis:** `schema.json` `version` (2.1.1), shown in the schema badge. It moves separately: a schema change bumps it without moving the registry axis alone, and CI and tooling changes do not bump the registry version by rule 8 of [`RELEASE_PATTERN.md`](./RELEASE_PATTERN.md).

**Semantic Versioning:** major for breaking schema changes, minor for new exchanges, new optional fields or new exports, patch for data corrections. Release notes are in [`CHANGELOG.md`](./CHANGELOG.md).

---

## 20. Project structure

```text
exchange-calendar/
├── VERSION                       # Registry version
├── calendar.json                 # Bundled: all 74 exchanges, built from exchanges/
├── checksums.json                # Checksums of the registry files (verify_checksums.py)
├── fetcher_manifest.json         # Hash and fetch date of four fetched sources (freshness check)
├── schema.json                   # JSON Schema, schema version 2.1.1
├── README.md                     # This file
├── CHANGELOG.md                  # Release history
├── CONTRIBUTING.md               # How to contribute, how to cite a source
├── BLOCKED.md                    # Blocked exchanges, by blocker class, with per-exchange findings
├── RELEASE_PATTERN.md            # Release invariants shared across the registry family
├── SECURITY.md                   # Security policy
├── LICENSE                       # Apache 2.0
├── Makefile                      # package, build-wheel, release
├── requirements.txt              # jsonschema, pyarrow, pytest, sqlglot
├── requirements-dev.txt          # Reference libraries and SQL drivers
├── exchange_calendar.sql         # Derived: SQL, generic (all five tables)
├── exchange_calendar.postgresql.sql
├── exchange_calendar.mysql.sql
├── exchange_calendar.sqlite.sql
├── exchange_calendar.<table>.csv         # Derived: 5 tables x 4 dialects = 20 files
├── exchange_calendar.<table>.excel.csv   #   .csv RFC, .excel.csv BOM,
├── exchange_calendar.<table>.european.csv#   .european.csv semicolon,
├── exchange_calendar.<table>.tsv         #   .tsv tab-separated
├── exchange_calendar.<table>.parquet     # Derived: 5 files, one per table
│                                         #   tables: exchanges, sessions, holidays,
│                                         #           ad_hoc_closures, confidence
├── exchanges/                    # Curated: 74 files, <MIC>.json
├── docs/
│   ├── DIVERGENCE.md             # Generated: divergence report
│   ├── divergence_triage.json    # Hand-checked verdicts per disagreeing date
│   ├── FETCHERS.md               # One note per exchange or group; expiring sources table
│   ├── facts.json                # Machine-readable counts (update_facts.py)
│   ├── CONSUMERS.md              # Who depends on the registry
│   ├── DRIFT.md                  # Drift notes
│   ├── AUDIT_FIX_REPORT.md       # Report of an audit pass
│   ├── schema-audit.md           # Schema freeze audit
│   ├── exchange_schema.md        # Field-level schema documentation
│   ├── recurrence_rules.md       # Rule types and observance
│   ├── status_at_semantics.md    # status_at / is_holiday behaviour
│   ├── update_semantics.md       # How updates apply
│   ├── predicted_dates_pending.md# Predicted Islamic dates awaiting confirmation
│   ├── fetcher_verification.md   # How fetchers were verified
│   ├── contributing_exchange.md  # Adding an exchange
│   ├── las_shell_integration.md  # LAS_Shell consumer notes
│   ├── MARKET_CONTEXT_SPEC.md    # Tempus @market_context specification
│   ├── task-20-holiday-rule-sweep.md  # Holiday-rule sweep tracking
│   ├── verifications/            # 5 dated verification artifacts (2026-09-17 to 2026-10-01)
│   └── decisions/                # ADRs 0008 to 0012
├── tools/                        # 45 entries: updater, builder, exporters, checks, divergence engine
│   ├── update_from_exchange.py   # Fetchers, one per exchange
│   ├── build.py                  # calendar.json builder
│   ├── generate_dates.py         # Recurrence engine
│   ├── validate.py               # Validator
│   ├── export_sql.py, export_csv.py, export_parquet.py
│   ├── check_*.py, verify_*.py   # The checks of Section 16
│   ├── divergence_test.py, divergence_report.py
│   ├── live_fetcher_check.py, update_facts.py, generate_checksums.py
│   ├── iso3166_snapshot.json (+ .meta.json), iso10383_snapshot.json (+ .meta.json)
│   ├── country_mapping.json, mic_allowlist.json, release_claims.json
│   └── cross_lang/               # run_python.py, run_javascript.js
├── scripts/
│   └── release.sh                # Release pipeline
├── tests/
│   ├── cross_language_queries.json   # Shared fixture, 24 queries
│   ├── fixtures/, ground_truth/      # Test inputs
│   ├── test_<exchange>_holidays.py   # 74 per-exchange suites
│   └── test_*.py                     # Tooling, export, wrapper, divergence tests (111 files in all)
├── wrappers/
│   ├── python/                   # exchange_calendar/, pyproject.toml, setup.py
│   ├── javascript/               # src/, tests/, package.json
│   ├── go/                       # exchange.go, registry.go, session.go, cmd/cross_lang, tests/
│   └── rust/                     # src/, examples/cross_lang.rs
└── .github/
    ├── workflows/                # validate, rust-verify, update-exchange, live-fetcher-check, divergence, publish.yml.disabled
    ├── ISSUE_TEMPLATE/           # 6 files
    ├── PULL_REQUEST_TEMPLATE.md
    └── dependabot.yml
```

There is no `examples/`, `bin/`, `docs/LAYERS.md` or `docs/v*-verification.md`.

---

## 21. Documentation index

| Document | What does it answer? |
|----------|----------------------|
| [`docs/DIVERGENCE.md`](./docs/DIVERGENCE.md) | Where does the registry disagree with the reference libraries, and what was decided? |
| [`docs/divergence_triage.json`](./docs/divergence_triage.json) | Which verdict, and which source, for each disagreeing date? |
| [`docs/FETCHERS.md`](./docs/FETCHERS.md) | What does the fetcher for each exchange read, and which sources expire? |
| [`BLOCKED.md`](./BLOCKED.md) | Why can an exchange not be fetched automatically, and when was that last checked? |
| [`docs/facts.json`](./docs/facts.json) | What are the counts that prose documents must agree with? |
| [`docs/exchange_schema.md`](./docs/exchange_schema.md) | What does each field of an exchange file mean? |
| [`docs/recurrence_rules.md`](./docs/recurrence_rules.md) | What do the recurrence rule types do, including observance? |
| [`docs/status_at_semantics.md`](./docs/status_at_semantics.md) | What do `status_at` and `is_holiday` return on a weekend? |
| [`docs/update_semantics.md`](./docs/update_semantics.md) | How does an update apply to existing data? |
| [`docs/predicted_dates_pending.md`](./docs/predicted_dates_pending.md) | Which predicted Islamic dates are awaiting confirmation? |
| [`docs/fetcher_verification.md`](./docs/fetcher_verification.md) | How was each fetcher verified? |
| [`docs/contributing_exchange.md`](./docs/contributing_exchange.md) | How do I add an exchange? |
| [`docs/CONSUMERS.md`](./docs/CONSUMERS.md) | Who depends on the registry, and what do they read? |
| [`docs/DRIFT.md`](./docs/DRIFT.md) | What drift notes are recorded? |
| [`docs/schema-audit.md`](./docs/schema-audit.md) | What did the schema-freeze audit find? |
| [`docs/AUDIT_FIX_REPORT.md`](./docs/AUDIT_FIX_REPORT.md) | What did an earlier audit pass fix? |
| [`docs/las_shell_integration.md`](./docs/las_shell_integration.md) | How does LAS_Shell consume the registry? |
| [`docs/MARKET_CONTEXT_SPEC.md`](./docs/MARKET_CONTEXT_SPEC.md) | What is the `@market_context` specification? |
| [`docs/task-20-holiday-rule-sweep.md`](./docs/task-20-holiday-rule-sweep.md) | What did the holiday-rule sweep cover, and what is left? |
| [`docs/verifications/`](./docs/verifications) | What did dated one-off verification passes find? |
| [`docs/decisions/`](./docs/decisions) | Why was each design choice made (ADRs 0008 to 0012)? |
| [`CHANGELOG.md`](./CHANGELOG.md) | What changed in each release? |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | How do I correct data, cite a source or add an exchange? |
| [`RELEASE_PATTERN.md`](./RELEASE_PATTERN.md) | What invariants does a release refuse on? |
| [`SECURITY.md`](./SECURITY.md) | How do I report a vulnerability? |
| `wrappers/*/README.md` | What is the full API of each wrapper? |

---

## 22. Contributing

Open an issue before a large change. [`CONTRIBUTING.md`](./CONTRIBUTING.md) covers adding an exchange, common data errors, how to cite a source (a hierarchy of source levels) and the pull request process. The quick workflow:

1. **Set up:** `pip install -r requirements.txt -r requirements-dev.txt` (and `tools/requirements.txt` to run fetchers).
2. **Change the data** in `exchanges/<MIC>.json`, citing the exchange's own publication in `source_url`. For a disagreement with a reference library, record the verdict in `docs/divergence_triage.json`.
3. **Validate:** `python3 tools/validate.py`.
4. **Rebuild and regenerate:**
   ```bash
   python3 tools/build.py && make package
   python3 tools/export_sql.py && python3 tools/export_csv.py && python3 tools/export_parquet.py
   python3 tools/generate_checksums.py
   python3 tools/update_facts.py
   ```
5. **Check drift:** the three exporters with `--check`, `python3 tools/update_facts.py --check`, `python3 tools/check_doc_facts.py`, `python3 tools/check_doc_links.py`.
6. **Divergence (if you changed 2024-2029 dates):** `python3 tools/divergence_test.py --exchanges all --year 2024-2029 && python3 tools/divergence_report.py`. The weekly workflow does this too; do it locally to see your change.
7. **Test:** `python3 -m pytest tests/ -q`.
8. **Rehearse a release:** `DRY_RUN=1 scripts/release.sh <version>`.

CI and tooling changes never bump the version alone ([`RELEASE_PATTERN.md`](./RELEASE_PATTERN.md) rule 8). Commit messages with several lines go through `git commit -F`.

---

## 23. Known limitations

Stated plainly, because a calendar is a claim and a claim needs its edges drawn.

- **24 of 74 exchanges have no reference library.** For 15 of them nothing independent re-reads the dates: XATH, XBAH, XBEY, XBUL, XCAI, XCAS, XDHA, XJKT, XMUS, XNAI, XTAD, XTUN, DSMD (no fetcher), plus XNSA and XKUW (a fetcher that cannot run in CI).
- **The two references are largely one.** PMC serves 46 of the exchanges both libraries cover from `exchange_calendars`; only XBOM and XNSE are PMC-native.
- **A reference is not the exchange.** The 99.6% agreement is agreement with libraries. `library_error` verdicts are hand checks against published pages.
- **213 disagreeing days are predictions** (2027-2029), recorded `unpublished` with a recheck date. They are not errors found; they are claims not yet checkable.
- **No verification-class field.** The 50 / 24 split exists in the divergence report and cannot be queried from the data or any wrapper.
- **`confidence` is coarse.** 560 of 564 rows are `medium` / `manual` with `last_verified` null; 4 are `high` / `fetcher`. It does not say which dates are verified.
- **The 1990-2023 backfill is unverified.** XNYS, XNAS, XLON, XASX, XHKG and XTKS carry 2,128 `Historical Holiday` entries copied from `exchange_calendars`; the divergence engine compares 2024-2029 only, and a library compared with itself proves nothing.
- **`generation_range` does not cover the past for most exchanges.** 68 exchanges start 2025-01-01; the registry does not answer for 2024 or earlier for them, and `generation_range` ends 2029-12-31 for 66 exchanges, shorter for 8.
- **The registry is a snapshot, not a history.** Holidays are not versioned per release; replaying a past state means checking out a tag.
- **5 fetchers do not run in CI as reliable checks:** XHKG, XNSA and XSHG are CI-unreachable; XKUW and XSAU are blocked (HTTP 403 on 2026-09-17).
- **29 exchanges are blocked** or have no fetcher ([`BLOCKED.md`](./BLOCKED.md)): 8 JS-rendered, 13 bot-walled, 3 PDF-grid, 5 dead-source, none behind a closed API. Findings are dated snapshots, not permanent facts.
- **Predicted Islamic and lunar dates.** 226 explicit entries are flagged `predicted`. Umm al-Qura dates (XSAU) can move by a day when the moon is sighted; `tools/verify_predicted_dates.py` tracks the pending ones.
- **Source URLs expire.** Several sources are year-stamped; `docs/FETCHERS.md` lists them, and the first expiries are 2027-03-31 (XWBO, XBUD, XZAG) and 2027-06-01 (XDFM, XCAI, XMAD URLs).
- **Only four fetchers have a freshness entry** in `fetcher_manifest.json` (XBUD, XDFM, XIST, XWBO).
- **No ad-hoc closures.** All 74 files have an empty `ad_hoc_closures`; an unscheduled closure will need a release.
- **Session times are compared for six exchanges only** (XNYS, XNAS, XLON, XTKS, XASX, XHKG), in the weekly workflow's `--mode sessions` run. Lunch breaks exist for 11 exchanges, auctions for 22; the report does not cover most.
- **No CLI**, no `examples/` directory, no per-release verification report.
- **Vendored snapshots are old and unreproducible.** `tools/iso3166_snapshot.json` is from ISO 3166 v1.5.2 and `tools/iso10383_snapshot.json` from ISO 10383 v1.0.4; both `review_by` 2027-03-01. No generator in the tree reproduces them.
- **The release gate does not run the export `--check` modes, the SQL execution gate or the doc-facts check;** CI does, and `release.sh` waits for `validate.yml`.
- **Wrapper versions do not track the registry.** The JavaScript package is `1.0.0`.
- **Language packages are not published** to PyPI, npm, crates.io or a Go proxy.
- **Go and Rust tests were not run in the audit environment**; their counts are static.

---

## 24. Consumed by

Exchange Calendar sits between registries. It **references** ISO 3166 and ISO 10383 and is **referenced** by consumers. "Verified" below means a check that runs in this repository's CI; "stated" means the claim lives elsewhere.

| Project | Edge | Status | Proof |
|---------|------|--------|-------|
| [ISO 3166](https://github.com/slimissa/iso3166) | `country_code` resolves to an active entry in a vendored snapshot, and `country` equals its `name` | **Verified** in this tree | `tools/iso3166_snapshot.json` (v1.5.2, `review_by` 2027-03-01), `tools/check_country_codes.py`, CI and release gate. The snapshot is behind the registry (ISO 3166 is at 1.12.x per its README) and has no generator here |
| [ISO 10383](https://github.com/slimissa/iso10383) | `mic` resolves to an entry (active or expired, operating or segment) in a vendored snapshot | **Verified** in this tree | `tools/iso10383_snapshot.json` (v1.0.4, `review_by` 2027-03-01), `tools/check_mic_codes.py`, CI and release gate |
| ISO 10383 (reverse edge) | ISO 10383 vendors a snapshot of this registry's MICs and fails its validator if one is missing | **Stated**; proof is in that repository | Its `tools/exchange_calendar_snapshot.json` (74 MICs, v2.15.4 at the time of its README), its README and CI. Not checkable from this tree. The snapshot there is behind this registry (2.23.13) |
| ISO 3166 (reverse edge) | ISO 3166 lists this registry as a consumer of `alpha_2`, `name` | **Stated** | Its README section 22 and `docs/JOINS.md`. Not checkable from this tree |
| ISO 4217 | No direct edge: exchanges carry no currency field | **None** | `docs/CONSUMERS.md` says "no direct edge today". A listing currency is not stored |
| Tempus | `@market_context` type-level validation; reads `sessions`, `confidence`, `as_of`, MICs | **Stated** (aspirational as far as this tree shows) | `docs/CONSUMERS.md` and `docs/MARKET_CONTEXT_SPEC.md`. No artifact in this tree depends on it, and ISO 3166 records the repository as not publicly reachable |
| LAS_Shell | Market status, scheduling and prompt display; reads `sessions`, `is_open`, `holidays.explicit`, MICs | **Stated** | `docs/CONSUMERS.md` and `docs/las_shell_integration.md`. Not checkable from this tree |
| Corporate Actions | No exchange-calendar edge found | **None** | ISO 10383 records no `exchange` field in its public data |
| Asset Identifiers | `exchange` references a MIC, so the join to this registry would go through the MIC | **Planned** | Declared in that repository's schema; no edge to this registry in the tree |

No external adopter is recorded. *Using this registry? Open a pull request to add a row.*

---

## 25. What's next

Nothing is scheduled. Each item starts when its trigger fires.

| Deferred item | Trigger to start |
|---------------|------------------|
| **A `verification_class` field**, or an equivalent the wrappers can return, so a consumer can read the class of an answer | A consumer needs it in code rather than in the report; it then needs a schema bump |
| **A second check for the 15 exchanges with neither a reference nor a running fetcher** | A fetcher becomes buildable for one of them (a source leaves a bot wall, or a page becomes static); `BLOCKED.md` records the dates of the last check |
| **The 30 blocked exchanges** | A browser-rendering fetcher is accepted for CI ([ADR 0009](./docs/decisions/0009-playwright-fetcher-category.md), [ADR 0010](./docs/decisions/0010-render-mode.md)) or an exchange publishes a machine-readable calendar |
| **Compare the 1990-2023 backfill with a source that is not `exchange_calendars`** | A primary source (an exchange archive) is found for any of the six exchanges |
| **Divergence for session times beyond six exchanges** | The weekly `--mode sessions` run is extended and its output joined to the report |
| **Formalise predicted Islamic and lunar dates** | An exchange publishes a year the registry predicts; `recheck_date` is the prompt |
| **`ad_hoc_closures` content** | The first unscheduled closure after v2.23.13 |
| **A CLI** | A consumer asks for shell queries, or the sibling registries' CLIs are mirrored here |
| **A companion example** (a fact table joined to the calendar) | The example is written; the ISO 4217 and ISO 10383 registries have one each |
| **A snapshot generator for ISO 3166 and ISO 10383, and refreshed snapshots** | A sibling release the snapshots depend on, or `review_by` (2027-03-01) approaching |
| **A single version-consistency script covering every site** | A fourth implementation of the release pattern, or a drift the CI job misses |
| **Per-release verification reports** | Adopting the ISO family's `docs/v<version>-verification.md` |
| **Publication to PyPI, npm, crates.io and a Go proxy** | A downstream consumer needs a package-registry install rather than a clone |

See [`CHANGELOG.md`](./CHANGELOG.md) for release history and [`docs/decisions/`](./docs/decisions) for locked decisions.

---

## License and author

Apache 2.0. See [`LICENSE`](./LICENSE). Schedule facts are public information published by each exchange; the compilation, schema, tooling and wrappers are licensed works.

**Le P'tit** — [github.com/slimissa](https://github.com/slimissa)
