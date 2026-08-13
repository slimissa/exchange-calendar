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
- [Writing Tests](#writing-tests)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

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
├── exchanges/               # Source of truth — one file per exchange
├── tools/                   # Validation, build, generation
├── wrappers/                # Language bindings
│   ├── python/
│   ├── javascript/
│   ├── go/
│   └── rust/
├── tests/                   # Test suites
│   ├── fixtures/            # Test data
│   ├── ground_truth/        # Manually verified references
│   └── test_*.py            # Test files
└── docs/                    # Documentation
```

### Key Files

| File | Purpose |
|------|---------|
| `schema.json` | Defines the structure every exchange file must follow |
| `exchanges/XXXX.json` | Exchange data — one file per MIC code |
| `tools/validate.py` | Validates schema + business logic + cross-exchange |
| `tools/build.py` | Produces `calendar.json` distribution artifact |
| `tools/generate_dates.py` | Expands recurrence rules into dates |

---

## Adding a New Exchange

### Step 1: Verify the Exchange Details

Before writing any JSON, gather:

- **MIC code** — 4-character ISO 10383 code (e.g., `XNYS` for NYSE)
- **Official exchange name** — as used by the exchange itself
- **IANA timezone** — e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`
- **Regular trading hours** — opening and closing times
- **Extended hours** — pre-market and after-hours (if applicable)
- **Lunch break** — if the exchange has one (e.g., Tokyo 11:30-12:30)
- **Holiday calendar** — the next 5 years of official closures
- **Early close days** — half-days with specific close times
- **Source URL** — the official exchange page listing the holiday calendar

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

### Step 4: Critical Rules

#### Holiday Models

Different exchanges follow different rules. Verify before submitting:

| Model | Example | Rule |
|-------|---------|------|
| US weekend adjustment | NYSE, NASDAQ, TSX | Saturday→Friday, Sunday→Monday |
| UK substitute days | LSE | Bank Holidays shift to Monday |
| No substitutes | Germany, Switzerland | Holidays on weekends are NOT shifted |
| Open on civil holidays | Euronext, BME | Exchange trades on legal holidays |
| Lunisolar explicit-only | China, Japan, Korea, HK, Singapore | No recurrence rules possible |
| Half-day sessions | ASX, SGX, HKEX | Early close on eves |

#### Key Mistakes to Avoid

1. **Including weekend dates in explicit array** — the market is already closed on weekends. Only weekdays should appear.

2. **Using `fixed_with_weekend_adjustment` when the exchange does NOT shift** — Germany and Switzerland do not substitute.

3. **Treating civil holidays as market closures** — Euronext Paris is OPEN on Bastille Day. BME is OPEN on Epiphany. Verify the exchange calendar, not the national holiday list.

4. **Using `last_weekday` for Victoria Day** — Victoria Day is "Monday preceding May 25", which is NOT always the last Monday of May (2027: May 24, not May 31).

5. **Including CNY Eve as a full closure when it's a half-day** — Singapore and Hong Kong have early closes on CNY Eve.

6. **Forgetting observed days for Sunday holidays** — Singapore, Australia, and Korea observe Sunday holidays on Monday.

### Step 5: Validate

```bash
python3 tools/validate.py
```

Must pass with 0 errors before submitting.

### Step 6: Write Tests

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

### Step 7: Run All Tests

```bash
python3 -m pytest tests/ -v
```

All tests must pass.

### Step 8: Submit

Commit and push:

```bash
git add exchanges/XXXX.json tests/test_XXXX_holidays.py
git commit -m "Add [Exchange Name] (XXXX): [brief description]"
git push
```

---

## Correcting Exchange Data

### When You Find an Error

1. **Verify against the official exchange source** — not Wikipedia, not memory
2. **Check the test file** — is there a test that should catch this?
3. **Fix the data** — update `exchanges/XXXX.json`
4. **Fix or add the test** — so the error can't recur
5. **Run the full test suite** — ensure nothing else broke
6. **Document the fix** in the commit message

### Source Citation

Every explicit holiday entry must include a `source_url` pointing to the
official exchange calendar page. If the exchange publishes a PDF or a page
that changes frequently, use the most stable URL available.

---

## Writing Tests

### Python Test Conventions

```python
class TestExchangeProperties:
    def test_code(self, fixture):
        assert fixture["code"] == "XXXX"

class TestExchange2025:
    def test_holiday_name(self, explicit_dates):
        assert "2025-01-01" in explicit_dates
        assert explicit_dates["2025-01-01"]["status"] == "closed"

class TestExchangeStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5
```

### Go Test Conventions

Use `testing` package with table-driven tests where appropriate.

### Rust Test Conventions

Use `#[cfg(test)]` modules with `#[test]` functions.

### JavaScript Test Conventions

Use `node:test` and `node:assert/strict`.

---

## Code Style

### Python

- PEP 8
- Line length: 100 characters
- Docstrings for all public functions
- Type hints where practical

### JavaScript

- ESLint recommended
- camelCase methods
- `'use strict';` at top of files

### Go

- `gofmt` formatting
- Exported names have doc comments
- Errors as values, no panics in public API

### Rust

- `rustfmt` formatting
- `clippy` clean
- Doc comments for public items

---

## Commit Messages

Format: `<type>: <description>`

Types:
- `Add` — new exchange, new feature
- `Fix` — bug fix, data correction
- `Update` — improvement, refactor
- `Docs` — documentation
- `Test` — test changes
- `Build` — build system, CI

Examples:
```
Add Tokyo Stock Exchange (XTKS): lunch break, 15:30 close, Japanese holidays
Fix XNYS July 3, 2025 early close date
Update validate.py: add IANA timezone check for Etc/GMT+X
Docs: update README with 14 exchanges
```

---

## Pull Request Process

1. **Create a feature branch** — `git checkout -b add-XXXX`
2. **Make changes** — follow the guidelines above
3. **Run tests** — all 1127+ tests must pass
4. **Update CHANGELOG.md** — under `[Unreleased]`
5. **Push** — `git push origin add-XXXX`
6. **Open PR** — describe what you added and why
7. **CI must pass** — GitHub Actions will run validation and tests
8. **Review** — at least one maintainer approval

### PR Checklist

- [ ] Exchange data validated with `python3 tools/validate.py`
- [ ] Test file created with minimum coverage
- [ ] All tests pass (`python3 -m pytest tests/ -v`)
- [ ] Source URL provided for every holiday entry
- [ ] No weekend dates in explicit array
- [ ] No duplicate dates
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow format

---

## Release Process

1. **Update CHANGELOG.md** — move `[Unreleased]` items to new version section
2. **Bump version** — Semantic Versioning:
   - Major: breaking schema changes
   - Minor: new exchanges, new features
   - Patch: data corrections
3. **Update wrappers** — sync version across Python (`__init__.py`), JavaScript (`package.json`), Go (no version), Rust (`Cargo.toml`)
4. **Run full test suite** — all tests must pass
5. **Tag the release** — `git tag -a v1.1.0 -m "Release v1.1.0"`
6. **Push tag** — `git push origin v1.1.0`
7. **Publish wrappers** — PyPI, npm, crates.io (if applicable)

---

## Questions?

Open an issue on GitHub with the `question` label. For data corrections,
use the `holiday_update` issue template.

---

## Thank You

Every contribution improves the registry for everyone. Precise data,
rigorous tests, and clear documentation are what make this project valuable.
