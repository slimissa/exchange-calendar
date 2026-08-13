/**
 * index.d.ts — TypeScript definitions for exchange-calendar-registry.
 *
 * Provides full type safety for consumers using TypeScript.
 * All types mirror the JavaScript implementation exactly.
 *
 * @example
 * import { CalendarRegistry, Exchange, SessionStatus } from 'exchange-calendar-registry';
 *
 * const registry: CalendarRegistry = new CalendarRegistry('calendar.json');
 * const xnys: Exchange | null = registry.exchange('XNYS');
 */

declare module 'exchange-calendar-registry' {
    /**
     * Session status values.
     * Matches the string values used in the registry JSON.
     */
    export type SessionStatusValue =
        | 'closed'
        | 'pre_market'
        | 'open'
        | 'early_close'
        | 'after_hours'
        | 'lunch_break';

    /**
     * SessionStatus — canonical status vocabulary.
     * Immutable frozen object with string constants.
     */
    export const SessionStatus: {
        readonly CLOSED: 'closed';
        readonly PRE_MARKET: 'pre_market';
        readonly OPEN: 'open';
        readonly EARLY_CLOSE: 'early_close';
        readonly AFTER_HOURS: 'after_hours';
        readonly LUNCH_BREAK: 'lunch_break';

        /**
         * Convert a string to a SessionStatus value.
         * Case-insensitive. Throws on unknown input.
         */
        fromString(value: string): SessionStatusValue;

        /**
         * Return true if status represents a trading state.
         * True for OPEN and EARLY_CLOSE only.
         */
        isTradingStatus(status: SessionStatusValue): boolean;

        /**
         * Return all valid status values.
         */
        values(): SessionStatusValue[];

        /**
         * Return all valid status keys (UPPER_SNAKE_CASE).
         */
        keys(): string[];

        /**
         * Return true if value is a valid SessionStatus.
         */
        isValid(value: unknown): value is SessionStatusValue;
    };

    /**
     * Regular trading hours for an exchange.
     */
    export interface RegularHours {
        open: string;   // HH:MM, e.g., "09:30"
        close: string;  // HH:MM, e.g., "16:00"
    }

    /**
     * Extended trading hours (pre-market and after-hours).
     */
    export interface ExtendedHours {
        pre_market?: RegularHours;
        after_hours?: RegularHours;
    }

    /**
     * A session within a trading day (auction or lunch break).
     */
    export interface Session {
        type: 'lunch_break' | 'auction' | 'other';
        open?: string;   // Required for lunch_break
        close?: string;  // Required for lunch_break
        at?: string;     // Required for auction
    }

    /**
     * A holiday or special session entry.
     */
    export interface HolidayEntry {
        date: string;              // YYYY-MM-DD
        name: string;
        status: 'closed' | 'early_close' | 'delayed_open' | 'special_session';
        early_close_time?: string; // HH:MM, required when status is early_close
        delayed_open_time?: string; // HH:MM, required when status is delayed_open
        source_url?: string;
    }

    /**
     * The holidays section of an exchange calendar.
     */
    export interface Holidays {
        explicit: HolidayEntry[];
        generated: HolidayEntry[];
    }

    /**
     * Raw exchange data as found in calendar.json.
     */
    export interface ExchangeData {
        code: string;
        name: string;
        mic: string;
        timezone: string;
        regular_hours: RegularHours;
        extended_hours?: ExtendedHours;
        sessions?: Session[];
        holidays: Holidays;
        ad_hoc_closures?: HolidayEntry[];
        generation_range?: [string, string];
    }

    /**
     * Exchange — represents a single exchange calendar.
     * Immutable after construction.
     */
    export class Exchange {
        /**
         * MIC code (e.g., "XNYS").
         */
        readonly code: string;

        /**
         * Full exchange name (e.g., "New York Stock Exchange").
         */
        readonly name: string;

        /**
         * ISO 10383 MIC, equal to code.
         */
        readonly mic: string;

        /**
         * IANA timezone (e.g., "America/New_York").
         */
        readonly timezone: string;

        /**
         * Regular trading hours.
         */
        readonly regularHours: RegularHours;

        /**
         * Extended trading hours.
         */
        readonly extendedHours: ExtendedHours;

        /**
         * Auction and lunch break sessions.
         */
        readonly sessions: Session[];

        /**
         * Create an Exchange from registry data.
         * @throws Error if data is malformed.
         */
        constructor(data: ExchangeData);

        /**
         * Return true if the market is fully closed on this date.
         * Includes weekends and explicit/generated holidays.
         */
        isHoliday(dateStr: string): boolean;

        /**
         * Return true if this date has an early close.
         */
        isEarlyClose(dateStr: string): boolean;

        /**
         * Return the early close time, or null if not an early close day.
         */
        earlyCloseTime(dateStr: string): string | null;

        /**
         * Return the full session status at a specific date and time.
         */
        statusAt(dateStr: string, timeStr: string): SessionStatusValue;

        /**
         * Return true if the market is open for trading.
         * @param dateStr ISO date (YYYY-MM-DD)
         * @param timeStr 24-hour time (HH:MM), defaults to "10:00"
         */
        isOpen(dateStr: string, timeStr?: string): boolean;

        /**
         * Return the next trading day after the given date.
         * Skips weekends and full holidays.
         */
        nextTradingDay(dateStr: string): string;

        /**
         * Return the previous trading day before the given date.
         * Skips weekends and full holidays.
         */
        previousTradingDay(dateStr: string): string;

        /**
         * Return the number of holidays, optionally filtered by year.
         */
        holidayCount(year?: number): number;

        /**
         * Return a sorted list of holiday entries.
         * Optionally filtered by year.
         */
        listHolidays(year?: number): HolidayEntry[];

        /**
         * Return a human-readable string representation.
         */
        toString(): string;

        /**
         * Return a summary object for JSON serialization.
         */
        toJSON(): object;
    }

    /**
     * CalendarRegistry — loads and queries the exchange calendar registry.
     * Immutable after construction.
     */
    export class CalendarRegistry {
        /**
         * Registry version (from meta.version).
         */
        readonly version: string;

        /**
         * Number of exchanges in the registry.
         */
        readonly exchangeCount: number;

        /**
         * Load and parse the registry from a JSON file.
         * @throws Error if file not found or invalid.
         */
        constructor(registryPath?: string);

        /**
         * Return the Exchange with the given MIC code.
         * Case-insensitive. Returns null if not found.
         */
        exchange(code: string): Exchange | null;

        /**
         * Return the Exchange with the given MIC code.
         * Throws if not found.
         */
        get(code: string): Exchange;

        /**
         * Return true if the given MIC code exists.
         */
        has(code: string): boolean;

        /**
         * Alias for has().
         */
        isExchange(code: string): boolean;

        /**
         * Return all exchanges, sorted by MIC code.
         */
        listExchanges(): Exchange[];

        /**
         * Return all MIC codes, sorted alphabetically.
         */
        codes(): string[];

        /**
         * Return all exchange names, sorted by MIC code.
         */
        names(): string[];

        /**
         * Return a summary object for JSON serialization.
         */
        toJSON(): object;

        /**
         * Return a human-readable string representation.
         */
        toString(): string;

        /**
         * Number of exchanges.
         */
        readonly size: number;

        /**
         * Alias for size.
         */
        readonly length: number;

        /**
         * Make the registry iterable.
         */
        [Symbol.iterator](): Iterator<Exchange>;
    }

    /**
     * Package version.
     */
    export const VERSION: string;
}