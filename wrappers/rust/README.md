# exchange-calendar (Rust)

Rust wrapper for the QuantOS exchange calendar registry.

A canonical, versioned, machine-readable registry of global exchange trading
calendars. This crate provides an idiomatic Rust API for loading and querying
exchange calendars — market holidays, early closes, trading hours, and
session status.

## Features

- **Type-safe enums** — `SessionStatus` is a proper Rust enum, not a string
- **Immutable structs** — safe to share across threads (`Send + Sync`)
- **Case-insensitive lookups** — `registry.exchange("xnys")` works
- **Complete status model** — 6 session states with `is_trading()` helpers
- **Date navigation** — next/previous trading day using `chrono`
- **Serde support** — all data types derive `Serialize` and `Deserialize`
- **Rich error types** — `ExchangeError`, `QueryError`, `RegistryError`
- **Zero runtime deps** — only `serde`, `serde_json`, and `chrono`
- **Ground truth verified** — 78 tests (65 unit + 13 doc)

## Installation

Add to your `Cargo.toml`:

```toml
[dependencies]
exchange-calendar = "1.0.0"
```

Or from GitHub:

```toml
[dependencies]
exchange-calendar = { git = "https://github.com/slimissa/exchange-calendar", subdir = "wrappers/rust" }
```

## Quick Start

```rust
use exchange_calendar::{Registry, SessionStatus};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load the registry
    let registry = Registry::load("calendar.json")?;

    // Get an exchange by MIC code (case-insensitive)
    let xnys = registry.get("XNYS")?;
    println!("{}", xnys);  // New York Stock Exchange (XNYS)

    // Check if the market is open
    assert!(xnys.is_open("2025-07-07", Some("10:00")));
    assert!(!xnys.is_open("2025-07-04", Some("10:00")));  // Independence Day
    assert!(!xnys.is_open("2025-07-05", Some("10:00")));  // Saturday

    // Check holiday status
    assert!(xnys.is_holiday("2025-07-04"));   // Independence Day
    assert!(xnys.is_holiday("2025-07-06"));   // Sunday
    assert!(!xnys.is_holiday("2025-07-03"));  // Early close, not full holiday

    // Get early close time
    assert_eq!(xnys.early_close_time("2025-07-03"), Some("13:00"));
    assert_eq!(xnys.early_close_time("2025-07-04"), None);

    // Get full session status
    let status = xnys.status_at("2025-07-07", "10:00")?;
    assert_eq!(status, SessionStatus::Open);

    let status = xnys.status_at("2025-07-03", "10:00")?;
    assert_eq!(status, SessionStatus::EarlyClose);

    let status = xnys.status_at("2025-07-03", "13:30")?;
    assert_eq!(status, SessionStatus::Closed);

    // Date navigation
    let next = xnys.next_trading_day("2025-07-03")?;
    assert_eq!(next, "2025-07-07");  // Monday

    let prev = xnys.previous_trading_day("2025-07-07")?;
    assert_eq!(prev, "2025-07-03");  // Thursday

    // List all exchanges
    for exchange in registry.list_exchanges() {
        println!("{}: {}", exchange.code, exchange.name);
    }

    // Registry metadata
    println!("Version: {}", registry.version);
    println!("Exchange count: {}", registry.len());
    println!("Codes: {:?}", registry.codes());

    Ok(())
}
```

## API Reference

### Registry

```rust
impl Registry {
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, RegistryError>;
    pub fn from_str(json: &str) -> Result<Self, RegistryError>;
    pub fn from_data(data: RegistryData) -> Result<Self, RegistryError>;

    pub fn exchange(&self, code: &str) -> Option<&Exchange>;
    pub fn get(&self, code: &str) -> Result<&Exchange, RegistryError>;
    pub fn has(&self, code: &str) -> bool;

    pub fn codes(&self) -> Vec<String>;
    pub fn names(&self) -> Vec<String>;
    pub fn list_exchanges(&self) -> Vec<&Exchange>;

    pub fn len(&self) -> usize;
    pub fn is_empty(&self) -> bool;
}
```

### Exchange

```rust
impl Exchange {
    pub fn new(data: ExchangeData) -> Result<Self, ExchangeError>;

    pub fn is_holiday(&self, date: &str) -> bool;
    pub fn is_early_close(&self, date: &str) -> bool;
    pub fn early_close_time(&self, date: &str) -> Option<&str>;

    pub fn status_at(&self, date: &str, time: &str) -> Result<SessionStatus, QueryError>;
    pub fn is_open(&self, date: &str, time: Option<&str>) -> bool;

    pub fn next_trading_day(&self, date: &str) -> Result<String, QueryError>;
    pub fn previous_trading_day(&self, date: &str) -> Result<String, QueryError>;

    pub fn holiday_count(&self, year: Option<i32>) -> usize;
    pub fn list_holidays(&self, year: Option<i32>) -> Vec<&HolidayEntry>;
}
```

