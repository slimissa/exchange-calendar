# Exchange Calendar Registry

**The world's most comprehensive open-source registry of global exchange trading calendars — 74 exchanges across 6 continents.**

One JSON file per exchange. Zero runtime dependencies. Four language wrappers.
Seventy-four exchanges. 4,070+ tests. 100% global coverage. All CI/CD green.

[![Validate](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml)
[![Update](https://github.com/slimissa/exchange-calendar/actions/workflows/update-exchange.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/update-exchange.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Schema Version](https://img.shields.io/badge/schema-1.0.0-green.svg)](./schema.json)
[![Registry Version](https://img.shields.io/badge/registry-2.1.0-orange.svg)](./CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-4070+-green.svg)](./tests/)
[![Exchanges](https://img.shields.io/badge/exchanges-74-blue.svg)](./exchanges/)
[![Coverage](https://img.shields.io/badge/coverage-6_continents-purple.svg)](./exchanges/)
[![Calendar Systems](https://img.shields.io/badge/calendar_systems-6-red.svg)](./docs/)
[![CI/CD](https://img.shields.io/badge/CI_CD-green-success.svg)](./.github/workflows/)

---

## Why?

Every trading system, quant library, and fintech app maintains its own exchange holiday list. They're often outdated, inconsistent, or just wrong. Some hardcode NYSE hours with no holiday awareness. Some scrape Wikipedia and miss observed days. Some include national holidays that exchanges don't actually observe.

**This project provides one versioned, schema-validated registry that any tool can depend on — instead of every project hand-rolling and hand-maintaining its own.** It covers every major exchange on earth — all G20 financial hubs, all emerging markets, and regional exchanges.

- **Las_shell** uses it for market status detection, scheduling, and prompt display
- **Tempus** uses it for `@market_context` type-level validation
- **Python quant libraries** use it for trading day calculation
- **Go trading systems** use it for order routing logic
- **Rust finance crates** use it for compile-time exchange verification
- **JavaScript fintech apps** use it for market hours display

The registry is language-agnostic by design. The JSON is the contract.

---

## What's New in v2.1.0

### CI/CD Fully Green
- ✅ **Validate workflow**: 6 jobs passing (Python core, Python wrapper, JS, Go, Rust, data integrity)
- ✅ **Update workflow**: Automated NYSE data fetching with dry-run support
- ✅ **Weekend-aware validation**: Correctly handles Friday-Saturday weekend systems
- ✅ **Islamic holiday exemption**: Eid, Islamic New Year, Prophet's Birthday follow Hijri calendar

### New Tooling
- ✅ **`update_from_exchange.py`**: Automated exchange data fetching (957 lines)
- ✅ **31 unit tests** for the updater
- ✅ **`tools/requirements.txt`**: Dependency management
- ✅ **Comprehensive `.gitignore`**: 10 sections covering all development scenarios

### Repository Quality
- ✅ **SECURITY.md**: Vulnerability reporting guidelines with PGP support
- ✅ **7 issue templates**: Data updates, bug reports, feature requests, and more
- ✅ **PR template**: Consistent contribution format
- ✅ **Dependabot**: Automated dependency updates
- ✅ **GitHub Actions**: 3 workflows (validate, update, publish)

---

## Global Coverage

### By Region

| Region | Exchanges | Count |
|--------|-----------|-------|
| North America | NYSE, NASDAQ, Toronto, Mexico, Bermuda, Cayman | 6 |
| Latin America | B3 Brazil, Santiago, Bogota, Lima, Buenos Aires | 5 |
| Europe | London, Euronext (Paris, Amsterdam, Brussels, Lisbon, Dublin), Deutsche Börse, SIX Swiss, Madrid, Vienna, Athens, Istanbul, Warsaw, Prague, Budapest, Luxembourg, Malta, Bulgaria, Zagreb | 20 |
| Nordic/Baltic | Stockholm, Oslo, Copenhagen, Helsinki, Iceland, Vilnius, Riga, Tallinn | 8 |
| Middle East | Saudi Tadawul, Dubai, Abu Dhabi, Qatar, Bahrain, Kuwait, Muscat, Cairo | 8 |
| Africa | Johannesburg, Nigeria, Nairobi, Tunis, Ghana, BRVM (West Africa), Casablanca | 7 |
| Asia-Pacific | Tokyo, Hong Kong, Shanghai, Shenzhen, Korea, Australia, Singapore, Taiwan, Indonesia, Malaysia, Philippines, Thailand, Ho Chi Minh, Karachi, Dhaka, Colombo, New Zealand, India (BSE, NSE) | 19 |
| Eurasia | Moscow Exchange | 1 |
| **Total** | | **74** |

### Weekend Systems Supported

| Weekend | Exchanges |
|---------|-----------|
| Saturday-Sunday (Western) | 67 exchanges (includes UAE: XDFM, XTAD — moved to Sat-Sun in Jan 2022) |
| Friday-Saturday (Islamic) | 7 exchanges (Saudi, Qatar, Bahrain, Kuwait, Oman, Egypt, Bangladesh) |

### Calendar Systems Supported

| Calendar | Holidays |
|----------|----------|
| Gregorian | New Year, Christmas, Labour Day, etc. |
| Orthodox | Easter, Christmas (Russia, Greece, Bulgaria, etc.) |
| Islamic (Hijri) | Eid al-Fitr, Eid al-Adha, Ashura, Prophet's Birthday |
| Buddhist | Makha Bucha, Visakha Bucha, Asahna Bucha (Thailand, Sri Lanka) |
| Chinese Lunar | Spring Festival, Qingming, Dragon Boat, Mid-Autumn |
| Hindu | Deepavali (Sri Lanka, Malaysia, Singapore) |

---

## Quick Start

```bash
git clone https://github.com/slimissa/exchange-calendar.git
cd exchange-calendar

# Validate all exchange data
python3 tools/validate.py
# Output: OK: 74 exchange file(s) validated successfully

# Build the distribution artifact
python3 tools/build.py
# Output: OK: Built calendar.json with 74 exchange(s)

# Run all Python tests
python3 -m pytest tests/ -v

# Update exchange data (dry run)
python3 tools/update_from_exchange.py --all --dry-run

# Update exchange data (actual)
python3 tools/update_from_exchange.py --exchange XNYS
```

---

## Language Wrappers

Each wrapper is idiomatic to its language while maintaining identical behavior:

| Language | Package | Import |
|----------|---------|--------|
| Python | `pip install exchange-calendar-registry` | `from exchange_calendar import CalendarRegistry` |
| JavaScript | `npm install exchange-calendar-registry` | `const { CalendarRegistry } = require('exchange-calendar-registry')` |
| Go | `go get github.com/slimissa/exchange-calendar/wrappers/go` | `import exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"` |
| Rust | `cargo add exchange-calendar` | `use exchange_calendar::Registry;` |

### Python Example

```python
from exchange_calendar import CalendarRegistry, SessionStatus

registry = CalendarRegistry("calendar.json")
xnys = registry.exchange("XNYS")

print(xnys.is_open("2025-07-03", "10:00"))   # True (before 13:00 early close)
print(xnys.is_open("2025-07-03", "13:30"))   # False (after early close)
print(xnys.is_holiday("2025-07-04"))         # True (Independence Day)
print(xnys.early_close_time("2025-07-03"))   # "13:00"
print(xnys.next_trading_day("2025-07-03"))   # "2025-07-07"
```

### JavaScript Example

```javascript
const { CalendarRegistry } = require('exchange-calendar-registry');

const registry = new CalendarRegistry('calendar.json');
const xlon = registry.get('XLON');

console.log(xlon.isOpen('2025-12-24', '12:00'));  // true (before 12:30 close)
console.log(xlon.isOpen('2025-12-24', '12:45'));  // false (after early close)
```

### Go Example

```go
package main

import (
    "fmt"
    exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"
)

func main() {
    registry, _ := exchangecalendar.LoadRegistry("calendar.json")
    xtks, _ := registry.Get("XTKS")
    status, _ := xtks.StatusAt("2025-07-07", "12:00")
    fmt.Println(status)  // "lunch_break"
}
```

### Rust Example

```rust
use exchange_calendar::Registry;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let registry = Registry::load("calendar.json")?;
    let xasx = registry.get("XASX")?;

    println!("{}", xasx.is_open("2025-12-24", Some("10:00")));  // true
    Ok(())
}
```

---

## Automated Updates

The registry includes a production-grade update tool:

```bash
# List available fetchers
python3 tools/update_from_exchange.py --list-fetchers

# Update a single exchange (dry run)
python3 tools/update_from_exchange.py --exchange XNYS --dry-run

# Update all exchanges (dry run)
python3 tools/update_from_exchange.py --all --dry-run

# Force update (bypass cache)
python3 tools/update_from_exchange.py --all --force
```

### Currently Supported Fetchers

**PROJECT COMPLETE: 45 of 74 registry exchanges now have automated
fetchers.** Every one of the 74 exchanges in this registry has now been
explicitly checked across 8 tiers of work — 45 built, 29 confirmed blocked
(via robots.txt, bot-detection, JS-rendering, unreadable PDFs, or confirmed
server instability). None remain in an ambiguous "not verified" state; the
last two (XNBO, XGSE) were resolved to decisive verdicts in this final
round.

#### Tier 1 (10 of 10)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| New York Stock Exchange | XNYS | ✅ Implemented | ir.theice.com (IR press release — see note below) |
| NASDAQ | XNAS | ✅ Implemented | Mirrors NYSE — see note below |
| London Stock Exchange | XLON | ✅ Implemented | UK gov bank-holidays.json (proxy, not LSE-published) |
| Deutsche Boerse Xetra | XETR | ✅ Implemented | cashmarket.deutsche-boerse.com |
| Australian Securities Exchange | XASX | ✅ Implemented | asx.com.au |
| Euronext Paris | XPAR | ✅ Implemented | euronext.com (shared Euronext fetcher) |
| Euronext Amsterdam | XAMS | ✅ Implemented | euronext.com (shared Euronext fetcher) |
| Tokyo Stock Exchange | XTKS | ✅ Implemented | jpx.co.jp (English-language table) |
| Shanghai Stock Exchange | XSHG | ✅ Implemented | english.sse.com.cn — see note below |
| Shenzhen Stock Exchange | XSHE | ✅ Implemented | szse.cn — see note below |
| Hong Kong Exchange | XHKG | ✅ Implemented | hkex.com.hk Stock Connect CSV — see note below |

#### Tier 2 (3 of 10 — regional hubs proved much harder to automate)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Toronto Stock Exchange | XTSE | ✅ Implemented | tsx.com — see note below |
| BME (Bolsa de Madrid) | XMAD | ✅ Implemented | bolsasymercados.es — see note below |
| Saudi Exchange (Tadawul) | XSAU | ✅ Implemented | saudiexchange.sa — see note below |
| Singapore Exchange | XSES | ⛔ Blocked | JS shell + derivatives-only PDF — see `BLOCKED.md` |
| SIX Swiss Exchange | XSWX | ⛔ Blocked | PDF visual grid, no per-day text labels — see `BLOCKED.md` |
| Korea Exchange | XKRX | ⛔ Blocked | JS/AJAX grid, no API found — see `BLOCKED.md` |
| BSE India | XBOM | ⛔ Blocked | Known page is bot-walled — see `BLOCKED.md` |
| NSE India | XNSE | ⛔ Blocked | JS/AJAX table behind dropdowns — see `BLOCKED.md` |
| Indonesia Stock Exchange | XJKT | ⛔ Blocked | Real PDF exists but bot-blocked — see `BLOCKED.md` |
| Taiwan Stock Exchange | XTAI | ⛔ Blocked | JS-rendered page; full public API spec reviewed, no holiday endpoint exists — see `BLOCKED.md` |

#### Tier 3 (3 of 10 — Gulf/EMEA; PDF-only was the dominant blocker here, not JS-rendering)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Dubai Financial Market | XDFM | ✅ Implemented | dfm.ae annual PDF circular — see note below |
| Boursa Kuwait | XKUW | ✅ Implemented | boursakuwait.com.kw — see note below |
| Moscow Exchange | XMOS | ✅ Implemented | moex.com — see note below (fragile source) |
| Abu Dhabi Securities Exchange | XTAD | ⛔ Blocked | Next.js JS SPA — see `BLOCKED.md` |
| Bahrain Bourse | XBAH | ⛔ Blocked | Official Holidays page content area is empty (client-side webpart) — see `BLOCKED.md` |
| Qatar Exchange | XQSE | ⛔ Blocked | JS/AJAX Liferay portal widget — see `BLOCKED.md` |
| Egyptian Exchange | XCAI | ⛔ Blocked | Static HTML but stuck serving 2019 data — see `BLOCKED.md` |
| Johannesburg Stock Exchange | XJSE | ⛔ Blocked | PDF exists but is itself bot-walled — see `BLOCKED.md` |
| Borsa Istanbul | XIST | ⛔ Blocked (deferred) | Real, fetchable PDF, but this sandbox structurally cannot download PDF bytes for this domain — confirmed 3 rounds running, deferred permanently — see `BLOCKED.md` |
| Muscat Securities Market | XMUS | ⛔ Blocked | Found the real page; content area is empty (client-side) — see `BLOCKED.md` |

#### Tier 4 (8 of 10 — European smaller markets; best hit rate after Tier 1)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Vienna Stock Exchange | XWBO | ✅ Implemented | wienerborse.at PDF — see note below |
| Warsaw Stock Exchange | XWAR | ✅ Implemented | gpw.pl — see note below |
| Prague Stock Exchange | XPRA | ✅ Implemented | pse.cz — cleanest source found this round |
| Budapest Stock Exchange | XBUD | ✅ Implemented | bse.hu PDF resolution |
| Euronext Dublin | XDUB | ✅ Implemented | euronext.com (shared Euronext fetcher) |
| Euronext Brussels | XBRU | ✅ Implemented | euronext.com (shared Euronext fetcher) |
| Euronext Lisbon | XLIS | ✅ Implemented | euronext.com (shared Euronext fetcher) |
| Oslo Bors (Euronext Oslo) | XOSL | ✅ Implemented | euronext.com — see note below (NOT Nasdaq Nordic) |
| Athens Exchange | XATH | ⛔ Blocked | Visual-grid PDF, no per-day text labels — see `BLOCKED.md` |

#### Tier 5 (7 of 7 — Nordic/Baltic; clean sweep via two shared sources)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Nasdaq Stockholm | XSTO | ✅ Implemented | nasdaq.com Nordic trading-hours page — see note below |
| Nasdaq Helsinki | XHEL | ✅ Implemented | nasdaq.com Nordic trading-hours page — see note below |
| Nasdaq Copenhagen | XCSE | ✅ Implemented | nasdaq.com Nordic trading-hours page — see note below |
| Nasdaq Iceland | XICE | ✅ Implemented | nasdaq.com Nordic trading-hours page — see note below |
| Nasdaq Tallinn | XTAL | ✅ Implemented | nasdaqbaltic.com — see note below |
| Nasdaq Riga | XRIS | ✅ Implemented | nasdaqbaltic.com — see note below |
| Nasdaq Vilnius | XLIT | ✅ Implemented | nasdaqbaltic.com — see note below |

#### Tier 6 (3 of 10 — emerging markets; thorough on Latin America, resolved the rest)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| B3 (Brazil) | XBSP | ✅ Implemented | b3.com.br — see note below (most complex fetcher in this registry) |
| Bolsa Mexicana de Valores | XMEX | ✅ Implemented | bmv.com.mx — see note below |
| Bolsas y Mercados Argentinos | XBUE | ✅ Implemented | byma.com.ar — see note below |
| Santiago Stock Exchange | XSGO | ⛔ Blocked | JS SPA shell — see `BLOCKED.md` |
| Bursa Malaysia | XKLS | ⛔ Blocked | Bot-walled — see `BLOCKED.md` |
| Bolsa de Valores de Colombia | XBOG | ⛔ Blocked | No first-party page found across two search attempts — see `BLOCKED.md` |
| Bolsa de Valores de Lima | XLIM | ⛔ Blocked | Found the page; confirmed JS SPA shell — see `BLOCKED.md` |
| Philippine Stock Exchange | XPHS | ⛔ Blocked | Found the exact holiday table; empty with unrendered template placeholder — see `BLOCKED.md` |
| Stock Exchange of Thailand | XBKK | ⛔ Blocked | Both PDF and "E-Calendar" are flipbook renderers, no extractable text — see `BLOCKED.md` |
| Ho Chi Minh Stock Exchange | XSTC | ✅ Implemented | staticfile.hsx.vn — resolved in Tier 7, see note below |

#### Tier 7 (4 of 9 — Africa/South Asia; infrastructure model applied as a predictive filter)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Nigerian Exchange Group | XNSA | ✅ Implemented | ngxgroup.com — see note below |
| BRVM (8 UEMOA countries) | XBRV | ✅ Implemented | brvm.org — see note below (shared-infrastructure win) |
| Colombo Stock Exchange | XCOL | ✅ Implemented | cdn.cse.lk official circular — see note below |
| Bourse de Tunis | XTUN | ⛔ Blocked | JS-rendered — see `BLOCKED.md` |
| Bourse de Casablanca | XCAS | ⛔ Blocked | robots.txt disallows automated access — see `BLOCKED.md` |
| Pakistan Stock Exchange | XKAR | ⛔ Blocked | Official PDF returns no extractable text — see `BLOCKED.md` |
| Dhaka Stock Exchange | XDHA | ⛔ Blocked | robots.txt disallows automated access — see `BLOCKED.md` |
| Nairobi Securities Exchange | XNBO | ⛔ Blocked | Resolved in Tier 8: 6 pages, identical JS-SPA signature — see `BLOCKED.md` |
| Ghana Stock Exchange | XGSE | ✅ Implemented | Resolved in Tier 8: gse.com.gh/events/ — see note below |

#### Tier 8 (6 of 8 — small/island markets; FINAL TIER)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Bermuda Stock Exchange | XBDA | ✅ Implemented | bsx.com — see note below (one of the cleanest sources in this registry) |
| Cayman Islands Stock Exchange | XCAY | ✅ Implemented | csx.ky — see note below |
| Luxembourg Stock Exchange | XLUX | ✅ Implemented | luxse.com — see note below (deliberately sparse, flagged) |
| Malta Stock Exchange | XMAL | ✅ Implemented | borzamalta.com.mt — see note below |
| Bulgarian Stock Exchange | XBUL | ⛔ Blocked | Calendar widget appears dynamically loaded — see `BLOCKED.md` |
| Zagreb Stock Exchange | XZAG | ✅ Implemented | zse.hr — see note below |
| Beirut Stock Exchange | XBEK | ⛔ Blocked | 2 independent timeouts — confirms the brief's own instability concern — see `BLOCKED.md` |
| New Zealand Exchange | XNZE | ⛔ Blocked | JS-loaded content + 2 dead-end PDF/page links — contradicts "likely simple" — see `BLOCKED.md` |

| *(29 exchanges)* | — | ⛔ Blocked | All confirmed blocked across Tiers 2-8 — see `BLOCKED.md` for full detail per exchange |

**NYSE note:** nyse.com blocks programmatic requests at the WAF level
("bot detection" — confirmed via `web_fetch`, not fixable with a different
User-Agent since it's not a header check; an earlier report of a plain
"403" from a sandboxed tool call was actually the sandbox's own network
allowlist, a mistake worth naming rather than glossing over). `NYSEFetcher`
now points at NYSE Group's own Investor Relations press release on
`ir.theice.com`, which publishes the same authoritative 3-year holiday table
and isn't blocked. **Updated again 2026-08-29** to the newer 2026-2028
release after the previous 2025-2027 one was flagged as going stale — this
had sat unfixed for two rounds after first being noted, fixed now rather
than deferred again. **This URL will need manual updating once the 2028
window it covers passes** — ICE posts a new press release, at an
unpredictable URL, roughly every year or two.

**NASDAQ note:** nasdaq.com/trading-calendar renders its calendar client-side
(confirmed by direct fetch — the raw HTML contains no holiday data, just a
blank day grid). Rather than ship a scraper against a page that doesn't
expose its data, `NASDAQFetcher` reuses `NYSEFetcher`'s parser against
whichever source `NYSEFetcher` itself currently uses (read dynamically, not
hardcoded, so the two can't silently drift apart the way they briefly did),
since NASDAQ and NYSE observe an identical US equity holiday calendar. Every
mirrored entry carries a `note` field documenting this.

**LSE note:** londonstockexchange.com does not publish its own scrapable
holiday table. `LSEFetcher` uses the UK government's bank-holidays JSON API
as a documented proxy. This has not been independently cross-checked
holiday-by-holiday against LSE's actual closures.

**XSHG/XSHE note:** both pages describe closures as natural-language date
ranges ("close from X to Y") rather than one row per date, so these fetchers
expand ranges into individual weekdays rather than reading dates directly.
**As of verification, neither page had published 2026 Golden Week dates yet**
— both fetchers read whatever year sections exist on the page rather than
hardcoding a year, so they'll pick up new years automatically once published,
but don't assume current-year coverage without checking the returned dates.

**XHKG note:** uses HKEX's own Stock Connect trading-calendar CSV, reading
only the "Hong Kong" column (not the combined Stock Connect / mainland
columns, which can show "Closed" on days HKEX itself is actually open — this
was verified against a real row where only the mainland side was marked
closed). This source doesn't provide specific holiday names, only
"Holiday"/"Half Day" — `HKEXFetcher` labels entries generically rather than
inventing names. Like NYSE, the CSV's URL is year-specific; `fetch()` tries
the current and next year automatically, but the URL template may need
updating if HKEX changes its naming convention.

**XTSE note:** tsx.com separates "Canadian Holidays" (real TSX closures)
from "U.S. Holidays" (settlement-schedule notices for USD-denominated
issues, not actual TSX closures) in the same accordion widget.
`TSXFetcher` only parses the Canadian section. Covers multiple years
(2025 and 2026 both present at verification time).

**XMAD note:** bolsasymercados.es gives no holiday names at all — only
"Nth of Month / Weekday" pairs — and only publishes the current year, no
multi-year table. `BMEMadridFetcher` uses generic labels ("BME Non-Trading
Day") rather than guessing real names, and exposes a
`current_year_only = True` class attribute so callers know not to expect
forward coverage the way NYSE/XETR/XSAU provide.

**XSAU note:** the richest Tier 2 source found — a real static table
spanning 2020-2029. The same table mixes in unrelated IPO "Listing of..."
announcement rows, filtered out via an allowlist (only rows mentioning
"Founding Day", "National Day", or "Eid Al") rather than a blacklist.
Weekend exclusion uses Friday/Saturday, not the Sat/Sun default used
elsewhere. `HolidayEntry.predicted` (defined in the schema and already used
by hand-maintained `XSAU.json` data, but never actually implemented by the
fetcher framework until now) is set to `True` for Eid dates still in the
future relative to when `fetch()` runs, `False` once they're in the past —
Founding Day and National Day are fixed Gregorian dates and are never
predicted. One row in the source table has an internally inverted date
range (end before start) relative to its own prose description;
`SaudiExchangeFetcher` skips that row and logs a warning rather than
guessing which value is correct.

**XDFM note:** the first fetcher in this codebase to use `PDFFetcher` —
dfm.ae's annual holiday circular is a real, clean, text-based PDF (not a
scanned image), added specifically because PDF-only sources turned out to
be the single most common blocker across all three tiers checked so far.
Islamic holidays are footnoted "*" by DFM itself as tentative, mapped
directly onto `HolidayEntry.predicted`. Like NYSE/HKEX, the PDF's URL is
circular-specific and year-specific; will need a manual update once DFM
issues its 2027 circular.

**XKUW note:** boursakuwait.com.kw is Gatsby-generated (built at compile
time), so its holiday table is present in the raw static HTML despite the
site otherwise looking like a JS app. Single-year only, same
`current_year_only` pattern as XMAD.

**XMOS note:** confirmed NOT sanctions-blocked, contrary to the initial
concern going into Tier 3 — moex.com is a real, accessible, static
English-language page. The actual problem is source fragility: the URL is
a year-specific news-post ID with no predictable naming pattern for future
years, worse than every other year-specific source in this registry. Format
is prose, not a table, and gives no per-day holiday name — only a combined
closure-date list, labeled generically as "Russian Public Holiday."

**XWBO note:** wienerborse.at's PDF has a 2-column layout — the left column
("Stock exchange holidays") is real closures, but the RIGHT column
("Additional holiday trading days") lists days the exchange stays OPEN
despite being Austrian public holidays. `ViennaFetcher` only keeps the left
column; discarding the right is deliberate, not an omission.

**XWAR/XBUD notes:** XWAR (gpw.pl) gives no holiday names, generic labels
used. XBUD (bse.hu PDF) does give real names; a footnote about certain
Saturdays being declared non-trading days is deliberately not parsed
separately, since those fall on the weekend already.

**Euronext family note (XPAR/XAMS/XDUB/XBRU/XLIS/XOSL):** all six markets
share one page and one fetcher class. **XOSL (Oslo Bors) was originally
assumed to need a separate "Nasdaq Nordic" source — that assumption was
wrong.** Oslo has been part of the Euronext group since 2019 and its
holiday data is a column in the same table already used for XPAR/XAMS since
Tier 1. Oslo trades in NOK, not EUR like the other five — confirmed
separately, not assumed. **A real bug was found and fixed while extending
this fetcher**: it previously only checked for `'closed'` in a cell,
silently skipping "Half Trading Day" cells — meaning XPAR and XAMS had been
missing their Dec 24/31 early closes since Tier 1. Fixed for all six
markets at once.

**Nasdaq Nordic note (XSTO/XHEL/XCSE/XICE):** one shared page
(nasdaq.com/european-market-activity/trading-hours) hands over
pre-aggregated "Closed" and "Half trading days" date lists per market
directly in the page text — the richest single source found across every
tier. The same page also lists Norway's holidays, deliberately not used for
XOSL since that MIC already has a working Euronext-sourced fetcher and
using two sources for one MIC risks silent disagreement. No per-day holiday
names given, only a combined list per market.

**Nasdaq Baltic note (XTAL/XRIS/XLIT):** one shared page
(nasdaqbaltic.com) with a single table covering all three markets, where a
"Market" column lists which of TLN/RIG/VLN close on each date — some
holidays are shared across all three, some are market-specific (e.g. Jan 2
is Riga-only). No holiday names given, generic labels used.

**XBSP note (Brazil):** the most complex fetcher in this registry.
b3.com.br mixes real Brazilian closures with US-holiday settlement-only
notices in the same table, plus delayed-open special-hours rows (Ash
Wednesday) and pure settlement-lag footnotes — none of which are actual
market closures. `B3BrazilFetcher` requires explicit "no trading on the
equity" language AND excludes the US-only settlement phrase, rather than
relying on a single icon or keyword check.

**XMEX note (Mexico):** the simplest Tier 6 source — a clean two-column
table with real names, current-year-only.

**XBUE note (Argentina):** byma.com.ar uses a footnote-reference system
per row (1)/(2)/(3)/(4); only (3) — "no settlement, but trading continues"
— is excluded from closures. Spanish month names are parsed via an
explicit lookup table, not locale-dependent `strptime`, since this
environment's C locale doesn't reliably support Spanish month names.

**XSTC note (Vietnam):** the source PDF's prose has nested parentheses (a
lunar-calendar cross-reference nested inside a rescheduling note) that
required stripping repeatedly, not just once, before date-range extraction
would work. The document also explicitly confirms that government-mandated
"make-up workday" Saturdays don't apply to the exchange, so no special
date-shifting logic was needed beyond standard weekend exclusion.

**XNSA note (Nigeria):** real static table, includes Eidul-Fitr and Eid
el-Kabir (both `predicted=True`, footnoted by NGX itself as dependent on
government announcement). Showing 2024 data at verification time — treated
as "not yet updated" rather than a structural blocker, since it's a plain
table with no evidence of the postback-gating that made XCAI's staleness
permanent.

**XBRV note (8 UEMOA countries):** a single shared page and fetcher covers
Benin, Burkina Faso, Guinea-Bissau, Cote d'Ivoire, Mali, Niger, Senegal,
and Togo under one MIC — the hypothesized shared-infrastructure pattern,
confirmed. Islamic holidays footnoted `(*)` by BRVM itself, mapped to
`predicted=True`.

**XCOL note (Sri Lanka):** includes both Buddhist Poya (full-moon) holidays
(not predicted — computable, not sighting-dependent) and Islamic holidays
(predicted). Found a real edge case: two holidays can share a date (May Day
and Vesak Poya both fall on 2026-05-01) — since `ExchangeData.validate()`
rejects duplicate dates, same-date entries are merged into one with a
combined name rather than changing that core validation rule.

**XGSE note (Ghana):** resolved via direct site navigation, not search —
found the real "Events & Holidays" nav link on the site's own homepage
after two earlier search-based attempts came up empty. Handles
alternate-date rows ("Friday July 1st/3rd") by matching each candidate
date's computed weekday against the row's stated weekday, confirmed
correct against the real 2026 calendar.

**XBDA note (Bermuda):** one of the cleanest sources in this entire
registry — real, static, multi-year (2024-2027). A bug was caught during
testing (not after shipping): early-close detection for Christmas Eve
initially checked the wrong table cell for the "AST Close" marker.

**XCAY note (Cayman):** two full year sections exist on the page with no
explicit year heading — the year is inferred per table by testing which
candidate year makes the first row's stated weekday match a computed date.

**XLUX note (Luxembourg):** real but deliberately sparse — only one
closure (Christmas Day) was confirmed present for 2026. This may
accurately reflect LuxSE's calendar (primarily a listing venue, not a
high-volume equity market) or may omit client-side-rendered entries. Every
entry carries an explicit `note` flagging this as not confirmed complete,
rather than presenting it with the same confidence as richer sources.

**XMAL note (Malta):** an explicit "TRADING" column distinguishes real MSE
closures from foreign-holiday settlement-only notices ("US Holiday" / "UK
Holiday") — the same foreign-holiday-exclusion pattern already seen in
XTSE and XBSP.

**XZAG note (Zagreb):** real, clean, single-year source with real names.

### CI/CD Automation

The GitHub Actions workflow runs weekly:
- **Sunday 00:00 UTC**: Automated update check
- **Manual trigger**: Via GitHub UI or CLI
- **Dry run first**: Previews changes before applying
- **Automated PR**: Creates PR when changes detected

---

## Testing

| Suite | Tests | Status |
|-------|-------|--------|
| Python — core tools | 3,774 | ✅ Passing |
| Python — wrapper | 64 | ✅ Passing |
| JavaScript | 82 | ✅ Passing |
| Go | 72 | ✅ Passing |
| Rust | 78 | ✅ Passing |
| **Total** | **4,070+** | ✅ All Green |

```bash
# Run all tests
make test

# Run specific test suites
python3 -m pytest tests/ -v                    # Python tests
node --test tests/test_wrappers.js             # JavaScript tests
cd wrappers/go && go test ./tests/ -v         # Go tests
cd wrappers/rust && cargo test                 # Rust tests

# Run update tool tests
python3 -m pytest tests/test_update_from_exchange.py -v
```

---

## Data Format

Each exchange file follows the JSON Schema in `schema.json`:

```json
{
  "code": "XNYS",
  "name": "New York Stock Exchange",
  "mic": "XNYS",
  "timezone": "America/New_York",
  "regular_hours": {
    "open": "09:30",
    "close": "16:00"
  },
  "extended_hours": {
    "pre_market": {"open": "04:00", "close": "09:30"},
    "after_hours": {"open": "16:00", "close": "20:00"}
  },
  "sessions": [],
  "holidays": {
    "explicit": [
      {
        "date": "2025-01-01",
        "name": "New Year's Day",
        "status": "closed",
        "source_url": "https://www.nyse.com/markets/hours-calendars"
      }
    ],
    "recurrence_rules": []
  },
  "ad_hoc_closures": [],
  "generation_range": ["2025-01-01", "2029-12-31"]
}
```

Every explicit holiday entry must include a `source_url` pointing to the official exchange calendar page.

---

## Project Structure

```
exchange-calendar/
├── .github/
│   ├── ISSUE_TEMPLATE/          # 7 issue templates
│   ├── workflows/               # 3 CI/CD workflows
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── exchanges/                   # 74 exchange JSON files
├── tools/
│   ├── update_from_exchange.py  # Automated data fetching
│   ├── validate.py              # Multi-layer validation
│   ├── build.py                 # Distribution artifact builder
│   ├── generate_dates.py        # Recurrence engine
│   └── requirements.txt         # Dependencies
├── wrappers/
│   ├── python/                  # pip package
│   ├── javascript/              # npm package
│   ├── go/                      # Go module
│   └── rust/                    # Rust crate
├── tests/                       # 4,070+ tests
├── docs/
├── SECURITY.md                  # Security policy
├── CONTRIBUTING.md              # Contribution guidelines
├── CHANGELOG.md                 # Version history
├── README.md                    # This file
├── schema.json                  # JSON Schema
└── LICENSE                      # Apache 2.0
```

---

## Security

Please report security vulnerabilities to:
- **GitHub**: [Private vulnerability reporting](https://github.com/slimissa/exchange-calendar/security/advisories/new)
- **Email**: security@exchange-calendar.dev

See [SECURITY.md](SECURITY.md) for the complete security policy.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Data corrections
- New exchange additions
- Wrapper ports
- Tooling improvements

**Quick correction workflow:**
1. Edit the exchange JSON file
2. Run `python3 tools/validate.py` — must pass with 0 errors
3. Run `python3 -m pytest tests/ -v` — all tests must pass
4. Submit a PR with your source cited

---

## License

Apache 2.0 — use it anywhere, no attribution required. The currency data in this registry is factual information. The compilation, schema, tooling, and wrappers are licensed works.

---

## Author

**Le P'tit** — [github.com/slimissa](https://github.com/slimissa)

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| **2.1.0** | 2026-08-19 | CI/CD green, update tool, security policy, 74 exchanges |
| **2.0.0** | 2026-08-19 | 74 exchanges, 6 calendar systems, 4 wrappers |
| **1.2.0** | 2026-08-13 | Added Euronext, major Asian exchanges |
| **1.0.0** | 2026-07-15 | Initial release with 14 exchanges |

See [CHANGELOG.md](CHANGELOG.md) for the complete version history.