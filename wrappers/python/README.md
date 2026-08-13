# exchange-calendar (Python)

Python wrapper for the QuantOS exchange calendar registry.

A canonical, versioned, machine-readable registry of global exchange trading
calendars. This package provides an idiomatic Python API for loading and
querying exchange calendars — market holidays, early closes, trading hours,
and session status.

## Features

- **Zero dependencies** — pure Python, only the standard library
- **Immutable API** — load once, query safely from multiple threads
- **Type hints** — full typing coverage for IDE support and static analysis
- **Case-insensitive lookups** — `registry.exchange("xnys")` works
- **Complete status model** — OPEN, CLOSED, EARLY_CLOSE, PRE_MARKET,
  AFTER_HOURS, LUNCH_BREAK
- **Date navigation** — next/previous trading day, skipping weekends and
  holidays
- **Ground truth verified** — all data backed by 289 tests

## Installation

### From PyPI (recommended)

```bash
pip install exchange-calendar
```

### From source

```bash
git clone https://github.com/slimissa/exchange-calendar.git
cd exchange-calendar/wrappers/python
pip install .
```

## Quick Start

```python
from exchange_calendar import CalendarRegistry, SessionStatus

# Load the registry (single JSON file)
registry = CalendarRegistry("calendar.json")

# Get an exchange by MIC code
xnys = registry.exchange("XNYS")
print(xnys)  # New York Stock Exchange (XNYS)

# Check if the market is open
print(xnys.is_open("2025-07-03", "10:00"))   # True (before 13:00 early close)
print(xnys.is_open("2025-07-03", "13:30"))   # False (after early close)

# Check holiday status
print(xnys.is_holiday("2025-07-04"))         # True (Independence Day)
print(xnys.is_holiday("2025-07-06"))         # True (Sunday)

# Get early close time
print(xnys.early_close_time("2025-07-03"))   # "13:00"

# Get full session status
status = xnys.status_at("2025-07-03", "10:00")
print(status)                                # SessionStatus.OPEN
print(status == SessionStatus.OPEN)          # True

# Date navigation
print(xnys.next_trading_day("2025-07-03"))   # "2025-07-07" (Monday)
print(xnys.previous_trading_day("2025-07-07"))  # "2025-07-03" (Thursday)

# List all exchanges
for exchange in registry.list_exchanges():
    print(f"{exchange.code}: {exchange.name}")

# Registry metadata
print(registry.exchange_count)               # 2
print(registry.version)                      # "1.0.0"
print(registry.codes())                      # ['XLON', 'XNYS']
```

## API Reference

### CalendarRegistry

| Method | Description |
|--------|-------------|
| `CalendarRegistry(path="calendar.json")` | Load the registry from a JSON file |
| `.exchange(code)` | Return Exchange or `None` (case-insensitive) |
| `.get(code)` | Return Exchange or raise `KeyError` |
| `.list_exchanges()` | List of all Exchange objects, sorted by code |
| `.codes()` | List of all MIC codes, sorted |
| `.names()` | List of all exchange names, sorted by code |
| `.is_exchange(code)` | `True` if code exists |
| `.to_dict()` | Summary dict with version, count, codes |
| `len(registry)` | Number of exchanges |
| `"XNYS" in registry` | Membership test |
| `for ex in registry:` | Iterate over exchanges |

### Exchange

| Method | Description |
|--------|-------------|
| `.is_holiday(date_str)` | `True` if market fully closed (weekend or holiday) |
| `.is_early_close(date_str)` | `True` if early close day |
| `.early_close_time(date_str)` | Early close time or `None` |
| `.status_at(date_str, time_str)` | Full `SessionStatus` at a moment |
| `.is_open(date_str, time_str="10:00")` | `True` if trading (OPEN or EARLY_CLOSE) |
| `.next_trading_day(date_str)` | Next day that is not a holiday/weekend |
| `.previous_trading_day(date_str)` | Previous day that is not a holiday/weekend |
| `.holiday_count(year=None)` | Count of explicit holidays, optional year filter |
| `.list_holidays(year=None)` | Sorted list of holiday entries |

### SessionStatus

| Value | Description |
|-------|-------------|
| `CLOSED` | Market closed (weekend, holiday, after close) |
| `PRE_MARKET` | Before regular hours (extended session) |
| `OPEN` | Regular trading hours |
| `EARLY_CLOSE` | Early close day, before close time |
| `AFTER_HOURS` | After regular hours (extended session) |
| `LUNCH_BREAK` | Intraday break (e.g., Tokyo lunch) |

## Data Format

The registry is a single JSON file (`calendar.json`) with this structure:

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
        "explicit": [ ... ],
        "generated": [ ... ]
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

| Code | Exchange | Timezone | Holiday Count (2025-2029) |
|------|----------|----------|---------------------------|
| `XNYS` | New York Stock Exchange | `America/New_York` | 62 |
| `XLON` | London Stock Exchange | `Europe/London` | 50 |

More exchanges are added continuously. See the
[registry repository](https://github.com/slimissa/exchange-calendar) for the
latest list.

## Thread Safety

`CalendarRegistry` and `Exchange` objects are **immutable** after construction.
All methods perform read-only operations on internal dictionaries. It is safe
to share a single `CalendarRegistry` instance across multiple threads without
additional locking.

## Error Handling

| Situation | Behavior |
|-----------|----------|
| File not found | Raises `FileNotFoundError` |
| Invalid JSON | Raises `json.JSONDecodeError` |
| Invalid registry structure | Raises `ValueError` |
| Exchange not found (`get()`) | Raises `KeyError` |
| Exchange not found (`exchange()`) | Returns `None` |
| Invalid date format | Raises `ValueError` |
| Invalid time format | Raises `ValueError` |
| Unknown status string | Raises `ValueError` |

## Type Hints

The package includes full type hints. Use with `mypy`:

```bash
mypy exchange_calendar/
```

## License

Apache 2.0 — see [LICENSE](../LICENSE).

## Links

- [Registry repository](https://github.com/slimissa/exchange-calendar)
- [Bug reports](https://github.com/slimissa/exchange-calendar/issues)
- [Contributing guide](../CONTRIBUTING.md)
```

---

## What this covers

- Installation from PyPI and source
- Quick start with 10+ copy-paste examples
- Complete API reference for all 3 public classes
- Data format documentation
- Thread safety guarantee
- Error handling table
- Type hints note
- License and links

---