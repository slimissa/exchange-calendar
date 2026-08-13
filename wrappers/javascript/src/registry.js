'use strict';

/**
 * registry.js — CalendarRegistry class for loading the exchange calendar registry.
 *
 * This class is the entry point for consuming the registry. It loads the
 * single-file distribution artifact (calendar.json) produced by tools/build.py
 * and provides access to individual exchanges by MIC code.
 *
 * @example
 * const { CalendarRegistry } = require('./registry');
 *
 * const registry = new CalendarRegistry('calendar.json');
 * const xnys = registry.exchange('XNYS');
 *
 * if (xnys.isOpen('2025-07-03', '10:00')) {
 *     console.log('NYSE is open');
 * }
 *
 * for (const exchange of registry) {
 *     console.log(exchange.toString());
 * }
 *
 * console.log(`Total exchanges: ${registry.exchangeCount}`);
 */

const fs = require('fs');
const path = require('path');
const { Exchange } = require('./exchange');

class CalendarRegistry {
    /**
     * Load and parse the registry from a JSON file.
     *
     * @param {string} registryPath — Path to calendar.json.
     *                                Can be relative or absolute.
     *
     * @throws {Error} If file not found.
     * @throws {SyntaxError} If JSON is malformed.
     * @throws {Error} If structure is invalid.
     *
     * @example
     * const registry = new CalendarRegistry('./calendar.json');
     * const registry2 = new CalendarRegistry('/path/to/calendar.json');
     */
    constructor(registryPath = 'calendar.json') {
        this._validatePath(registryPath);

        const resolvedPath = path.resolve(registryPath);

        if (!fs.existsSync(resolvedPath)) {
            throw new Error(`CalendarRegistry: file not found: ${resolvedPath}`);
        }

        let data;
        try {
            const raw = fs.readFileSync(resolvedPath, 'utf8');
            data = JSON.parse(raw);
        } catch (e) {
            if (e instanceof SyntaxError) {
                throw new SyntaxError(`CalendarRegistry: invalid JSON: ${e.message}`);
            }
            throw e;
        }

        this._validateRegistry(data);

        const meta = data.meta || {};
        this.version = meta.version || 'unknown';
        this.exchangeCount = meta.exchange_count || 0;

        /** @type {Map<string, Exchange>} */
        this.exchanges = new Map();

        for (const exchangeData of data.exchanges || []) {
            const exchange = new Exchange(exchangeData);
            this.exchanges.set(exchange.code, exchange);
        }
    }

    // ──────────────────────────────────────────────────────────
    // Internal validation
    // ──────────────────────────────────────────────────────────

    _validatePath(registryPath) {
        if (typeof registryPath !== 'string') {
            throw new TypeError(
                `CalendarRegistry: path must be a string, got ${typeof registryPath}`
            );
        }
        if (registryPath.trim() === '') {
            throw new Error('CalendarRegistry: path must not be empty');
        }
    }

    _validateRegistry(data) {
        if (!data || typeof data !== 'object' || Array.isArray(data)) {
            throw new Error('CalendarRegistry: registry must be a JSON object');
        }

        if (!('meta' in data)) {
            throw new Error("CalendarRegistry: missing 'meta' field");
        }

        if (!('exchanges' in data)) {
            throw new Error("CalendarRegistry: missing 'exchanges' field");
        }

        if (!Array.isArray(data.exchanges)) {
            throw new Error(
                `CalendarRegistry: 'exchanges' must be an array, got ${typeof data.exchanges}`
            );
        }

        // Check for duplicate codes
        const codes = data.exchanges
            .filter(e => 'code' in e)
            .map(e => e.code);

        const seen = new Set();
        const duplicates = new Set();

        for (const code of codes) {
            if (seen.has(code)) {
                duplicates.add(code);
            }
            seen.add(code);
        }

        if (duplicates.size > 0) {
            throw new Error(
                `CalendarRegistry: duplicate exchange codes: ${Array.from(duplicates).join(', ')}`
            );
        }
    }

