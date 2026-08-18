The CONTRIBUTING.md needs updating for v2.0.0. Here are the key changes needed:

```markdown
# Contributing to exchange-calendar

Thank you for contributing to the QuantOS exchange calendar registry.

This document provides guidelines for adding new exchanges, correcting data,
fixing bugs, and improving the codebase. Following these guidelines helps
maintain data integrity — the core value of this project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Adding a New Exchange](#adding-a-new-exchange)
- [Correcting Exchange Data](#correcting-exchange-data)
- [Common Data Errors](#common-data-errors)
- [Writing Tests](#writing-tests)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Review Priorities](#review-priorities)
- [Release Process](#release-process)
- [Getting Help](#getting-help)

---

## Code of Conduct

Be respectful. Be constructive. Financial data requires precision — critique
the data, not the person who submitted it.

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | ≥ 3.8 | Core tools, validation, tests |
| Node.js | ≥ 14 | JavaScript wrapper |
| Go | ≥ 1.21 | Go wrapper |
| Rust | ≥ 1.74 | Rust wrapper |
| jsonschema | ≥ 4.0 | Python validation dependency |

### Setup

```bash
# Clone the repository
git clone https://github.com/slimissa/exchange-calendar.git
cd exchange-calendar

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run all tests
python3 -m pytest tests/ -v

