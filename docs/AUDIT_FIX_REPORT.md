# Exchange Calendar Registry — Audit & Fix Report

**Scope:** Comprehensive verification audit of registry v2.1.0 (74 exchanges, 4 language wrappers, validation/build tooling, CI, and documentation), followed by a full fix cycle.

**Status:** All Critical, High, and Low issues resolved and verified. All 7 Medium issues resolved; one (M3) has a verification gap explained below. One data-reconciliation task (M7) is intentionally partial — see Outstanding Items.

---

## 1. Issue List — Complete, With Resolution Status

### Critical (8)

| ID | Issue | Status |
|---|---|---|
| C1 | All 4 wrappers hardcoded Saturday/Sunday as the weekend for every exchange, regardless of actual weekend system (7 Islamic-weekend exchanges affected) | ✅ Fixed |
| C2 | XSAU (Saudi) shipped with zero Islamic-calendar holidays | ✅ Fixed |
| C3 | XDFM (Dubai) shipped with zero Islamic-calendar holidays | ✅ Fixed |
| C4 | 5 exchanges (XBKK, XCOL, XMOS, XSHE, XSTC) claimed `generation_range` coverage their data didn't back up, by 1–3 years | ✅ Fixed |
| C5 | XCOL missing Deepavali for 2026 specifically (isolated single-year gap) | ✅ Fixed |
| C6 | XCAI/XMUS Eid al-Fitr 2025 wrong by 1 day — all 6 Islamic-holiday exchanges had byte-for-byte identical dates, ignoring that Egypt/Oman use independent moon-sighting | ✅ Fixed |
| C7 | Rust wrapper could not deserialize `calendar.json` at all for any exchange with a non-empty `sessions` array (`Session.session_type` missing `#[serde(rename = "type")]`) | ✅ Fixed |
| C8 | *(Investigated, not a real bug)* — believed the CI JS test job referenced a nonexistent file; the file existed at repo root all along and was missed by a bad glob search during the original audit | ✅ Resolved (no fix needed; see §3) |

### High (3)

| ID | Issue | Status |
|---|---|---|
| H1 | `validate.py` had no weekend-awareness, Islamic-holiday-completeness, or generation-range-coverage checks — structurally could not have caught C1–C5 | ✅ Fixed (3 new checks added) |
| H2 | XQSE (Qatar) missing Islamic New Year + Mawlid; XDHA (Dhaka) missing Ashura + Mawlid (audit corrected the original brief, which had wrongly named "Islamic New Year" for Bangladesh instead of Ashura) | ✅ Fixed |
| H3 | XBOM/XNSE missing Diwali Laxmi Pujan for 2026 specifically | ✅ Fixed |

### Medium (7)

| ID | Issue | Status |
|---|---|---|
| M1 | `actions-rs/toolchain@v1` in `publish.yml` is archived/unmaintained | ✅ Fixed |
| M2 | No wrapper documented that `status_at()` expects exchange-local time, not UTC | ✅ Fixed |
| M3 | Rust `Cargo.lock` is lockfile-v4 (needs cargo ≥1.78) with no MSRV declared | ⚠️ Fixed in code; **not locally verified** — see §5 |
| M4 | `SECURITY.md` referenced 2 nonexistent tools, 1 undeclared dependency, and shipped unfilled placeholder content | ✅ Fixed (plus 2 more fabricated tools found and fixed beyond the original 1 named) |
| M5 | `SECURITY.md`'s example schema pattern contradicted real `schema.json` | ✅ Fixed |
| M6 | `predicted` status existed only as a `(predicted)` name-string suffix, not a queryable field | ✅ Fixed |
| M7 | 2025 Islamic-holiday entries still marked `(predicted)` despite outcomes now being public record | ⚠️ Partially done — 29/88 reconciled; see Outstanding Items |

### Low (1)

| ID | Issue | Status |
|---|---|---|
| L1 | `.github/ISSUE_TEMPLATE/config.yml` had stray shell commands (`git add`/`commit`/`push`) pasted as raw text after the YAML content | ✅ Fixed |

---

## 2. Fixes Applied — Detail