### SessionStatus

```rust
pub enum SessionStatus {
    Closed,
    PreMarket,
    Open,
    EarlyClose,
    AfterHours,
    LunchBreak,
}

impl SessionStatus {
    pub fn as_str(&self) -> &'static str;
    pub fn is_trading(&self) -> bool;
    pub fn is_non_trading(&self) -> bool;
    pub fn all() -> [SessionStatus; 6];
    pub fn trading_statuses() -> [SessionStatus; 2];
    pub fn non_trading_statuses() -> [SessionStatus; 4];
    pub fn parse(s: &str) -> Result<Self, ParseSessionStatusError>;
    pub fn must_parse(s: &str) -> Self;
}
```

### SessionStatus Variants

| Variant | `as_str()` | Description |
|---------|-----------|-------------|
| `Closed` | `"closed"` | Market closed (weekend/holiday/outside hours) |
| `PreMarket` | `"pre_market"` | Before regular hours |
| `Open` | `"open"` | Regular trading hours |
| `EarlyClose` | `"early_close"` | Early close day, before close time |
| `AfterHours` | `"after_hours"` | After regular hours |
| `LunchBreak` | `"lunch_break"` | Intraday break (e.g., Tokyo lunch) |

### Error Types

| Error | Description |
|-------|-------------|
| `ExchangeError` | Construction failures (missing fields, code/MIC mismatch, invalid time) |
| `QueryError` | Invalid date/time format, no trading day found |
| `RegistryError` | File not found, invalid JSON, duplicate codes, exchange not found |
| `ParseSessionStatusError` | Unknown status string |

All error types implement `std::error::Error`.

## Data Format

The registry is a single JSON file (`calendar.json`):

```json
{
  "meta": {
    "version": "1.0.0",
    "exchange_count": 2
  },
  "exchanges": [
    {
      "code": "XNYS",
      "name": "New York Stock Exchange",
      "mic": "XNYS",
      "timezone": "America/New_York",
      "regular_hours": { "open": "09:30", "close": "16:00" },
      "holidays": {
        "explicit": [],
        "generated": []
      }
    }
  ]
}
```

All structs derive `Serialize` and `Deserialize` — you can deserialize
`calendar.json` directly into `RegistryData` and then construct a `Registry`
from it.

## Supported Exchanges

| Code | Exchange | Timezone |
|------|----------|----------|
| `XNYS` | New York Stock Exchange | `America/New_York` |
| `XLON` | London Stock Exchange | `Europe/London` |

## Thread Safety

`Registry` and `Exchange` are **immutable** after construction. All public
fields are read-only. Both types are `Send + Sync`, meaning they can be
safely shared across threads.

```rust
use std::sync::Arc;
use std::thread;

let registry = Arc::new(Registry::load("calendar.json").unwrap());

let handles: Vec<_> = (0..4).map(|_| {
    let reg = Arc::clone(&registry);
    thread::spawn(move || {
        let xnys = reg.get("XNYS").unwrap();
        assert!(xnys.is_open("2025-07-07", Some("10:00")));
    })
}).collect();

for handle in handles {
    handle.join().unwrap();
}
```

## Traits Implemented

| Trait | Type | Purpose |
|-------|------|---------|
| `Debug` | All types | Debugging |
| `Clone` | All types | Cloning |
| `PartialEq`, `Eq` | All types | Comparison |
| `Hash` | `SessionStatus` | HashMap keys |
| `PartialOrd`, `Ord` | `SessionStatus` | Sorting |
| `Display` | `SessionStatus`, `Exchange`, `Registry`, errors | String output |
| `FromStr` | `SessionStatus` | `"open".parse()` |
| `From<SessionStatus> for String` | `SessionStatus` | `String::from(status)` |
| `AsRef<str>` | `SessionStatus` | `status.as_ref()` |
| `IntoIterator` | `Registry`, `&Registry` | `for exchange in &registry` |
| `std::error::Error` | All error types | `?` operator |

## MSRV (Minimum Supported Rust Version)

Rust 1.74 or later (edition 2021).

## License

Apache 2.0 — see [LICENSE](../../LICENSE).

## Links

- [Registry repository](https://github.com/slimissa/exchange-calendar)
- [Bug reports](https://github.com/slimissa/exchange-calendar/issues)
- [Python wrapper](../python/)
- [JavaScript wrapper](../javascript/)
- [Go wrapper](../go/)



