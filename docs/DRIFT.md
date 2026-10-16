# README drift note (v2.15.4)

Documentation-only correction. No data, schema, wrapper or version change.

## What was wrong

Every claim below disagreed with the tree at `9c98f07`. Most dated from the
v2.1.11 era and were never updated when later releases changed the registry.

| Claim | Was | Now | Source of truth |
|-------|-----|-----|-----------------|
| Registered fetchers (lines 6, 232) | 45 | 46 | `update_from_exchange.py --list-fetchers` (XIST gained a fetcher in v2.9.0) |
| CI-verified fetchers (line 6, 232, badge) | 40 | 41 | registry minus the 5 jobs-excluded MICs in `live-fetcher-check.yml` |
| Remaining blocked, no fetcher (lines 6, 232, 348) | 29 | 28 | 74 − 46 |
| "as of v2.1.11" (line 232) | v2.1.11 | v2.15.4 | `VERSION` |
| Blocked badge | 35 | 30 | `BLOCKED.md` summary table |
| Tier 3 / Tier 4 / Tier 8 headers | 3 of 10 / 9 of 10 / 6 of 8 | 4 of 10 / 8 of 9 / 5 of 8 | registered fetchers per README tier table |
| Europe / Middle East region counts | 20 / 8 | 19 / 9 | `exchanges/*.json` (Beirut was unlisted; Europe absorbed it) |
| Testing table and badge | 4,070+ | 4,512 (badge 4500+) | pytest 4,259, node 94, Go 81, Rust 78 |
| Issue templates / workflows (tree comments) | 7 / 3 | 5 / 4 | `.github/` |
| XNSA status, Tier 7 table | ✅ Implemented | ⚠️ CI-unreachable | `BLOCKED.md`, workflow exclusion |

Go and Rust counts are static (`func Test`, `#[test]`); the toolchains were not available, so those suites were not run.

## Left alone on purpose

- The XHKG row stays `⚠️ CI-unreachable` while `BLOCKED.md` marks it `resolved`. The exchange is built; `live-fetcher-check.yml` still excludes it as CI-unreachable. Intentional.

## Follow-ups

Closed after v2.15.4, documentation only (no version bump):

- XIST row corrected: `BLOCKED.md` said `resolved`, the README said blocked. It now reads Implemented.
- `What's New in v2.1.11` retired, superseded by `CHANGELOG.md`.
- Beirut added to the Middle East list, so the names match the count of 9.
- JavaScript test path corrected, and the `make test` line removed (the Makefile has no `test` target).
- `docs/CONSUMERS.md` registry version fixed in `34a1b28`.
- Schema badge (2.1.1) no longer disagrees with `schema.json` `version`: the schema was bumped from 2.0.0 to 2.1.1 (see `CHANGELOG.md`).

## Why CI did not catch it

`version-consistency` compares four sources: `VERSION`, the README registry
badge, the `CHANGELOG` top entry and `calendar.json` meta. It does not read
prose, other badges, tier headers or tables, so a stale count passes.

## What will catch it

Phase 1's `docs/facts.json` is the mechanism: counts are derived once from the
tree and checked against every number the README states.
