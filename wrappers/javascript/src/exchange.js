'use strict';

/**
 * exchange.js — Exchange class for querying a single exchange calendar.
 *
 * This is the core class in the JavaScript wrapper. It represents one
 * exchange and answers questions like:
 *   - Is the market open right now?
 *   - Is this date a holiday?
 *   - Is this date an early close?
 *   - What time does the market close today?
 *   - What is the next trading day?
 *
 * The class is immutable after construction. All date/time arguments use
 * ISO 8601 date strings (YYYY-MM-DD) and 24-hour time strings (HH:MM).
 *
 * @example
 * const { Exchange } = require('./exchange');
 *
 * const xnys = new Exchange(exchangeData);
 * xnys.isOpen('2025-07-03', '10:00');   // true (before 13:00 early close)
 * xnys.isOpen('2025-07-03', '13:30');   // false (after early close)
 * xnys.isHoliday('2025-07-04');         // true (Independence Day)
 * xnys.earlyCloseTime('2025-07-03');    // "13:00"
 * xnys.nextTradingDay('2025-07-03');    // "2025-07-07" (Monday)
 */

const { SessionStatus } = require('./session');

class Exchange {
    /**
     * Create an Exchange from a registry data object.
     *
     * @param {Object} data — Exchange data as found in calendar.json.
     * @param {string} data.code — MIC code (e.g., "XNYS").
     * @param {string} data.name — Full exchange name.
     * @param {string} data.mic — ISO 10383 MIC, equal to code.
     * @param {string} data.timezone — IANA timezone (e.g., "America/New_York").
     * @param {Object} data.regular_hours — { open: "09:30", close: "16:00" }.
     * @param {Object} [data.extended_hours] — Pre-market and after-hours.
     * @param {Array} [data.sessions] — Auction and lunch break sessions.
     * @param {Object} data.holidays — { explicit: [...], generated: [...] }.
     *
     * @throws {Error} If required fields are missing or malformed.
     */
    constructor(data) {
        this._validateData(data);

        this.code = data.code;
        this.name = data.name;
        this.mic = data.mic;
        this.timezone = data.timezone;
        this.weekendDays = data.weekend_days || [5, 6];
        this.regularHours = data.regular_hours;
        this.extendedHours = data.extended_hours || {};
        this.sessions = data.sessions || [];

        const holidays = data.holidays || {};
        const explicit = holidays.explicit || [];
        const generated = holidays.generated || [];

        // Build lookup maps for O(1) date queries
        this._holidayByDate = new Map();
        this._statusByDate = new Map();
        this._earlyCloseTimeByDate = new Map();

        for (const entry of [...explicit, ...generated]) {
            this._indexEntry(entry);
        }
    }

    // ──────────────────────────────────────────────────────────
    // Data validation
    // ──────────────────────────────────────────────────────────

    _validateData(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Exchange: data must be an object');
        }

        const required = ['code', 'name', 'mic', 'timezone', 'regular_hours'];
        for (const field of required) {
            if (!(field in data)) {
                throw new Error(`Exchange: missing required field '${field}'`);
            }
        }

        if (!data.regular_hours.open || !data.regular_hours.close) {
            throw new Error("Exchange: regular_hours must have 'open' and 'close'");
        }

        Exchange._validateTimeFormat(data.regular_hours.open);
        Exchange._validateTimeFormat(data.regular_hours.close);

