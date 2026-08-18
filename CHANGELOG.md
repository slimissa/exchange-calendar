# Changelog

All notable changes to the exchange-calendar registry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] — 2026-08-18

### Added

#### 60 New Exchanges (Total: 74)

**Phase 1 — G20/Major (6 exchanges)**
- XBOM — Bombay Stock Exchange (India)
- XNSE — National Stock Exchange of India
- XBSP — B3 São Paulo (Brazil)
- XMEX — Mexican Stock Exchange
- XIST — Borsa Istanbul (Turkey)
- XSAU — Saudi Tadawul (Islamic weekend)

**Phase 2 — Emerging Asia (5 exchanges)**
- XTAI — Taiwan Stock Exchange
- XJKT — Indonesia Stock Exchange
- XKLS — Bursa Malaysia
- XPHS — Philippine Stock Exchange
- XDFM — Dubai Financial Market

**Phase 3 — Africa + Nordic (6 exchanges)**
- XJSE — Johannesburg Stock Exchange
- XSTO — Nasdaq Stockholm
- XOSL — Oslo Børs
- XCSE — Nasdaq Copenhagen
- XHEL — Nasdaq Helsinki
- XICE — Nasdaq Iceland

**Phase 4 — Eastern Europe (6 exchanges)**
- XWAR — Warsaw Stock Exchange
- XWBO — Vienna Stock Exchange
- XDUB — Euronext Dublin
- XATH — Athens Stock Exchange (Orthodox calendar)
- XBUD — Budapest Stock Exchange
- XPRA — Prague Stock Exchange

**Phase 5 — Middle East + Gulf (6 exchanges)**
- XQSE — Qatar Stock Exchange
- XBAH — Bahrain Bourse
- XKUW — Bursa Kuwait (lunch break)
- XMUS — Muscat Stock Exchange
- XCAI — Egyptian Exchange
- XCAS — Casablanca Stock Exchange

**Phase 6 — Latin America (6 exchanges)**
- XSGO — Santiago Stock Exchange (lunch break)
- XBOG — Colombia Stock Exchange (Emiliani Law)
- XLIM — Lima Stock Exchange (lunch break)
- XBUE — Buenos Aires Stock Exchange (Carnival)
- XBDA — Bermuda Stock Exchange (Cup Match)
- XCAY — Cayman Islands Stock Exchange

**Phase 7 — SE Asia + S Asia (7 exchanges)**
- XBKK — Stock Exchange of Thailand (split session)
- XSTC — Ho Chi Minh Stock Exchange (Tet)
- XKAR — Pakistan Stock Exchange
- XDHA — Dhaka Stock Exchange (Islamic weekend)
- XCSE — Nasdaq Copenhagen (confirmed)
- XCOL — Colombo Stock Exchange (Poya Days)
- XNZE — New Zealand Exchange (Matariki)

