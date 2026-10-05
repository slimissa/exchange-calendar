# ADR 0011 — MIC→LEI connector

**Status:** Accepted (v2.13.0)
**Date:** 2026-10-05
**Depends on:** none

## Context

A MIC→LEI connector was proposed at v2.12.5: a companion file
holding one entry per operating MIC with the LEI of its legal
operator, vendored from ISO 10383. The reconnaissance found that
the file does not exist, should not, and — on EC's side — has
nowhere to be vendored to.

## Reconnaissance

Two findings, from two registries.

**ISO 10383 (Phase 0, 2026-10-05).** GLEIF's 2026-09-18 MIC-to-LEI
file is a strict subset of the `lei` field on `iso10383.json`:

| Metric | Count |
|--------|-------|
| GLEIF MIC-LEI pairs | 1,024 |
| Operating MICs in `iso10383.json` v1.0.4 | 1,594 |
| Operating MICs with `lei` populated | 1,144 |
| MICs in both sources | 1,024 |
| MICs in GLEIF not in the field | 0 |
| Disagreements where both have a value | 0 |

`docs/PROVENANCE.md` on ISO 10383's side confirms the field's
source: the `LEI` column in SWIFT's monthly MIC publication.
First-party, refreshed monthly, not downstream enrichment.

**EC (this session).** EC's vendored snapshot at
`tools/iso10383_snapshot.json` is `{meta, mics}` where `mics` is a
list of 2,883 MIC code strings. It exists for one purpose: to
validate EC's 74 exchange records against the MIC set, via
`tools/check_mic_codes.py`. It carries no per-entry metadata, has
no generator script in this repo, and is not referenced by
`schema.json`.

## Decision

**Decline the connector. Ship no artifact.**

Three reasons, in order of weight:

1. **No companion file exists to vendor.** ISO 10383 declined it
   after finding GLEIF's file is a strict subset of a field the
   registry already carries. There is nothing on the sibling side
   for EC to consume.

2. **EC's vendored snapshot is not a place to put the field.**
   The snapshot is a minimal validation artifact — 2,883 strings,
   no structure. Adding `lei` means either changing its shape
   (which touches `check_mic_codes.py` and any test asserting the
   shape) or producing a second snapshot for the same source.
   Neither is justified without a consumer.

3. **No consumer has asked for the LEI of an exchange operator.**
   The data exists on the sibling's registry. A consumer that
   wants it can read the sibling's `iso10383.json` directly, or
   EC can re-vendor with the field when a request arrives.

This is the same discipline ISO 10383 applied to its own
companion: a proposal that duplicates a field on an artifact
someone already vendored is not a connector. It is a copy of the
artifact under a different name.

## Consequences

### Positive

- No new artifact, no new snapshot, no new CI surface, no change
  to `check_mic_codes.py`.
- The connector's data remains on ISO 10383's registry, which is
  its correct source of truth.
- v3.0.0's exports are unaffected — there was no MIC→LEI field to
  project.

### Negative

- A consumer that wants exchange-operator LEIs has no single-file
  read path today. The answer is "read the sibling's registry",
  which is a single file with a documented schema; the cost of
  that path is small.

### Neutral

- The "MIC→LEI connector" as a named artifact is retired. If a
  consumer asks, the shape is Shape 2 from v2.13.0's roadmap: a
  dedicated `tools/iso10383_mic_lei_snapshot.json` extracted from
  `iso10383.json`, with a `.meta.json` sibling. That shape is
  correct when there is a consumer; it is premature now.

## Reopen condition

A consumer asks for the LEI of an exchange operator as a
first-class read on EC's side. At that point the correct shape is
a projection of ISO 10383's `lei` field into a dedicated EC
snapshot, not a change to the existing MIC-set snapshot.

Second reopen condition: ISO 10383 changes the source of its
`lei` field (e.g., stops being first-party from SWIFT). In that
case the field's authority changes and the vendor relationship
needs revisiting — but that is ISO 10383's decision to signal, not
EC's to anticipate.

## Related

- ISO 10383 `docs/mic_lei_source_format.md` — the sibling's
  Phase 0 reconnaissance.
- ISO 10383 `docs/decisions/0008-mic-lei-companion-declined.md`
  — the sibling's parallel decision.
- `docs/decisions/0010-render-mode.md` — ADR 0010's non-goals
  section named XJSE URL discovery; this ADR is the analogous
  record for the MIC→LEI connector.
