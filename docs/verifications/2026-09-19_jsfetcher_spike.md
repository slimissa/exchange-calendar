# Playwright spike — 2026-09-19

## Question
Can a headless browser read any of the 13 "JS-rendered" exchanges
that `requests` + BeautifulSoup cannot?

## Method
Playwright 1.63.0, Chromium 153. Tested XTAD, XSGO, XLIM, XPHS.

## Result: not viable as planned

| Exchange | HTTP | Bytes | Real calendar? | Reason |
|----------|------|-------|----------------|--------|
| XTAD | 403 | 4,697 | No | Cloudflare (HTTP-level) |
| XSGO | 200 | 18,712 | No | hCaptcha + Perfdrive |
| XLIM | 200 | 26,538 | No | 79 requests, no calendar API |
| XPHS | 200 | 528,057 | No | reCAPTCHA |

## Conclusion
The 13 "JS-rendered" exchanges are blocked by anti-automation
services, not by client-side rendering. A headless browser triggers
the same CAPTCHA as `requests`. `BLOCKED.md`'s "JS-rendered" label
is inaccurate for these entries.

## Recommendation
Redefine v2.3.0 as a verdict-precision pass: sweep all 13, record
the actual blocker for each, update BLOCKED.md. Do not attempt to
bypass anti-bot protections — the cost is a permanent arms race
for 13 of 74 exchanges.
