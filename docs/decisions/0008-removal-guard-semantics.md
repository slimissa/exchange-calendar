# ADR 0008 — Removal Guard Semantics

**Status:** Accepted (v2.7.0)
**Date:** (fill on merge)

## Context

`tools/check_removed_entries.py` classifies three removal classes
between two exchange datasets: holiday removed, exchange removed,
MIC renamed. A per-exchange write path (`update_exchange()`) can
only encounter the first two — the MIC is present on both sides of
the comparison and its `name` is unchanged.

Two consumers therefore need the tool, with different scopes:

| Consumer | Scope | Classes reachable |
|----------|-------|-------------------|
| `update_exchange(mic)` | one exchange, current vs. merged | holidays, all_holidays_removed |
| `check_removed_entries.py --old A --new B` | whole directory, A vs. B | all four, incl. mic_renames |

## Decisions

1. **Guard fires on the write path only.** `update_exchange()` calls
   `diff_removals` against the *merged* output
   (`generate_exchange_json`), not the raw fetch. Merge semantics can
   preserve holidays the fetcher did not return; the guard must see
   what would actually be written.

2. **Block, don't warn.** When any removal is detected,
   `update_exchange()` returns `FetchStatus.BLOCKED_BY_REMOVAL` and
   writes nothing. The previous file is preserved. Local
   `--all --dry-run` and real runs behave identically: both report
   the block, neither writes.

3. **No `--allow-removals` override in v2.7.0.** A legitimate removal
   is resolved by editing the JSON by hand and re-running; the guard
   then sees "no change" and returns `UNCHANGED`. An override flag is
   a v2.7.x refinement if the false-positive rate proves noisy.
   Rationale: relaxing is easy, tightening is not.

4. **New enum member** `FetchStatus.BLOCKED_BY_REMOVAL`. Recorded in
   the CHANGELOG under Changed so downstream consumers (LAS_Shell,
   Tempus) do not treat `FetchStatus` as frozen.

5. **Exit code 3** from `update_from_exchange.py` when any exchange
   is blocked. 0 success, 1 usage error, 2 fatal, 3 partial block.

## Consequences

- The `update-exchange.yml` workflow surfaces blocked removals in the
  PR body, does not auto-merge, and does not fail the job for a block
  alone (a human reviews).
- The existing empty-holidays guard (fires before `compare_holidays`)
  remains; the new guard does not subsume it. Distinct edge cases.
