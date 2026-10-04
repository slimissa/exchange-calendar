# Market Context Specification - v1.0.0

**Status:** Draft for implementation
**Registry schema required:** `>= 2.1.1`
**Depends on:** ISO 10383 MIC registry, Exchange Calendar registry
**Audience:** A compiler that resolves `@market_context` annotations.

---

## 1. Scope

This document specifies the interface between the Exchange Calendar
registry and a compiler that type-checks `@market_context`
annotations. It defines:

- The annotation's grammar and field semantics.
- The five checks a compiler performs against the registry.
- The diagnostic format for each failure.
- The versioning rules that govern compatibility.

It does **not** specify parsing strategy, error recovery, code
generation, or any behavior of the compiler beyond the checks
themselves. Those are the compiler's responsibility.

---

## 2. Definitions

### 2.1 MIC

A Market Identifier Code per ISO 10383. Four uppercase alphanumerics.
The registry vendors an ISO 10383 snapshot at
`tools/iso10383_snapshot.json`; the snapshot is the compiler's
authority for MIC validity.

### 2.2 Session

A typed trading window on a specific calendar day. The Exchange
Calendar registry defines six session types. Two classes:

- **Interval types** carry `open` and `close`: `regular`,
  `pre_market`, `post_market`, `lunch_break`.
- **Point types** carry `at`: `auction`, `halt`.

Only interval types are used for market-context checks. A point-type
session marks an instant, not a period, and does not bound a signal.

### 2.3 Confidence level

Per-exchange, per-year assessment of the calendar data's reliability.
Values `high`, `medium`, `low` with total order
`high > medium > low`. Retrievable via `confidence(mic, year)` in any
wrapper. A year absent from the map is treated as `low`.

### 2.4 Window

An inclusive range of calendar years, e.g. `2020..2023`. All checks
that iterate over time iterate over the years in this range.

### 2.5 Bound MIC

A MIC named in the annotation's `mic` or `mics` field. A bound MIC
participates in every check.

---

## 3. The annotation

### 3.1 Grammar

market_context_attr := '@market_context' '{'
mc_field (',' mc_field)* ','? '}'
mc_field := 'mic' ':' MIC
| 'mics' ':' '[' MIC (',' MIC)* ']'
| 'window' ':' YEAR '..' YEAR
| 'min_confidence' ':' ('high' | 'medium' | 'low')
text


`mic` and `mics` are mutually exclusive; exactly one must appear.
`window` and `min_confidence` are both required.

### 3.2 Field semantics

- `mic` / `mics` - the bound MICs.
- `window` - the years the annotated function is compiled against.
- `min_confidence` - the minimum acceptable level for every bound
  MIC in every year of the window.

---

## 4. The five checks

### R1 - MIC resolution

**Statement.** Every bound MIC appears in the vendored ISO 10383
snapshot.

**Data.** `tools/iso10383_snapshot.json`, `mics[].mic`.

**Failure.** Diagnostic `MC001`.

**Example.** `mic: XZZZ` where `XZZZ` is not a MIC fails; `mic: XNYS`
passes.

### R2 - Calendar coverage

**Statement.** Every bound MIC has an entry in the registry's
exchange set.

**Data.** `calendar.json`, `exchanges[].mic`.

**Failure.** Diagnostic `MC002`.

**Note.** R2 is stricter than R1. ISO 10383 has ~2,883 MICs; this
registry covers 74. A MIC may be valid per R1 and still lack a
calendar per R2.

### R3 - Confidence threshold

**Statement.** For every bound MIC `m` and every year `y` in the
window, `confidence(m, y).level >= min_confidence`.

**Data.** `confidence(mic, year)` in any wrapper. Years absent from
the confidence map are treated as `low`.

**Failure.** Diagnostic `MC003`, naming the MIC, the year, the
actual level, and the required level.

**Example.** `min_confidence: high` fails for XNYS in 2022 if
`confidence("XNYS", 2022).level == "medium"`.

### R4 - Evaluation instant in a session

**Statement.** Every signal produced by the annotated function is
evaluated at a wall-clock instant that lies inside an interval
session of at least one bound MIC, on a date in the window whose
year satisfies R3.

