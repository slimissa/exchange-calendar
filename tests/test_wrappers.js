'use strict';

/**
 * test_wrappers.js — Tests for the JavaScript wrapper.
 *
 * Verifies that the JavaScript wrapper correctly:
 *   1. Loads the registry from calendar.json
 *   2. Looks up exchanges by MIC code (case-insensitive)
 *   3. Reports correct session status for known dates/times
 *   4. Identifies holidays and early closes correctly
 *   5. Performs date navigation (next/previous trading day)
 *   6. Handles errors gracefully
 *   7. Provides iteration and membership
 *
 * Run:
 *   node --test tests/test_wrappers.js
 *
 * Or with npm:
 *   npm test
 */

const { test, describe, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');

const { CalendarRegistry, Exchange, SessionStatus } = require('../wrappers/javascript/src/index');

// ──────────────────────────────────────────────────────────────
// Fixtures
// ──────────────────────────────────────────────────────────────

function createTempRegistry() {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'exchange-calendar-test-'));
    const registryFile = path.join(tmpDir, 'calendar.json');

    const data = {
        meta: { version: '1.0.0', exchange_count: 1 },
        exchanges: [
            {
                code: 'TEST',
                name: 'Test Exchange',
                mic: 'TEST',
                timezone: 'Europe/London',
                regular_hours: { open: '09:00', close: '17:00' },
                extended_hours: {},
                sessions: [],
                holidays: {
                    explicit: [
                        {
                            date: '2025-01-01',
                            name: "New Year's Day",
                            status: 'closed',
                        },
                        {
                            date: '2025-07-03',
                            name: 'Early Close Day',
                            status: 'early_close',
                            early_close_time: '13:00',
                        },
                    ],
                    generated: [],
                },
                ad_hoc_closures: [],
                generation_range: ['2025-01-01', '2025-12-31'],
            },
        ],
    };

    fs.writeFileSync(registryFile, JSON.stringify(data));
    return registryFile;
}

function getRegistryPath() {
    return path.join(__dirname, '..', 'calendar.json');
}

// ──────────────────────────────────────────────────────────────
// Registry loading
// ──────────────────────────────────────────────────────────────

describe('Registry loading', () => {
    test('loads real registry', () => {
        const registry = new CalendarRegistry(getRegistryPath());
        assert.equal(registry.version, '1.0.0');
        assert.equal(registry.exchangeCount, 74);
        assert.equal(registry.size, 74);
        assert.equal(registry.length, 74);
    });

    test('throws on missing file', () => {
        assert.throws(
            () => new CalendarRegistry('/nonexistent/path/calendar.json'),
            /file not found/
        );
    });

    test('throws on invalid JSON', () => {
        const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'exchange-calendar-bad-'));
        const badFile = path.join(tmpDir, 'bad.json');
        fs.writeFileSync(badFile, '{invalid json');

        assert.throws(
            () => new CalendarRegistry(badFile),
            /invalid JSON/
        );
    });

    test('throws on missing meta', () => {
        const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'exchange-calendar-nometa-'));
        const badFile = path.join(tmpDir, 'bad.json');
        fs.writeFileSync(badFile, JSON.stringify({ exchanges: [] }));

        assert.throws(
            () => new CalendarRegistry(badFile),
            /meta/
        );
    });

    test('throws on duplicate codes', () => {
        const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'exchange-calendar-dupe-'));
        const badFile = path.join(tmpDir, 'bad.json');
        const data = {
            meta: { version: '1.0.0', exchange_count: 2 },
            exchanges: [
                {
                    code: 'DUPE', name: 'First', mic: 'DUPE',
                    timezone: 'Europe/London',
                    regular_hours: { open: '09:00', close: '17:00' },
                    holidays: { explicit: [], generated: [] },
                },
                {
                    code: 'DUPE', name: 'Second', mic: 'DUPE',
                    timezone: 'Europe/London',
                    regular_hours: { open: '09:00', close: '17:00' },
                    holidays: { explicit: [], generated: [] },
                },
            ],
        };
        fs.writeFileSync(badFile, JSON.stringify(data));

        assert.throws(
            () => new CalendarRegistry(badFile),
            /duplicate exchange codes/
        );
    });

    test('string representation', () => {
        const registry = new CalendarRegistry(getRegistryPath());
        const s = registry.toString();
        assert.ok(s.includes('Exchange Calendar Registry'));
        assert.ok(s.includes('1.0.0'));
        assert.ok(s.includes('74'));
    });
});

