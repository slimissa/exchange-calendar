'use strict';

/**
 * session.js — SessionStatus enum for exchange calendar states.
 *
 * Defines the possible states of an exchange at any given moment.
 * The enum is used by the Exchange class to report whether the market
 * is open, closed, in pre-market, after-hours, or in an early close.
 *
 * This is the canonical status vocabulary for the entire QuantOS ecosystem.
 * All language wrappers must map to the same semantic states.
 *
 * Immutable by design — use Object.freeze to prevent mutation.
 *
 * @example
 * const { SessionStatus } = require('./session');
 *
 * SessionStatus.OPEN;                    // 'open'
 * SessionStatus.fromString('CLOSED');    // 'closed'
 * SessionStatus.isTradingStatus(SessionStatus.OPEN);  // true
 */

const SessionStatus = Object.freeze({
    /**
     * Market is closed (weekend, holiday, or outside all hours).
     * @type {string}
     */
    CLOSED: 'closed',

    /**
     * Before regular trading hours (extended session).
     * @type {string}
     */
    PRE_MARKET: 'pre_market',

    /**
     * Regular trading hours.
     * @type {string}
     */
    OPEN: 'open',

    /**
     * Early close day, before the early close time.
     * @type {string}
     */
    EARLY_CLOSE: 'early_close',

    /**
     * After regular trading hours (extended session).
     * @type {string}
     */
    AFTER_HOURS: 'after_hours',

    /**
     * Intraday break (exchanges with lunch pauses, e.g. TSE).
     * @type {string}
     */
    LUNCH_BREAK: 'lunch_break',

    /**
     * Convert a string to a SessionStatus value.
     *
     * Accepts case-insensitive input. Throws on unknown input.
     *
     * @param {string} value — The string to convert.
     * @returns {string} The matching SessionStatus value.
     * @throws {TypeError} If value is not a string.
     * @throws {Error} If value does not match any known status.
     *
     * @example
     * SessionStatus.fromString('open');         // 'open'
     * SessionStatus.fromString('CLOSED');       // 'closed'
     * SessionStatus.fromString('early_close');  // 'early_close'
     */
    fromString(value) {
        if (typeof value !== 'string') {
            throw new TypeError(
                `SessionStatus.fromString: expected string, got ${typeof value}`
            );
        }

        const normalized = value.trim().toLowerCase();

        for (const [key, val] of Object.entries(SessionStatus)) {
            // Skip methods — only compare string values
            if (typeof val === 'string' && val === normalized) {
                return SessionStatus[key];
            }
        }

        const valid = Object.values(SessionStatus)
            .filter(v => typeof v === 'string')
            .join(', ');

        throw new Error(
            `SessionStatus.fromString: unknown status '${value}'. Valid values: ${valid}`
        );
    },

    /**
     * Return true if the given status represents a state where trading
     * is currently possible (regular hours or early close before close).
     *
     * @param {string} status — A SessionStatus value.
     * @returns {boolean} True if trading is possible.
     *
     * @example
     * SessionStatus.isTradingStatus(SessionStatus.OPEN);         // true
     * SessionStatus.isTradingStatus(SessionStatus.EARLY_CLOSE);  // true
     * SessionStatus.isTradingStatus(SessionStatus.CLOSED);       // false
     * SessionStatus.isTradingStatus(SessionStatus.PRE_MARKET);   // false
     */
    isTradingStatus(status) {
        return (
            status === SessionStatus.OPEN ||
            status === SessionStatus.EARLY_CLOSE
        );
    },

    /**
     * Return all valid status values as an array.
     *
     * @returns {string[]} Array of status values.
     *
     * @example
     * SessionStatus.values();  // ['closed', 'pre_market', 'open', ...]
     */
    values() {
        return Object.values(SessionStatus).filter(v => typeof v === 'string');
    },

    /**
     * Return all valid status keys as an array.
     *
     * @returns {string[]} Array of status keys.
     *
     * @example
     * SessionStatus.keys();  // ['CLOSED', 'PRE_MARKET', 'OPEN', ...]
     */
    keys() {
        return Object.keys(SessionStatus).filter(k => typeof SessionStatus[k] === 'string');
    },

    /**
     * Return true if the given value is a valid SessionStatus.
     *
     * @param {*} value — Any value to test.
     * @returns {boolean} True if value is a valid SessionStatus.
     *
     * @example
     * SessionStatus.isValid('open');     // true
     * SessionStatus.isValid('OPEN');     // true
     * SessionStatus.isValid('bogus');    // false
     * SessionStatus.isValid(null);       // false
     */
    isValid(value) {
        if (typeof value !== 'string') {
            return false;
        }
        const normalized = value.trim().toLowerCase();
        return SessionStatus.values().includes(normalized);
    },
});

module.exports = { SessionStatus };