# ADR 0010 — Render mode and OCR for remaining blocked exchanges

**Status:** Accepted (v2.12.0)
**Date:** YYYY-MM-DD
**Supersedes:** nothing
**Depends on:** ADR 0009 (Playwright fetch mode)

## Context

ADR 0009 adopted Playwright in fetch mode only: the browser
issues the request, the existing parser handles the body. That
decision resolved two exchanges (XJSE at v2.10.0 pending URL
discovery; a framework introduced at v2.10.0) and left three
candidates unaddressed:

| Exchange | ADR 0009 finding | Class of block |
|----------|------------------|----------------|
| XKRX | `page.goto` under headless Chromium redirects to `COM/403.html`; response unchanged after 8s JS wait | Headless-client block |
| XATH | Visual-grid PDF, no per-day text labels (BLOCKED.md 2026-08-31) | Render-and-extract |
| XBKK | AnyFlip flipbook, pages served as images (BLOCKED.md) | Render-and-extract |

XJSE and XPHS are not candidates for this ADR. XJSE moved to
URL discovery in ADR 0009's Amendment; XPHS is blocked by
robots.txt, which no browser technique overrides.

## Reconnaissance

On YYYY-MM-DD, three probes were run. Results:

### XKRX

Technique tried: headful Chromium via `xvfb-run`. Result:
<pass|fail>. [One sentence on what the response looked like.]

### XATH

Source URL: <URL>. Extracted text: <N chars>. Shape: <text-layer
| visual-grid>. [One sentence on what the extraction showed.]

### XBKK

AnyFlip config URL: <URL>. Source file type: <pdf | images |
unknown>. [One sentence on what the config revealed.]

## Decisions

### D1 — XKRX

**Decision:** `<attempt|permanent-block>`

**Technique:** `<xvfb-headful|chrome-profile|alternate-source|none>`

**Rationale:** [One paragraph. If attempted: what the CI cost is,
what the failure mode is, what a follow-up would look like. If
permanent: why no further technique is worth trying.]

### D2 — XATH

**Decision:** `<attempt|permanent-block|defer>`

**Technique:** `<layout-parse|ocr|alternate-source|none>`

**Rationale:** [One paragraph.]

### D3 — XBKK

**Decision:** `<attempt|permanent-block|defer>`

**Technique:** `<pdf-extract|ocr|alternate-source|none>`

**Rationale:** [One paragraph.]

### D4 — CI cost

If D1, D2, or D3 elects to attempt, the technique's CI cost is:

| Technique | Time per fetch | Disk | Dependency |
|-----------|----------------|------|------------|
| `xvfb-headful` | +2–5 s | ~5 MB | `xvfb`, `xauth` |
| `chrome-profile` | +5–10 s | ~100 MB (persistent) | none beyond Chromium |
| `ocr` | +10–30 s per page | ~30 MB | `tesseract`, `pytesseract` |
| `layout-parse` | +0 s | 0 | none (existing `pdfplumber`) |

**Decision:** [Which techniques are approved for v2.12.x, if any.]

### D5 — Generalization

**Decision:** `<shared-in-RELEASE_PATTERN | ec-local | not-applicable>`

**Rationale:** The technique shapes that could generalize are:

- **Headful-via-Xvfb bypass.** A registry with a fetcher that
  is blocked by a headless-detection WAF. Generalizes if EC is
  not the only ecosystem member that will hit this.
- **OCR for visual-grid documents.** A registry with a
  first-party document that has no text layer. Generalizes if
  another registry publishes such a document.

[State which, if any, goes into `RELEASE_PATTERN.md` under a
new section, and why.]

## Consequences

### Positive

- [Per decision.]

### Negative

- [Per decision, with concrete CI cost.]

### Neutral

- [Any exchange left in `defer` state; any technique left
  untested.]

## Non-goals

- Not deciding what happens to XJSE (URL discovery, tracked
  separately in BLOCKED.md).
- Not deciding what happens to XPHS (robots.txt, no browser
  technique applies).
- Not committing to a specific OCR implementation if D2/D3
  do not elect to attempt OCR.

## Related

- ADR 0009 — Playwright fetch mode.
- `BLOCKED.md` — per-exchange findings.
- `RELEASE_PATTERN.md` § Sources unreachable from CI — the
  section this ADR may extend.
