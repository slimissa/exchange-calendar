# ADR 0009 — Playwright as a fetcher category

**Status:** Accepted (v2.9.5)
**Date:** 2026-10-04

## Context

Five exchanges remain blocked with failure modes that the current
fetcher shapes do not cover:

| Exchange | BLOCKED.md verdict | Failure mode |
|----------|--------------------|--------------|
| XKRX | HTTP 200, HTML body titled "403 Page" | Client-fingerprint WAF |
| XJSE | "Site blocked the request (bot detection)" | Client-fingerprint WAF on the PDF URL |
| XATH | "Visual-grid PDF, no per-day text labels" | Render-only content |
| XBKK | AnyFlip flipbook, no static PDF | Render-only content |
| XPHS | JS-rendered table, source XHR unresolved | Runtime-generated DOM |

These split into two classes:

- **Fetch problems.** The bytes never arrive because a WAF refuses
  the request shape. XKRX, XJSE.
- **Render problems.** The bytes arrive but carry no extractable
  data without a JavaScript runtime or a rendering pass. XATH,
  XBKK, XPHS.

A single tool — a headless browser — solves both, but the two uses
have different costs and different maintenance profiles. The ADR
must decide whether to adopt it, in which mode, and whether the
shape generalizes beyond EC.

## Decisions

### 1. Adopt Playwright, fetch mode first

Playwright + Chromium becomes an optional dependency for fetchers
that need it. The first mode shipped is **fetch-only**: the browser
issues the request, the fetcher receives the response, and the
existing HTML/PDF parser handles the body. No JavaScript
interaction, no screenshots, no OCR.

This mode unlocks XKRX and XJSE. Both are WAF blocks; a real
browser session bypasses client-fingerprint checks that a plain
HTTP client cannot fake. Both fetchers keep their current parsers;
only the transport changes.

### 2. Defer render+OCR to ADR 0010

Render mode — load the page in a headless browser, wait for the
DOM, extract the visible grid — unlocks XATH and XBKK. It requires
either DOM scraping (for HTML-rendered calendars) or OCR (for
image-rendered PDFs). The two are different problems with different
dependencies.

XPHS is ambiguous: the AJAX source might be found by watching
network traffic in a headless session (which is Playwright in fetch
mode), so it may not need render mode at all. The ADR defers that
determination to the XPHS probe in v2.10.x.

**The render path is deferred to a second ADR** because it adds
an OCR runtime, a longer CI surface, and a different maintenance
burden. Bundling it here would answer a question that fetch mode
does not create.

### 3. CI cost is bounded and named

The cost of Playwright in CI:

- **Image size**: Chromium adds ~200 MB to the runner cache.
- **Time**: ~5 s per browser launch, plus page-load time (10–30 s
  per source at default settings).
- **Network**: a Chromium download on first run per runner.

For two fetchers on a weekly cadence, this is ~1 minute of CI
per week and ~30 MB of state. Acceptable.

For five fetchers, ~3 minutes per week. Still acceptable, but the
rationale for narrowing to fetch mode first is that the render
mode adds a larger multiplier (screenshot → OCR pipeline).

### 4. Maintenance model: same as any other fetcher

A browser-driven fetcher drifts when the source renames a route,
changes a login flow, or adds a challenge that even a headless
session cannot pass. That drift is the fetcher owner's problem, the
same as an HTML-parser fetcher whose source is redesigned.

**No special maintenance tier.** The fetcher_manifest records
Playwright fetches the same way it records HTTP fetches; the
freshness check treats them identically. If a Playwright fetcher
stops working, its manifest entry goes stale and the freshness
check surfaces it.

### 5. Playwright is EC-local, not shared

The question for RELEASE_PATTERN.md: does "browser-driven fetcher"
belong in the shared convention, alongside the CI-unreachable
section?

**No, with one caveat.**

The pattern is EC-specific because EC is the only registry in the
family with fetchers that hit heterogeneous sources. ISO 10383 has
one fetcher on one URL. ISO 3166 and ISO 4217 have none. There is
no sibling to compare against and no second implementation to
validate the shape.

The one portable idea is the **fetch/render split itself** — the
observation that a browser solves two different problems and
should be scoped to one at a time. That sentence can go in
RELEASE_PATTERN.md as a note under "Sources unreachable from CI",
because it's a refinement of the same concept (an exchange that
cannot be reached from a plain HTTP client). It does not need its
own section.

## Consequences

### Positive

- XKRX and XJSE have a concrete fix path that ships in v2.10.0.
- The fetch/render distinction is documented before either mode is
  implemented, so v2.10.0 does not attempt both at once.
