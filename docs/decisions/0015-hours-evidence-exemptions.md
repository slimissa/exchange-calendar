# ADR 0015 — Hours-evidence exemptions

**Status:** Accepted
**Date:** 2026-11-28
**Decided by:** the CTO (session 4b13 brief, closing Phase 4b-lite)

## Context

ADR 0014 made check 6 (hours evidence, `tools/check_verification.py`)
non-blocking for Phase 4b-lite and said it would become blocking for every
`reference_compared` exchange at the end of the phase. By session 4b12, 43
of the 48 `reference_compared` exchanges had hours evidence, and all but 5
had verified current hours or a `schema_limited` item. For the other 5
(XBOG, XBOM, XLIM, XNSE, XSGO) the maintainer could not obtain a readable
official schedule. The pages render by script and print empty, the archive
denies access, or no hours page was found. Waiting for them would keep the
check non-blocking indefinitely, and a non-blocking check lets a regression
in any of the other 43 pass unnoticed.

Two easy answers are wrong. Marking the 5 verified would claim evidence
that does not exist. Dropping them from the rule would hide them. This ADR
closes Phase 4b-lite with a third answer: the check blocks, and each
exchange that cannot meet it yet is carried by a written, expiring
exemption that records what was tried.

## Decision

### 1. Check 6 is blocking

Every `reference_compared` exchange must have one of:

- verified current hours (ADR 0014 section 7: the entry in force on the
  evaluation day has a `verified` item whose `verified_from` is on or
  before that day);
- a `schema_limited` item for that entry (ADR 0014 section 6); or
- a valid exemption under this ADR.

Hours-evidence findings for any exchange (missing items, values that
differ from `regular_hours`, an `unconfirmed` item without a recheck date
within the cap, and the rest of ADR 0014's item rules) also fail the
check. `tools/check_verification.py` runs in `tools/local_gate.sh`, so in
`scripts/release.sh` and in CI.

### 2. What an exemption records

Exemptions live in `tools/hours_evidence_exemptions.json`, validated by
`tools/hours_evidence_exemptions.py`. Each entry has:

- `mic`: the exchange;
- `reason`: why the official hours could not be read;
- `sources_tried`: one or more records of `source` (a URL or a path),
  `tried` (the date, YYYY-MM-DD) and `outcome` (what happened, such as
  "renders by script; print empty" or "Access Denied");
- `leads`: pointers not yet read, each with `label` "unread lead" and
  `pointer`. A lead is never evidence and is never quoted as a fact;
  it says where to look next;
- `added` and `expires`: dates, YYYY-MM-DD;
- `next_action`: what would let the exemption be removed.

### 3. Lifetime

An exemption lives at most 70 days from `added`. It lives less where the
registry value is suspected stale: XNSE's is 30 days, because its close may
predate a closing-auction change NSE announced in 2026.

### 4. When the gate fails

The check fails when:

- an exemption has expired (the checker's today is after `expires`);
- an exemption exists for a MIC that already has verified current hours or
  a `schema_limited` item. The exemption is stale: remove it;
- an exemption names a MIC that is not `reference_compared`, or no
  exchange at all;
- `expires` is more than 70 days after `added`, or before it;
- a required field is missing or empty, or a source record or lead lacks
  its parts; or
- a MIC has more than one exemption.

### 5. When the gate warns

An exemption that expires within 14 days prints a warning. The check still
passes.

### 6. What an exemption is not

An exemption changes no data in `exchanges/*.json`, is not evidence, and
never raises "hours evidence", "current hours verified" or "history
verified". The checker reports exempt exchanges separately, with the
exemption count and the nearest expiry. The checker takes its today as a
parameter, so tests fix the date rather than read the wall clock.

## Consequences

- From session 4b13, a `reference_compared` exchange that loses its
  verified current hours, or a new one that arrives without them, turns
  the gate red.
- An exemption buys time; it does not settle anything. When it expires, the
  gate is red again until the evidence is read, or the exemption is
  renewed with a new record of what was tried.
- Phase 4b-lite is closed. Phase 4b full (history) and the dated-sessions
  work of Phase 4f keep their own plans.