**Data.** `sessions(mic)` returns the interval and point sessions
for an exchange. Only interval types count.

**Failure.** Diagnostic `MC004`, naming the signal's declared type
and the bound MICs it fails to satisfy.

**Example.** A `Signal<f64, @t-1>` in a function bound to XNYS
cannot be evaluated at 03:00 on 2026-01-02 - no session of XNYS
contains that instant.

### R5 - Offset anchor in a session

**Statement.** A signal tagged `@t+N` or `@t-N` requires that the
anchor `t` resolve to an interval session of at least one bound MIC.
`N` steps by sessions, not by wall-clock days.

**Data.** Same as R4.

**Failure.** Diagnostic `MC005`.

**Example.** `Signal<f64, @t+1>` at a Friday close resolves to
Monday's regular session; at the Friday of a long weekend, resolves
to the next session that exists. If no session exists anywhere in
the window, the signal is invalid.

---

## 5. Diagnostic format

Every failure produces a compiler error with:

- A **code** `MC001`–`MC005`.
- The **source location** of the annotation field or the signal
  reference that failed.
- A **one-line message** naming the check that failed.
- A **detail block** with the concrete data that failed the check.

Example:

error[MC003]: confidence below threshold
--> strategy.tms:3:22
|
3 | min_confidence: high,
| ^^^^ required high
|
= exchange XNYS, year 2022 has confidence medium
= source: confidence("XNYS", 2022) = {level: "medium", ...}
text


The diagnostic references the wrapper method and its return value,
not just the abstract rule. This gives the user a path from the
error to the data.

---

## 6. Worked example

```tms
@market_context {
    mic: XNYS,
    window: 2024..2026,
    min_confidence: high,
}
fn momentum(prices: TimeSeries<Price<USD>, Daily>)
    -> Signal<f64, @t-1>
{
    // body
}
```

A conforming compiler performs, in order:

    R1 - XNYS in tools/iso10383_snapshot.json. Pass.

    R2 - XNYS has an entry in calendar.json. Pass.

    R3 - For y ∈ {2024, 2025, 2026}, confidence("XNYS", y).level >= high.

        If confidence("XNYS", 2024) = manual/medium, fail with MC003.

    R4 - Every signal in the body is evaluated at an instant inside
    an interval session of XNYS. The compiler cannot verify this for
    arbitrary bodies; it requires that the function's return type
    Signal<f64, @t-1> and the annotation's MIC set are compatible.

    R5 - @t-1 from an anchor t requires t-1 to resolve to a
    session. The compiler verifies the anchor exists during type
    inference.

The compiler reports every failure it finds. It does not stop at the
first.

## 7. Versioning

The spec carries its own version (1.0.0 in the title) independent
from the registry version.

    Patch - clarifications that do not change what passes or fails.

    Minor - new checks, new optional annotation fields, new
    session types that participate.

    Major - removal of a check, renaming of a field, change to the
    confidence ordering or a rule that turns a passing program into a
    failing one.

Any change to the registry's confidence semantics, session type
enum, or exchange coverage is a candidate for a spec revision if it
affects the outcome of R1–R5. When in doubt, the registry's schema
version is the authority: a schema bump to 2.2 or higher requires
reviewing this spec.

## 8. Non-goals

This specification does not check:

    Whether a strategy is profitable or well-designed.

    Whether a MIC is appropriate for a particular instrument.

    Whether an instrument's currency matches its MIC's country.

    Whether a strategy's holidays or sessions align with a
    specific order-routing venue.

    Whether two bound MICs share overlapping sessions.

Those concerns belong to a future @instrument_context or a
strategy-level linter, not to @market_context.

## 9. Data sources
Item	Location
ISO 10383 MIC snapshot	tools/iso10383_snapshot.json
Exchange records	calendar.json
Per-exchange confidence	confidence(mic, year) on any wrapper
Per-exchange sessions	sessions(mic) on any wrapper
Schema definition	schema.json

All four wrappers expose the same methods with identical semantics:
Python (CalendarRegistry), JavaScript (Registry), Rust
(Registry), Go (Registry).

Spec version: 1.0.0 | Registry schema: 2.1.1 | 2026-10-04
