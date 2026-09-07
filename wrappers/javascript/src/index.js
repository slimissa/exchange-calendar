'use strict';

/**
 * index.js — Public entry point for the exchange-calendar package.
 *
 * This is the only file consumers should require. It re-exports the
 * three public classes from their respective modules.
 *
 * @example
 * const { CalendarRegistry, SessionStatus, Exchange } = require('exchange-calendar');
 *
 * const registry = new CalendarRegistry('calendar.json');
 * const xnys = registry.exchange('XNYS');
 *
 * if (xnys.isOpen('2025-07-03', '10:00')) {
 *     console.log('NYSE is open');
 * }
 */

const { SessionStatus } = require('./session');
const { Exchange } = require('./exchange');
const { CalendarRegistry } = require('./registry');

/**
 * Package version. Must match the registry version and package.json.
 * @type {string}
 */
const VERSION = '1.0.0';

module.exports = {
    SessionStatus,
    Exchange,
    CalendarRegistry,
    VERSION,
};

// Also export named properties for destructuring
module.exports.default = {
    SessionStatus,
    Exchange,
    CalendarRegistry,
    VERSION,
};

// Support both CommonJS and ESM import styles
// ESM: import { CalendarRegistry } from 'exchange-calendar'
// CJS: const { CalendarRegistry } = require('exchange-calendar')