// ──────────────────────────────────────────────────────────────
// Exchange lookup
// ──────────────────────────────────────────────────────────────

describe('Exchange lookup', () => {
    let registry;

    beforeEach(() => {
        registry = new CalendarRegistry(getRegistryPath());
    });

    test('lookup by code', () => {
        const xnys = registry.exchange('XNYS');
        assert.ok(xnys);
        assert.equal(xnys.code, 'XNYS');
        assert.equal(xnys.name, 'New York Stock Exchange');
    });

    test('lookup case-insensitive', () => {
        const xnys = registry.exchange('xnys');
        assert.ok(xnys);
        assert.equal(xnys.code, 'XNYS');
    });

    test('not found returns null', () => {
        assert.equal(registry.exchange('XXXX'), null);
    });

    test('get throws on not found', () => {
        assert.throws(
            () => registry.get('XXXX'),
            /not found/
        );
    });

    test('has returns boolean', () => {
        assert.equal(registry.has('XNYS'), true);
        assert.equal(registry.has('XXXX'), false);
    });

    test('isExchange alias', () => {
        assert.equal(registry.isExchange('XLON'), true);
        assert.equal(registry.isExchange('XXXX'), false);
    });

    test('codes sorted', () => {
        assert.equal(registry.codes().length, 74)
        assert.equal(registry.codes()[0], 'XAMS')
        assert.equal(registry.codes()[73], 'XZAG');
    });

    test('names sorted', () => {
        assert.equal(registry.names().length, 74)
        assert.ok(registry.names().includes('London Stock Exchange'))
        assert.ok(registry.names().includes('New York Stock Exchange'));
    });

    test('listExchanges sorted', () => {
        const codes = registry.listExchanges().map(e => e.code);
        assert.equal(codes.length, 74)
        assert.deepEqual(codes, [...codes].sort());
    });

    test('iteration works', () => {
        const codes = [];
        for (const exchange of registry) {
            codes.push(exchange.code);
        }
        assert.equal(codes.length, 74)
        assert.deepEqual(codes, [...codes].sort());
    });

    test('toJSON summary', () => {
        const d = registry.toJSON();
        assert.equal(d.version, '1.0.0');
        assert.equal(d.exchange_count, 74);
        assert.equal(d.codes.length, 74);
    });

    test('throws on non-string code', () => {
        assert.throws(
            () => registry.exchange(123),
            TypeError
        );
    });
});

// ──────────────────────────────────────────────────────────────
// Exchange properties
// ──────────────────────────────────────────────────────────────

describe('Exchange properties', () => {
    let registry;

    beforeEach(() => {
        registry = new CalendarRegistry(getRegistryPath());
    });

    test('XNYS properties', () => {
        const xnys = registry.get('XNYS');
        assert.equal(xnys.code, 'XNYS');
        assert.equal(xnys.mic, 'XNYS');
        assert.equal(xnys.name, 'New York Stock Exchange');
        assert.equal(xnys.timezone, 'America/New_York');
        assert.deepEqual(xnys.regularHours, { open: '09:30', close: '16:00' });
    });

    test('XLON properties', () => {
        const xlon = registry.get('XLON');
        assert.equal(xlon.code, 'XLON');
        assert.equal(xlon.mic, 'XLON');
        assert.equal(xlon.name, 'London Stock Exchange');
        assert.equal(xlon.timezone, 'Europe/London');
        assert.deepEqual(xlon.regularHours, { open: '08:00', close: '16:30' });
    });

    test('toString method', () => {
        const xnys = registry.get('XNYS');
        const s = xnys.toString();
        assert.ok(s.includes('New York Stock Exchange'));
        assert.ok(s.includes('XNYS'));
    });

    test('toJSON method', () => {
        const xnys = registry.get('XNYS');
        const d = xnys.toJSON();
        assert.equal(d.code, 'XNYS');
        assert.equal(d.name, 'New York Stock Exchange');
        assert.ok(d.holiday_count > 0);
    });

    test('XLON has auction sessions', () => {
        const xlon = registry.get('XLON');
        assert.ok(xlon.sessions.length >= 2);
        const auctions = xlon.sessions.filter(s => s.type === 'auction');
        assert.equal(auctions.length, 2);
    });
});

// ──────────────────────────────────────────────────────────────
// Holiday detection
// ──────────────────────────────────────────────────────────────

