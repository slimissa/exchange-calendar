# Recurrence Rules Documentation

This document describes the recurrence rule engine used by the
exchange-calendar registry to generate future holiday dates from
deterministic patterns.

**Engine:** [`tools/generate_dates.py`](../tools/generate_dates.py)  
**Schema:** [`schema.json`](../schema.json)  
**Version:** 1.0.0

---

## Table of Contents

- [Overview](#overview)
- [Rule Types](#rule-types)
- [Rule Reference](#rule-reference)
- [Weekend Adjustment](#weekend-adjustment)
- [Easter Algorithm](#easter-algorithm)
- [When NOT to Use Rules](#when-not-to-use-rules)
- [Examples](#examples)
- [Testing](#testing)

---

## Overview

Recurrence rules generate holiday dates for years beyond the explicit date
range. They are **generation convenience** — never the primary source of truth.

**Key principle:**

> Explicit dates are always primary. Recurrence rules only generate dates
> that are not already in the explicit array. If a conflict occurs, the
> explicit date wins.

---

## Rule Types

| Rule | Description | Example |
|------|-------------|---------|
| `fixed_date` | Same date every year, no shift | Dec 25 (Germany) |
| `fixed_with_weekend_adjustment` | Same date, shifts from weekends | Jan 1 (US) |
| `nth_weekday` | Nth weekday of a month | 3rd Monday Jan (MLK) |
| `last_weekday` | Last weekday of a month | Last Monday May (Memorial) |
| `easter_offset` | Days relative to Easter Sunday | Good Friday (-2) |

---

## Rule Reference

### `fixed_date`

Same date every year. No weekend adjustment.

```json
{
  "rule": "fixed_date",
  "month": 12,
  "day": 25,
  "name": "Christmas Day",
  "status": "closed"
}
```

**Required fields:** `month`, `day`  
**Used by:** Germany (Christmas Eve, Christmas Day, Boxing Day)

**When to use:**
- The exchange closes on the exact date regardless of weekday
- The exchange does NOT shift holidays from weekends

**When NOT to use:**
- If the exchange shifts Saturday→Friday or Sunday→Monday (use `fixed_with_weekend_adjustment`)

---

### `fixed_with_weekend_adjustment`

Same date every year. Saturday→Friday, Sunday→Monday.

```json
{
  "rule": "fixed_with_weekend_adjustment",
  "month": 7,
  "day": 4,
  "name": "Independence Day",
  "status": "closed"
}
```

**Required fields:** `month`, `day`  
**Used by:** US exchanges (New Year's Day, Independence Day, Christmas Day)

**Weekend Shift Logic:**

| Date Falls On | Observed On |
|--------------|-------------|
| Monday-Friday | Same day |
| Saturday | Previous Friday |
| Sunday | Following Monday |

**Example:**

| Year | July 4 Falls On | Observed |
|------|----------------|----------|
| 2025 | Friday | Friday July 4 |
| 2026 | Saturday | Friday July 3 |
| 2027 | Sunday | Monday July 5 |
| 2028 | Tuesday | Tuesday July 4 |

---

### `nth_weekday`

Nth occurrence of a weekday in a month.

```json
{
  "rule": "nth_weekday",
  "month": 1,
  "weekday": "monday",
  "n": 3,
  "name": "Martin Luther King Jr. Day",
  "status": "closed"
}
```

**Required fields:** `month`, `weekday`, `n`  
**Used by:** US (MLK Day, Presidents Day, Labor Day, Thanksgiving)

**`n` values:**

| n | Meaning |
|---|---------|
| 1 | First occurrence |
| 2 | Second occurrence |
| 3 | Third occurrence |
| 4 | Fourth occurrence |
| 5 | Fifth occurrence (rarely used) |

**Valid weekdays:** `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`

**Examples:**

| Holiday | Rule |
|---------|------|
| MLK Day | 3rd Monday January |
| Presidents Day | 3rd Monday February |
| Labor Day (US) | 1st Monday September |
| Thanksgiving (US) | 4th Thursday November |

---

### `last_weekday`

Last occurrence of a weekday in a month.

```json
{
  "rule": "last_weekday",
  "month": 5,
  "weekday": "monday",
  "name": "Memorial Day",
  "status": "closed"
}
```

**Required fields:** `month`, `weekday`  
**Used by:** US (Memorial Day), UK (Spring Bank Holiday)

**Difference from `nth_weekday` with n=5:**
- `last_weekday` always finds the last occurrence, even if it's the 4th
- `nth_weekday` with n=5 fails if the month only has 4 occurrences

**Example:**
- May 2025 has 4 Mondays (5, 12, 19, 26)
- `last_weekday` returns May 26 ✓
- `nth_weekday` with n=5 would error

---

### `easter_offset`

Days relative to Easter Sunday.

```json
{
  "rule": "easter_offset",
  "offset_days": -2,
  "name": "Good Friday",
  "status": "closed"
}
```

**Required fields:** `offset_days`  
**Used by:** Nearly all exchanges (Good Friday, Easter Monday, Ascension, Whit Monday)

**Common offsets:**

| Offset | Holiday | Used By |
|--------|---------|---------|
| -2 | Good Friday | US, UK, Europe, HK, Singapore, Australia |
| +1 | Easter Monday | UK, Europe, HK, Australia |
| +39 | Ascension Day | Europe (France, Switzerland) |
| +50 | Whit Monday | Europe (France, Switzerland) |

---

## Weekend Adjustment

The `fixed_with_weekend_adjustment` rule applies this logic:

```
If date is Saturday:
    return date - 1 day (Friday)
If date is Sunday:
    return date + 1 day (Monday)
Otherwise:
    return date unchanged
```

**Edge case:** What if the adjusted date falls in a different month or year?

| Original Date | Adjusted Date | Month/Year Change |
|---------------|---------------|-------------------|
| Jan 1, 2028 (Saturday) | Dec 31, 2027 (Friday) | Yes — previous year |
| Dec 31, 2028 (Sunday) | Jan 1, 2029 (Monday) | Yes — next year |

The engine handles this correctly because it generates the date first, then adjusts the weekday, then checks if the result is already in the explicit array.

---

## Easter Algorithm

The engine uses the **Oudin algorithm** (also known as the Anonymous Gregorian algorithm) to calculate Easter Sunday.

```python
def easter_sunday(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)
```

**Verified against 18 known dates** from 1800 to 2034 in the test suite.

**Easter Sunday range:** March 22 to April 25.

---

## When NOT to Use Rules

### 1. Lunisolar Holidays

Chinese New Year, Seollal, Chuseok, Buddha's Birthday, Tuen Ng, Mid-Autumn, Diwali, Holi.

**Why:** These dates depend on the lunar calendar and cannot be expressed as simple rules. They require astronomical calculation or manual date entry.

**Used by:** China (XSHG), Hong Kong (XHKG), Korea (XKRX), Singapore (XSES), Taiwan (XTAI), India (XBOM, XNSE).

### 2. Equinox Dates

Japanese Vernal Equinox Day and Autumnal Equinox Day.

**Why:** These are determined by astronomical observations and vary between March 20-21 and September 22-23.

**Used by:** Japan (XTKS).

### 3. Victoria Day (Canada)

Victoria Day is "Monday preceding May 25" — NOT "last Monday of May."

**Why `last_weekday` fails:**

| Year | Correct Date | Last Monday (wrong) |
|------|-------------|---------------------|
| 2025 | May 19 | May 26 |
| 2027 | May 24 | May 31 |
| 2028 | May 22 | May 29 |

The rule is: `May 24 - (May 24's weekday - Monday)`, capped between May 18 and May 24.

**Correct approach:** Explicit-only.

### 4. Black Friday (US)

Black Friday is "day after 4th Thursday of November" — NOT "4th Friday."

**Why `nth_weekday` fails:**

| Year | Thanksgiving | Black Friday | 4th Friday (wrong) |
|------|-------------|-------------|-------------------|
| 2033 | Nov 24 | Nov 25 | Nov 25 (same) |
| 2035 | Nov 22 | Nov 23 | Nov 25 (wrong) |

**Correct approach:** Explicit-only, or implement `offset_from_nth_weekday` rule type.

### 5. Complex Substitute Holidays

Korean Daeche Gonghyuil (substitute holidays), Japanese Citizens' Holidays (Kokumin no Kyūjitsu), Singapore observed days.

**Why:** These depend on complex legal conditions (sandwiched days, Sunday-only observation, specific holiday clusters).

**Correct approach:** Explicit-only.

### 6. Christmas Eve and New Year's Eve (Conditional Early Closes)

These are half-days only when they fall on weekdays. Many exchanges skip them entirely when they fall on weekends.

**Why:** A simple `fixed_date` rule would generate early closes on Saturday/Sunday, which is wrong.

**Correct approach:** Explicit-only, or a conditional rule type.

---

## Examples

### US Exchange (XNYS)

```json
"recurrence_rules": [
  {"rule": "fixed_with_weekend_adjustment", "month": 1, "day": 1, "name": "New Year's Day", "status": "closed"},
  {"rule": "nth_weekday", "month": 1, "weekday": "monday", "n": 3, "name": "Martin Luther King Jr. Day", "status": "closed"},
  {"rule": "nth_weekday", "month": 2, "weekday": "monday", "n": 3, "name": "Presidents Day", "status": "closed"},
  {"rule": "easter_offset", "offset_days": -2, "name": "Good Friday", "status": "closed"},
  {"rule": "last_weekday", "month": 5, "weekday": "monday", "name": "Memorial Day", "status": "closed"},
  {"rule": "fixed_with_weekend_adjustment", "month": 6, "day": 19, "name": "Juneteenth", "status": "closed"},
  {"rule": "fixed_with_weekend_adjustment", "month": 7, "day": 4, "name": "Independence Day", "status": "closed"},
  {"rule": "nth_weekday", "month": 9, "weekday": "monday", "n": 1, "name": "Labor Day", "status": "closed"},
  {"rule": "nth_weekday", "month": 11, "weekday": "thursday", "n": 4, "name": "Thanksgiving Day", "status": "closed"},
  {"rule": "fixed_with_weekend_adjustment", "month": 12, "day": 25, "name": "Christmas Day", "status": "closed"}
]
```

**Not included:**
- Black Friday (day after Thanksgiving) — needs custom rule
- Christmas Eve (conditional early close) — explicit-only

### UK Exchange (XLON)

```json
"recurrence_rules": [
  {"rule": "fixed_with_weekend_adjustment", "month": 1, "day": 1, "name": "New Year's Day", "status": "closed"},
  {"rule": "easter_offset", "offset_days": -2, "name": "Good Friday", "status": "closed"},
  {"rule": "easter_offset", "offset_days": 1, "name": "Easter Monday", "status": "closed"},
  {"rule": "nth_weekday", "month": 5, "weekday": "monday", "n": 1, "name": "Early May Bank Holiday", "status": "closed"},
  {"rule": "last_weekday", "month": 5, "weekday": "monday", "name": "Spring Bank Holiday", "status": "closed"},
  {"rule": "last_weekday", "month": 8, "weekday": "monday", "name": "Summer Bank Holiday", "status": "closed"}
]
```

**Not included:**
- Christmas Day / Boxing Day (complex substitute rules) — explicit-only
- Christmas Eve / New Year's Eve (early closes) — explicit-only

### German Exchange (XETR)

```json
"recurrence_rules": [
  {"rule": "fixed_date", "month": 1, "day": 1, "name": "New Year's Day", "status": "closed"},
  {"rule": "easter_offset", "offset_days": -2, "name": "Good Friday", "status": "closed"},
  {"rule": "easter_offset", "offset_days": 1, "name": "Easter Monday", "status": "closed"},
  {"rule": "fixed_date", "month": 5, "day": 1, "name": "Labour Day", "status": "closed"},
  {"rule": "fixed_date", "month": 12, "day": 24, "name": "Christmas Eve", "status": "closed"},
  {"rule": "fixed_date", "month": 12, "day": 25, "name": "Christmas Day", "status": "closed"},
  {"rule": "fixed_date", "month": 12, "day": 26, "name": "Boxing Day", "status": "closed"},
  {"rule": "fixed_date", "month": 12, "day": 31, "name": "New Year's Eve", "status": "closed"}
]
```

**Germany uses `fixed_date` everywhere** because it does NOT shift holidays from weekends.

---

## Testing

The recurrence engine is tested in `tests/test_recurrence.py`:

```bash
python3 -m pytest tests/test_recurrence.py -v
```

**66 tests covering:**

- Easter calculation: 18 known dates from 1800-2034
- Easter boundaries: March 22 ≤ Easter ≤ April 25
- Pre-Gregorian rejection (before 1583)
- Weekend adjustment: Saturday→Friday, Sunday→Monday
- `nth_weekday`: valid and invalid n, month boundaries, invalid weekdays
- `last_weekday`: leap years, month boundaries
- `easter_offset`: Good Friday, Easter Monday
- Error handling: missing fields, unknown rule types
- Duplicate avoidance with explicit dates
- Year range overrides
- Sort order
- Early close time preservation
- Source URL propagation

---

## See Also

- [exchange_schema.md](exchange_schema.md) — Field reference
- [contributing_exchange.md](contributing_exchange.md) — How to add an exchange
- [las_shell_integration.md](las_shell_integration.md) — Consumer spec
- [../tools/generate_dates.py](../tools/generate_dates.py) — Engine implementation
