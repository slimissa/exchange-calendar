# Verification contract

Each exchange carries one `verification` object. Its `class` says what kind of independent evidence the registry can point to for that exchange. It is **per exchange**, not per date or per year: a consumer reading a date for exchange X gets the class of X, whatever the year.

```
verification(mic).class     # Python: registry.verification(mic)["class"]
                            # JS: .class   Rust: .class   Go: .Class
```

The method returns the object (`class`, `basis`, `last_checked`, `reference_note`), or `None` / `null` / `nil` for an unknown MIC. The class is derived, never authored: `tools/derive_verification.py` computes it from `fetcher_status` and `docs/DIVERGENCE.md`, and `--check` fails on drift.

## The four classes

| `class` | Derived when | What it means |
|---|---|---|
| `single_source` | `fetcher_status` is `blocked` or `none`, and no reference library | Curated by hand. Nothing re-reads the exchange and nothing is compared. |
| `ci_unreachable` | `fetcher_status` is `ci_unreachable` (**even if a reference library covers the exchange**) | A fetcher exists; CI cannot reach the source. |
| `source_verified` | `fetcher_status` is `implemented`, and no reference library | A fetcher reads the exchange's own page in the weekly live check (`live-fetcher-check.yml`). |
| `reference_compared` | A reference library covers the exchange, and `fetcher_status` is not `ci_unreachable` | The registry is compared with `exchange_calendars` or `pandas_market_calendars`. The exchange may also have a working fetcher; the class does not say. |

These are kinds of evidence, not a ranking. The rules above are applied in the order `ci_unreachable`, then reference coverage, then fetcher status, so a class can hide a stronger signal: XHKG and XSHG are `ci_unreachable` although a reference library covers them, and 33 exchanges with a running fetcher are `reference_compared`. Read `fetcher_status` and `docs/DIVERGENCE.md` alongside the class. The class values are exactly the enum at `properties.verification.properties.class` in `schema.json`.

## Compared is not verified

`reference_compared` means we looked. `docs/DIVERGENCE.md` says what we found: at the time of writing 20 of the 50 exchanges with a reference library have at least one disagreement (the report's own line reads "Exchanges with no disagreement: 30 of 50", and it is regenerated every Monday). A disagreement does not say which side is right, and agreement is not confirmation: the two libraries are mostly one source, because `pandas_market_calendars` serves most shared exchanges straight from `exchange_calendars`.

## What this does not mean

- **Not the exchange's own calendar**, except `source_verified` (and a fetcher behind a `reference_compared` class, which the class does not report).
- **Not every year.** The comparison covers 2024 to 2029 (session times for six exchanges cover 1990 to 2029). The registry answers only inside `generation_range`, and values for years the exchange has not published are predictions. The six `Historical Holiday` backfills before 2024 are copied from `exchange_calendars` and have no independent check.
- **Not a date.** `last_checked` is the day the class was derived, not the day the calendar was verified.

A consumer who needs more confidence than the class permits must verify the date independently.

## Checking each claim

- Class of an exchange: `verification(mic).class`, or `exchanges/<MIC>.json`.
- Class definitions: `schema.json` and `tools/derive_verification.py`.
- Disagreements: `docs/DIVERGENCE.md`, Summary table and "Disagreements by year".