describe('Holiday detection', () => {
    let xnys;
    let xlon;

    beforeEach(() => {
        const registry = new CalendarRegistry(getRegistryPath());
        xnys = registry.get('XNYS');
        xlon = registry.get('XLON');
    });

    test('New Year\'s Day is holiday', () => {
        assert.equal(xnys.isHoliday('2025-01-01'), true);
    });

    test('weekend is holiday', () => {
        assert.equal(xnys.isHoliday('2025-03-15'), true); // Saturday
        assert.equal(xnys.isHoliday('2025-03-16'), true); // Sunday
    });

    test('weekday is not holiday', () => {
        assert.equal(xnys.isHoliday('2025-03-14'), false); // Friday
    });

    test('early close is not full holiday', () => {
        assert.equal(xnys.isHoliday('2025-07-03'), false);
    });

    test('Boxing Day is holiday for XLON', () => {
        assert.equal(xlon.isHoliday('2025-12-26'), true);
    });

    test('Easter Monday is holiday for XLON', () => {
        assert.equal(xlon.isHoliday('2025-04-21'), true);
    });

    test('holiday count XNYS', () => {
        assert.equal(xnys.holidayCount(), 62);
    });

    test('holiday count XNYS 2025', () => {
        assert.equal(xnys.holidayCount(2025), 14);
    });

    test('holiday count XLON', () => {
        assert.ok(xlon.holidayCount() > 0);
    });

    test('list holidays sorted', () => {
        const holidays = xnys.listHolidays();
        const dates = holidays.map(h => h.date);
        assert.deepEqual(dates, [...dates].sort());
    });

    test('list holidays year filter', () => {
        const holidays = xnys.listHolidays(2025);
        assert.ok(holidays.every(h => h.date.startsWith('2025-')));
    });
});

// ──────────────────────────────────────────────────────────────
// Early close detection
// ──────────────────────────────────────────────────────────────

describe('Early close detection', () => {
    let xnys;
    let xlon;

    beforeEach(() => {
        const registry = new CalendarRegistry(getRegistryPath());
        xnys = registry.get('XNYS');
        xlon = registry.get('XLON');
    });

    test('XNYS July 3 is early close', () => {
        assert.equal(xnys.isEarlyClose('2025-07-03'), true);
    });

    test('XNYS July 3 time', () => {
        assert.equal(xnys.earlyCloseTime('2025-07-03'), '13:00');
    });

    test('non-early close returns null', () => {
        assert.equal(xnys.earlyCloseTime('2025-07-04'), null);
    });

    test('XLON Christmas Eve is early close', () => {
        assert.equal(xlon.isEarlyClose('2025-12-24'), true);
    });

    test('XLON Christmas Eve time', () => {
        assert.equal(xlon.earlyCloseTime('2025-12-24'), '12:30');
    });

    test('XLON New Year\'s Eve is early close', () => {
        assert.equal(xlon.isEarlyClose('2025-12-31'), true);
    });

    test('early close times differ between exchanges', () => {
        assert.equal(xnys.earlyCloseTime('2025-07-03'), '13:00');
        assert.equal(xlon.earlyCloseTime('2025-12-24'), '12:30');
        assert.notEqual(
            xnys.earlyCloseTime('2025-07-03'),
            xlon.earlyCloseTime('2025-12-24')
        );
    });
});

// ──────────────────────────────────────────────────────────────
// Status at specific date/time
// ──────────────────────────────────────────────────────────────

