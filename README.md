# Exchange Calendar Registry

**The world's most comprehensive open-source registry of global exchange trading calendars — 74 exchanges across 6 continents.**

One JSON file per exchange. Zero runtime dependencies. Four language wrappers.
Seventy-four exchanges. 46 have registered fetchers — 41 verified against live sources from CI on every run, 5 documented as CI-unreachable (XHKG, XSHG, XNSA) or blocked, HTTP 403 on 2026-09-17 (XKUW, XSAU). The remaining 28 have no fetcher and are documented as blocked sources (30 exchanges are blocked in total, counting XKUW and XSAU), with reasoning recorded in [BLOCKED.md](./BLOCKED.md).

[![Validate](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml)
[![Update](https://github.com/slimissa/exchange-calendar/actions/workflows/update-exchange.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/update-exchange.yml)
[![Divergence](https://github.com/slimissa/exchange-calendar/actions/workflows/divergence.yml/badge.svg)](https://github.com/slimissa/exchange-calendar/actions/workflows/divergence.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Schema Version](https://img.shields.io/badge/schema-2.1.1-green.svg)](./schema.json)
[![Registry Version](https://img.shields.io/badge/registry-2.23.2-orange.svg)](./CHANGELOG.md)
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

**46 of 74 registry exchanges have automated fetchers as of v2.23.2** — 41 verified against live sources from CI on every run, plus 5 documented as CI-unreachable (XHKG, XSHG, XNSA) or blocked, HTTP 403 on 2026-09-17 (XKUW, XSAU). The remaining 28 have no fetcher and are documented as blocked sources (30 exchanges are blocked in total, counting XKUW and XSAU) in [`BLOCKED.md`](./BLOCKED.md), with the reasoning for each verdict recorded per exchange.

Sorted by MIC. ✅ implemented, verified from CI on every run · ⚠️ CI-unreachable: a fetcher exists, but the source rejects GitHub-hosted runners (XSHG: 403; XHKG: CDN returns 404 to GitHub IPs; XNSA: see its BLOCKED.md entry) · ⛔ blocked: the source cannot be fetched automatically and the calendar is maintained by hand.

| Exchange | MIC | Status | Source | Notes |
|----------|-----|:------:|--------|-------|
| Qatar Exchange | DSMD | ⛔ | qe.com.qa | [BLOCKED.md#dsmd](BLOCKED.md#dsmd) |
| Euronext Amsterdam | XAMS | ✅ | euronext.com | [#xams](docs/FETCHERS.md#xams) |
| Australian Securities Exchange | XASX | ✅ | asx.com.au | [#xasx](docs/FETCHERS.md#xasx) |
| Athens Exchange | XATH | ⛔ | athens.euronext.com | [BLOCKED.md#xath](BLOCKED.md#xath) |
| Bahrain Bourse | XBAH | ⛔ | bahrainbourse.com | [BLOCKED.md#xbah](BLOCKED.md#xbah) |
| Bermuda Stock Exchange | XBDA | ✅ | bsx.com | [#xbda](docs/FETCHERS.md#xbda) |
| Beirut Stock Exchange | XBEY | ⛔ | bse.com.lb | [BLOCKED.md#xbey](BLOCKED.md#xbey) |
| Stock Exchange of Thailand | XBKK | ⛔ | set.or.th | [BLOCKED.md#xbkk](BLOCKED.md#xbkk) |
| Bolsa de Valores de Colombia | XBOG | ⛔ | bvc.com.co | [BLOCKED.md#xbog](BLOCKED.md#xbog) |
| BSE India | XBOM | ⛔ | bseindia.com | [BLOCKED.md#xbom](BLOCKED.md#xbom) |
| Euronext Brussels | XBRU | ✅ | euronext.com | [#xbru](docs/FETCHERS.md#xbru) |
| BRVM (8 UEMOA countries) | XBRV | ✅ | brvm.org | [#xbrv](docs/FETCHERS.md#xbrv) |
| B3 (Brazil) | XBSP | ✅ | b3.com.br | [#xbsp](docs/FETCHERS.md#xbsp) |
| Budapest Stock Exchange | XBUD | ✅ | bse.hu | [#xbud](docs/FETCHERS.md#xbud) |
| Bolsas y Mercados Argentinos | XBUE | ✅ | byma.com.ar | [#xbue](docs/FETCHERS.md#xbue) |
| Bulgarian Stock Exchange | XBUL | ⛔ | bse-sofia.bg | [BLOCKED.md#xbul](BLOCKED.md#xbul) |
| Egyptian Exchange | XCAI | ⛔ | egx.com.eg | [BLOCKED.md#xcai](BLOCKED.md#xcai) |
| Bourse de Casablanca | XCAS | ⛔ | casablanca-bourse.com | [BLOCKED.md#xcas](BLOCKED.md#xcas) |
| Cayman Islands Stock Exchange | XCAY | ✅ | csx.ky | [#xcay](docs/FETCHERS.md#xcay) |
| Colombo Stock Exchange | XCOL | ✅ | cdn.cse.lk | [#xcol](docs/FETCHERS.md#xcol) |
| Nasdaq Copenhagen | XCSE | ✅ | nasdaq.com | [#xcse](docs/FETCHERS.md#xcse) |
| Dubai Financial Market | XDFM | ✅ | assets.dfm.ae | [#xdfm](docs/FETCHERS.md#xdfm) |
| Dhaka Stock Exchange | XDHA | ⛔ | dsebd.org | [BLOCKED.md#xdha](BLOCKED.md#xdha) |
| Euronext Dublin | XDUB | ✅ | euronext.com | [#xdub](docs/FETCHERS.md#xdub) |
| Deutsche Boerse Xetra | XETR | ✅ | cashmarket.deutsche-boerse.com | [#xetr](docs/FETCHERS.md#xetr) |
| Ghana Stock Exchange | XGSE | ✅ | gse.com.gh | [#xgse](docs/FETCHERS.md#xgse) |
| Nasdaq Helsinki | XHEL | ✅ | nasdaq.com | [#xhel](docs/FETCHERS.md#xhel) |
| Hong Kong Exchange | XHKG | ⚠️ | hkex.com.hk | [#xhkg](docs/FETCHERS.md#xhkg), [BLOCKED.md#xhkg](BLOCKED.md#xhkg) |
| Nasdaq Iceland | XICE | ✅ | nasdaq.com | [#xice](docs/FETCHERS.md#xice) |
| Borsa Istanbul | XIST | ✅ | borsaistanbul.com | [#xist](docs/FETCHERS.md#xist) |
| Indonesia Stock Exchange | XJKT | ⛔ | idx.co.id | [BLOCKED.md#xjkt](BLOCKED.md#xjkt) |
| Johannesburg Stock Exchange | XJSE | ⛔ | jse.co.za | [BLOCKED.md#xjse](BLOCKED.md#xjse) |
| Pakistan Stock Exchange | XKAR | ⛔ | psx.com.pk | [BLOCKED.md#xkar](BLOCKED.md#xkar) |
| Bursa Malaysia | XKLS | ⛔ | bursamalaysia.com | [BLOCKED.md#xkls](BLOCKED.md#xkls) |
| Korea Exchange | XKRX | ⛔ | global.krx.co.kr | [BLOCKED.md#xkrx](BLOCKED.md#xkrx) |
| Boursa Kuwait | XKUW | ⛔ | boursakuwait.com.kw | [#xkuw](docs/FETCHERS.md#xkuw), [BLOCKED.md#xkuw](BLOCKED.md#xkuw) |
| Bolsa de Valores de Lima | XLIM | ⛔ | bvl.com.pe | [BLOCKED.md#xlim](BLOCKED.md#xlim) |
| Euronext Lisbon | XLIS | ✅ | euronext.com | [#xlis](docs/FETCHERS.md#xlis) |
| Nasdaq Vilnius | XLIT | ✅ | nasdaqbaltic.com | [#xlit](docs/FETCHERS.md#xlit) |
| London Stock Exchange | XLON | ✅ | gov.uk | [#xlon](docs/FETCHERS.md#xlon) |
| Luxembourg Stock Exchange | XLUX | ✅ | luxse.com | [#xlux](docs/FETCHERS.md#xlux) |
| BME (Bolsa de Madrid) | XMAD | ✅ | bolsasymercados.es | [#xmad](docs/FETCHERS.md#xmad) |
| Malta Stock Exchange | XMAL | ✅ | borzamalta.com.mt | [#xmal](docs/FETCHERS.md#xmal) |
| Bolsa Mexicana de Valores | XMEX | ✅ | bmv.com.mx | [#xmex](docs/FETCHERS.md#xmex) |
| Moscow Exchange | XMOS | ✅ | moex.com | [#xmos](docs/FETCHERS.md#xmos) |
| Muscat Securities Market | XMUS | ⛔ | msx.om | [BLOCKED.md#xmus](BLOCKED.md#xmus) |
| Nairobi Securities Exchange | XNAI | ⛔ | nse.co.ke | [BLOCKED.md#xnai](BLOCKED.md#xnai) |
| NASDAQ | XNAS | ✅ | ir.theice.com | [#xnas](docs/FETCHERS.md#xnas) |
| Nigerian Exchange Group | XNSA | ⚠️ | ngxgroup.com | [#xnsa](docs/FETCHERS.md#xnsa), [BLOCKED.md#xnsa](BLOCKED.md#xnsa) |
| NSE India | XNSE | ⛔ | nseindia.com | [BLOCKED.md#xnse](BLOCKED.md#xnse) |
| New York Stock Exchange | XNYS | ✅ | ir.theice.com | [#xnys](docs/FETCHERS.md#xnys) |
| New Zealand Exchange | XNZE | ⛔ | nzx.com | [BLOCKED.md#xnze](BLOCKED.md#xnze) |
| Oslo Bors (Euronext Oslo) | XOSL | ✅ | euronext.com | [#xosl](docs/FETCHERS.md#xosl) |
| Euronext Paris | XPAR | ✅ | euronext.com | [#xpar](docs/FETCHERS.md#xpar) |
| Philippine Stock Exchange | XPHS | ⛔ | pse.com.ph | [BLOCKED.md#xphs](BLOCKED.md#xphs) |
| Prague Stock Exchange | XPRA | ✅ | pse.cz | [#xpra](docs/FETCHERS.md#xpra) |
| Nasdaq Riga | XRIS | ✅ | nasdaqbaltic.com | [#xris](docs/FETCHERS.md#xris) |
| Saudi Exchange (Tadawul) | XSAU | ⛔ | saudiexchange.sa | [#xsau](docs/FETCHERS.md#xsau), [BLOCKED.md#xsau](BLOCKED.md#xsau) |
| Singapore Exchange | XSES | ⛔ | sgx.com | [BLOCKED.md#xses](BLOCKED.md#xses) |
| Santiago Stock Exchange | XSGO | ⛔ | bolsadesantiago.com | [BLOCKED.md#xsgo](BLOCKED.md#xsgo) |
| Shenzhen Stock Exchange | XSHE | ✅ | szse.cn | [#xshe](docs/FETCHERS.md#xshe) |
| Shanghai Stock Exchange | XSHG | ⚠️ | english.sse.com.cn | [#xshg](docs/FETCHERS.md#xshg), [BLOCKED.md#xshg](BLOCKED.md#xshg) |
| Ho Chi Minh Stock Exchange | XSTC | ✅ | staticfile.hsx.vn | [#xstc](docs/FETCHERS.md#xstc) |
| Nasdaq Stockholm | XSTO | ✅ | nasdaq.com | [#xsto](docs/FETCHERS.md#xsto) |
| SIX Swiss Exchange | XSWX | ⛔ | six-group.com | [BLOCKED.md#xswx](BLOCKED.md#xswx) |
| Abu Dhabi Securities Exchange | XTAD | ⛔ | adx.ae | [BLOCKED.md#xtad](BLOCKED.md#xtad) |
| Taiwan Stock Exchange | XTAI | ⛔ | twse.com.tw | [BLOCKED.md#xtai](BLOCKED.md#xtai) |
| Nasdaq Tallinn | XTAL | ✅ | nasdaqbaltic.com | [#xtal](docs/FETCHERS.md#xtal) |
| Tokyo Stock Exchange | XTKS | ✅ | jpx.co.jp | [#xtks](docs/FETCHERS.md#xtks) |
| Toronto Stock Exchange | XTSE | ✅ | tsx.com | [#xtse](docs/FETCHERS.md#xtse) |
| Bourse de Tunis | XTUN | ⛔ | bvmt.com.tn | [BLOCKED.md#xtun](BLOCKED.md#xtun) |
| Warsaw Stock Exchange | XWAR | ✅ | gpw.pl | [#xwar](docs/FETCHERS.md#xwar) |
| Vienna Stock Exchange | XWBO | ✅ | wienerborse.at | [#xwbo](docs/FETCHERS.md#xwbo) |
| Zagreb Stock Exchange | XZAG | ✅ | zse.hr | [#xzag](docs/FETCHERS.md#xzag) |

Fetcher notes (source quirks, known limitations, expiring sources) are in [`docs/FETCHERS.md`](./docs/FETCHERS.md); the reasoning behind every blocked source is in [`BLOCKED.md`](./BLOCKED.md).

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

`regular_hours` is one object, or a list of objects with `effective_from` dates
for an exchange whose hours changed. The entry in force on a date is the latest
one whose `effective_from` is on or before it:

```json
"regular_hours": [
  {"effective_from": "1997-01-01", "open": "09:00", "close": "15:00"},
  {"effective_from": "2024-11-05", "open": "09:00", "close": "15:30"}
]
```

The wrappers read either form (`regular_hours_on(date)` returns the hours for a
day); `regular_hours` on an exchange is the hours in force now. The SQL, CSV and
Parquet exports and the `sessions` list carry the hours in force now only.

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