    // ──────────────────────────────────────────────────────────
    // Public API — lookup
    // ──────────────────────────────────────────────────────────

    /**
     * Return the Exchange with the given MIC code.
     * Case-insensitive — "xnys" works too.
     *
     * @param {string} code — MIC code (e.g., "XNYS").
     * @returns {Exchange|null} The Exchange, or null if not found.
     */
    exchange(code) {
        if (typeof code !== 'string') {
            throw new TypeError(
                `CalendarRegistry.exchange: expected string, got ${typeof code}`
            );
        }
        return this.exchanges.get(code.toUpperCase()) || null;
    }

    /**
     * Return the Exchange with the given MIC code, throwing if not found.
     *
     * @param {string} code — MIC code (case-insensitive).
     * @returns {Exchange} The requested exchange.
     * @throws {Error} If exchange not found.
     */
    get(code) {
        const exchange = this.exchange(code);
        if (exchange === null) {
            const available = this.codes().join(', ');
            throw new Error(
                `CalendarRegistry.get: exchange '${code}' not found. Available: ${available}`
            );
        }
        return exchange;
    }

    /**
     * Return true if the given MIC code exists in the registry.
     *
     * @param {string} code — MIC code (case-insensitive).
     * @returns {boolean} True if exchange exists.
     */
    has(code) {
        return this.exchange(code) !== null;
    }

    /**
     * Alias for has().
     *
     * @param {string} code — MIC code (case-insensitive).
     * @returns {boolean} True if exchange exists.
     */
    isExchange(code) {
        return this.has(code);
    }

    // ──────────────────────────────────────────────────────────
    // Public API — listing
    // ──────────────────────────────────────────────────────────

    /**
     * Return all exchanges, sorted by MIC code.
     *
     * @returns {Exchange[]} Sorted array of Exchange objects.
     */
    listExchanges() {
        return this.codes().map(code => this.exchanges.get(code));
    }

    /**
     * Return all MIC codes, sorted alphabetically.
     *
     * @returns {string[]} Sorted array of MIC codes.
     */
    codes() {
        return Array.from(this.exchanges.keys()).sort();
    }

    /**
     * Return all exchange names, sorted by MIC code.
     *
     * @returns {string[]} Array of exchange names.
     */
    names() {
        return this.codes().map(code => this.exchanges.get(code).name);
    }

    // ──────────────────────────────────────────────────────────
    // Public API — convenience
    // ──────────────────────────────────────────────────────────

    /**
     * Return the registry as a plain object with summary info.
     *
     * @returns {Object} { version, exchange_count, codes }
     */
    toJSON() {
        return {
            version: this.version,
            exchange_count: this.exchangeCount,
            codes: this.codes(),
        };
    }

    /**
     * Return a human-readable string representation.
     *
     * @returns {string} Summary string.
     */
    toString() {
        return `Exchange Calendar Registry v${this.version} (${this.exchangeCount} exchanges)`;
    }

    // ──────────────────────────────────────────────────────────
    // Iteration protocol
    // ──────────────────────────────────────────────────────────

    /**
     * Make the registry iterable.
     *
     * @returns {Iterator<Exchange>} Iterator over exchanges sorted by code.
     */
    [Symbol.iterator]() {
        const exchanges = this.listExchanges();
        let index = 0;

        return {
            next: () => {
                if (index < exchanges.length) {
                    return { value: exchanges[index++], done: false };
                }
                return { value: undefined, done: true };
            },
        };
    }

    /**
     * Return the number of exchanges.
     *
     * @returns {number} Exchange count.
     */
    get size() {
        return this.exchanges.size;
    }

    /**
     * Alias for size.
     *
     * @returns {number} Exchange count.
     */
    get length() {
        return this.exchanges.size;
    }
}

module.exports = { CalendarRegistry };