# Run specific test suite
python3 -m pytest tests/test_nyse_holidays.py -v
```

---

## Development Environment

### Project Structure

```
exchange-calendar/
├── schema.json              # JSON Schema — the contract
├── exchanges/               # Source of truth — 74 exchange files
├── tools/                   # Validation, build, generation
├── wrappers/                # Language bindings
│   ├── python/
│   ├── javascript/
│   ├── go/
│   └── rust/
├── tests/                   # Test suites (5,300+ tests)
│   ├── fixtures/            # Test data
│   ├── ground_truth/        # Manually verified references
│   └── test_*.py            # Test files (one per exchange)
└── docs/                    # Documentation
```

### ⚠️ Stale Data Warning

**After any change to `exchanges/*.json`, you MUST rebuild `calendar.json`:**

```bash
python3 tools/build.py
```

The Go and Rust wrappers read from `calendar.json` at test time. CI runs
`tools/build.py` automatically — do it locally to save a failed PR.

---

## Adding a New Exchange

### Step 1: Verify the Exchange Details

- **MIC code** — 4-character ISO 10383 code (e.g., `XNYS` for NYSE)
- **Official exchange name** — as used by the exchange itself
- **IANA timezone** — e.g., `America/New_York`, `Asia/Tokyo`
- **Regular trading hours** — opening and closing times
- **Lunch break** — if applicable (Tokyo 11:30-12:30, Shanghai 11:30-13:00)
- **Weekend system** — Western (Sat-Sun) or Islamic (Fri-Sat)
- **Holiday calendar** — next 5 years of official closures
- **Source URL** — official exchange calendar page

### Step 2: Create the File

```bash
touch exchanges/XXXX.json  # Replace XXXX with the MIC code
```

### Step 3: Write the JSON

Follow the schema in `schema.json`. Every entry must include:

```json
{
  "code": "XXXX",
  "name": "Full Exchange Name",
  "mic": "XXXX",
  "timezone": "Continent/City",
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
        "source_url": "https://www.example-exchange.com/holidays"
      }
    ],
    "recurrence_rules": []
  },
  "ad_hoc_closures": [],
  "generation_range": ["2025-01-01", "2029-12-31"]
}
```

### Step 4: Validate

```bash
python3 tools/validate.py
```

Must pass with 0 errors before submitting.

### Step 5: Write Tests

Create `tests/test_XXXX_holidays.py` following the pattern of existing tests.

Minimum test coverage:
- Exchange properties (code, mic, name, timezone, hours)
- All holidays for 2025
- Weekend observation rules (if applicable)
- Early close times (if applicable)
- Lunch break (if applicable)
- No weekend dates
- No duplicate dates
- All entries have source URLs

### Step 6: Rebuild calendar.json

```bash
python3 tools/build.py
```

### Step 7: Run All Tests

```bash
python3 -m pytest tests/ -v
```

All tests must pass.

### Step 8: Submit

Commit and push:

```bash
git add exchanges/XXXX.json tests/test_XXXX_holidays.py calendar.json
git commit -m "Add [Exchange Name] (XXXX): [brief description]"
git push
```

---

## Common Data Errors

### 1. Weekend Dates in Explicit Arrays

**Only weekdays should appear in explicit arrays.**

For Western weekend exchanges (65 exchanges):
- No Saturday or Sunday dates

For Islamic weekend exchanges (9 exchanges: XSAU, XDFM, XTAD, XQSE, XBAH, XKUW, XMUS, XCAI, XDHA):
- No Friday or Saturday dates
- Sunday is a working day

### 2. Wrong Weekend Observation Model (Expanded)

| Model | Exchanges |
|-------|-----------|
| US weekend adjustment | XNYS, XNAS, XTSE |
| UK substitute days | XLON, XDUB |
| No substitutes | XETR, XSWX, XWBO, Nordic, Baltic, Poland, Czech |
| Open on civil holidays | Euronext (XPAR, XAMS, XBRU, XLIS), XMAD |
| Islamic weekend (Fri-Sat) | XSAU, XDFM, XTAD, XQSE, XBAH, XKUW, XMUS, XCAI, XDHA |
| Orthodox Easter | XATH, XBUL, XMOS |
| Buddhist holidays | XBKK, XCOL |
| Chinese lunar | XSHG, XSHE, XHKG, XTAI |
| Multi-day festivals | Chinese New Year, Eid, Songkran, Tet |

### 3. Civil Holidays as Market Closures

Euronext Paris is **OPEN** on Bastille Day (July 14).  
BME Madrid is **OPEN** on Epiphany (January 6).  
Deutsche Börse is **OPEN** on German Unity Day (October 3).

**Always verify the exchange calendar, not the national holiday list.**

### 4. Victoria Day Miscalculation

Victoria Day is **"Monday preceding May 25"**, not "last Monday of May."

| Year | Correct Date | Last Monday (wrong) |
|------|-------------|---------------------|
| 2025 | May 19 | May 26 |
| 2027 | May 24 | May 31 |
| 2028 | May 22 | May 29 |

### 5. Black Friday Miscalculation

Black Friday is **"day after 4th Thursday of November"**, not "4th Friday."

These dates diverge when Thanksgiving falls early:
- 2035: Thanksgiving Nov 22, Black Friday Nov 23 (4th Friday is Nov 25)

### 6. CNY Eve as Full Closure

Singapore and Hong Kong have **half-day sessions** (early close at 12:30)
on Chinese New Year Eve, not full closures.

### 7. Forgetting Observed Days for Sunday Holidays

Singapore, Australia, and Korea observe Sunday holidays on Monday.
Germany and Switzerland do NOT.

### 8. Missing Lunch Break

Tokyo (11:30-12:30), Hong Kong (12:00-13:00), and Shanghai (11:30-13:00)
have lunch breaks. Singapore and Korea do **NOT** (continuous trading).

---

## Testing Statistics

Current test counts:
- **74 exchange test files** (`tests/test_*_holidays.py`)
- **5,300+ total tests** across 4 languages
- Each exchange has 35-70 tests covering:
  - Properties (code, MIC, timezone, hours)
  - Fixed holidays (verified against official sources)
  - Movable holidays (Easter, Islamic, Chinese lunar)
  - Weekend pattern checks
  - Substitution logic
  - Structural integrity (no duplicates, no weekend dates)

---

## Pull Request Process

1. **Create a feature branch**
2. **Make changes**
3. **Run tests** — `python3 -m pytest tests/ -v` (all 5,300+ must pass)
4. **Rebuild `calendar.json`** — `python3 tools/build.py`
5. **Update CHANGELOG.md** — under `[Unreleased]`
6. **Push and open PR**

### PR Checklist

- [ ] Exchange data validated with `python3 tools/validate.py`
- [ ] Test file created with minimum coverage (35+ tests)
- [ ] All 5,300+ tests pass
- [ ] `calendar.json` rebuilt
- [ ] Source URL provided for every holiday entry
- [ ] No weekend dates (correct for exchange's weekend system)
- [ ] No duplicate dates
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow format

---

## Review Priorities

1. **Data accuracy** — backed by official exchange source?
2. **Schema compliance** — validates against `schema.json`?
3. **Test coverage** — all 5,300+ tests pass?
4. **Weekend system** — Western or Islamic applied correctly?
5. **Calendar system** — Gregorian, Orthodox, Islamic, Buddhist, Chinese, Hindu?
6. **Early close times** — correct for the specific exchange?
7. **Lunch breaks** — continuous or break?
8. **Substitution rules** — shifts or no-shifts?
9. **Documentation** — CHANGELOG.md updated?

---

## Release Process

1. **Update CHANGELOG.md**
2. **Bump version** — Semantic Versioning
3. **Update wrappers** — sync versions
4. **Rebuild calendar.json**
5. **Run full test suite**
6. **Tag release** — `git tag -a v2.1.0 -m "Release v2.1.0"`
7. **Push tag**
8. **Publish wrappers**

---

## Getting Help

- Open an issue with appropriate label
- Use issue templates for data corrections

---

## Thank You

Every contribution improves the registry for everyone. With 74 exchanges
and 5,300+ tests, precise data and rigorous testing are essential.

---
