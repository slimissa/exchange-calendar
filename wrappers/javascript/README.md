# exchange-calendar-registry (JavaScript)

JavaScript wrapper for the QuantOS exchange calendar registry.

A canonical, versioned, machine-readable registry of global exchange trading
calendars. This package provides an idiomatic JavaScript API for loading and
querying exchange calendars — market holidays, early closes, trading hours,
and session status.

## Features

- **Zero dependencies** — pure Node.js, only the standard library
- **Immutable API** — load once, query safely from multiple contexts
- **Case-insensitive lookups** — `registry.exchange("xnys")` works
- **Complete status model** — OPEN, CLOSED, EARLY_CLOSE, PRE_MARKET,
  AFTER_HOURS, LUNCH_BREAK
- **Date navigation** — next/previous trading day, skipping weekends and
  holidays
- **Iterable registry** — `for...of` support
- **Ground truth verified** — all data backed by 368 tests
- **Both CommonJS and ESM** — `require()` and `import` supported

## Installation

### From npm

```bash
npm install exchange-calendar-registry
```

### From source

```bash
git clone https://github.com/slimissa/exchange-calendar.git
cd exchange-calendar/wrappers/javascript
npm install
```

## Quick Start

```javascript
const { CalendarRegistry, SessionStatus } = require('exchange-calendar-registry');

// Load the registry (single JSON file)
const registry = new CalendarRegistry('calendar.json');

// Get an exchange by MIC code
const xnys = registry.exchange('XNYS');
console.log(xnys.toString());  // New York Stock Exchange (XNYS)

// Check if the market is open
console.log(xnys.isOpen('2025-07-03', '10:00'));   // true (before 13:00 early close)
console.log(xnys.isOpen('2025-07-03', '13:30'));   // false (after early close)

// Check holiday status
console.log(xnys.isHoliday('2025-07-04'));         // true (Independence Day)
console.log(xnys.isHoliday('2025-07-06'));         // true (Sunday)

// Get early close time
console.log(xnys.earlyCloseTime('2025-07-03'));    // "13:00"

// Get full session status
const status = xnys.statusAt('2025-07-03', '10:00');
console.log(status);                                // "open"
console.log(status === SessionStatus.OPEN);         // true

// Date navigation
console.log(xnys.nextTradingDay('2025-07-03'));     // "2025-07-07" (Monday)
console.log(xnys.previousTradingDay('2025-07-07')); // "2025-07-03" (Thursday)

// List all exchanges
for (const exchange of registry) {
    console.log(`${exchange.code}: ${exchange.name}`);
}

// Registry metadata
console.log(registry.exchangeCount);                // 2
console.log(registry.version);                      // "1.0.0"
console.log(registry.codes());                      // ['XLON', 'XNYS']
```

### ES Modules

```javascript
import { CalendarRegistry, SessionStatus } from 'exchange-calendar-registry';

const registry = new CalendarRegistry('calendar.json');
const xlon = registry.get('XLON');

console.log(xlon.isOpen('2025-12-24', '12:00'));    // true (before 12:30 close)
console.log(xlon.isOpen('2025-12-24', '12:45'));    // false (after early close)
```

## API Reference

### CalendarRegistry

| Method / Property | Description |
|-------------------|-------------|
| `new CalendarRegistry(path)` | Load registry from JSON file |
| `.exchange(code)` | Return Exchange or `null` (case-insensitive) |
| `.get(code)` | Return Exchange or throw |
| `.has(code)` | `true` if code exists |
| `.isExchange(code)` | Alias for `.has()` |
| `.listExchanges()` | Array of all Exchange objects, sorted by code |
| `.codes()` | Array of all MIC codes, sorted |
| `.names()` | Array of all exchange names, sorted |
| `.toJSON()` | Summary object with version, count, codes |
| `.toString()` | Human-readable summary |
| `.size` / `.length` | Number of exchanges |
| `for...of registry` | Iterate over exchanges |

### Exchange