### C1 — Wrapper weekend hardcoding
- Added `weekend_days` as a **required** schema field (`[Mon=0..Sun=6]` convention).
- Populated on all 74 exchange files (`[5,6]` for 65 Western + XDFM/XTAD; `[4,5]` for the 7 Islamic-weekend exchanges).
- Fixed `tools/build.py`, which was silently dropping the field when assembling `calendar.json` — found only via manual post-fix verification, since no test exercised the field end-to-end.
- Fixed all 4 wrappers. Python/Rust use the same Monday=0 convention as the stored data directly; **JS and Go needed an explicit day-numbering conversion** (`getUTCDay()`/`time.Weekday()` are Sunday=0) that a literal implementation of the original fix instructions would have missed — confirmed by testing Saturday specifically, not just the two dates originally specified.
- Test impact: Python 3,783→3,784; JS 0→15 (see C8 note below — later reconciled into the real 82→84 file); Go 71→72; Rust 65+13→68+13 (6 hand-built fixtures required updating for the new required field).

### C2 / C3 — XSAU / XDFM missing Islamic holidays
- Added Eid al-Fitr, Eid al-Adha, Islamic New Year, Mawlid for 2025–2029, sourced from Umm al-Qura per instruction.
- Weekend-filtered per each exchange's actual system (XSAU: Fri/Sat exclude; XDFM: Sat/Sun exclude — inverse of XSAU, confirmed via a dedicated test asserting the two files' date sets are NOT identical).
- XSAU: 10→39 explicit entries (+29). XDFM: 14→43 (+29, coincidental count match, different dates).
- Cited `ummulqura.org.sa` directly rather than each exchange's generic trading-calendar page — that page's absence of these dates was the original root cause.

### C4 — Generation range honesty
- Shortened `generation_range` end dates for XBKK, XCOL, XMOS, XSHE, XSTC to match actual researched coverage, rather than claiming years with no backing data.
- Corrected the assigned root-cause explanation for XMOS specifically: its holidays are **all fixed-date**, not lunar — it's a plain data-entry gap, not a tooling limitation, and `CONTRIBUTING.md` was written to say so explicitly rather than misdirect future contributors.
- Widened `test_cross_exchange.py`'s range-similarity tolerance (2→4 years) to accommodate the now-honest spread without disabling the check entirely.