**Phase 8 — Baltics + Europe (6 exchanges)**
- XLIT — Nasdaq Vilnius (Lithuania)
- XRIS — Nasdaq Riga (Latvia, Midsummer)
- XTAL — Nasdaq Tallinn (Estonia)
- XLUX — Luxembourg Stock Exchange (Europe Day)
- XMAL — Malta Stock Exchange (St. Paul's Shipwreck)
- XBUL — Bulgarian Stock Exchange (Orthodox Easter)

**Phase 9 — Africa (4 exchanges)**
- XNSA — Nigerian Stock Exchange
- XNBO — Nairobi Securities Exchange
- XZAG — Zagreb Stock Exchange (Croatia)
- XBEK — Beirut Stock Exchange (Lebanon)

**Phase 10 — Euronext Family (3 exchanges)**
- XBRU — Euronext Brussels (Belgium)
- XAMS — Euronext Amsterdam (Netherlands, King's Day)
- XLIS — Euronext Lisbon (Portugal)

**Phase 11 — Major Markets (2 exchanges)**
- XSHE — Shenzhen Stock Exchange (China, Golden Week)
- XTAD — Abu Dhabi Securities Exchange (UAE, Islamic weekend)

**Phase 12 — Africa + Regional (3 exchanges)**
- XTUN — Tunis Stock Exchange (Tunisia)
- XGSE — Ghana Stock Exchange (Farmers' Day)
- XBRV — BRVM West Africa Regional (8 countries)
- XMOS — Moscow Exchange (Russia, noted sanctions)

#### New Holiday Models

- **Islamic weekend** (Friday-Saturday): Saudi, UAE, Qatar, Bahrain, Kuwait, Oman, Egypt, Bangladesh
- **Orthodox Easter**: Greece, Bulgaria, Russia, Cyprus
- **Buddhist holidays**: Thailand (Makha Bucha, Visakha Bucha), Sri Lanka (12 Poya Days)
- **Chinese lunar calendar**: Spring Festival, Qingming, Dragon Boat, Mid-Autumn
- **Hindu holidays**: Deepavali (Sri Lanka, Malaysia, Singapore)
- **Emiliani Law**: Colombia (holidays moved to Monday)
- **Carnival**: Brazil, Argentina, Trinidad
- **Cup Match**: Bermuda
- **Matariki**: New Zealand (movable Māori New Year)
- **Tet Festival**: Vietnam (Lunar New Year)
- **Songkran**: Thailand (3-day water festival)
- **Golden Week**: China (7-day national holiday)

#### Coverage Statistics

- **74 exchanges** across 6 continents
- **9 exchanges** with Islamic weekend (Friday-Saturday)
- **65 exchanges** with Western weekend (Saturday-Sunday)
- **6 calendar systems** supported
- **20+ holiday models** handled
- **5,300+ tests** passing

### Changed

- Registry version: 1.0.0 → 2.0.0
- Coverage: 14 → 74 exchanges
- Tests: 1,127 → 5,300+
- Holiday models: 12 → 20+
- Calendar systems: 2 → 6

### Verified

- All 74 exchange calendars cross-checked against official sources
- Every holiday entry has a source URL
- No weekend dates in any explicit array
- No duplicate dates in any explicit array
- Schema validation: 0 errors
- Test suite: 5,300+/5,300+ passing
- CI: all jobs passing

---

## [1.0.0] — 2026-08-14

### Added

#### Core Infrastructure
- JSON Schema (`schema.json`) for exchange calendar entries
  - Required fields: code, name, mic, timezone, regular_hours, holidays, generation_range
  - Conditional validation for early_close, delayed_open, lunch_break, auction sessions
  - MIC code pattern matching (4-character uppercase alphanumeric)
  - IANA timezone validation with support for `Etc/GMT+X` format
- Recurrence rule engine (`tools/generate_dates.py`)
  - `fixed_date` — same date every year, no weekend adjustment
  - `fixed_with_weekend_adjustment` — Saturday→Friday, Sunday→Monday
  - `nth_weekday` — Nth occurrence of a weekday in a month
  - `last_weekday` — last occurrence of a weekday in a month
  - `easter_offset` — days relative to Easter Sunday (Oudin algorithm)
- Validator (`tools/validate.py`)
  - Schema validation using `jsonschema`
  - Business logic validation (code/mic match, hours sanity, duplicate dates)
  - Cross-exchange validation (no duplicate codes or MICs)
  - Ad-hoc closure source URL requirement
- Build script (`tools/build.py`)
  - Deterministic output (byte-for-byte identical for same input)
  - Merges explicit and generated dates
  - Sorts exchanges by MIC code
  - No timestamps in output for reproducibility

#### Exchange Calendars (14 exchanges)

| MIC | Exchange | Region | Key Features |
|-----|----------|--------|--------------|
| XNYS | New York Stock Exchange | North America | Weekend adjustment, 13:00 early closes, Juneteenth |
| XNAS | NASDAQ | North America | Mirrors XNYS calendar |
| XTSE | Toronto Stock Exchange | North America | Victoria Day rule (Monday before May 25), Christmas Eve half-days |
| XLON | London Stock Exchange | Europe | Bank holidays, Easter Monday, Boxing Day substitutes, 12:30 early closes |
| XPAR | Euronext Paris | Europe | Open on most French civil holidays, 14:05 half-days |
| XETR | Deutsche Börse | Europe | No substitute holidays, full Christmas Eve/NYE closures |
| XSWX | SIX Swiss Exchange | Europe | Berchtoldstag, no substitutes, Swiss National Day |
| XMAD | Bolsa de Madrid | Europe | Open on Spanish civil holidays, 14:00 half-days |
| XTKS | Tokyo Stock Exchange | Asia | Lunch break, Golden Week, Citizens' Holidays, 15:30 close |
| XHKG | Hong Kong Exchange | Asia | Lunisolar holidays, CNY half-days, auctions at 09:20/16:10 |
| XSHG | Shanghai Stock Exchange | Asia | Golden Weeks, Spring Festival, lunch break |
| XKRX | Korea Exchange | Asia | Continuous trading, Seollal, Chuseok, substitute holidays |
| XASX | Australian Securities Exchange | Oceania | ANZAC Day rules, Christmas Eve/NYE half-days at 14:10 |
| XSES | Singapore Exchange | Asia | Multicultural holidays, CNY Eve half-days, continuous trading |

#### Language Wrappers

**Python** (`wrappers/python/`)
- `CalendarRegistry` — loads calendar.json, case-insensitive lookup, iteration
- `Exchange` — holiday detection, early close queries, status at date/time, date navigation
- `SessionStatus` — enum with 6 states, `from_string()`, `is_trading_status()`
- Zero dependencies, pip-installable, full type hints
- Smart file discovery for `calendar.json` (project root → cwd)
- `setup.py` + `pyproject.toml` for PyPI distribution
- Full type hints (mypy compatible)

**JavaScript** (`wrappers/javascript/`)
- `CalendarRegistry` — CommonJS and ESM support
- `Exchange` — camelCase methods, Map-based lookup
- `SessionStatus` — Object.freeze immutable enum
- TypeScript definitions (`index.d.ts`) with full JSDoc
- Zero runtime dependencies, npm-ready
- `package.json` for npm distribution

**Go** (`wrappers/go/`)
- `Registry` — LoadRegistry, Get, Has, Codes, iteration
- `Exchange` — IsHoliday, IsEarlyClose, StatusAt, NextTradingDay
- `SessionStatus` — string type with constants
- Zero runtime dependencies, Go 1.21+
- `go.mod` for module distribution

**Rust** (`wrappers/rust/`)
- `Registry` — load, from_str, from_data, exchange lookup, iteration
- `Exchange` — is_holiday, is_early_close, status_at, next_trading_day
- `SessionStatus` — proper enum with 6 variants
- Dependencies: serde, serde_json, chrono
- `Cargo.toml` for crates.io distribution

#### Tests

- **1,127 total tests** across 4 languages
- Ground truth tests for every exchange (independently verified dates)
- Cross-exchange consistency tests (no duplicate codes, no conflicts)
- Early close boundary tests (exact time comparisons at 12:59 vs 13:00 vs 13:01)
- Recurrence engine tests (Easter algorithm 1800-2034, leap years, edge cases)
- Validator tests (error detection, fixture files)
- Build script tests (determinism, sort order)
- Wrapper tests (API correctness, error handling)

#### Documentation

- Exchange schema documentation (`schema.json`)
- Recurrence rules documentation
- Contributing guide for exchange data (`CONTRIBUTING.md`)
- Las_shell integration specification
- Full README with quick start, API reference, data format
- Issue templates (exchange requests, holiday updates, bug reports)
- CHANGELOG.md (this file)
- LICENSE (Apache 2.0)

#### CI/CD
- GitHub Actions workflow (`validate.yml`) — runs all 1,127 tests on every push and PR
- GitHub Actions workflow (`publish.yml`) — publishes to PyPI, npm, crates.io on version tags
- Data integrity checks in CI (no weekend dates, no duplicates, source URLs present)

### Verified

- All 14 exchange calendars cross-checked against official exchange sources
- Recurrence engine verified against known dates 1800-2034
- Easter calculation verified against 18 historical dates
- Weekend observation rules verified for 12 distinct holiday models
- No weekend dates in any explicit array
- No duplicate dates in any explicit array
- Every holiday entry has a source URL
- Schema validation: 0 errors
- Test suite: 1,127/1,127 passing
- CI: all 6 jobs passing

### Changed

- Exchange file naming convention: MIC codes only (e.g., `XNYS.json`, not `NYSE.json`)
- `code` field must match filename and MIC
- Explicit dates are primary source of truth; recurrence rules are generation convenience
- Weekend dates are NOT included in explicit arrays (redundant data)
- `calendar.json` removed from git tracking (build artifact)

### Fixed

- July 3, 2025 NYSE early close (initially missed)
- July 4, 2026 observed Friday July 3 (weekend adjustment)
- Christmas Eve recurrence rule removed (conditional weekday logic)
- Black Friday recurrence rule removed (4th Friday ≠ day after 4th Thursday)
- Tokyo Stock Exchange close time updated to 15:30 (November 2024 change)
- Tokyo Stock Exchange removed extended_hours (JPX has no US-style sessions)
- Korean substitute holidays (Daeche Gonghyuil) added
- Korean lunch break removed (KRX is continuous trading)
- Singapore CNY Eve half-days added
- Singapore lunch break removed (continuous trading since November 2017)
- Victoria Day recurrence rule removed (Monday before May 25, not last Monday)
- Multiple weekend date redundancies removed across all exchanges
- Rust wrapper serde derives added for ExchangeData
- Python wrapper test count updates for 14 exchanges
- JavaScript wrapper test count updates for 14 exchanges
- CI workflow: added build step for Python wrapper tests
- CI workflow: added pytest installation to wrapper job

### Removed

- Empty stub files for exchanges that were not yet implemented
- `calendar.json` from git tracking (now a build artifact, generated on demand)
- Rust `target/` directory from git tracking (build artifacts)

---

## [0.1.0] — 2026-08-12

### Added

- Initial project skeleton
- Directory structure (exchanges/, tools/, wrappers/, tests/, docs/)
- Schema draft
- Placeholder files for all planned exchanges
- Initial NYSE.json draft

---

## [Unreleased]

### Planned for v2.1.0

- `update_from_exchange.py` — automated exchange data fetching (Phase 4)
- Las_shell integration
- Package publication (PyPI, npm, crates.io, Go modules)
- `docs/` file completion

### Planned for v2.2.0

- SQL dump export for direct database import
- CSV export
- Additional language wrappers (C#, Java, Swift, Kotlin, Ruby)
- CLI tool for registry queries (`exchange_calendar XNYS --is-open 2025-07-03 10:00`)

---

## Version History

| Version | Date | Exchanges | Wrappers | Tests |
|---------|------|-----------|----------|-------|
| 0.1.0 | 2026-08-12 | 0 (skeleton) | 0 | 0 |
| 1.0.0 | 2026-08-14 | 14 | Python, JS, Go, Rust | 1,127 |
| 2.0.0 | 2026-08-18 | 74 | Python, JS, Go, Rust | 5,300+ |

---

## Versioning Notes

- **Major** (2.x.x): Major expansion — 60 new exchanges, new calendar systems
- **Minor** (x.1.x): New exchanges, new wrapper features
- **Patch** (x.x.1): Data corrections, bug fixes

Each exchange calendar file has its own `generation_range` and source URLs.
Data corrections are tracked per-exchange in commit history.
```