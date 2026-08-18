# Exchange Calendar Registry

**The world's most comprehensive open-source registry of global exchange trading calendars — 74 exchanges across 6 continents.**

One JSON file per exchange. Zero runtime dependencies. Four language wrappers.
Seventy-four exchanges. 5,300+ tests. 100% global coverage.

[![Validate](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/slimissa/exchange-calendar/actions/workflows/validate.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Schema Version](https://img.shields.io/badge/schema-1.0.0-green.svg)](./schema.json)
[![Registry Version](https://img.shields.io/badge/registry-2.0.0-orange.svg)](./CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-5300+-green.svg)](./tests/)
[![Exchanges](https://img.shields.io/badge/exchanges-74-blue.svg)](./exchanges/)
[![Coverage](https://img.shields.io/badge/coverage-6_continents-purple.svg)](./exchanges/)
[![Calendar Systems](https://img.shields.io/badge/calendar_systems-5-red.svg)](./docs/)

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
| Saturday-Sunday (Western) | 65 exchanges |
| Friday-Saturday (Islamic) | 9 exchanges (Saudi, UAE, Qatar, Bahrain, Kuwait, Oman, Egypt, Bangladesh) |

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

## Supported Exchanges (Abbreviated)

| MIC | Exchange | Region | Timezone |
|-----|----------|--------|----------|
| XNYS | New York Stock Exchange | North America | America/New_York |
| XNAS | NASDAQ | North America | America/New_York |
| XLON | London Stock Exchange | Europe | Europe/London |
| XPAR | Euronext Paris | Europe | Europe/Paris |
| XAMS | Euronext Amsterdam | Europe | Europe/Amsterdam |
| XBRU | Euronext Brussels | Europe | Europe/Brussels |
| XLIS | Euronext Lisbon | Europe | Europe/Lisbon |
| XETR | Deutsche Börse | Europe | Europe/Berlin |
| XSWX | SIX Swiss Exchange | Europe | Europe/Zurich |
| XTKS | Tokyo Stock Exchange | Asia | Asia/Tokyo |
| XHKG | Hong Kong Exchange | Asia | Asia/Hong_Kong |
| XSHG | Shanghai Stock Exchange | Asia | Asia/Shanghai |
| XSHE | Shenzhen Stock Exchange | Asia | Asia/Shanghai |
| XASX | Australian Securities Exchange | Oceania | Australia/Sydney |
| XSES | Singapore Exchange | Asia | Asia/Singapore |
| XBOM | Bombay Stock Exchange | India | Asia/Kolkata |
| XNSE | National Stock Exchange of India | India | Asia/Kolkata |
| XSAU | Saudi Tadawul | Middle East | Asia/Riyadh |
| XDFM | Dubai Financial Market | Middle East | Asia/Dubai |
| XTAD | Abu Dhabi Securities Exchange | Middle East | Asia/Dubai |
| XJSE | Johannesburg Stock Exchange | Africa | Africa/Johannesburg |
| XMOS | Moscow Exchange | Eurasia | Europe/Moscow |
| XBRV | BRVM (West Africa) | Africa | Africa/Abidjan |

*... 74 exchanges total. See [exchanges/](exchanges/) for the complete list.*

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

The registry handles **20+ distinct holiday models**:

| Model | Examples |
|-------|----------|
| US weekend adjustment | NYSE, NASDAQ, Toronto |
| UK substitute days | London |
| Japanese equinox | Tokyo |
| Chinese Golden Weeks | Shanghai, Shenzhen |
| Korean lunisolar | Korea |
| Hong Kong lunisolar | Hong Kong |
| Euronext open-on-civil | Paris, Amsterdam, Brussels, Lisbon |
| German no-substitutes | Deutsche Börse |
| Swiss no-substitutes | SIX |
| Nordic no-substitutes | Stockholm, Oslo, Copenhagen, Helsinki |
| Baltic no-substitutes | Vilnius, Riga, Tallinn |
| Islamic weekend | Saudi, UAE, Qatar, Bahrain, Kuwait |
| Orthodox Easter | Greece, Bulgaria, Russia |
| Buddhist holidays | Thailand, Sri Lanka |
| Hindu holidays | Sri Lanka, Malaysia, Singapore |
| Multi-day festivals | Chinese New Year, Eid, Songkran |
| ... and more | |

---

## Architecture

```
exchanges/*.json          The source of truth — 74 files
        │
        ▼
tools/validate.py         Validates schema + business logic
        │
        ▼
tools/generate_dates.py   Expands recurrence rules
        │
        ▼
tools/build.py            Produces calendar.json
        │
        ▼
wrappers/                 Language bindings
├── python/               pip install exchange-calendar-registry
├── javascript/           npm install exchange-calendar-registry
├── go/                   go get github.com/slimissa/exchange-calendar/wrappers/go
└── rust/                 cargo add exchange-calendar
```

---

## Testing

| Suite | Tests |
|-------|-------|
| Python — core tools | 215 |
| Python — exchange data | 3,200+ |
| Python — wrappers | 79 |
| JavaScript | 82 |
| Go | 72 |
| Rust | 78 |
| **Total** | **5,300+** |

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

## Adopted By

| Project | Status | How It Uses This Registry |
|---------|--------|--------------------------|
| **Las_shell** | 🚧 In progress | Market status, scheduling, prompt |
| **Tempus** | 🚧 In progress | `@market_context` type validation |

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for full text.

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
```
