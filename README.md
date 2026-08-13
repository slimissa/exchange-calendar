# Exchange Calendar Registry

**A canonical, versioned, machine-readable registry of global exchange trading calendars — 14 major exchanges across North America, Europe, and Asia-Pacific.**

One JSON file per exchange. Zero runtime dependencies. Four language wrappers.
Fourteen exchanges. 1,127 tests.

> **Coverage status:** this registry currently covers 14 of the world's major exchanges — all G7 markets, all G20 financial hubs, and the key Asia-Pacific exchanges. It does not yet include emerging market exchanges (India, Brazil, Turkey, Saudi Arabia) or smaller European venues. See [Coverage](#coverage) for the full v1.1.0 target list.

[![Validate](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Schema Version](https://img.shields.io/badge/schema-1.0.0-green.svg)](./schema.json)
[![Registry Version](https://img.shields.io/badge/registry-1.0.0-orange.svg)](./CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-1127-green.svg)](./tests/)

---

## Why?

Every trading system, quant library, and fintech app maintains its own exchange holiday list. They're often outdated, inconsistent, or just wrong. Some hardcode NYSE hours with no holiday awareness. Some scrape Wikipedia and miss observed days. Some include national holidays that exchanges don't actually observe.

**This project provides one versioned, schema-validated registry that any tool can depend on — instead of every project hand-rolling and hand-maintaining its own.** It covers the exchanges where the vast majority of global trading volume actually flows. It does not yet cover every exchange on earth. See [Coverage](#coverage).

- **Las_shell** uses it for market status detection, scheduling, and prompt display
- **Python quant libraries** use it for trading day calculation
- **Go trading systems** use it for order routing logic
- **Rust finance crates** use it for compile-time exchange verification
- **JavaScript fintech apps** use it for market hours display

The registry is language-agnostic by design. The JSON is the contract.

---

## Supported Exchanges

| MIC | Exchange | Region | Timezone | Lunch Break | Early Close |
|-----|----------|--------|----------|-------------|-------------|
| XNYS | New York Stock Exchange | North America | America/New_York | No | 13:00 |
| XNAS | NASDAQ | North America | America/New_York | No | 13:00 |
| XTSE | Toronto Stock Exchange | North America | America/Toronto | No | 13:00 |
| XLON | London Stock Exchange | Europe | Europe/London | No | 12:30 |
| XPAR | Euronext Paris | Europe | Europe/Paris | No | 14:05 |
| XETR | Deutsche Börse | Europe | Europe/Berlin | No | Full closures |
| XSWX | SIX Swiss Exchange | Europe | Europe/Zurich | No | Full closures |
| XMAD | Bolsa de Madrid | Europe | Europe/Madrid | No | 14:00 |
| XTKS | Tokyo Stock Exchange | Asia | Asia/Tokyo | 11:30–12:30 | None |
| XHKG | Hong Kong Exchange | Asia | Asia/Hong_Kong | 12:00–13:00 | 12:00 (eves) |
| XSHG | Shanghai Stock Exchange | Asia | Asia/Shanghai | 11:30–13:00 | None |
| XKRX | Korea Exchange | Asia | Asia/Seoul | No | None |
| XASX | Australian Securities Exchange | Oceania | Australia/Sydney | No | 14:10 |
| XSES | Singapore Exchange | Asia | Asia/Singapore | No | 12:30 (eves) |

---

## Coverage

**v1.0.0 includes 14 exchanges.** This is not exhaustive global coverage. It is the set of exchanges most trading, quant, and fintech systems actually need first: all G7 markets, all G20 financial hubs, and the key Asia-Pacific exchanges.

### Included in v1.0.0

- **North America:** NYSE, NASDAQ, Toronto Stock Exchange
- **Europe:** London Stock Exchange, Euronext Paris, Deutsche Börse, SIX Swiss Exchange, Bolsa de Madrid
- **Asia-Pacific:** Tokyo Stock Exchange, Hong Kong Exchange, Shanghai Stock Exchange, Korea Exchange, Australian Securities Exchange, Singapore Exchange

### Not yet included — targeted for v1.1.0

| Region | Exchanges |
|--------|-----------|
| India | XBOM (Bombay Stock Exchange), XNSE (National Stock Exchange of India) |
| Middle East | XSAU (Saudi Tadawul), XDFM (Dubai Financial Market), XTAE (Tel Aviv) |
| Latin America | XBSP (B3 São Paulo), XMEX (Mexican Stock Exchange) |
| Emerging Asia | XTAI (Taiwan Stock Exchange), XJKT (Indonesia Stock Exchange), XKLS (Bursa Malaysia), XPHS (Philippine Stock Exchange) |
| Africa | XJSE (Johannesburg Stock Exchange) |
| Eastern Europe | XIST (Borsa Istanbul), XWAR (Warsaw Stock Exchange) |
| Nordic | XSTO (Nasdaq Stockholm), XOSL (Oslo Børs), XCSE (Nasdaq Copenhagen), XHEL (Nasdaq Helsinki), XICE (Nasdaq Iceland) |
| Other Europe | XWBO (Vienna Stock Exchange), XDUB (Euronext Dublin) |
| Russia | XMOS (Moscow Exchange) — deferred due to sanctions |

This list is a planning target, not a commitment to exact scope or timing. If you need an exchange from this list today, open an issue or PR — see [Contributing](#contributing).

---

## Quick Start

### Build the registry

```bash
git clone https://github.com/slimissa/exchange-calendar.git
cd exchange-calendar

# Validate all exchange data
python3 tools/validate.py
# Output: OK: 14 exchange file(s) validated successfully

# Build the distribution artifact
python3 tools/build.py
# Output: OK: Built calendar.json with 14 exchange(s)

# Run all Python tests
python3 -m pytest tests/ -v
```

### Python

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

```bash
pip install exchange-calendar-registry
```

### JavaScript

```javascript
const { CalendarRegistry } = require('exchange-calendar-registry');

const registry = new CalendarRegistry('calendar.json');
const xlon = registry.get('XLON');

console.log(xlon.isOpen('2025-12-24', '12:00'));  // true (before 12:30 close)
console.log(xlon.isOpen('2025-12-24', '12:45'));  // false (after early close)
```

```bash
npm install exchange-calendar-registry
```

### Go

```go
package main

import (
    "fmt"
    "log"
    exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"
)

func main() {
    registry, err := exchangecalendar.LoadRegistry("calendar.json")
    if err != nil {
        log.Fatal(err)
    }

    xtks, _ := registry.Get("XTKS")
    status, _ := xtks.StatusAt("2025-07-07", "12:00")
    fmt.Println(status)  // "lunch_break"
}
```

```bash
go get github.com/slimissa/exchange-calendar/wrappers/go
```

### Rust

```rust
use exchange_calendar::Registry;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let registry = Registry::load("calendar.json")?;
    let xasx = registry.get("XASX")?;

    println!("{}", xasx.is_open("2025-12-24", Some("10:00")));  // true
    Ok(())
}
```

```bash
cargo add exchange-calendar
```

---

## Holiday Models

The registry handles 12 distinct holiday models across the world's exchanges:

| Model | Exchange | Key Feature |
|-------|----------|-------------|
| US weekend adjustment | XNYS, XNAS, XTSE | Saturday→Friday, Sunday→Monday |
| UK substitute days | XLON | Bank Holidays shift to Monday |
| Japanese equinox + Citizens' | XTKS | Astronomical dates, Kokumin no Kyūjitsu |
| Chinese Golden Weeks | XSHG | Spring Festival, National Day 7-8 days |
| Korean lunisolar + substitutes | XKRX | Seollal, Chuseok, Daeche Gonghyuil |
| Hong Kong lunisolar | XHKG | CNY, Buddha, Tuen Ng, Mid-Autumn |
| Euronext open-on-civil | XPAR, XMAD | Exchange trades on legal holidays |
| German no-substitutes | XETR | Kein Feiertagsausgleich |
| Swiss no-substitutes | XSWX | Berchtoldstag, no shifts |
| Australian weekend + ANZAC | XASX | Sunday→Monday, Saturday not shifted |
| Singapore multicultural | XSES | Chinese, Malay, Indian, Christian, Buddhist |
| Canadian Victoria Day rule | XTSE | Monday before May 25 (not last Monday) |

### Common Mistakes the Registry Prevents

1. **Weekend dates in explicit arrays** — the market is closed on weekends anyway. Including them is redundant.

2. **Civil holidays as market closures** — Euronext Paris is OPEN on Bastille Day. BME is OPEN on Epiphany. The registry models actual exchange calendars, not national holiday lists.

3. **Incorrect weekend observation** — Germany and Switzerland do NOT shift holidays from weekends. The US and Canada DO.

4. **Victoria Day miscalculation** — "Monday before May 25" is NOT the same as "last Monday of May" (2027: May 24, not May 31).

5. **Black Friday miscalculation** — "Day after 4th Thursday" is NOT "4th Friday" (they diverge in some years).

---

## Architecture

```
exchanges/*.json          The source of truth — one file per exchange
        │
        ▼
tools/validate.py         Validates schema + business logic + cross-exchange
        │
        ▼
tools/generate_dates.py   Expands recurrence rules into explicit dates
        │
        ▼
tools/build.py            Produces calendar.json (distribution artifact)
        │
        ▼
wrappers/                 Language bindings
├── python/               pip install exchange-calendar-registry
├── javascript/           npm install exchange-calendar-registry
├── go/                   go get github.com/slimissa/exchange-calendar/wrappers/go
└── rust/                 cargo add exchange-calendar
```

---

## Recurrence Rules

Five rule types generate future dates deterministically:

| Rule | Description | Example |
|------|-------------|---------|
| `fixed_date` | Same date every year, no shift | Dec 25 (Germany) |
| `fixed_with_weekend_adjustment` | Sat→Fri, Sun→Mon | Jan 1 (US), Jul 4 (US) |
| `nth_weekday` | Nth weekday of month | 3rd Monday Jan (MLK) |
| `last_weekday` | Last weekday of month | Last Monday May (Memorial) |
| `easter_offset` | Days relative to Easter Sunday | Good Friday (-2), Easter Monday (+1) |

**Explicit dates are always primary.** Recurrence rules are generation convenience — they never override hand-curated dates.

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

## Testing

| Suite | Tests | Coverage |
|-------|-------|----------|
| Python — core tools | 215 | Recurrence, validator, build |
| Python — exchange data | 563 | Ground truth per exchange |
| Python — wrappers | 79 | Wrapper API |
| JavaScript | 82 | Wrapper API |
| Go | 72 | Wrapper API |
| Rust | 78 | Wrapper API |
| **Total** | **1,127** | All passing in CI |

```bash
# Full Python suite
python3 -m pytest tests/ -v

# JavaScript
node --test tests/test_wrappers.js

# Go
cd wrappers/go && go test ./tests/ -v

# Rust
cd wrappers/rust && cargo test
```

CI runs all suites on every push and pull request via GitHub Actions.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Adding a new exchange
- Correcting holiday data
- Writing tests per language
- Code style
- Pull request process

Key rules:

1. Weekend dates never appear in explicit arrays
2. Every holiday entry must have a `source_url`
3. Civil holidays ≠ market closures (verify exchange calendar, not national list)
4. Victoria Day is "Monday before May 25" — not "last Monday of May"
5. Black Friday is "day after 4th Thursday" — not "4th Friday"
6. Germany and Switzerland do NOT observe substitute holidays

---

## Adopted By

| Project | How It Uses This Registry |
|---------|--------------------------|
| **Las_shell** *(planned)* | Market status detection, scheduling, prompt display |
| **Tempus** *(planned)* | `@market_context` annotation for trading-day validation |

*Using this registry in your project? Open a PR to add your name here.*

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for full text.

The exchange data in this registry is factual information sourced from official exchange calendars. The compilation, schema, tooling, and wrappers are licensed works.

Copyright 2026 **Le P'tit**

---

## Author

**Le P'tit** — [github.com/slimissa](https://github.com/slimissa)

---

## Links

- [GitHub Repository](https://github.com/slimissa/exchange-calendar)
- [Issue Tracker](https://github.com/slimissa/exchange-calendar/issues)
- [CHANGELOG.md](CHANGELOG.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

---