describe('Status at specific date/time', () => {
    let xnys;
    let xlon;

    beforeEach(() => {
        const registry = new CalendarRegistry(getRegistryPath());
        xnys = registry.get('XNYS');
        xlon = registry.get('XLON');
    });

    test('open during regular hours', () => {
        assert.equal(xnys.statusAt('2025-07-07', '10:00'), SessionStatus.OPEN);
        assert.equal(xnys.statusAt('2025-07-07', '15:00'), SessionStatus.OPEN);
    });

    test('closed on weekend', () => {
        assert.equal(xnys.statusAt('2025-07-05', '10:00'), SessionStatus.CLOSED);
        assert.equal(xnys.statusAt('2025-07-06', '10:00'), SessionStatus.CLOSED);
    });

    test('closed on holiday', () => {
        assert.equal(xnys.statusAt('2025-07-04', '10:00'), SessionStatus.CLOSED);
    });

    test('pre-market', () => {
        assert.equal(xnys.statusAt('2025-07-07', '08:00'), SessionStatus.PRE_MARKET);
    });

    test('after-hours', () => {
        assert.equal(xnys.statusAt('2025-07-07', '17:00'), SessionStatus.AFTER_HOURS);
    });

    test('early close before close time', () => {
        assert.equal(xnys.statusAt('2025-07-03', '10:00'), SessionStatus.EARLY_CLOSE);
    });

    test('early close after close time', () => {
        assert.equal(xnys.statusAt('2025-07-03', '13:30'), SessionStatus.CLOSED);
    });

    test('early close exact close time', () => {
        assert.equal(xnys.statusAt('2025-07-03', '13:00'), SessionStatus.CLOSED);
    });

    test('isOpen during regular hours', () => {
        assert.equal(xnys.isOpen('2025-07-07', '10:00'), true);
    });

    test('isOpen during early close', () => {
        assert.equal(xnys.isOpen('2025-07-03', '10:00'), true);
    });

    test('isOpen after early close', () => {
        assert.equal(xnys.isOpen('2025-07-03', '13:30'), false);
    });

    test('isOpen on holiday', () => {
        assert.equal(xnys.isOpen('2025-07-04', '10:00'), false);
    });

    test('isOpen on weekend', () => {
        assert.equal(xnys.isOpen('2025-07-05', '10:00'), false);
    });

    test('isOpen default time', () => {
        assert.equal(xnys.isOpen('2025-07-07'), true);
    });

    test('XLON hours', () => {
        assert.equal(xlon.statusAt('2025-07-07', '08:30'), SessionStatus.OPEN);
        assert.equal(xlon.statusAt('2025-07-07', '07:00'), SessionStatus.PRE_MARKET);
        assert.equal(xlon.statusAt('2025-07-07', '17:00'), SessionStatus.AFTER_HOURS);
    });
});

// ──────────────────────────────────────────────────────────────
// Date navigation
// ──────────────────────────────────────────────────────────────

describe('Date navigation', () => {
    let xnys;
    let xlon;

    beforeEach(() => {
        const registry = new CalendarRegistry(getRegistryPath());
        xnys = registry.get('XNYS');
        xlon = registry.get('XLON');
    });

    test('next trading day after regular day', () => {
        assert.equal(xnys.nextTradingDay('2025-07-07'), '2025-07-08');
    });

    test('next trading day skips weekend', () => {
        assert.equal(xnys.nextTradingDay('2025-07-03'), '2025-07-07');
    });

    test('next trading day skips holiday', () => {
        assert.equal(xnys.nextTradingDay('2025-07-03'), '2025-07-07');
    });

    test('next trading day early close is trading day', () => {
        assert.equal(xnys.nextTradingDay('2025-07-02'), '2025-07-03');
    });

    test('previous trading day after weekend', () => {
        assert.equal(xnys.previousTradingDay('2025-07-07'), '2025-07-03');
    });

    test('previous trading day skips holiday', () => {
        assert.equal(xnys.previousTradingDay('2025-07-07'), '2025-07-03');
    });

    test('next trading day XLON', () => {
        assert.equal(xlon.nextTradingDay('2025-04-17'), '2025-04-22');
    });

    test('previous trading day XLON', () => {
        assert.equal(xlon.previousTradingDay('2025-04-22'), '2025-04-17');
    });
});

// ──────────────────────────────────────────────────────────────
// Error handling
// ──────────────────────────────────────────────────────────────

describe('Error handling', () => {
    let xnys;

    beforeEach(() => {
        const registry = new CalendarRegistry(getRegistryPath());
        xnys = registry.get('XNYS');
    });

    test('invalid date format', () => {
        assert.throws(
            () => xnys.isHoliday('2025/01/01'),
            /date/
        );
    });

    test('invalid time format', () => {
        assert.throws(
            () => xnys.statusAt('2025-07-07', '10am'),
            /time/
        );
    });

    test('invalid time hours', () => {
        assert.throws(
            () => xnys.statusAt('2025-07-07', '25:00'),
            /time/
        );
    });

    test('invalid time minutes', () => {
        assert.throws(
            () => xnys.statusAt('2025-07-07', '10:60'),
            /time/
        );
    });

    test('nonexistent date', () => {
        assert.throws(
            () => xnys.isHoliday('2025-02-30'),
            /date/
        );
    });

    test('unknown status string', () => {
        assert.throws(
            () => SessionStatus.fromString('not_a_status'),
            /unknown status/
        );
    });

    test('status fromString non-string', () => {
        assert.throws(
            () => SessionStatus.fromString(123),
            TypeError
        );
    });

    test('exchange non-string code', () => {
        const registry = new CalendarRegistry(getRegistryPath());
        assert.throws(
            () => registry.exchange(123),
            TypeError
        );
    });
});

