# Exchange Schema Documentation

This document describes the JSON Schema used by the exchange-calendar registry.
Every exchange file in `exchanges/` must conform to this schema.

**Schema file:** [`schema.json`](../schema.json)  
**Version:** 1.0.0  
**Format:** JSON Schema Draft 7

---

## Table of Contents

- [Top-Level Structure](#top-level-structure)
- [Required Fields](#required-fields)
- [Optional Fields](#optional-fields)
- [Field Reference](#field-reference)
- [Conditional Validation](#conditional-validation)
- [Validation Examples](#validation-examples)
- [Common Errors](#common-errors)

---

## Top-Level Structure

Every exchange file is a JSON object with this shape:

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
    "explicit": [],
    "recurrence_rules": []
  },
  "ad_hoc_closures": [],
  "generation_range": ["2025-01-01", "2029-12-31"]
}
```

---

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | MIC code, 4 uppercase alphanumeric characters |
| `name` | string | Full exchange name, minimum 3 characters |
| `mic` | string | ISO 10383 MIC, must equal `code` |
| `timezone` | string | IANA timezone identifier |
| `regular_hours` | object | `{open, close}` — regular trading hours |
| `holidays` | object | `{explicit, recurrence_rules}` — holiday data |
| `generation_range` | array | `[start_date, end_date]` — verified date range |

---

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `extended_hours` | object | Pre-market and after-hours sessions |
| `sessions` | array | Lunch breaks and auction moments |
| `ad_hoc_closures` | array | Unplanned closures with source URLs |

---

## Field Reference

### `code`

The MIC code identifying the exchange.

```json
"code": "XNYS"
```

**Constraints:**
- Exactly 4 characters
- Uppercase letters A-Z and digits 0-9 only
- Must match the filename (e.g., `XNYS.json` has `"code": "XNYS"`)
- Must equal `mic`

**Examples:**
| Exchange | code |
|----------|------|
| New York Stock Exchange | `XNYS` |
| London Stock Exchange | `XLON` |
| Tokyo Stock Exchange | `XTKS` |

---

### `name`

The full official exchange name.

```json
"name": "New York Stock Exchange"
```

**Constraints:**
- Minimum 3 characters
- Use the exchange's official English name

---

### `mic`

The ISO 10383 Market Identifier Code. Must equal `code`.

```json
"mic": "XNYS"
```

**Why both `code` and `mic`?**  
They are always identical in this registry. The duplication exists because:
1. The filename is the MIC (`XNYS.json`)
2. The `code` field is the primary identifier used in lookups
3. The `mic` field is explicitly documented for ISO 10383 compliance

---

### `timezone`

IANA timezone identifier.

```json
"timezone": "America/New_York"
```

**Constraints:**
- Must contain a slash (`Continent/City`)
- Valid IANA identifiers include:
  - `America/New_York`
  - `Europe/London`
  - `Asia/Tokyo`
  - `Australia/Sydney`
  - `Etc/GMT+5`
  - `America/Port-au-Prince` (hyphen in city name)

**Pattern:**
```
^[A-Za-z0-9_+\-]+/[A-Za-z0-9_+\-]+(?:/[A-Za-z0-9_+\-]+)?$
```

This handles:
- Standard format: `Continent/City`
- Three-segment: `America/Argentina/Buenos_Aires`
- UTC offsets: `Etc/GMT+5`
- Hyphenated cities: `America/Port-au-Prince`

---

### `regular_hours`

```json
"regular_hours": {
  "open": "09:30",
  "close": "16:00"
}
```

**Both fields are required.**

| Field | Type | Pattern | Description |
|-------|------|---------|-------------|
| `open` | string | `HH:MM` | Market opening time |
| `close` | string | `HH:MM` | Market closing time |

**Time format:** 24-hour, zero-padded.

```json
{"open": "09:00", "close": "17:30"}   // Euronext Paris
{"open": "09:30", "close": "16:00"}   // NYSE
{"open": "10:00", "close": "16:00"}   // ASX
```

**Validation:** `open` must be before `close`. The validator rejects:

```json
{"open": "17:00", "close": "09:00"}   // INVALID
```

---

### `extended_hours` (Optional)

```json
"extended_hours": {
  "pre_market": {"open": "04:00", "close": "09:30"},
  "after_hours": {"open": "16:00", "close": "20:00"}
}
```

Both sub-objects follow the same `{open, close}` format as `regular_hours`.

**Exchanges with extended hours:**

| Exchange | Pre-market | After-hours |
|----------|-----------|-------------|
| XNYS | 04:00–09:30 | 16:00–20:00 |
| XNAS | 04:00–09:30 | 16:00–20:00 |
| XTSE | 07:00–09:30 | 16:00–17:00 |

**Exchanges WITHOUT extended hours:**

| Exchange | Why |
|----------|-----|
| XTKS | No US-style extended sessions |
| XHKG | Brief auction periods, not extended trading |
| XKRX | No extended equity sessions |

**Omit the entire `extended_hours` field if the exchange doesn't have it.**

---

### `sessions` (Optional)

Array of non-trading periods within a regular day.

```json
"sessions": [
  {
    "type": "lunch_break",
    "open": "11:30",
    "close": "12:30"
  },
  {
    "type": "auction",
    "at": "09:25"
  }
]
```

#### Session Types

| Type | Fields | Description |
|------|--------|-------------|
| `lunch_break` | `open`, `close` | Midday trading pause |
| `auction` | `at` | Point-in-time auction moment |

#### Lunch Break Sessions

```json
{"type": "lunch_break", "open": "11:30", "close": "12:30"}
```

| Exchange | Lunch Break |
|----------|-------------|
| XTKS (Tokyo) | 11:30–12:30 |
| XHKG (Hong Kong) | 12:00–13:00 |
| XSHG (Shanghai) | 11:30–13:00 |

**Exchanges WITHOUT lunch breaks (continuous trading):**

| Exchange | Notes |
|----------|-------|
| XNYS, XNAS, XTSE | US markets — continuous |
| XLON, XPAR, XETR, XSWX, XMAD | European — continuous |
| XKRX (Korea) | Continuous since 2017 |
| XSES (Singapore) | Continuous since 2017 |
| XASX (Australia) | Continuous |

#### Auction Sessions

```json
{"type": "auction", "at": "09:25"}
```

Auction moments represent the uncrossing time of opening or closing auctions.

| Exchange | Opening Auction | Closing Auction |
|----------|-----------------|-----------------|
| XHKG | 09:20 | 16:10 |
| XSHG | 09:25 | — |
| XTKS | 09:00 | 15:30 |

---

### `holidays`

```json
"holidays": {
  "explicit": [],
  "recurrence_rules": []
}
```

#### `explicit` (Required)

Array of dated holiday entries.

```json
{
  "date": "2025-01-01",
  "name": "New Year's Day",
  "status": "closed",
  "early_close_time": null,
  "source_url": "https://www.nyse.com/markets/hours-calendars"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | Yes | `YYYY-MM-DD` format |
| `name` | string | Yes | Human-readable holiday name |
| `status` | string | Yes | `closed`, `early_close`, `delayed_open`, `special_session` |
| `early_close_time` | string | Conditional | `HH:MM` — required when status is `early_close` |
| `delayed_open_time` | string | Conditional | `HH:MM` — required when status is `delayed_open` |
| `source_url` | string | Recommended | Official exchange source |

#### `recurrence_rules` (Optional)

Array of rule definitions for date generation.

```json
{
  "rule": "fixed_with_weekend_adjustment",
  "month": 7,
  "day": 4,
  "name": "Independence Day",
  "status": "closed"
}
```

See [recurrence_rules.md](recurrence_rules.md) for full documentation.

---

### `ad_hoc_closures` (Optional)

```json
"ad_hoc_closures": [
  {
    "date": "2025-01-09",
    "name": "National Day of Mourning (Jimmy Carter)",
    "status": "closed",
    "source_url": "https://www.nyse.com/trader-update/history#110000921074"
  }
]
```

**Required field:** `source_url` — ad-hoc closures MUST have a citation.

**Do NOT duplicate dates between `holidays.explicit` and `ad_hoc_closures`.**  
The validator rejects duplicates.

---

### `generation_range`

```json
"generation_range": ["2025-01-01", "2029-12-31"]
```

- Exactly 2 dates: `[start, end]`
- Both in `YYYY-MM-DD` format
- `start` must be before `end`
- Defines the date range within which explicit dates are verified

---

## Conditional Validation

The schema uses `if`/`then` logic to require additional fields:

| Condition | Requirement |
|-----------|-------------|
| `status == "early_close"` | `early_close_time` is required |
| `status == "delayed_open"` | `delayed_open_time` is required |
| `type == "lunch_break"` | `open` and `close` are required |
| `type == "auction"` | `at` is required |
| Rule type `fixed_date` | `month` and `day` are required |
| Rule type `fixed_with_weekend_adjustment` | `month` and `day` are required |
| Rule type `nth_weekday` | `month`, `weekday`, `n` are required |
| Rule type `last_weekday` | `month`, `weekday` are required |
| Rule type `easter_offset` | `offset_days` is required |
| Rule `status == "early_close"` | `early_close_time` is required |

---

## Validation Examples

### Valid Exchange

```json
{
  "code": "XNYS",
  "name": "New York Stock Exchange",
  "mic": "XNYS",
  "timezone": "America/New_York",
  "regular_hours": {"open": "09:30", "close": "16:00"},
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
  "generation_range": ["2025-01-01", "2029-12-31"]
}
```

### Invalid: Missing Required Field

```json
{
  "code": "XNYS",
  "name": "New York Stock Exchange",
  "mic": "XNYS",
  "regular_hours": {"open": "09:30", "close": "16:00"},
  "holidays": {"explicit": [], "recurrence_rules": []}
  // Missing "timezone" and "generation_range"
}
```

### Invalid: Early Close Without Time

```json
{
  "date": "2025-07-03",
  "name": "Day before Independence Day",
  "status": "early_close"
  // Missing "early_close_time"
}
```

### Invalid: Code/MIC Mismatch

```json
{
  "code": "XNYS",
  "mic": "XNAS"  // Must equal code
}
```

### Invalid: Time Format

```json
"regular_hours": {"open": "9:30", "close": "16:00"}  // Missing leading zero
"regular_hours": {"open": "09:30", "close": "16.00"}  // Dot instead of colon
```

---

## Common Errors

### 1. Filename Mismatch

**Wrong:** `NYSE.json` with `"code": "XNYS"`  
**Right:** `XNYS.json` with `"code": "XNYS"`

The filename MUST be the MIC code.

### 2. Weekend Dates in Explicit

**Wrong:**
```json
{"date": "2025-12-25", "name": "Christmas Day", "status": "closed"}
```
(December 25, 2025 is a Thursday — this is fine. But December 27, 2025 would be Saturday — wrong.)

### 3. Open ≥ Close

**Wrong:** `{"open": "17:00", "close": "09:00"}` — validator rejects.

### 4. Missing Source URL on Ad-Hoc Closure

**Wrong:**
```json
{"date": "2025-01-09", "name": "National Day of Mourning", "status": "closed"}
```
**Right:** Must include `source_url`.

### 5. Duplicate Dates

**Wrong:**
```json
{
  "holidays": {
    "explicit": [
      {"date": "2025-01-01", "name": "New Year's Day", "status": "closed"},
      {"date": "2025-01-01", "name": "Duplicate", "status": "closed"}
    ]
  }
}
```

---

## Schema Evolution

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| New optional field | Minor | Add `note` field to holiday entries |
| New session type | Minor | Add `afternoon_break` to session types |
| New rule type | Minor | Add `offset_from_nth_weekday` |
| Removing required field | Major | Remove `mic` (breaking change) |
| Renaming field | Major | Rename `code` to `exchange_code` |
| Change pattern constraint | Major | Loosen `mic` from 4 to 3-6 chars |

---

## See Also

- [recurrence_rules.md](recurrence_rules.md) — Rule types and date generation
- [contributing_exchange.md](contributing_exchange.md) — How to add an exchange
- [las_shell_integration.md](las_shell_integration.md) — Las_shell consumer spec
- [../schema.json](../schema.json) — The actual JSON Schema file
