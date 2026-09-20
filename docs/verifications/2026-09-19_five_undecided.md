# Five undecided exchanges — retest

## Question
Do XKRX, XTUN, XLIM, XTAD and XPHS, left undecided by the 2026-09-19 sweep
(`2026-09-19_js_sweep.md`), load their holiday data through an XHR/fetch JSON
endpoint that plain `requests` can call without a browser?

## Method
The maintainer ran `retest_five.py` (a one-off script, not committed) locally.
For each exchange it loads the candidate URLs in headless Playwright Chromium
with a realistic User-Agent, logging every response from before navigation. It
navigates with `wait_until="domcontentloaded"` (45 s timeout), then waits up to
30 s for `table, [class*=holiday], [id*=holiday], [class*=calendar]` or the
30 s timeout, whichever fires first, plus a 5 s network-idle settle. JSON
responses are scanned for keys containing holiday/date/name/eid and for
Holiday/Eid/Ramadan/Arafat values; candidate endpoints are re-requested with
plain `requests` (GET, or a POST replay of the captured request). Candidate URLs
include the pages BLOCKED.md checked, since the registry `source_url` for
XTUN, XLIM, XTAD and XPHS is not that page. Raw output
(`/tmp/five_undecided_results.json`) is not committed, and the values below are
as reported from that run. Verdicts are the maintainer's corrected ones, not
the script's proposals.

## Results

| MIC | HTTP | XHR JSON endpoints | API endpoint? | Verdict |
|-----|------|--------------------|---------------|---------|
| XKRX | not recorded | POST `/contents/GLB/99/GLB99000001.jspx` returns holiday rows | yes | RESOLVED (JSON endpoint at https://global.krx.co.kr/contents/GLB/99/GLB99000001.jspx; plain requests works) |
| XPHS | not recorded | POST `/wp-admin/admin-ajax.php` returns holiday entries | yes | RESOLVED (JSON endpoint at https://www.pse.com.ph/wp-admin/admin-ajax.php; plain requests works) |
| XLIM | not recorded | `stock-quote/home` (equities data only) | no | BLOCKED (no holiday endpoint) |
| XTAD | not recorded | `_next/data` files, no holiday keys | no | BLOCKED (no holiday endpoint) |
| XTUN | 39-byte body on every URL | none | no | BLOCKED (empty response) |

## Resolved endpoints

### XKRX
- **Request:** `POST https://global.krx.co.kr/contents/GLB/99/GLB99000001.jspx`
- **Response shape:** JSON with a `block1[]` array. Each row carries `calnd_dd`
  (calendar date) and `holdy_eng_nm` (English holiday name). Rows cover 2026.
- **Plain requests:** reaches it without a browser.
- **Not recorded here:** the POST body/parameters, required headers and status
  code. A fetcher needs them; take them from `json_candidates[].post_data` in
  the run's results JSON.

### XPHS
- **Request:** `POST https://www.pse.com.ph/wp-admin/admin-ajax.php`
- **Response shape:** JSON with a `data[]` array. Each entry carries
  `cf:holiday_title` (holiday name), `content` (dates) and `categories`
  (years).
- **Plain requests:** reaches it without a browser.
- **Not recorded here:** the POST body (the WordPress `action` and its
  parameters), required headers and status code, as above.

## False positives

- **XLIM `stock-quote/home`.** The script's proposal rule flagged it RESOLVED
  because it returned JSON with `date` and `name` keys and fetched with plain
  requests. It is equities quote data, not holidays. The calendar page is an
  SPA with no reachable holiday source, so the verdict is BLOCKED (no holiday
  endpoint). The script's `date`+`name` key heuristic is too loose.
- **XTAD `recaptcha-challenge` marker.** The script reported it for the second
  URL, but the marker matches the string `g-recaptcha-response`, which any page
  with a reCAPTCHA form contains. It is not evidence of a block, and the XTAD
  verdict rests on the `_next/data` files having no holiday keys.

## Conclusion
2 of 5 resolve with plain requests: XKRX and XPHS each load their calendar
from a JSON endpoint that needs no browser (fetchers are a follow-up). 3
remain blocked: XLIM and XTAD have no holiday endpoint, and XTUN returns an
empty 39-byte response. For XKRX and XPHS the earlier "JS/AJAX-populated"
findings in BLOCKED.md were accurate; the sweep's fixed 8 s wait and wrong
URLs had simply missed the XHR.