- CI cost is bounded and stated.
- The "EC-local, not shared" decision is explicit, so no registry
  in the family adds Playwright on the basis of this ADR alone.

### Negative

- A new dependency enters the fetcher framework. Only the fetchers
  that use it need it, but any environment that runs the full test
  suite now needs Chromium installed.
- The  gains a line, and a first-run install step
  is added to CI. This is not free — it is bounded and named.
- XATH and XBKK stay blocked until ADR 0010. The five-candidate set
  becomes a two-release path, not one.

### Neutral

- XPHS remains ambiguous. Fetch mode may resolve it; it may not.
  The ADR does not commit either way.

## Alternatives considered

### A. Do nothing — leave all five blocked

Rejected. XKRX and XJSE have a known, standard fix. Refusing to
adopt it makes the registry's blocked list a policy statement
rather than a technical one.

### B. Adopt Playwright for both modes at once

Rejected. The two modes have different costs, different failure
surfaces, and different dependencies (OCR). Bundling them means
any decision to relax one requires re-opening both.

### C. Use a lighter headless tool (e.g. requests-html, pyppeteer)

Rejected for now. Playwright is the maintained choice, has stable
Chromium downloads, and its Python API matches the fetcher
framework's existing request/parse split. If a lighter tool proves
sufficient in v2.10.0, a subsequent ADR can revisit.

### D. Proxy or mirror the source

Rejected for XKRX and XJSE. A proxy does not resolve the
underlying block; it merely routes around it, and the same WAF
rule will eventually catch the proxy's IP range. The browser
solution is honest: it is what a human would do.

## Open questions

- **XPHS resolution.** Whether the AJAX source surfaces in a
  headless session's network log. Probe scheduled for v2.10.x.
- **First-run Chromium install.** Whether the CI runner needs an
  explicit `playwright install chromium` step or whether the
  fetcher framework can invoke it lazily. Depends on how the
  fetcher API is extended.
- **Timeout policy.** Browser fetches may need a longer timeout
  than the current 30 s default. The framework's per-fetcher
  `MAX_AGE_DAYS` pattern suggests the right place is a
  `FETCH_TIMEOUT_SECONDS` class attribute — a v2.10.0 decision.


## Amendment — 2026-10-04

Fetch mode was implemented and probed against both candidate
exchanges. The result was asymmetric.

**XJSE — fetch mode works.** `page.goto("https://www.jse.co.za/")`
through headless Chromium returns HTTP 200 with the site's own
HTML (402 KB, title "JSE | Leading Stock Market and Exchange in
Africa"). Cloudflare's challenge is satisfied by a real browser
session. The PDF URLs are reachable from that session; the fetcher
is writable.

**XKRX — fetch mode does not work.** `page.goto` to the JSON
endpoint redirects to `https://global.krx.co.kr/contents/COM/403.html`,
title "403 Page", 584 bytes. The response is unchanged after an
8-second JavaScript wait. The WAF blocks headless Chromium at the
server side — the redirect happens before the browser renders
anything. This is not a client-fingerprint problem that a browser
can spoof its way past; it is a server-side rule against headless
clients.

The two failure modes were previously grouped as "WAF blocks". They
are not the same class:

- **Client-fingerprint block.** Blocks plain HTTP clients. A real
  browser session bypasses it. XJSE.
- **Headless-client block.** Blocks headless browsers specifically.
  A headful browser may or may not bypass it; a real user's Chrome
  from a residential IP probably would. XKRX.

Fetch mode (Decision 1) addresses the first class. It does not
address the second. XKRX moves to the render bucket pending
ADR 0010, which will decide between:

1. Headful Chromium with a virtual display (Xvfb).
2. Real Chrome with a persistent user profile.
3. An alternate data source (KRX's own open-data portal, if one
   exists).
4. Permanent BLOCKED status, documented.

Decision 1 stands for XJSE (fetch mode works; the fetcher is
pending URL discovery — see BLOCKED.md). Decision 2 (defer
render+OCR) is unchanged. XKRX moves to ADR 0010's bucket; the
render ADR will decide between headful Xvfb, a real Chrome
profile with a persistent user-data dir, an alternate KRX
source, or permanent BLOCKED.


## Related

- `docs/MARKET_CONTEXT_SPEC.md` — the interface this registry offers to a compiler that resolves `@market_context`.


- ADR 0003 (monthly refresh) — the diff-based refresh model that
  Playwright fetchers plug into.
- ADR 0008 (removal guard) — the guard that fires when a
  Playwright fetcher returns data that would remove existing
  entries.
- BLOCKED.md — per-exchange findings for XKRX, XJSE, XATH,
  XBKK, XPHS.
- RELEASE_PATTERN.md § Sources unreachable from CI — the note
  this ADR refines.
