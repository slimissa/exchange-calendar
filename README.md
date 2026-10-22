# Exchange Calendar Registry

**The world's most comprehensive open-source registry of global exchange trading calendars — 74 exchanges across 6 continents.**

One JSON file per exchange. Zero runtime dependencies. Four language wrappers.
Seventy-four exchanges. 46 have registered fetchers — 41 verified against live sources from CI on every run, 5 documented as CI-unreachable (XHKG, XSHG, XNSA) or permanently blocked (XKUW, XSAU). The remaining 28 are documented as blocked sources, with reasoning recorded in [BLOCKED.md](./BLOCKED.md).

[![Validate](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml)
[![Update](https://github.com/slimissa/exchange-calendar/actions/workflows/update-exchange.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/update-exchange.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Schema Version](https://img.shields.io/badge/schema-2.1.1-green.svg)](./schema.json)
[![Registry Version](https://img.shields.io/badge/registry-2.18.1-orange.svg)](./CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-4500+-green.svg)](./tests/)
[![Exchanges](https://img.shields.io/badge/exchanges-74-blue.svg)](./exchanges/)
[![Fetchers](https://img.shields.io/badge/fetchers-41_CI--verified-green.svg)](./.github/workflows/live-fetcher-check.yml)
[![Blocked](https://img.shields.io/badge/blocked-30-lightgrey.svg)](./BLOCKED.md)
[![Coverage](https://img.shields.io/badge/coverage-6_continents-purple.svg)](./exchanges/)
[![Calendar Systems](https://img.shields.io/badge/calendar_systems-6-red.svg)](./docs/)

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

## Cross-registry edges

Every exchange entry joins to two sibling registries. Both edges are
validated in CI.

- **ISO 3166 (country codes).** `country_code` resolves to an active
  entry in [`tools/iso3166_snapshot.json`](./tools/iso3166_snapshot.json),
  and `country` matches the ISO 3166 `name` field byte-for-byte.
  Checked by [`tools/check_country_codes.py`](./tools/check_country_codes.py).
- **ISO 10383 (MICs).** `mic` resolves to an entry in
  [`tools/iso10383_snapshot.json`](./tools/iso10383_snapshot.json)
  (active or expired, operating or segment). Checked by
  [`tools/check_mic_codes.py`](./tools/check_mic_codes.py). See
  [iso10383 `docs/JOINS.md`](https://github.com/slimissa/iso10383/blob/main/docs/JOINS.md)
  for the shared MIC contract.

Both snapshots carry a `review_by` date.
[`tools/check_snapshot_freshness.py`](./tools/check_snapshot_freshness.py)
warns when either falls past due.

---

Release notes for every version are in [CHANGELOG.md](CHANGELOG.md).

---

## Global Coverage

### By Region

| Region | Exchanges | Count |
|--------|-----------|-------|
| North America | NYSE, NASDAQ, Toronto, Mexico, Bermuda, Cayman | 6 |
| Latin America | B3 Brazil, Santiago, Bogota, Lima, Buenos Aires | 5 |
| Europe | London, Euronext (Paris, Amsterdam, Brussels, Lisbon, Dublin), Deutsche Börse, SIX Swiss, Madrid, Vienna, Athens, Istanbul, Warsaw, Prague, Budapest, Luxembourg, Malta, Bulgaria, Zagreb | 19 |
| Nordic/Baltic | Stockholm, Oslo, Copenhagen, Helsinki, Iceland, Vilnius, Riga, Tallinn | 8 |
| Middle East | Saudi Tadawul, Dubai, Abu Dhabi, Qatar, Bahrain, Kuwait, Muscat, Cairo, Beirut | 9 |
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
| Rust | `cargo add exchange-calendar-registry` | `use exchange_calendar::Registry;` |

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

**46 of 74 registry exchanges have automated fetchers as of v2.15.4** — 41 verified against live sources from CI on every run, plus 5 documented as CI-unreachable (XHKG, XSHG, XNSA) or permanently blocked (XKUW, XSAU). The remaining 28 are documented as blocked sources in [`BLOCKED.md`](./BLOCKED.md), with the reasoning for each verdict recorded per exchange.

#### Tier 1 (11 of 11)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| New York Stock Exchange | XNYS | ✅ Implemented | ir.theice.com (IR press release — see [FETCHERS.md#xnys](./docs/FETCHERS.md#xnys)) |
| NASDAQ | XNAS | ✅ Implemented | Mirrors NYSE — see [FETCHERS.md#xnas](./docs/FETCHERS.md#xnas) |
| London Stock Exchange | XLON | ✅ Implemented | UK gov bank-holidays.json (proxy, not LSE-published) — see [FETCHERS.md#xlon](./docs/FETCHERS.md#xlon) |
| Deutsche Boerse Xetra | XETR | ✅ Implemented | cashmarket.deutsche-boerse.com — see [FETCHERS.md#xetr](./docs/FETCHERS.md#xetr) |
| Australian Securities Exchange | XASX | ✅ Implemented | asx.com.au — see [FETCHERS.md#xasx](./docs/FETCHERS.md#xasx) |
| Euronext Paris | XPAR | ✅ Implemented | euronext.com (shared Euronext fetcher) — see [FETCHERS.md#xpar](./docs/FETCHERS.md#xpar) |
| Euronext Amsterdam | XAMS | ✅ Implemented | euronext.com (shared Euronext fetcher) — see [FETCHERS.md#xams](./docs/FETCHERS.md#xams) |
| Tokyo Stock Exchange | XTKS | ✅ Implemented | jpx.co.jp (English-language table) — see [FETCHERS.md#xtks](./docs/FETCHERS.md#xtks) |
| Shanghai Stock Exchange | XSHG | ⚠️ CI-unreachable | english.sse.com.cn — 403 from GitHub runners, works from residential IP — see [FETCHERS.md#xshg](./docs/FETCHERS.md#xshg) |
| Shenzhen Stock Exchange | XSHE | ✅ Implemented | szse.cn — parser rewritten 2026-09-17 for prose format (was table-based) — see [FETCHERS.md#xshe](./docs/FETCHERS.md#xshe) |
| Hong Kong Exchange | XHKG | ⚠️ CI-unreachable | hkex.com.hk Stock Connect CSV — CDN returns 404 to GitHub IPs — see [FETCHERS.md#xhkg](./docs/FETCHERS.md#xhkg) |

#### Tier 2 (3 of 10 — regional hubs proved much harder to automate)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Toronto Stock Exchange | XTSE | ✅ Implemented | tsx.com — see [FETCHERS.md#xtse](./docs/FETCHERS.md#xtse) |
| BME (Bolsa de Madrid) | XMAD | ✅ Implemented | bolsasymercados.es — see [FETCHERS.md#xmad](./docs/FETCHERS.md#xmad) |
| Saudi Exchange (Tadawul) | XSAU | ⛔ Blocked (403 from all IPs) | saudiexchange.sa — see `BLOCKED.md` and [FETCHERS.md#xsau](./docs/FETCHERS.md#xsau) |
| Singapore Exchange | XSES | ⛔ Blocked | JS shell + derivatives-only PDF — see `BLOCKED.md` |
| SIX Swiss Exchange | XSWX | ⛔ Blocked | PDF visual grid, no per-day text labels — see `BLOCKED.md` |
| Korea Exchange | XKRX | ⛔ Blocked | JS/AJAX grid, no API found — see `BLOCKED.md` |
| BSE India | XBOM | ⛔ Blocked | Known page is bot-walled — see `BLOCKED.md` |
| NSE India | XNSE | ⛔ Blocked | JS/AJAX table behind dropdowns — see `BLOCKED.md` |
| Indonesia Stock Exchange | XJKT | ⛔ Blocked | Real PDF exists but bot-blocked — see `BLOCKED.md` |
| Taiwan Stock Exchange | XTAI | ⛔ Blocked | JS-rendered page; full public API spec reviewed, no holiday endpoint exists — see `BLOCKED.md` |

#### Tier 3 (4 of 10 — Gulf/EMEA; PDF-only was the dominant blocker here, not JS-rendering)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Dubai Financial Market | XDFM | ✅ Implemented | dfm.ae annual PDF circular — see [FETCHERS.md#xdfm](./docs/FETCHERS.md#xdfm) |
| Boursa Kuwait | XKUW | ⛔ Blocked (403 from all IPs) | boursakuwait.com.kw — see `BLOCKED.md` and [FETCHERS.md#xkuw](./docs/FETCHERS.md#xkuw) |
| Moscow Exchange | XMOS | ✅ Implemented | moex.com — see [FETCHERS.md#xmos](./docs/FETCHERS.md#xmos) (fragile source) |
| Abu Dhabi Securities Exchange | XTAD | ⛔ Blocked | Next.js JS SPA — see `BLOCKED.md` |
| Bahrain Bourse | XBAH | ⛔ Blocked | Official Holidays page content area is empty (client-side webpart) — see `BLOCKED.md` |
| Qatar Exchange | DSMD | ⛔ Blocked | JS/AJAX Liferay portal widget — see `BLOCKED.md` |
| Egyptian Exchange | XCAI | ⛔ Blocked | Static HTML but stuck serving 2019 data — see `BLOCKED.md` |
| Johannesburg Stock Exchange | XJSE | ⛔ Blocked | PDF exists but is itself bot-walled — see `BLOCKED.md` |
| Borsa Istanbul | XIST | ✅ Implemented | borsaistanbul.com equity-market holiday PDF (one PDF per market segment; Turkish closures only) — see `BLOCKED.md` and [FETCHERS.md#xist](./docs/FETCHERS.md#xist) |
| Muscat Securities Market | XMUS | ⛔ Blocked | Found the real page; content area is empty (client-side) — see `BLOCKED.md` |

#### Tier 4 (8 of 9 — European smaller markets; best hit rate after Tier 1)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Vienna Stock Exchange | XWBO | ✅ Implemented | wienerborse.at PDF — see [FETCHERS.md#xwbo](./docs/FETCHERS.md#xwbo) |
| Warsaw Stock Exchange | XWAR | ✅ Implemented | gpw.pl — see [FETCHERS.md#xwar](./docs/FETCHERS.md#xwar) |
| Prague Stock Exchange | XPRA | ✅ Implemented | pse.cz — cleanest source found this round — see [FETCHERS.md#xpra](./docs/FETCHERS.md#xpra) |
| Budapest Stock Exchange | XBUD | ✅ Implemented | bse.hu PDF resolution — see [FETCHERS.md#xbud](./docs/FETCHERS.md#xbud) |
| Euronext Dublin | XDUB | ✅ Implemented | euronext.com (shared Euronext fetcher) — see [FETCHERS.md#xdub](./docs/FETCHERS.md#xdub) |
| Euronext Brussels | XBRU | ✅ Implemented | euronext.com (shared Euronext fetcher) — see [FETCHERS.md#xbru](./docs/FETCHERS.md#xbru) |
| Euronext Lisbon | XLIS | ✅ Implemented | euronext.com (shared Euronext fetcher) — see [FETCHERS.md#xlis](./docs/FETCHERS.md#xlis) |
| Oslo Bors (Euronext Oslo) | XOSL | ✅ Implemented | euronext.com — see [FETCHERS.md#xosl](./docs/FETCHERS.md#xosl) (NOT Nasdaq Nordic) |
| Athens Exchange | XATH | ⛔ Blocked | Visual-grid PDF, no per-day text labels — see `BLOCKED.md` |

#### Tier 5 (7 of 7 — Nordic/Baltic; clean sweep via two shared sources)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Nasdaq Stockholm | XSTO | ✅ Implemented | nasdaq.com Nordic trading-hours page — see [FETCHERS.md#xsto](./docs/FETCHERS.md#xsto) |
| Nasdaq Helsinki | XHEL | ✅ Implemented | nasdaq.com Nordic trading-hours page — see [FETCHERS.md#xhel](./docs/FETCHERS.md#xhel) |
| Nasdaq Copenhagen | XCSE | ✅ Implemented | nasdaq.com Nordic trading-hours page — see [FETCHERS.md#xcse](./docs/FETCHERS.md#xcse) |
| Nasdaq Iceland | XICE | ✅ Implemented | nasdaq.com Nordic trading-hours page — see [FETCHERS.md#xice](./docs/FETCHERS.md#xice) |
| Nasdaq Tallinn | XTAL | ✅ Implemented | nasdaqbaltic.com — see [FETCHERS.md#xtal](./docs/FETCHERS.md#xtal) |
| Nasdaq Riga | XRIS | ✅ Implemented | nasdaqbaltic.com — see [FETCHERS.md#xris](./docs/FETCHERS.md#xris) |
| Nasdaq Vilnius | XLIT | ✅ Implemented | nasdaqbaltic.com — see [FETCHERS.md#xlit](./docs/FETCHERS.md#xlit) |

#### Tier 6 (4 of 10 implemented — emerging markets; thorough on Latin America, resolved the rest)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| B3 (Brazil) | XBSP | ✅ Implemented | b3.com.br — see [FETCHERS.md#xbsp](./docs/FETCHERS.md#xbsp) (most complex fetcher in this registry) |
| Bolsa Mexicana de Valores | XMEX | ✅ Implemented | bmv.com.mx — see [FETCHERS.md#xmex](./docs/FETCHERS.md#xmex) |
| Bolsas y Mercados Argentinos | XBUE | ✅ Implemented | byma.com.ar — see [FETCHERS.md#xbue](./docs/FETCHERS.md#xbue) |
| Santiago Stock Exchange | XSGO | ⛔ Blocked | JS SPA shell — see `BLOCKED.md` |
| Bursa Malaysia | XKLS | ⛔ Blocked | Bot-walled — see `BLOCKED.md` |
| Bolsa de Valores de Colombia | XBOG | ⛔ Blocked | No first-party page found across two search attempts — see `BLOCKED.md` |
| Bolsa de Valores de Lima | XLIM | ⛔ Blocked | Found the page; confirmed JS SPA shell — see `BLOCKED.md` |
| Philippine Stock Exchange | XPHS | ⛔ Blocked | Found the exact holiday table; empty with unrendered template placeholder — see `BLOCKED.md` |
| Stock Exchange of Thailand | XBKK | ⛔ Blocked | Both PDF and "E-Calendar" are flipbook renderers, no extractable text — see `BLOCKED.md` |
| Ho Chi Minh Stock Exchange | XSTC | ✅ Implemented | staticfile.hsx.vn — resolved in Tier 7, see [FETCHERS.md#xstc](./docs/FETCHERS.md#xstc) |

#### Tier 7 (4 of 9 — Africa/South Asia; infrastructure model applied as a predictive filter)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Nigerian Exchange Group | XNSA | ⚠️ CI-unreachable | ngxgroup.com — see [FETCHERS.md#xnsa](./docs/FETCHERS.md#xnsa) |
| BRVM (8 UEMOA countries) | XBRV | ✅ Implemented | brvm.org — see [FETCHERS.md#xbrv](./docs/FETCHERS.md#xbrv) (shared-infrastructure win) |
| Colombo Stock Exchange | XCOL | ✅ Implemented | cdn.cse.lk official circular — see [FETCHERS.md#xcol](./docs/FETCHERS.md#xcol) |
| Bourse de Tunis | XTUN | ⛔ Blocked | JS-rendered — see `BLOCKED.md` |
| Bourse de Casablanca | XCAS | ⛔ Blocked | robots.txt disallows automated access — see `BLOCKED.md` |
| Pakistan Stock Exchange | XKAR | ⛔ Blocked | Official PDF returns no extractable text — see `BLOCKED.md` |
| Dhaka Stock Exchange | XDHA | ⛔ Blocked | robots.txt disallows automated access — see `BLOCKED.md` |
| Nairobi Securities Exchange | XNAI | ⛔ Blocked | Resolved in Tier 8: 6 pages, identical JS-SPA signature — see `BLOCKED.md` |
| Ghana Stock Exchange | XGSE | ✅ Implemented | Resolved in Tier 8: gse.com.gh/events/ — see [FETCHERS.md#xgse](./docs/FETCHERS.md#xgse) |

#### Tier 8 (5 of 8 — small/island markets; FINAL TIER)

| Exchange | MIC | Status | Source |
|----------|-----|--------|--------|
| Bermuda Stock Exchange | XBDA | ✅ Implemented | bsx.com — see [FETCHERS.md#xbda](./docs/FETCHERS.md#xbda) (one of the cleanest sources in this registry) |
| Cayman Islands Stock Exchange | XCAY | ✅ Implemented | csx.ky — see [FETCHERS.md#xcay](./docs/FETCHERS.md#xcay) |
| Luxembourg Stock Exchange | XLUX | ✅ Implemented | luxse.com — see [FETCHERS.md#xlux](./docs/FETCHERS.md#xlux) (deliberately sparse, flagged) |
| Malta Stock Exchange | XMAL | ✅ Implemented | borzamalta.com.mt — see [FETCHERS.md#xmal](./docs/FETCHERS.md#xmal) |
| Bulgarian Stock Exchange | XBUL | ⛔ Blocked | Calendar widget appears dynamically loaded — see `BLOCKED.md` |
| Zagreb Stock Exchange | XZAG | ✅ Implemented | zse.hr — see [FETCHERS.md#xzag](./docs/FETCHERS.md#xzag) |
| Beirut Stock Exchange | XBEY | ⛔ Blocked | 2 independent timeouts — confirms the brief's own instability concern — see `BLOCKED.md` |
| New Zealand Exchange | XNZE | ⛔ Blocked | JS-loaded content + 2 dead-end PDF/page links — contradicts "likely simple" — see `BLOCKED.md` |

| *(28 exchanges)* | — | ⛔ Blocked | All confirmed blocked across Tiers 2-8 — see `BLOCKED.md` for full detail per exchange |

Per-exchange fetcher notes (source quirks, known limitations, expiring sources) are in [`docs/FETCHERS.md`](./docs/FETCHERS.md); each row above that has a fetcher links to its section.

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
| Python — core tools | 4,164 | ✅ Passing |
| Python — wrapper | 95 | ✅ Passing |
| JavaScript | 94 | ✅ Passing |
| Go | 81 | ✅ Passing |
| Rust | 78 | ✅ Passing |
| **Total** | **4,512** | ✅ All Green |

```bash
# Run test suites
python3 -m pytest tests/ -v                    # Python tests
node --test wrappers/javascript/tests/test_wrappers.js  # JavaScript tests
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
│   ├── ISSUE_TEMPLATE/          # 5 issue templates
│   ├── workflows/               # 4 CI/CD workflows
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
├── tests/                       # 4,500+ tests
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


## Specifications
- [`docs/decisions/0010-render-mode.md`](./docs/decisions/0010-render-mode.md) — the render-mode and OCR decision for the remaining blocked exchanges.


- [`docs/MARKET_CONTEXT_SPEC.md`](./docs/MARKET_CONTEXT_SPEC.md) — the
  `@market_context` interface. Defines the five checks a compiler
  performs against this registry for market-context annotations, and
  the diagnostic format for each.

## License

Apache 2.0 — use it anywhere, no attribution required. The exchange calendar data in this registry is factual information. The compilation, schema, tooling, and wrappers are licensed works.

---

## Author

**Le P'tit** — [github.com/slimissa](https://github.com/slimissa)

---

## Version History

See [CHANGELOG.md](CHANGELOG.md) for the complete version history.