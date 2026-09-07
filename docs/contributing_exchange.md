# Adding a New Exchange — Step-by-Step Guide

This guide walks through the complete process of adding a new exchange
calendar to the registry. It assumes you have already read
[CONTRIBUTING.md](../CONTRIBUTING.md) and understand the project structure.

---

## Table of Contents

- [Before You Start](#before-you-start)
- [Step 1: Research the Exchange](#step-1-research-the-exchange)
- [Step 2: Gather the Data](#step-2-gather-the-data)
- [Step 3: Create the JSON File](#step-3-create-the-json-file)
- [Step 4: Validate the Data](#step-4-validate-the-data)
- [Step 5: Write Tests](#step-5-write-tests)
- [Step 6: Rebuild calendar.json](#step-6-rebuild-calendarjson)
- [Step 7: Run All Tests](#step-7-run-all-tests)
- [Step 8: Submit](#step-8-submit)
- [Complete Example](#complete-example)
- [Checklist](#checklist)

---

## Before You Start

**Verify the exchange is not already in the registry:**

```bash
ls exchanges/
```

Current exchanges: XNYS, XNAS, XTSE, XLON, XPAR, XETR, XSWX, XMAD,
XTKS, XHKG, XSHG, XKRX, XASX, XSES.

**Check if it's on the deferred list:**

XBOM, XNSE, XSAU, XDFM, XTAE, XBSP, XMEX, XTAI, XJKT, XKLS, XPHS,
XJSE, XIST, XWAR, XSTO, XOSL, XCSE, XHEL, XICE, XWBO, XDUB, XMOS.

**Open an issue** with the `add_exchange` template to coordinate and avoid
duplication.

---

## Step 1: Research the Exchange

### 1.1 Find the MIC Code

Look up the ISO 10383 MIC code:

- Search [ISO 10383](https://www.iso10383.org/) (if accessible)
- Check the exchange's official website
- Use a reliable financial data reference

Common MICs:

| Exchange | MIC |
|----------|-----|
| New York Stock Exchange | XNYS |
| NASDAQ | XNAS |
| London Stock Exchange | XLON |
| Tokyo Stock Exchange | XTKS |
| Euronext Paris | XPAR |

### 1.2 Find the IANA Timezone

Look up the IANA timezone:

- [IANA Time Zone Database](https://www.iana.org/time-zones)
- [List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

Examples:

| Exchange | Timezone |
|----------|----------|
| NYSE | America/New_York |
| LSE | Europe/London |
| TSE | Asia/Tokyo |
| ASX | Australia/Sydney |

### 1.3 Find Trading Hours

From the exchange's official website:

- Regular open/close times
- Pre-market / after-hours (if applicable)
- Lunch break (if applicable)

### 1.4 Find the Holiday Calendar

The exchange's official website will have a trading calendar page.
Some examples:

- NYSE: `nyse.com/markets/hours-calendars`
- LSE: `londonstockexchange.com/market-data/trading-services/trading-hours`
- TSE: `jpx.co.jp/english/corporate/about-jpx/calendar/`

---

## Step 2: Gather the Data

### 2.1 Create a Research Document

Before writing JSON, create a reference document with:

| Item | Value | Source URL |
|------|-------|-----------|
| MIC Code | XXXX | [URL] |
| Exchange Name | Full name | [URL] |
| Timezone | Continent/City | [URL] |
| Regular Hours | open–close | [URL] |
| Extended Hours | pre/after (if any) | [URL] |
| Lunch Break | times (if any) | [URL] |
| Holiday 1 | date, name, status | [URL] |
| Holiday 2 | date, name, status | [URL] |
| ... | ... | ... |

### 2.2 Verify the Holiday Model

Before entering data, determine which holiday model applies:

| Model | Description | Example |
|-------|-------------|---------|
| US weekend adjustment | Sat→Fri, Sun→Mon | NYSE, NASDAQ, TSX |
| UK substitute days | Bank Holidays shift to Monday | LSE |
| No substitutes | Weekend holidays NOT shifted | Germany, Switzerland |
| Open on civil holidays | Exchange trades on legal holidays | Euronext, BME |
| Lunisolar explicit-only | No recurrence rules possible | China, Japan, Korea, HK, Singapore |
| Half-day sessions | Early close on eves | ASX, SGX, HKEX, TSX |

### 2.3 Verify Weekend Rules

Ask these questions:

1. When a fixed holiday falls on Saturday, does the exchange close Friday?
2. When a fixed holiday falls on Sunday, does the exchange close Monday?
3. Are there substitute holidays (Daeche Gonghyuil in Korea, etc.)?
4. Does the exchange observe Sunday holidays on Monday (Singapore, Australia)?

---

## Step 3: Create the JSON File

### 3.1 Create the File

```bash
touch exchanges/XXXX.json  # Replace XXXX with the MIC code
```

### 3.2 Write the JSON

Use this template:

```json
{
  "code": "XXXX",
  "name": "Full Exchange Name",
  "mic": "XXXX",
  "timezone": "Continent/City",
  "regular_hours": {
    "open": "HH:MM",
    "close": "HH:MM"
  },
  "extended_hours": {
    "pre_market": {"open": "HH:MM", "close": "HH:MM"},
    "after_hours": {"open": "HH:MM", "close": "HH:MM"}
  },
  "sessions": [],
  "holidays": {
    "explicit": [
      {
        "date": "YYYY-MM-DD",
        "name": "Holiday Name",
        "status": "closed",
        "source_url": "https://exchange.com/holidays"
      }
    ],
    "recurrence_rules": []
  },
  "ad_hoc_closures": [],
  "generation_range": ["2025-01-01", "2029-12-31"]
}
```

### 3.3 Data Entry Rules

#### Explicit Dates

- Only **weekdays** (Monday-Friday). Weekend dates are redundant.
- Sort chronologically by `date`.
- Use ISO 8601 date format: `YYYY-MM-DD`.
- Include `source_url` for every entry.
- Use the exchange's official holiday name.

#### Early Close Entries

```json
{
  "date": "2025-12-24",
  "name": "Christmas Eve (half-day)",
  "status": "early_close",
  "early_close_time": "13:00",
  "source_url": "https://exchange.com/holidays"
}
```

#### Recurrence Rules

Only use recurrence rules for dates that are **deterministic**:

| Rule | Use When |
|------|----------|
| `fixed_date` | Same date every year, no shift (Germany Dec 25) |
| `fixed_with_weekend_adjustment` | Same date every year, shifts from weekends (US Jan 1) |
| `nth_weekday` | Nth weekday of month (MLK Day = 3rd Monday Jan) |
| `last_weekday` | Last weekday of month (Memorial Day = last Monday May) |
| `easter_offset` | Relative to Easter (Good Friday = Easter - 2) |

**Do NOT use recurrence rules for:**
- Lunisolar holidays (Chinese New Year, Chuseok, Seollal)
- Equinox dates (Japanese Vernal/Autumnal Equinox)
- Victoria Day (Monday before May 25, NOT last Monday)
- Black Friday (day after 4th Thursday, NOT 4th Friday)
- Complex substitute holiday logic

#### Ad Hoc Closures

```json
{
  "date": "2025-01-09",
  "name": "National Day of Mourning (Jimmy Carter)",
  "status": "closed",
  "source_url": "https://exchange.com/notice"
}
```

**Must include `source_url`** — ad-hoc closures require citation.

---

## Step 4: Validate the Data

```bash
python3 tools/validate.py
```

**Expected output:**
```
OK: N exchange file(s) validated successfully
```

If validation fails, fix the errors and re-run.

---

## Step 5: Write Tests

### 5.1 Create the Test File

```bash
touch tests/test_XXXX_holidays.py
```

### 5.2 Follow the Test Pattern

```python
#!/usr/bin/env python3
"""Ground truth tests for XXXX (Exchange Name)."""

import json
import pytest
from datetime import date
from pathlib import Path


@pytest.fixture(scope="module")
def exchange_data():
    path = Path(__file__).parent.parent / "exchanges" / "XXXX.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(exchange_data):
    return {e["date"]: e for e in exchange_data["holidays"]["explicit"]}


class TestProperties:
    def test_code(self, exchange_data):
        assert exchange_data["code"] == "XXXX"

    def test_mic(self, exchange_data):
        assert exchange_data["mic"] == "XXXX"

    def test_name(self, exchange_data):
        assert exchange_data["name"] == "Full Exchange Name"

    def test_timezone(self, exchange_data):
        assert exchange_data["timezone"] == "Continent/City"

    def test_regular_hours(self, exchange_data):
        assert exchange_data["regular_hours"]["open"] == "HH:MM"
        assert exchange_data["regular_hours"]["close"] == "HH:MM"


class TestHolidays2025:
    def test_new_year(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

    # ... additional holidays


class TestStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5

    def test_no_duplicates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_all_have_source(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "source_url" in entry
```

### 5.3 Minimum Coverage Requirements

| Test Type | Required |
|-----------|----------|
| Properties (code, mic, name, timezone, hours) | Yes |
| All holidays for 2025 | Yes |
| Weekend observation rules | Yes (if applicable) |
| Early close times | Yes (if applicable) |
| Lunch break | Yes (if applicable) |
| No weekend dates | Yes |
| No duplicate dates | Yes |
| All entries have source URLs | Yes |

---

## Step 6: Rebuild calendar.json

```bash
python3 tools/build.py
```

**This step is critical.** The Go and Rust wrappers read from `calendar.json`.
If you skip this, CI will fail.

---

## Step 7: Run All Tests

```bash
python3 -m pytest tests/ -v
```

All tests must pass. If any fail, fix before submitting.

---

## Step 8: Submit

```bash
git add exchanges/XXXX.json tests/test_XXXX_holidays.py calendar.json
git commit -m "Add [Exchange Name] (XXXX): [brief description]"
git push
```

Open a PR with the `add_exchange` issue template filled out.

---

## Complete Example

### Adding XBOM (Bombay Stock Exchange)

**Step 1: Research**

| Item | Value |
|------|-------|
| MIC | XBOM |
| Name | Bombay Stock Exchange |
| Timezone | Asia/Kolkata |
| Hours | 09:15–15:30 |
| Lunch | None (continuous) |
| Holidays | Diwali, Holi, Republic Day, Independence Day, etc. |

**Step 2: Determine Model**

India follows a mixed model:
- Fixed dates (Republic Day Jan 26, Independence Day Aug 15)
- Lunisolar festivals (Diwali, Holi)
- Weekend observation for some but not all holidays

**Step 3: Write JSON**

```json
{
  "code": "XBOM",
  "name": "Bombay Stock Exchange",
  "mic": "XBOM",
  "timezone": "Asia/Kolkata",
  "regular_hours": {
    "open": "09:15",
    "close": "15:30"
  },
  "sessions": [],
  "holidays": {
    "explicit": [
      {
        "date": "2025-01-26",
        "name": "Republic Day",
        "status": "closed",
        "source_url": "https://www.bseindia.com/markets/marketinfo/market_holidays.html"
      }
    ],
    "recurrence_rules": []
  },
  "ad_hoc_closures": [],
  "generation_range": ["2025-01-01", "2029-12-31"]
}
```

**Step 4: Validate**

```bash
python3 tools/validate.py
```

**Step 5-8: Test, Build, Submit**

Follow the same steps as above.

---

## Checklist

Before submitting a PR, verify:

- [ ] MIC code is correct (4 characters, uppercase)
- [ ] `code` matches filename
- [ ] `code` equals `mic`
- [ ] Timezone is valid IANA identifier
- [ ] Regular hours are correct (open before close)
- [ ] Extended hours included only if the exchange actually has them
- [ ] Lunch break included only if the exchange actually has one
- [ ] Auction sessions use `at`, not `open`/`close`
- [ ] All explicit dates are weekdays (Monday-Friday)
- [ ] All explicit dates are sorted chronologically
- [ ] Every explicit entry has a `source_url`
- [ ] Early close entries have `early_close_time`
- [ ] No weekend dates in explicit array
- [ ] No duplicate dates
- [ ] Recurrence rules only for deterministic dates
- [ ] Victoria Day (if applicable) is explicit, not `last_weekday`
- [ ] Black Friday (if applicable) is explicit, not `nth_weekday`
- [ ] Ad hoc closures have `source_url`
- [ ] `generation_range` is `[start, end]` in correct order
- [ ] Validation passes: `python3 tools/validate.py`
- [ ] Test file created with minimum coverage
- [ ] `calendar.json` rebuilt: `python3 tools/build.py`
- [ ] All tests pass: `python3 -m pytest tests/ -v`
- [ ] CHANGELOG.md updated under `[Unreleased]`

---

## See Also

- [exchange_schema.md](exchange_schema.md) — Field reference
- [recurrence_rules.md](recurrence_rules.md) — Rule types
- [las_shell_integration.md](las_shell_integration.md) — Consumer spec
- [../CONTRIBUTING.md](../CONTRIBUTING.md) — General guidelines