// ──────────────────────────────────────────────────────────────
// SessionStatus
// ──────────────────────────────────────────────────────────────

describe('SessionStatus', () => {
    test('all statuses exist', () => {
        assert.equal(SessionStatus.CLOSED, 'closed');
        assert.equal(SessionStatus.PRE_MARKET, 'pre_market');
        assert.equal(SessionStatus.OPEN, 'open');
        assert.equal(SessionStatus.EARLY_CLOSE, 'early_close');
        assert.equal(SessionStatus.AFTER_HOURS, 'after_hours');
        assert.equal(SessionStatus.LUNCH_BREAK, 'lunch_break');
    });

    test('isTradingStatus', () => {
        assert.equal(SessionStatus.isTradingStatus(SessionStatus.OPEN), true);
        assert.equal(SessionStatus.isTradingStatus(SessionStatus.EARLY_CLOSE), true);
        assert.equal(SessionStatus.isTradingStatus(SessionStatus.CLOSED), false);
        assert.equal(SessionStatus.isTradingStatus(SessionStatus.PRE_MARKET), false);
        assert.equal(SessionStatus.isTradingStatus(SessionStatus.AFTER_HOURS), false);
        assert.equal(SessionStatus.isTradingStatus(SessionStatus.LUNCH_BREAK), false);
    });

    test('fromString case-insensitive', () => {
        assert.equal(SessionStatus.fromString('OPEN'), SessionStatus.OPEN);
        assert.equal(SessionStatus.fromString('open'), SessionStatus.OPEN);
        assert.equal(SessionStatus.fromString('Open'), SessionStatus.OPEN);
        assert.equal(SessionStatus.fromString(' early_close '), SessionStatus.EARLY_CLOSE);
    });

    test('values', () => {
        const values = SessionStatus.values();
        assert.equal(values.length, 6);
        assert.ok(values.includes('open'));
        assert.ok(values.includes('closed'));
    });

    test('keys', () => {
        const keys = SessionStatus.keys();
        assert.equal(keys.length, 6);
        assert.ok(keys.includes('OPEN'));
        assert.ok(keys.includes('CLOSED'));
    });

    test('isValid', () => {
        assert.equal(SessionStatus.isValid('open'), true);
        assert.equal(SessionStatus.isValid('OPEN'), true);
        assert.equal(SessionStatus.isValid('bogus'), false);
        assert.equal(SessionStatus.isValid(null), false);
        assert.equal(SessionStatus.isValid(123), false);
    });
});

// ──────────────────────────────────────────────────────────────
// Minimal custom registry
// ──────────────────────────────────────────────────────────────

describe('Minimal custom registry', () => {
    let registryFile;

    beforeEach(() => {
        registryFile = createTempRegistry();
    });

    test('loads minimal registry', () => {
        const registry = new CalendarRegistry(registryFile);
        assert.equal(registry.exchangeCount, 1);
        assert.equal(registry.size, 1);
    });

    test('gets exchange', () => {
        const registry = new CalendarRegistry(registryFile);
        const test = registry.get('TEST');
        assert.equal(test.code, 'TEST');
        assert.equal(test.name, 'Test Exchange');
    });

    test('holiday detection', () => {
        const registry = new CalendarRegistry(registryFile);
        const test = registry.get('TEST');
        assert.equal(test.isHoliday('2025-01-01'), true);
        assert.equal(test.isHoliday('2025-01-02'), false);
    });

    test('early close detection', () => {
        const registry = new CalendarRegistry(registryFile);
        const test = registry.get('TEST');
        assert.equal(test.isEarlyClose('2025-07-03'), true);
        assert.equal(test.earlyCloseTime('2025-07-03'), '13:00');
        assert.equal(test.statusAt('2025-07-03', '10:00'), SessionStatus.EARLY_CLOSE);
        assert.equal(test.statusAt('2025-07-03', '13:30'), SessionStatus.CLOSED);
    });
});