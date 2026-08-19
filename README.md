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

| Exchange | MIC | Status |
|----------|-----|--------|
| New York Stock Exchange | XNYS | ✅ Implemented |

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