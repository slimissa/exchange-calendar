# Exchange Calendar Registry

**A canonical, versioned, machine-readable registry of global exchange trading calendars.**

One JSON file per exchange. Zero runtime dependencies. Four language wrappers.
Fourteen exchanges. 1,127 tests.

---

## Overview

The exchange-calendar registry is the definitive source of truth for global
exchange trading calendars — market holidays, early closes, lunch breaks,
auction sessions, and trading hours.

Unlike ad-hoc holiday lists or hardcoded date checks, this registry provides:

- **Verified data** — every holiday date is cross-checked against the official
  exchange calendar with source URLs
- **Machine-readable schema** — JSON Schema validation ensures data integrity
- **Recurrence rules** — deterministic generation of future holiday dates
- **Language wrappers** — idiomatic APIs for Python, JavaScript, Go, and Rust
- **Comprehensive tests** — 1,127 tests including ground truth verification

---

## Supported Exchanges

| MIC | Exchange | Region | Timezone | Lunch Break | Early Closes |
|-----|----------|--------|----------|-------------|--------------|
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

## Quick Start

### Build the registry

```bash
# Clone
git clone https://github.com/slimissa/exchange-calendar.git
cd exchange-calendar

# Validate all exchange data
python3 tools/validate.py

# Build the distribution artifact
python3 tools/build.py
# Produces calendar.json containing all 14 exchanges

# Run all tests
python3 -m pytest tests/ -v
```

### Python

```python
from exchange_calendar import CalendarRegistry, SessionStatus

registry = CalendarRegistry("calendar.json")
xnys = registry.exchange("XNYS")

if xnys.is_open("2025-07-03", "10:00"):
    print("NYSE is open")  # Before 13:00 early close

print(xnys.early_close_time("2025-07-03"))  # "13:00"
print(xnys.is_holiday("2025-07-04"))        # True (Independence Day)
print(xnys.next_trading_day("2025-07-03"))  # "2025-07-07"
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

    xtks := registry.Get("XTKS")
    fmt.Println(xtks.IsOpen("2025-07-07", "12:00"))  // false (lunch break)
}
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

### Data Flow

```
Source Exchange Calendar (official website)
        │
        ▼
exchanges/XXXX.json       Hand-curated explicit dates + recurrence rules
        │
        ▼
calendar.json             Built artifact (validated, merged, sorted)
        │
        ▼
Language Wrappers         Consumer APIs
```

---

## Holiday Models

The registry handles 12 distinct holiday models:

| Model | Example | Key Feature |
|-------|---------|-------------|
| US weekend adjustment | XNYS, XNAS, XTSE | Sat→Fri, Sun→Mon |
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

---

## Recurrence Rules

Five rule types generate future dates deterministically:

| Rule | Description | Example |
|------|-------------|---------|
| `fixed_date` | Same date every year, no shift | Dec 25 |
| `fixed_with_weekend_adjustment` | Sat→Fri, Sun→Mon | Jan 1, Jul 4 |
| `nth_weekday` | Nth weekday of month | 3rd Monday Jan (MLK) |
| `last_weekday` | Last weekday of month | Last Monday May (Memorial) |
| `easter_offset` | Days relative to Easter Sunday | Good Friday (-2), Easter Monday (+1) |

**Explicit dates are always primary.** Recurrence rules are generation
convenience — they never override hand-curated dates.

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
| **Total** | **1,127** | All passing |

Run:

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

CI runs all suites on every push and pull request.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Adding a new exchange
- Correcting holiday data
- Writing tests
- Code style per language
- Pull request process

Key rules:

1. Weekend dates never appear in explicit arrays
2. Every holiday entry must have a `source_url`
3. Civil holidays ≠ market closures (verify exchange calendar, not national list)
4. Victoria Day is "Monday before May 25" — not "last Monday of May"
5. Black Friday is "day after 4th Thursday" — not "4th Friday"

---

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — version history
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution guidelines
- [docs/](docs/) — exchange schema, recurrence rules, integration specs

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for full text.

Copyright 2026 Le P'tit

---

## Links

- [GitHub Repository](https://github.com/slimissa/exchange-calendar)
- [Issue Tracker](https://github.com/slimissa/exchange-calendar/issues)
- [Python Package](https://pypi.org/project/exchange-calendar-registry/)
- [npm Package](https://www.npmjs.com/package/exchange-calendar-registry)
- [crates.io](https://crates.io/crates/exchange-calendar)

---
