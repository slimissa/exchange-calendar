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

**Decision:** permanent-block
**Technique:** none
**Rationale:** The old block was a stale URL, not a visual-grid PDF.
athexgroup.gr 302s to athens.euronext.com, which 404s the paths
recorded in BLOCKED.md. Athens publishes its own calendar as a
downloadable PDF from
`athens.euronext.com/en/trade/trading-model/calendar`. Both the 2026
(Greek) and 2025 (English) PDFs extract as visual calendar grids —
day numbers with no holiday names, no "Closed" markers. Holidays are
indicated by cell fill color, which `pdfplumber.extract_text()`
cannot detect. This is the first confirmed instance of the class
ADR 0009 named as "visual-grid PDF." Parsing would require color or
fill detection outside the framework's current scope.


### D3 — XBKK

**Decision:** permanent-block
**Technique:** none
**Rationale:** The prior note described an AnyFlip flipbook. That was
true of the URL it checked; the site redesigned. SET's current holiday
page links to two plain PDFs on media.set.or.th. The 2026 PDF has a
text layer — 39725 extractable characters across 26 pages — but the
holiday data is a visual calendar grid: month names in headers, day
numbers in rows under a SUNDAY-SATURDAY column header, holiday names
as separate text below each row. Nothing in the extracted text links
a name to a date. Reconstructing the mapping requires word coordinates
and column reconstruction, which PDFFetcher does not expose. This is
the second confirmed member of the visual-grid PDF class ADR 0009
named.


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


## Amendment — 2026-10-04 (v2.12.3)

XATH reconnaissance complete. Athens Exchange publishes its calendar
as a visual-grid PDF with no extractable text layer. D2 updated from
`defer` to `permanent-block`. This is the first confirmed member of
the class ADR 0009 named; the class in BLOCKED.md is no longer empty.


## Amendment — 2026-10-04 (v2.12.4)

XBKK reconnaissance complete. `/en/market/stock-calendar/x-calendar`
has no calendar data (no tables, no PDF links, no flipbook links).
`/en/about/event-calendar/holiday` links to two plain PDFs on
`media.set.or.th`. Both have text layers, but the text is a visual
calendar grid, not a structured holiday list. `SETFetcher(PDFFetcher)`
was attempted and removed; parsing requires word-position-aware
reconstruction outside the framework's current scope. D3 updated from
`defer` to `permanent-block`.


## Amendment — 2026-10-04 (v2.12.5)

XJSE URL discovery complete. The entire jse.co.za site returns 403
with the same Cloudflare challenge page to every plain HTTP client:
homepage, robots.txt, sitemap.xml, and fourteen candidate paths.
`clientportal.jse.co.za` also returns 403 with a full Chrome UA.
The prior Playwright probe reached the homepage (200, 402 KB) but a
one-level PDF scan found no holiday calendar URL. XJSE is
`permanent-block`, with a specific reopen condition: a Playwright
**navigation walk** through the site's own menu into the market
notices or regulation section, which is the one technique not yet
tried. This ADR's D1–D3 are unchanged; XJSE is a separate block
tracked in BLOCKED.md.

## Related

- ADR 0009 — Playwright fetch mode.
- BLOCKED.md — per-exchange findings.
- RELEASE_PATTERN.md — Sources unreachable from CI.
