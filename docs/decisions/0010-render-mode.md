# ADR 0010 — Render mode and OCR for remaining blocked exchanges

**Status:** Accepted (v2.12.2)
**Date:** 2026-10-04
**Depends on:** ADR 0009 (Playwright fetch mode)

## Context

ADR 0009 adopted Playwright in fetch mode only. It left three
candidates unaddressed:

| Exchange | ADR 0009 finding | Class of block |
|----------|------------------|----------------|
| XKRX | page.goto under headless Chromium redirects to COM/403.html | Headless-client block |
| XATH | Visual-grid PDF, no per-day text labels (BLOCKED.md 2026-08-31) | Render-and-extract |
| XBKK | AnyFlip flipbook, pages served as images (BLOCKED.md) | Render-and-extract |

XJSE and XPHS are not candidates. XJSE moved to URL discovery in
ADR 0009's Amendment; XPHS is blocked by robots.txt, which no
browser technique overrides.

## Reconnaissance

Probes were run on 2026-10-04.

### XKRX

- **Headless Chromium (v2.10.0)**: redirect to COM/403.html, 584 bytes.
- **Headful Chromium via Xvfb (v2.12.0)**: same result. A 5-second
  wait does not resolve the redirect.
- **Real Chrome (channel="chrome")**: not testable in this
  environment (Chrome not installed). The delta from Playwright
  Chromium to real Chrome is small: same Blink engine, similar TLS
  fingerprint. The headless-versus-headful delta — which is larger —
  already failed at the server side with no challenge to solve.

### XATH

- **Old URLs 302 to athens.euronext.com/en/... and return 404.**
  The Athens Exchange has been rebranded and its site has moved.
  The athexgroup.gr paths recorded in BLOCKED.md are dead.
- The codebase already shares one source across six Euronext
  exchanges (EuronextFetcher, with subclasses for XPAR, XAMS,
  XDUB, XBRU, XLIS, XOSL). Athens is now a Euronext venue.

### XBKK

- The SET calendar page at /en/market/trading/calendar links to:
  - /en/market/stock-calendar/x-calendar
  - /en/about/event-calendar/holiday
- Neither was probed. The AnyFlip source was not reached because
  the candidate set was empty when the probe ran.

## Decisions

### D1 — XKRX

**Decision:** permanent-block
**Technique:** none
**Rationale:** Two browser mechanisms tested — headless Chromium and
headful Chromium via Xvfb — both fail with a server-side redirect
to COM/403.html. Real Chrome is the only untested variant and the
delta from Playwright Chromium to Chrome (same engine, similar TLS
fingerprint) is smaller than the headless-to-headful delta, which
also failed. The block is not a client-fingerprint problem a further
browser variant will bypass. Marked permanent.

### D2 — XATH

**Decision:** defer
**Technique:** alternate-source (likely a Euronext shared source)
**Rationale:** The recorded block was never "visual-grid PDF." The
URL in BLOCKED.md pointed at a page that no longer exists.
athexgroup.gr redirects to athens.euronext.com, which 404s the
paths BLOCKED.md names. The codebase already has a shared
EuronextFetcher for six sibling exchanges; Athens is now a Euronext
venue and its holiday data is likely on the same page. The next
session probes athens.euronext.com for the shared source and, if
found, adds an EuronextAthensFetcher subclass. This is not
render-mode work.

### D3 — XBKK

**Decision:** defer
**Technique:** alternate-source (probe the two SET URLs)
**Rationale:** The SET calendar page links to two pages not yet
probed: /en/market/stock-calendar/x-calendar and
/en/about/event-calendar/holiday. Either may host the holiday data
as HTML or a fetchable PDF, in which case XBKK is not a render
problem. The AnyFlip URL was never reached because the candidate
set was empty when the probe ran.

### D4 — CI cost

No new technique is adopted. No new CI cost is incurred.

### D5 — Generalization

**Decision:** not-applicable
**Rationale:** No technique is being adopted that could generalize.
The XKRX finding is that a class of WAF blocks all tested browser
variants; that is a fact about XKRX, not a shape for
RELEASE_PATTERN.md.

## Consequences

### Positive

XKRX is closed permanently. No further engineering time will be
spent on it. The three tested mechanisms are recorded so a future
session does not repeat them.

XATH's real block was identified: the site moved. The old
BLOCKED.md finding was about the wrong problem. The Euronext
shared-source pattern is likely the fix.

XBKK's next step is a specific URL probe, not a technique decision.

### Negative

Neither XATH nor XBKK is resolved. The fetcher track stays open
for at least two more sessions.

### Neutral

The "visual-grid PDF" class in BLOCKED.md is empty after this ADR.
XATH was the only member of that class and its real block is
different. No exchange in the registry is currently blocked for
the reason that class name was written to describe.

## Non-goals

- XJSE (URL discovery, tracked in BLOCKED.md).
- XPHS (robots.txt).
- A specific OCR implementation. No exchange has been confirmed to
  need OCR.

## Related

- ADR 0009 — Playwright fetch mode.
- BLOCKED.md — per-exchange findings.
- RELEASE_PATTERN.md — Sources unreachable from CI.