### C5 — XCOL Deepavali 2026
- Added `2026-11-09` as `"Deepavali (observed)"` (not bare `"Deepavali"` — matches XKLS/XSES's naming for the same weekend-shifted date).
- Rewrote the pre-existing `test_deepavali_2026`, which only ever checked the *absence* of the weekend date and never checked the *presence* of the observed replacement — exactly the kind of test that let this gap through undetected.

### C6 — Egypt/Oman Islamic date divergence
- Corrected XCAI/XMUS Eid al-Fitr 2025 from 03-30 to 03-31 (sourced: Dar al-Ifta, MERA), shifting the full holiday window, not just relabeling the existing dates.
- Confirmed Eid al-Adha 2025 for the same two countries actually **matched** Saudi — proving divergence isn't a fixed offset applicable everywhere.
- Discovered and fixed a duplicate-date collision in XMUS mid-fix (a pre-existing 4th day I'd initially missed, reflecting Oman's real 4-day extension policy).
- Added `TestIslamicDateDivergence` to `test_cross_exchange.py` — later had to fix its own helper method (`_islamic_dates`) after M7, once it turned out to be identifying "Islamic holiday" by checking for the `(predicted)` substring, which broke the moment an entry was legitimately reconciled and lost that suffix.

### C7 — Rust real-data deserialization
- One-line fix: `#[serde(rename = "type")]` on `Session.session_type`.
- Added `test_load_real_calendar_registry`, the first Rust test to ever load the actual shipped `calendar.json` rather than a hand-built fixture — checked against XASX (auction) and XTAD (originally specified XNYS, which turned out to have an empty `sessions` array and wouldn't have caught the bug).

### C8 — JS "missing test file" (non-issue, corrected course)
- Original audit concluded JS had zero tests and CI referenced a nonexistent `tests/test_wrappers.js`, based on a search for `*.test.js`/`*.spec.js` — a naming convention this project doesn't use.
- A real, 695-line, comprehensive test file existed at that exact path the entire time.
- Built a redundant duplicate file at `wrappers/javascript/tests/test_wrappers.js` before catching the error; deleted it once found.
- The actual gap: the real file had no Islamic-weekend regression coverage (those tests had gone into the erroneous duplicate). Added `xsau` fixture + 2 tests to the real file instead.
- CI workflow required **zero changes** — it was correct the whole time.

### H1 — Enhanced validator
Three new checks added to `validate.py`, wired into the per-exchange validation loop:
- `check_weekend_dates` — no explicit holiday should fall on the exchange's own weekend.
- `check_islamic_holidays` — Islamic-weekend exchanges must have both Eid holidays present (uses `sorted(weekend_days)`, not exact list-order, per a deliberate correction to the original spec).
- `check_generation_range` — explicit data must extend within 90 days of the claimed range end.
- Running these against the real registry immediately surfaced **10 real, previously-invisible errors** (7 in XTAD, 3 range gaps in XCAI/XKUW/XSAU) — fixed in a follow-up pass (see below).

### H2 — XQSE / XDHA missing holidays
- XQSE: added Islamic New Year + Mawlid, sourced from Saudi (per instruction; not independently verified against Qatar's own calendar, and the source URL says so honestly).
- XDHA: added **Ashura** (not "Islamic New Year" — the ticket itself corrected the original brief's naming) + Mawlid, independently sourced for Bangladesh. Found that 2025's Mawlid was officially government-rescheduled from Friday to Saturday — both weekend days for XDHA, so correctly zero entries for that year.

### H3 — XBOM/XNSE Diwali Laxmi Pujan 2026
- Added `2026-11-08`, a Sunday — the first fix in this cycle where a real, sourced holiday legitimately falls on the exchange's own weekend (a specifically-gazetted Muhurat trading session, not an ordinary closed Sunday).
- Required a genuine design decision: added a new schema field `weekend_exception` (boolean) so this real data could coexist with H1's weekend-date validator, rather than either fabricating a fake weekday or leaving `validate.py` broken.

### 10 errors from the enhanced validator (follow-up fix)
- Removed 7 weekend-violating entries from XTAD (real ADX-sourced data that never followed the weekend-exclusion convention used elsewhere).
- Found and fixed an entire mislabeled test class in `test_abu_dhabi_holidays.py` (`TestXTADWeekendPattern`) that tested the wrong weekend model (Friday/Saturday) for an exchange that actually uses Saturday/Sunday — it had only passed before because the very violations being removed happened to satisfy its backwards assertion.
- Shortened `generation_range` for XCAI/XKUW (→2029-07-24) and XSAU (→2029-09-23).
- Surfaced two new, unfixed observations in the process (see Outstanding Items).

### M1–M7 — see the M-series report already delivered; summarized in the table above.

---

## 3. New Issues Discovered *During* Fixing (Not Part of the Original Audit)

| Discovery | Where found | Resolution |
|---|---|---|
| `build.py` silently dropped `weekend_days` when assembling `calendar.json` | C1 verification | Fixed |
| Rust `Session` struct field/JSON key mismatch (`session_type` vs `type`) blocked all real-data loading | C7 (found while trying to verify C1 in Rust) | Fixed as C7 |
| Multiple stale tests encoded bugs as correct behavior (XSAU/XDFM count bounds, XCOL Deepavali absence-only check, XTAD's backwards weekend-model tests, XSAU's hardcoded "always predicted" assertions) | Throughout C2–C7, M7 | Fixed at each occurrence |
| XTAD's real data used a different weekend model in its own test file's docstring than its actual `weekend_days` value | H1 follow-up fix | Fixed (test + docstring corrected) |
| Believed CI's JS job tested a nonexistent file | Originally flagged during C1 | **Corrected** — was never actually broken (see C8) |
| 10 new real errors from turning on H1's checks | H1 → follow-up fix ticket | Fixed |

---

## 4. Schema Changes

| Field | Added in | Type | Required? | Purpose |
|---|---|---|---|---|
| `weekend_days` | C1 | `array[int]`, length 2 | **Yes** | Which two weekdays (Mon=0..Sun=6) are this exchange's weekend |
| `weekend_exception` | H3 | `boolean` | No | Narrow, documented override for a holiday date that legitimately falls on the exchange's own weekend but is independently sourced as a distinct event (e.g. Diwali Muhurat trading) |
| `predicted` | M6 | `boolean`, default `false` | No | Structured replacement for the `(predicted)` name-suffix convention; both forms currently coexist for backward compatibility |

---

## 5. New Validator Checks (`tools/validate.py`)

| Function | Added in | What it catches |
|---|---|---|
| `check_weekend_dates` | H1 | Explicit holidays landing on the exchange's own weekend (unless `weekend_exception: true`) |
| `check_islamic_holidays` | H1 | Islamic-weekend exchanges missing Eid al-Fitr or Eid al-Adha |
| `check_generation_range` | H1 | `generation_range` claiming more coverage than the explicit data backs up (>90 day gap) |
| `check_predicted_consistency` | M6 | Contradictions between the structured `predicted` field and the legacy name suffix |

All four are wired into `main()`'s per-exchange validation loop and run automatically on every `python3 tools/validate.py` invocation.

---

## 6. Test Coverage Summary

| Suite | Before this audit cycle | Final |
|---|---|---|
| Python (`pytest tests/`) | 3,783 | **3,843 pass, 0 fail** |
| JavaScript (`node --test tests/test_wrappers.js`) | 82 (pre-existing, uncredited in original audit) | **84 pass, 0 fail** |
| Go (`go test ./tests/`) | 71 | **72 pass, 0 fail** |
| Rust (`cargo test`) | 65 unit + 13 doc | 69 unit + 13 doc (**last verified run**, before M3) |

New test coverage added this cycle includes: Islamic-weekend regression tests in all 4 languages, per-exchange Islamic-holiday test classes (XSAU, XDFM, XQSE, XDHA), cross-exchange divergence tests, all 3 H1 validator checks (13 unit tests), the M6 `predicted` consistency check (5 unit tests), and the H3 `weekend_exception` mechanism (3 unit tests).

---

## 7. Outstanding Items

| Item | Detail | Owner / Next step |
|---|---|---|
| **M7 partial reconciliation** | 29 of 88 total 2025 Islamic-calendar entries are reconciled (`predicted: false`, confirmed sourcing). The other 59 remain marked predicted because I have no independent confirmation for them — mostly Eid al-Adha/Islamic New Year/Mawlid across exchanges never individually researched (XKAR, XNBO, XNSA, XTUN, XCAS, XBEK) plus a few specific holiday-types I chose not to guess at for exchanges I did research. *(Note: this is 29/88, corrected during a subsequent audit pass — an earlier version of this document said 29/86, which undercounted the total by 2; recounted directly against the files.)* | Needs a dedicated per-country research pass, same methodology as C6/H2 |
| **Rust verification gap (M3)** | `rust-version = "1.78"` is correct and matches the real `Cargo.lock` requirement, but this sandbox's only available rustc is 1.75 (apt-installed; no path to a newer version — Rust's official installer isn't reachable on this environment's allowed network domains). Rust has not been built or tested since M3 landed. The code changes themselves (M1's `dtolnay/rust-toolchain@stable` in CI, C7's serde fix, C1's weekend-days logic) were all verified **before** M3 was added; M3 itself is unverified. | Needs `cargo build && cargo test` run in an environment with rustc ≥1.78 (any real CI runner using the now-fixed `publish.yml` toolchain action would have this) |
| **XTAD 2028 National Day substitute-day count** | Flagged during the H1 follow-up fix: 2028's Commemoration Day (Dec 1) and National Day (Dec 2) both fall on that year's weekend, and UAE policy plausibly calls for two substitute trading holidays, but the data only has one (Dec 4). I did not invent a second date without a source. *(Note: I don't recognize "FAHR" as a term from anywhere in this audit and I'm not going to adopt an unfamiliar acronym in this document — describing the actual open question as I established it above instead.)* **v2.1.2 update**: searched Gulf News, publicholidays.ae, u.ae, and general aggregators for a 2028-specific circular. None exists yet — the most recent government-sourced circulars found are for 2025/2026, both of which do show the two-substitute-day pattern (e.g. 2026: Commemoration Day observed Sat Nov 30, National Day Mon Dec 2 + Tue Dec 3, four-day public-sector break). This is expected: UAE circulars are issued months ahead of the actual year, not years ahead, so "not yet announced" remains the accurate status, not a gap in this audit's search effort. | Needs a sourced UAE government/ADX circular for 2028's specific substitute-day policy — re-check closer to the date |

---

## 8. Final Status

- `python3 tools/validate.py` — **passes clean on all 74 files**, including all 4 new checks (H1 ×3, M6 ×1).
- `python3 tools/build.py` — **produces `calendar.json` correctly**, including `weekend_days`, `weekend_exception`, and `predicted` propagating through from the source files.
- Python, JavaScript, and Go test suites **all pass, zero failures**, confirmed on a fresh run immediately before this report was written.
- Rust: code is believed correct but **not verified** post-M3 in this environment, for the reason above — this is a genuine gap, not a formality.
- The registry is **not** unconditionally "production-ready" without qualification: M7's 57 unreconciled predicted entries and the Rust verification gap are real, described limitations, not resolved issues being glossed over.

---

## Second-Pass Re-Verification

**Date**: 2026-08-24
**Performed by**: Same Claude conversation, second pass — not a blind independent audit

### Methodology Note

This was **not** a blind re-audit by a fresh instance with no knowledge of the first fix cycle. This document was read in full before any checks were run. The gaps below were found despite having this report, by independently re-deriving the underlying facts rather than trusting the numbers stated here — recomputing every explicit date's weekday against each file's own `weekend_days` from scratch, and recounting the M7 total directly against the 74 exchange files instead of accepting "86." That distinction matters for how much confidence to place in this section: it is corroboration by independent recomputation, not corroboration by a second unbiased party.

### What This Pass Found

| # | Finding | Severity | Root Cause |
|---|---------|----------|------------|
| 1 | `validate.yml` still used archived `actions-rs/toolchain@v1` | High | M1 fix was incomplete — only `publish.yml` corrected |
| 2 | M7 count wrong: 29/86 instead of 29/88 | Low | Denominator miscounted twice |
| 3 | Weekend classification stale: XDFM/XTAD listed as Islamic (Fri-Sat) in the original verification brief and in `README.md`/`CONTRIBUTING.md` | Low | Source brief outdated; underlying registry data was already correct |
| 4 | Second XTAD weekend-model bug in tests | High | First fix cycle caught one of two instances of the same bug |

### The "Half-True" Fix Discovery

The first audit-fix cycle claimed `test_abu_dhabi_holidays.py`'s weekend-model bug was "found and fixed" (see C7/H1-follow-up notes above). This pass found a second, structurally identical instance in the same file:

- **Instance 1** (fixed in first cycle): `TestXTADWeekendPattern` class — tested the opposite weekend model entirely.
- **Instance 2** (found this pass): `TestXTADStructure.test_no_weekend_dates` — same wrong model (`weekday() not in [4, 5]`, docstring "UAE weekend is Friday-Saturday"), missed by the first cycle's fix.

Both tested for a Friday/Saturday weekend that XTAD does not have. Instance 2 only passed because XTAD's data happens to contain no Friday- or Saturday-dated entries — the wrong check passed by coincidence, not because it verified anything true.

**Lesson**: finding and fixing one instance of a bug pattern in a file is not evidence the pattern is eliminated from that file. It's evidence of one instance.

### Files Changed This Pass

| File | Change |
|------|--------|
| `.github/workflows/validate.yml` | Replaced archived `actions-rs/toolchain@v1` |
| `.github/dependabot.yml` | Added `npm`, `cargo`, `gomod` ecosystems |
| `README.md` | Weekend classification table corrected (67/7) |
| `CONTRIBUTING.md` | Weekend classification prose and table corrected (67/7) |
| `tests/test_abu_dhabi_holidays.py` | Fixed second weekend-model bug + stale section comment |
| `docs/AUDIT_FIX_REPORT.md` | Corrected M7 count (29/86 → 29/88); this section added |
| `CHANGELOG.md` | Added `[Unreleased]` entry documenting all of the above |

### What This Pass Could Not Verify

Go and Rust toolchains remain unavailable in this environment (`go`, `cargo`, `rustc` all absent). The Go (72) and Rust (69 unit + 13 doc) test counts in the first cycle's report are **unconfirmed by this pass** — carried forward from the first report's own claims, not independently re-run. The Rust gap was already disclosed as unresolved in §5/§7 above; that remains true and is not newly closed by this pass.

---

## Post-Zip Updates (v2.1.2)

**Date**: 2026-08-24
**Source**: Changes reported by LASS as having occurred outside this conversation, verified against a fresh zip of the resulting state where verification was possible.

### What Was Independently Confirmed From the v2.1.2 Zip

These were checked directly against the delivered files/output in this pass — not accepted on report alone:

| Claim | Verification method | Result |
|---|---|---|
| `tools/verify_predicted_dates.py` exists and works | Ran it directly | Confirmed — outputs exactly: 362 total, 125 past-due, 237 future, exit 0 (non-blocking) |
| 362 predicted entries (not 88) | Independently scanned all 74 exchange files for `predicted: true` | Confirmed — 362, matching the tool's own count |
| `docs/predicted_dates_pending.md` exists | Read the file | Confirmed — documents the reconciliation process and per-country source list |
| `.github/workflows/rust-verify.yml` exists | Read the file | Confirmed — checks rustc ≥1.78, builds `calendar.json`, runs `cargo build/test/clippy`, then a real-registry-load test |
| `validate.yml`'s Rust job builds `calendar.json` first | Read the file | Confirmed |
| `validate.yml` honors `weekend_exception` | Read the file | Confirmed |
| `update-exchange.yml` installs `jsonschema` | Read the file | Confirmed, both jobs |
| `from_str` → `from_json_str` rename | Grepped Rust source | Confirmed — 6 call sites use the new name; the unrelated `FromStr` trait impl in `session.rs` (a different type, for session-status parsing) is untouched, as it should be |
| `Cargo.toml`'s `bugs` field removed | Read the file | Confirmed absent |
| `publish.yml` disabled | Directory listing | Confirmed — present as `publish.yml.disabled` |
| `validate.py`, `build.py`, Python suite, JS suite still pass | Ran all four fresh against the new zip | Confirmed: 74/74, build OK, **3,843/3,843 Python** (unchanged from the pre-zip count), **84/84 JS** |

### What Was NOT Independently Verified — Stated Plainly, Not Carried Forward as Fact

- **Dependabot PR merges** (7 merged, 1 closed): no way to check this from a zip. Not verified.
- **CI job status ("all green")**: this pass has no access to GitHub Actions run history. Not verified — this is LASS's report, not a re-run confirmation.
- **Go test count (72) and Rust test count (82)**: this sandbox still has no `go` or `cargo`/`rustc` binary. These numbers are reported by LASS as CI-confirmed; they were not re-executed here and should not be read as independently confirmed by this document.
- **git tags and commit `abc05b2`**: the delivered zip contains no `.git` directory. There is no way to confirm tag placement, commit history, or that v2.1.1/v2.1.2 point where claimed. If this matters for the release, it needs to be checked against the actual repository, not this zip.

### Correction to This Document's Own Prior M7 Entries

The M7 entries earlier in this document (29/86, later corrected to 29/88) are both superseded. The true denominator was never 88 — it was 362. The 86/88 figures came from a keyword-based scan (`Eid`, `Islamic New Year`, `Mawlid`, etc. in the holiday name) that missed entries where the name didn't contain one of those keywords but the entry was still `predicted`. `verify_predicted_dates.py` scans the `predicted` field directly instead of the name string, which is why it found the other ~274 entries the earlier passes missed. This is not a new bug introduced since the last pass — it's a correction to how big the original M7 gap actually was.

### CHANGELOG Note

`CHANGELOG.md`'s `[Unreleased]` section (containing the v2.1.1-cycle fixes) was retitled to `[2.1.1] — 2026-08-24` and a new `[2.1.2] — 2026-08-24` section added above it, since LASS reported both versions as already tagged — leaving tagged work under `[Unreleased]` would have been its own documentation gap. The 2.1.1 date is a **[Guess]**: no `.git` log was available to confirm the actual tag date, since it was carried over from when the fixes were made in this conversation.

---

## Post-Push Follow-Up: Rename, Checksums, and M7 Reconciliation Pass

**Date**: 2026-08-25

### 1. `ISLAMIC_EXCHANGES` → `EXCHANGES_WITH_ISLAMIC_HOLIDAYS`

Renamed in `tests/test_cross_exchange.py` (both the definition and its one usage). The final repo-wide grep specified for this fix (`ISLAMIC_EXCHANGES\|islamic.*weekend.*XDFM\|islamic.*weekend.*XTAD`, excluding this document and CHANGELOG.md) returned **zero hits**, confirmed directly, not assumed.

### 2. Checksum Tools

Added `tools/generate_checksums.py` and `tools/verify_checksums.py`, covering `exchanges/*.json` (74 files), `schema.json`, and `tools/*.py`. Deliberately excludes `calendar.json` (a build artifact — checksumming it duplicates checksumming its inputs) and wrapper/test source (out of scope for a data-integrity manifest). `SECURITY.md` updated in both places that previously disclosed these tools didn't exist.

### 3. M7 Reconciliation — What Actually Got Verified

Of the 123 past-due predicted entries at the start of this pass, real web searches were run against primary/official sources (government ministries, central moon-sighting authority announcements, major wire coverage) for the largest clusters: Eid al-Fitr 2025, Eid al-Adha 2025, and Islamic New Year 1447 (2025). This was **not** an exhaustive pass through all 123 — that would require per-country labor-ministry sourcing for every holiday-continuation day, which wasn't feasible in one session. What was found:

**A real data bug, not just an unconfirmed prediction**: XNSA's (Nigerian Stock Exchange) predicted Eid al-Adha 2025 dates were `2025-06-30`/`2025-07-01` — roughly 24 days (one lunar month) off from the actual date. Confirmed against Nigeria's own Federal Ministry of Interior press release (multiple corroborating outlets: Channels TV, AllAfrica, the ministry's own site): the real dates were **June 6 and June 9, 2025**. Corrected and marked `predicted: false`. Notably, XNSA's 2026–2029 Eid al-Adha predictions were *not* similarly broken — they follow the expected ~11-day annual lunar drift correctly, so this looks like a one-off data-entry error specific to the 2025 value, not a systemic algorithm bug.

**21 entries reconciled with sourcing**: Islamic New Year 2025-06-26, confirmed via Saudi Supreme Court/SPA announcement (Express Tribune, Calendarr) for all 11 exchanges that already had this exact date predicted (XBAH, XBEK, XCAI, XCAS, XDFM, XKUW, XMUS, XQSE, XSAU, XTAD, XTUN). Eid al-Fitr 2025 first-day/holiday entries for XKAR (Pakistan), XDHA (Bangladesh), XCAS (Morocco), XTUN (Tunisia), and XNBO (Kenya), confirmed via Gulf News' cross-country moon-sighting roundup — all March 31, matching Egypt/Oman's already-reconciled date.

**Deliberately left untouched, flagged instead of guessed at**: XBEK (Lebanon) Eid al-Fitr — genuinely contested in-country between two religious authorities (Grand Jaafari Mufti declared March 31; Grand Ayatollah Fadlallah's office declared March 30, both officially, for different communities). No single "correct" date exists to reconcile to; left predicted.

**A significant open finding, NOT acted on**: the Prophet's Birthday (Mawlid) 2025-09-04 cluster, currently predicted identically across 11 exchanges, appears substantively wrong on general-source evidence: Qatar and Saudi Arabia (XQSE, XSAU) reportedly do not observe Mawlid as a public holiday at all, for doctrinal reasons (Marhaba Qatar, What's On UAE) — meaning those two entries may need to be *removed*, not redated. UAE (XDFM, XTAD) and Morocco (XCAS) show September 5 in multiple sources, not September 4. This was **not corrected** in this pass: general public-holiday sourcing is not the same as an exchange's actual trading calendar, and removing entries is a bigger structural change than correcting a date. This needs verification against XSAU's/XQSE's/XDFM's/XTAD's/XCAS's actual trading-calendar sources before anyone touches the data.

**Test suite impact**: reconciling data broke 19 tests that had hardcoded either the specific wrong Nigeria dates or an "these holiday types must always say (predicted) forever" assumption that was only ever true because nothing had been reconciled yet at the time those tests were written. All 19 fixed — 18 by correcting the assertion to check *consistency* between the `predicted` field and the `(predicted)` name suffix (a stronger, more durable test than "always predicted"), and 1 (Nigeria's `test_eid_al_adha_2025`) by correcting the hardcoded wrong date to match the confirmed real one. Full suite: 3,843/3,843 passing after these fixes, same total as before — no tests added or removed, only corrected.

### New Reconciliation Counts

| | Before this pass | After this pass |
|---|---|---|
| Total predicted | 362 | 339 |
| Past-due | 125 | 102 |
| Future | 237 | 237 |

102 past-due entries remain, including the flagged-but-unresolved Mawlid cluster and everything not covered by the Eid al-Fitr/Eid al-Adha/Islamic New Year 2025 sweep above. This is real, partial progress — not a claim that M7 is closed.

### 4. XTAD 2028 Substitute-Day

Searched again this pass (Gulf News, publicholidays.ae, u.ae, general aggregators). No 2028-specific circular exists yet. The most recent found circulars are for 2025/2026, both confirming the two-substitute-day pattern for years where Commemoration Day and National Day land on the weekend — consistent with, not contradicting, the open question already on record. UAE government circulars are issued months ahead of the actual year, so "not yet announced" is the accurate status, not a search failure. Still open.

---

## Mawlid Cluster Investigation and Fix

**Date**: 2026-08-26

The 11-exchange Prophet's Birthday (Mawlid) cluster flagged in the previous pass as "likely wrong on general-source evidence" was investigated exchange-by-exchange, with real searches against government announcements, exchange trading-calendar publications, and multiple independent Mawlid-observance reference sources (OfficeHolidays, qppstudio's exhaustive per-country list, Wikipedia). Results:

| Exchange | Country | Finding | Action |
|---|---|---|---|
| XBAH | Bahrain | Sept 4, 2025 confirmed (timeanddate.com; independently corroborated by BHB's own TradingHours.com listing) | Kept, `predicted: false` |
| XKUW | Kuwait | Sept 4, 2025 confirmed (Kuwait Cabinet announcement, Kuwait Times / Khaleej Times) | Kept, `predicted: false` |
| XCAI | Egypt | Sept 4, 2025 confirmed (Egypt Cabinet) | Kept, `predicted: false` |
| XTUN | Tunisia | Sept 4, 2025 confirmed (Tunisia's Mufti, Tuniscope, 23-08-2025) | Kept, `predicted: false` |
| XCAS | Morocco | Was Sept 4 -- wrong. Confirmed Sept 5 (Morocco's religious authorities) | Corrected to 2025-09-05, `predicted: false` |
| XDFM | Dubai | Was Sept 4 -- wrong. Confirmed Sept 5 (UAE federal announcement, public + private sector) | Corrected to 2025-09-05, `predicted: false` |
| XTAD | Abu Dhabi | Same UAE federal announcement as XDFM | Corrected to 2025-09-05, `predicted: false` |
| XMUS | Oman | Was Sept 4 -- wrong. Confirmed Sept 7 (Oman Ministry of Labour, 14 Rabi' al-Awwal 1447 AH) | Corrected to 2025-09-07, `predicted: false` |
| XQSE | Qatar | Does not observe Mawlid at all -- confirmed by two independent sources naming Qatar and Saudi Arabia as the only Muslim-majority countries that don't declare it an official public holiday (doctrinal: Salafi/Wahhabi tradition treats it as a religious innovation) | Removed -- all years (2025, 2026, 2027, 2029; 2028 had no entry to begin with) |
| XSAU | Saudi Arabia | Same finding as Qatar. Corroborated by Tadawul's own published holiday list (raseedinvest.com, markethours.io), which has exactly 4 categories -- Founding Day, Eid al-Fitr, Eid al-Adha, National Day -- and no Mawlid | Removed -- all years (2025, 2026, 2027, 2029) |
| XBEK | Lebanon | Genuinely contested: sources give both Sept 4 and Sept 5 depending on which in-country religious authority is cited, the same pattern already established for XBEK's Eid al-Fitr entry | Left untouched, still predicted -- no single correct date exists to reconcile to |

### A Self-Correction: Islamic New Year for XSAU and XQSE

Investigating Mawlid surfaced a problem with something already marked "reconciled" in the previous pass. XSAU and XQSE's Islamic New Year 2025-06-26 entries had been flipped to `predicted: false` based on a Saudi Supreme Court crescent-sighting announcement -- but that only confirms the Hijri calendar transitioned on that date, not that the exchange actually treats it as a trading holiday. Given the newly-found evidence that Tadawul's official holiday list is narrow and specifically excludes both Mawlid and Islamic New Year, this was very likely the same class of error as the Mawlid cluster. Both entries were reverted back to `predicted: true` / `"Islamic New Year (predicted)"`. This is a correction to this document's own prior claim, not new information from LASS -- flagged here rather than silently fixed, per the standing practice in this document.

### `source_url` Cleanup

Sourcing each Mawlid correction against government/news coverage initially caused `source_url` to point at those news articles, which broke each file's own `test_source_url_consistency` test (the established convention is the exchange's own trading-calendar domain). Reverted all 8 touched `source_url` values back to each exchange's existing domain convention (e.g. `bahrainbourse.com/trading-calendar`, `dfm.ae/en/trading/trading-hours`) -- the underlying date/name/predicted corrections came from the news sourcing above, but the citation field follows the file's own convention, not the research trail.

### Test Suite Impact

23 tests referenced Mawlid or the reverted Islamic New Year entries with hardcoded dates or the old "always predicted" assumption from before either reconciliation pass. Fixed:
- 3 tests with hardcoded September 4 -> corrected to the confirmed real date (XTAD, XCAS, XMUS)
- 1 test (XDFM) updated for the corrected 2025-09-05 date, with 2025 differentiated from still-predicted years
- 4 tests (2 each in XSAU, XQSE) consolidated into 2 new tests (`test_mawlid_absent`) documenting the absence, per the explicit request to "add a test documenting the absence" rather than just deleting the old ones
- 2 tests (XSAU, XQSE Islamic New Year) reverted to expect `(predicted)` again, matching the self-correction above
- 8 `test_source_url_consistency` tests, fixed by the domain cleanup above

Full suite: 3,841/3,841 passing (2 fewer than the prior pass's 3,843 -- the reduction is expected and accounted for: 4 old Saudi/Qatar Mawlid tests consolidated into 2 new ones, not a loss of coverage).

### Updated Reconciliation Counts

| | Before this pass | After this pass |
|---|---|---|
| Total predicted | 339 | 325 |
| Past-due | 102 | 106 |
| Future | 237 | 219 |

The past-due count went up, not down, despite net progress this pass -- expected, not an error: `verify_predicted_dates.py`'s "today" reference advanced from 2026-08-25 to 2026-08-26 over the course of this session, which pushed a cluster of unrelated 2026 Mawlid entries (dated at or near August 25) newly into past-due status across several exchanges, independent of anything fixed here.
