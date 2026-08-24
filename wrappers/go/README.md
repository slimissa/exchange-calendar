# exchange-calendar (Go)

Go wrapper for the QuantOS exchange calendar registry.

A canonical, versioned, machine-readable registry of global exchange trading
calendars. This package provides an idiomatic Go API for loading and querying
exchange calendars — market holidays, early closes, trading hours, and
session status.

## Features

- **Zero runtime dependencies** — standard library only
- **Idiomatic Go** — errors as values, variadic optional parameters
- **Immutable** — all structs read-only after construction
- **Case-insensitive lookups** — `registry.Exchange("xnys")` works
- **Complete status model** — 6 session states via `SessionStatus` type
- **Date navigation** — next/previous trading day, skipping weekends and holidays
- **Thread-safe** — immutable structs can be shared across goroutines
- **Ground truth verified** — all data backed by 72 Go tests

## Installation

```bash
go get github.com/slimissa/exchange-calendar/wrappers/go
```

## Quick Start

```go
package main

import (
	"fmt"
	"log"

	exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"
)

func main() {
	// Load the registry
	registry, err := exchangecalendar.LoadRegistry("calendar.json")
	if err != nil {
		log.Fatal(err)
	}

	// Get an exchange by MIC code
	xnys, err := registry.Get("XNYS")
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(xnys.String()) // New York Stock Exchange (XNYS)

	// Check if the market is open
	fmt.Println(xnys.IsOpen("2025-07-03", "10:00")) // true (before 13:00 early close)
	fmt.Println(xnys.IsOpen("2025-07-03", "13:30")) // false (after early close)

	// Check holiday status
	fmt.Println(xnys.IsHoliday("2025-07-04"))  // true (Independence Day)
	fmt.Println(xnys.IsHoliday("2025-07-06"))  // true (Sunday)

	// Get early close time
	fmt.Println(xnys.EarlyCloseTime("2025-07-03")) // "13:00"

	// Get full session status
	status, err := xnys.StatusAt("2025-07-03", "10:00")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(status)                          // "early_close"
	fmt.Println(status == exchangecalendar.StatusEarlyClose) // true

	// Date navigation
	next, _ := xnys.NextTradingDay("2025-07-03")
	fmt.Println(next) // "2025-07-07" (Monday)

	prev, _ := xnys.PreviousTradingDay("2025-07-07")
	fmt.Println(prev) // "2025-07-03" (Thursday)

	// List all exchanges
	for _, exchange := range registry.ListExchanges() {
		fmt.Printf("%s: %s\n", exchange.Code, exchange.Name)
	}

	// Registry metadata
	fmt.Println(registry.Version)       // "1.0.0"
	fmt.Println(registry.ExchangeCount) // 2
	fmt.Println(registry.Codes())       // ["XLON", "XNYS"]
}
```

## API Reference

### Registry

| Method | Description |
|--------|-------------|
| `LoadRegistry(path string) (*Registry, error)` | Load from JSON file |
| `MustLoadRegistry(path string) *Registry` | Load or panic |
| `NewRegistry(data registryData) (*Registry, error)` | From parsed JSON |
| `.Exchange(code string) *Exchange` | Return exchange or `nil` (case-insensitive) |
| `.Get(code string) (*Exchange, error)` | Return exchange or error |
| `.Has(code string) bool` | `true` if code exists |
| `.Codes() []string` | All MIC codes, sorted |
| `.Names() []string` | All exchange names, sorted by code |
| `.ListExchanges() []*Exchange` | All exchanges, sorted |
| `.Len() int` | Number of exchanges |
| `.String() string` | Human-readable summary |

### Exchange

| Method | Description |
|--------|-------------|
| `NewExchange(data ExchangeData) (*Exchange, error)` | Create from data |
| `MustNewExchange(data ExchangeData) *Exchange` | Create or panic |
| `.IsHoliday(dateStr string) bool` | `true` if fully closed (weekend/holiday) |
| `.IsEarlyClose(dateStr string) bool` | `true` if early close day |
| `.EarlyCloseTime(dateStr string) string` | Time or empty string |
| `.StatusAt(dateStr, timeStr string) (SessionStatus, error)` | Full status |
| `.IsOpen(dateStr string, timeStrs ...string) bool` | `true` if trading |
| `.NextTradingDay(dateStr string) (string, error)` | Next trading day |
| `.PreviousTradingDay(dateStr string) (string, error)` | Previous trading day |
| `.HolidayCount(year ...int) int` | Count, optional year filter |
| `.ListHolidays(year ...int) []HolidayEntry` | Sorted entries |
| `.String() string` | Human-readable |

### SessionStatus

| Constant | Value |
|----------|-------|
| `StatusClosed` | `"closed"` |
| `StatusPreMarket` | `"pre_market"` |
| `StatusOpen` | `"open"` |
| `StatusEarlyClose` | `"early_close"` |
| `StatusAfterHours` | `"after_hours"` |
| `StatusLunchBreak` | `"lunch_break"` |

### SessionStatus Methods

| Method | Description |
|--------|-------------|
| `.String() string` | String value |
| `.IsValid() bool` | `true` for defined constants |
| `.IsTradingStatus() bool` | `true` for OPEN and EARLY_CLOSE |
| `ParseSessionStatus(s string) (SessionStatus, error)` | Case-insensitive parse |
| `MustParseSessionStatus(s string) SessionStatus` | Parse or panic |

### Package-level Helpers

| Function | Description |
|----------|-------------|
| `AllSessionStatuses() []SessionStatus` | All 6 statuses |
| `TradingStatuses() []SessionStatus` | OPEN, EARLY_CLOSE |
| `NonTradingStatuses() []SessionStatus` | CLOSED, PRE_MARKET, AFTER_HOURS, LUNCH_BREAK |

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

## Supported Exchanges

| Code | Exchange | Timezone |
|------|----------|----------|
| `XNYS` | New York Stock Exchange | `America/New_York` |
| `XLON` | London Stock Exchange | `Europe/London` |

## Thread Safety

`Registry` and `Exchange` are **immutable** after construction. All exported
fields are read-only by convention. It is safe to share a single `*Registry`
across multiple goroutines without additional synchronization.

## Error Handling

| Situation | Behavior |
|-----------|----------|
| File not found | Returns `error` |
| Invalid JSON | Returns `error` |
| Invalid registry structure | Returns `error` |
| Exchange not found (`Get()`) | Returns `error` |
| Exchange not found (`Exchange()`) | Returns `nil` |
| Invalid date format | Returns `error` |
| Invalid time format | Returns `error` |
| Unknown status string | Returns `error` |

## Go Version

Requires Go 1.21 or later.

## License

Apache 2.0 — see [LICENSE](../../LICENSE).

## Links

- [Registry repository](https://github.com/slimissa/exchange-calendar)
- [Bug reports](https://github.com/slimissa/exchange-calendar/issues)
- [Python wrapper](../python/)
- [JavaScript wrapper](../javascript/)
```