        if (data.code !== data.mic) {
            throw new Error(
                `Exchange: code '${data.code}' must equal mic '${data.mic}'`
            );
        }
    }

    static _validateTimeFormat(timeStr) {
        if (typeof timeStr !== 'string') {
            throw new Error(`Exchange: invalid time format '${timeStr}'. Expected HH:MM.`);
        }
        const match = timeStr.match(/^([01]\d|2[0-3]):([0-5]\d)$/);
        if (!match) {
            throw new Error(`Exchange: invalid time format '${timeStr}'. Expected HH:MM.`);
        }
    }

    static _validateDateFormat(dateStr) {
        if (typeof dateStr !== 'string') {
            throw new Error(`Exchange: invalid date format '${dateStr}'. Expected YYYY-MM-DD.`);
        }
        const match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (!match) {
            throw new Error(`Exchange: invalid date format '${dateStr}'. Expected YYYY-MM-DD.`);
        }

        const year = parseInt(match[1], 10);
        const month = parseInt(match[2], 10);
        const day = parseInt(match[3], 10);

        const d = new Date(Date.UTC(year, month - 1, day));
        if (
            d.getUTCFullYear() !== year ||
            d.getUTCMonth() !== month - 1 ||
            d.getUTCDate() !== day
        ) {
            throw new Error(`Exchange: invalid date '${dateStr}'. Date does not exist.`);
        }
    }

    // ──────────────────────────────────────────────────────────
    // Internal indexing
    // ──────────────────────────────────────────────────────────

    _indexEntry(entry) {
        const dateStr = entry.date;
        const status = entry.status || 'closed';

        this._holidayByDate.set(dateStr, entry);
        this._statusByDate.set(dateStr, status);

        if (status === 'early_close' && entry.early_close_time) {
            this._earlyCloseTimeByDate.set(dateStr, entry.early_close_time);
        }
    }

    // ──────────────────────────────────────────────────────────
    // Date helpers
    // ──────────────────────────────────────────────────────────

    _isWeekend(dateStr) {
        Exchange._validateDateFormat(dateStr);
        const d = new Date(`${dateStr}T00:00:00Z`);
        // getUTCDay() is 0=Sunday..6=Saturday. weekend_days is stored using
        // 0=Monday..6=Sunday (matching the Python wrapper / stored data),
        // so convert before comparing — do not compare raw getUTCDay()
        // output against weekend_days directly.
        const isoDay = (d.getUTCDay() + 6) % 7; // 0=Monday..6=Sunday
        return this.weekendDays.includes(isoDay);
    }

    _isHoliday(dateStr) {
        Exchange._validateDateFormat(dateStr);
        return this._statusByDate.get(dateStr) === 'closed';
    }

    _isEarlyCloseDay(dateStr) {
        Exchange._validateDateFormat(dateStr);
        return this._earlyCloseTimeByDate.has(dateStr);
    }

    // ──────────────────────────────────────────────────────────
    // Public API — holiday queries
    // ──────────────────────────────────────────────────────────

    /**
     * Return true if the market is fully closed on this date.
     * Includes weekends and explicit/generated holidays.
     *
     * @param {string} dateStr — ISO date (YYYY-MM-DD).
     * @returns {boolean} True if market closed all day.
     */
    isHoliday(dateStr) {
        if (this._isWeekend(dateStr)) {
            return true;
        }
        return this._isHoliday(dateStr);
    }

    /**
     * Return true if this date has an early close.
     *
     * @param {string} dateStr — ISO date (YYYY-MM-DD).
     * @returns {boolean} True if market closes early.
     */
    isEarlyClose(dateStr) {
        return this._isEarlyCloseDay(dateStr);
    }

    /**
     * Return the early close time for this date, or null if not an early close.
     *
     * @param {string} dateStr — ISO date (YYYY-MM-DD).
     * @returns {string|null} Early close time as HH:MM, or null.
     */
    earlyCloseTime(dateStr) {
        return this._earlyCloseTimeByDate.get(dateStr) || null;
    }

    // ──────────────────────────────────────────────────────────
    // Public API — status
    // ──────────────────────────────────────────────────────────

    /**
     * Return the full session status at a specific date and time.
     *
     * Checks in order:
     *   1. Weekend → CLOSED
     *   2. Full holiday → CLOSED
     *   3. Early close day and time >= early_close_time → CLOSED
     *   4. Lunch break (if configured) → LUNCH_BREAK
     *   5. Before regular open → PRE_MARKET
     *   6. After regular close → AFTER_HOURS
     *   7. Otherwise → OPEN (or EARLY_CLOSE on early close day)
     *
     * @param {string} dateStr — ISO date (YYYY-MM-DD).
     * @param {string} timeStr — 24-hour time (HH:MM), interpreted as
     *   this exchange's LOCAL time (per its `timezone` field), NOT
     *   UTC and not the caller's local time. This wrapper does no
     *   timezone conversion -- `timezone` is exposed for
     *   informational purposes only and is not read by any
     *   status/date logic here. If you have a UTC or other-zone
     *   timestamp, convert it to this exchange's local time yourself
     *   before calling statusAt().
     * @returns {string} SessionStatus value.
     */
    statusAt(dateStr, timeStr) {
        Exchange._validateDateFormat(dateStr);
        Exchange._validateTimeFormat(timeStr);

        // 1. Weekend
        if (this._isWeekend(dateStr)) {
            return SessionStatus.CLOSED;
        }

        // 2. Full holiday
        if (this._isHoliday(dateStr)) {
            return SessionStatus.CLOSED;
        }

        // 3. Early close day — check if past the early close time
        const isEarlyCloseDay = this._isEarlyCloseDay(dateStr);
        if (isEarlyCloseDay) {
            const closeTime = this._earlyCloseTimeByDate.get(dateStr);
            if (timeStr >= closeTime) {
                return SessionStatus.CLOSED;
            }
        }

        // 4. Lunch break
        for (const session of this.sessions) {
            if (session.type === 'lunch_break') {
                const breakOpen = session.open;
                const breakClose = session.close;
                if (breakOpen && breakClose && breakOpen <= timeStr && timeStr < breakClose) {
                    return SessionStatus.LUNCH_BREAK;
                }
            }
        }

        // 5. Before regular open
        if (timeStr < this.regularHours.open) {
            return SessionStatus.PRE_MARKET;
        }

        // 6. After regular close
        if (timeStr >= this.regularHours.close) {
            return SessionStatus.AFTER_HOURS;
        }

        // 7. Within regular hours
        if (isEarlyCloseDay) {
            return SessionStatus.EARLY_CLOSE;
        }
        return SessionStatus.OPEN;
    }

    /**
     * Return true if the market is open for trading at the given moment.
     * Convenience wrapper around statusAt().
     *
     * @param {string} dateStr — ISO date (YYYY-MM-DD).
     * @param {string} [timeStr='10:00'] — 24-hour time (HH:MM).
     * @returns {boolean} True if trading is possible.
     */
    isOpen(dateStr, timeStr = '10:00') {
        const status = this.statusAt(dateStr, timeStr);
        return SessionStatus.isTradingStatus(status);
    }

    // ──────────────────────────────────────────────────────────
    // Public API — date navigation
    // ──────────────────────────────────────────────────────────

    /**
     * Return the next trading day after the given date.
     * Skips weekends and full holidays. Early close days count.
     *
     * @param {string} dateStr — ISO date (YYYY-MM-DD).
     * @returns {string} ISO date of the next trading day.
     */
    nextTradingDay(dateStr) {
        Exchange._validateDateFormat(dateStr);

        const d = new Date(`${dateStr}T00:00:00Z`);
        d.setUTCDate(d.getUTCDate() + 1);

        for (let i = 0; i < 30; i++) {
            const candidate = d.toISOString().slice(0, 10);
            if (!this.isHoliday(candidate)) {
                return candidate;
            }
            d.setUTCDate(d.getUTCDate() + 1);
        }

        throw new Error(`Exchange: no trading day found within 30 days after ${dateStr}`);
    }

    /**
     * Return the previous trading day before the given date.
     * Skips weekends and full holidays. Early close days count.
     *
     * @param {string} dateStr — ISO date (YYYY-MM-DD).
     * @returns {string} ISO date of the previous trading day.
     */
    previousTradingDay(dateStr) {
        Exchange._validateDateFormat(dateStr);

        const d = new Date(`${dateStr}T00:00:00Z`);
        d.setUTCDate(d.getUTCDate() - 1);

        for (let i = 0; i < 30; i++) {
            const candidate = d.toISOString().slice(0, 10);
            if (!this.isHoliday(candidate)) {
                return candidate;
            }
            d.setUTCDate(d.getUTCDate() - 1);
        }

        throw new Error(`Exchange: no trading day found within 30 days before ${dateStr}`);
    }

    // ──────────────────────────────────────────────────────────
    // Public API — metadata
    // ──────────────────────────────────────────────────────────

    /**
     * Return the number of explicit holidays in the registry.
     *
     * @param {number} [year] — Optional year filter.
     * @returns {number} Holiday count.
     */
    holidayCount(year = null) {
        if (year === null) {
            return this._holidayByDate.size;
        }

        const prefix = `${year}-`;
        let count = 0;
        for (const dateStr of this._holidayByDate.keys()) {
            if (dateStr.startsWith(prefix)) {
                count++;
            }
        }
        return count;
    }

    /**
     * Return a sorted list of holiday entries.
     *
     * @param {number} [year] — Optional year filter.
     * @returns {Array<Object>} Sorted holiday entries.
     */
    listHolidays(year = null) {
        const entries = Array.from(this._holidayByDate.values());

        if (year !== null) {
            const prefix = `${year}-`;
            return entries
                .filter(e => e.date.startsWith(prefix))
                .sort((a, b) => a.date.localeCompare(b.date));
        }

        return entries.sort((a, b) => a.date.localeCompare(b.date));
    }

    // ──────────────────────────────────────────────────────────
    // Dunder methods
    // ──────────────────────────────────────────────────────────

    toString() {
        return `${this.name} (${this.code})`;
    }

    toJSON() {
        return {
            code: this.code,
            name: this.name,
            mic: this.mic,
            timezone: this.timezone,
            regular_hours: this.regularHours,
            extended_hours: this.extendedHours,
            sessions: this.sessions,
            holiday_count: this._holidayByDate.size,
        };
    }
}

module.exports = { Exchange };