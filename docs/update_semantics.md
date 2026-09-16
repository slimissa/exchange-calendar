# Update Semantics

`tools/update_from_exchange.py` maintains `exchanges/*.json` from live fetchers.
This document defines what "update" means when the fetched data and the
on-disk file disagree.

## Rule

**Fetched data is the source of truth for `holidays.explicit`.** Every
successful run replaces the holiday list for that MIC with whatever the
fetcher returned. The on-disk list is not merged with the fetched list; it
is overwritten.

Consequences:
- A holiday the fetcher no longer reports is deleted.
- A holiday whose name, status, or early-close time the fetcher changed is
  updated.
- A holiday the fetcher adds is added.

Other fields — `extended_hours`, `sessions`, `ad_hoc_closures`,
`recurrence_rules`, `generation_range`, `weekend_days` — are preserved from
the existing file if the fetcher does not produce them. Fetchers today
produce none of these, so in practice all are preserved.

If the fetcher returns zero holidays, the update aborts with
`FetchStatus.FAILED` and the file is left untouched.

## Why not merge?

Because merging produces a file that reflects neither the source data nor
any human's intent. The previous behavior:

- preferred existing entries by date, so a corrected name never replaced a
  stale one
- never removed entries, so a false-positive holiday would stay forever
- treated the file as an append-only log rather than a mirror of the source

That is only correct if the file is hand-curated and the fetcher merely
proposes additions for human review. It is not how this project uses the
tool: `update-exchange.yml` opens a PR when the fetch produces changes, and
PR review is the human gate. Merging the data itself duplicates that gate
badly.

## Manual corrections

If a fetcher is wrong about a specific date, fix the fetcher's parser or
its source — not the output file. A hand-edit to `exchanges/*.json` will
be overwritten the next time the fetcher runs successfully.

A future release may add a `"manual": true` marker on individual entries
that opts them out of overwrite. That is deliberately not in this version:
it adds a schema field and a failure mode (marked-stale entries nobody
revisits) without evidence yet that it is needed.