| Method | Description |
|--------|-------------|
| `.isHoliday(dateStr)` | `true` if market fully closed (weekend/holiday) |
| `.isEarlyClose(dateStr)` | `true` if early close day |
| `.earlyCloseTime(dateStr)` | Early close time or `null` |
| `.statusAt(dateStr, timeStr)` | Full `SessionStatus` at a moment |
| `.isOpen(dateStr, timeStr?)` | `true` if trading (OPEN or EARLY_CLOSE) |
| `.nextTradingDay(dateStr)` | Next day that is not a holiday/weekend |
| `.previousTradingDay(dateStr)` | Previous day that is not a holiday/weekend |
| `.holidayCount(year?)` | Count of holidays, optional year filter |
| `.listHolidays(year?)` | Sorted array of holiday entries |
| `.toString()` | Human-readable: "New York Stock Exchange (XNYS)" |
| `.toJSON()` | Summary object |

### SessionStatus

| Value | Description |
|-------|-------------|
| `CLOSED` | `'closed'` — market closed |
| `PRE_MARKET` | `'pre_market'` — before regular hours |
| `OPEN` | `'open'` — regular trading hours |
| `EARLY_CLOSE` | `'early_close'` — early close, before close time |
| `AFTER_HOURS` | `'after_hours'` — after regular hours |
| `LUNCH_BREAK` | `'lunch_break'` — intraday break |

### SessionStatus Methods

| Method | Description |
|--------|-------------|
| `SessionStatus.fromString(str)` | Case-insensitive string → status |
| `SessionStatus.isTradingStatus(status)` | `true` for OPEN and EARLY_CLOSE |
| `SessionStatus.values()` | Array of all status strings |
| `SessionStatus.keys()` | Array of all status keys |
| `SessionStatus.isValid(value)` | `true` if valid status |

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

- `explicit` dates are hand-curated and source-verified
- `generated` dates are produced from recurrence rules
- Early closes are flagged with `status: "early_close"` and include
  `early_close_time`

## Supported Exchanges

| Code | Exchange | Timezone |
|------|----------|----------|
| `XNYS` | New York Stock Exchange | `America/New_York` |
| `XLON` | London Stock Exchange | `Europe/London` |

More exchanges are added continuously. See the
[registry repository](https://github.com/slimissa/exchange-calendar).

## Immutability

`CalendarRegistry` and `Exchange` objects are **immutable** after construction.
All internal state is private (using closure scope and private fields).
Objects can be safely shared across modules and contexts without additional
synchronization.

## Error Handling

| Situation | Behavior |
|-----------|----------|
| File not found | Throws `Error` |
| Invalid JSON | Throws `SyntaxError` |
| Invalid registry structure | Throws `Error` |
| Exchange not found (`get()`) | Throws `Error` with available codes |
| Exchange not found (`exchange()`) | Returns `null` |
| Invalid date format | Throws `Error` |
| Invalid time format | Throws `Error` |
| Unknown status string | Throws `Error` |
| Non-string argument | Throws `TypeError` |

## TypeScript Support

TypeScript definitions (`.d.ts`) are provided in `src/index.d.ts`.

```typescript
import { CalendarRegistry, Exchange, SessionStatus } from 'exchange-calendar-registry';

const registry: CalendarRegistry = new CalendarRegistry('calendar.json');
const xnys: Exchange | null = registry.exchange('XNYS');

if (xnys) {
    const status: string = xnys.statusAt('2025-07-07', '10:00');
    // ...
}
```

## Node.js Compatibility

| Node.js Version | Status |
|-----------------|--------|
| >= 14.0.0 | Full support |
| 12.x | Mostly works (untested) |
| < 12 | Not supported |

## License

Apache 2.0 — see [LICENSE](../LICENSE).

## Links

- [Registry repository](https://github.com/slimissa/exchange-calendar)
- [Bug reports](https://github.com/slimissa/exchange-calendar/issues)
- [Contributing guide](../CONTRIBUTING.md)
- [Python wrapper](../python/)