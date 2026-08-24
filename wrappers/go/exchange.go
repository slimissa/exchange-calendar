package exchangecalendar

import (
	"fmt"
	"sort"
	"strings"
	"time"
)

// RegularHours represents the regular trading hours of an exchange.
type RegularHours struct {
	Open  string `json:"open"`  // HH:MM, e.g., "09:30"
	Close string `json:"close"` // HH:MM, e.g., "16:00"
}

// ExtendedHours represents pre-market and after-hours trading sessions.
type ExtendedHours struct {
	PreMarket  *RegularHours `json:"pre_market,omitempty"`
	AfterHours *RegularHours `json:"after_hours,omitempty"`
}

// Session represents a non-trading period within a regular trading day
// (e.g., lunch break or auction).
type Session struct {
	Type  string `json:"type"`            // "lunch_break", "auction", "other"
	Open  string `json:"open,omitempty"`  // Required for lunch_break
	Close string `json:"close,omitempty"` // Required for lunch_break
	At    string `json:"at,omitempty"`    // Required for auction
}

// HolidayEntry represents a single holiday or special session.
type HolidayEntry struct {
	Date           string `json:"date"`                      // YYYY-MM-DD
	Name           string `json:"name"`                      // Human-readable name
	Status         string `json:"status"`                    // "closed", "early_close", etc.
	EarlyCloseTime string `json:"early_close_time,omitempty"` // HH:MM when status is early_close
	DelayedOpenTime string `json:"delayed_open_time,omitempty"` // HH:MM when status is delayed_open
	SourceURL      string `json:"source_url,omitempty"`       // Source citation
}

// ExchangeData represents the raw JSON structure for one exchange in calendar.json.
type ExchangeData struct {
	Code          string         `json:"code"`
	Name          string         `json:"name"`
	MIC           string         `json:"mic"`
	Timezone      string         `json:"timezone"`
	WeekendDays   []int          `json:"weekend_days,omitempty"`
	RegularHours  RegularHours   `json:"regular_hours"`
	ExtendedHours ExtendedHours  `json:"extended_hours,omitempty"`
	Sessions      []Session      `json:"sessions,omitempty"`
	Holidays      HolidaysData   `json:"holidays"`
	AdHocClosures []HolidayEntry `json:"ad_hoc_closures,omitempty"`
	GenerationRange []string     `json:"generation_range,omitempty"`
}

// HolidaysData holds explicit and generated holiday entries.
type HolidaysData struct {
	Explicit  []HolidayEntry `json:"explicit"`
	Generated []HolidayEntry `json:"generated"`
}

// Exchange represents a single exchange calendar.
//
// The struct is immutable after construction. All exported fields are
// read-only by convention — do not modify them.
type Exchange struct {
	Code         string
	Name         string
	MIC          string
	Timezone     string
	WeekendDays  []int
	RegularHours RegularHours
	ExtendedHours ExtendedHours
	Sessions     []Session

	// Unexported lookup maps for O(1) queries
	holidayByDate       map[string]HolidayEntry
	statusByDate        map[string]string
	earlyCloseTimeByDate map[string]string
}

// NewExchange creates an Exchange from raw registry data.
//
// Returns an error if required fields are missing or malformed.
func NewExchange(data ExchangeData) (*Exchange, error) {
	if err := validateExchangeData(data); err != nil {
		return nil, err
	}

	e := &Exchange{
		Code:          data.Code,
		Name:          data.Name,
		MIC:           data.MIC,
		Timezone:      data.Timezone,
		WeekendDays:   weekendDaysOrDefault(data.WeekendDays),
		RegularHours:  data.RegularHours,
		ExtendedHours: data.ExtendedHours,
		Sessions:      data.Sessions,

		holidayByDate:        make(map[string]HolidayEntry),
		statusByDate:         make(map[string]string),
		earlyCloseTimeByDate: make(map[string]string),
	}

	// Index all holidays
	for _, entry := range append(data.Holidays.Explicit, data.Holidays.Generated...) {
		e.indexEntry(entry)
	}

	return e, nil
}

// MustNewExchange creates an Exchange or panics on error.
//
// Use only with known-valid data.
func MustNewExchange(data ExchangeData) *Exchange {
	e, err := NewExchange(data)
	if err != nil {
		panic(err)
	}
	return e
}

// ──────────────────────────────────────────────────────────────
// Internal validation
// ──────────────────────────────────────────────────────────────

func validateExchangeData(data ExchangeData) error {
	if data.Code == "" {
		return fmt.Errorf("exchange: missing code")
	}
	if data.Name == "" {
		return fmt.Errorf("exchange: missing name")
	}
	if data.MIC == "" {
		return fmt.Errorf("exchange: missing mic")
	}
	if data.Code != data.MIC {
		return fmt.Errorf("exchange: code %q must equal mic %q", data.Code, data.MIC)
	}
	if data.Timezone == "" {
		return fmt.Errorf("exchange: missing timezone")
	}
	if data.RegularHours.Open == "" || data.RegularHours.Close == "" {
		return fmt.Errorf("exchange: regular_hours must have open and close")
	}
	if err := validateTimeFormat(data.RegularHours.Open); err != nil {
		return fmt.Errorf("exchange: regular_hours.open: %w", err)
	}
	if err := validateTimeFormat(data.RegularHours.Close); err != nil {
		return fmt.Errorf("exchange: regular_hours.close: %w", err)
	}
	if data.RegularHours.Open >= data.RegularHours.Close {
		return fmt.Errorf("exchange: regular_hours.open (%s) must be before close (%s)",
			data.RegularHours.Open, data.RegularHours.Close)
	}
	return nil
}

func validateTimeFormat(timeStr string) error {
	if len(timeStr) != 5 {
		return fmt.Errorf("invalid time format %q: expected HH:MM", timeStr)
	}
	if timeStr[2] != ':' {
		return fmt.Errorf("invalid time format %q: expected HH:MM", timeStr)
	}
	hours := (timeStr[0]-'0')*10 + (timeStr[1] - '0')
	minutes := (timeStr[3]-'0')*10 + (timeStr[4] - '0')
	if hours > 23 || minutes > 59 {
		return fmt.Errorf("invalid time %q: hours must be 00-23, minutes 00-59", timeStr)
	}
	return nil
}

func validateDateFormat(dateStr string) error {
	if len(dateStr) != 10 {
		return fmt.Errorf("invalid date format %q: expected YYYY-MM-DD", dateStr)
	}
	_, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		return fmt.Errorf("invalid date %q: %w", dateStr, err)
	}
	return nil
}

// ──────────────────────────────────────────────────────────────
// Internal indexing
// ──────────────────────────────────────────────────────────────

func (e *Exchange) indexEntry(entry HolidayEntry) {
	e.holidayByDate[entry.Date] = entry
	e.statusByDate[entry.Date] = entry.Status

	if entry.Status == string(StatusEarlyClose) && entry.EarlyCloseTime != "" {
		e.earlyCloseTimeByDate[entry.Date] = entry.EarlyCloseTime
	}
}

// ──────────────────────────────────────────────────────────────
// Internal helpers
// ──────────────────────────────────────────────────────────────

// weekendDaysOrDefault falls back to Saturday/Sunday (in Monday=0..Sunday=6
// form) if the registry data omits weekend_days, for backward compatibility
// with older data files.
func weekendDaysOrDefault(wd []int) []int {
	if len(wd) == 0 {
		return []int{5, 6}
	}
	return wd
}

// isoWeekday converts Go's time.Weekday (Sunday=0..Saturday=6) into the
// Monday=0..Sunday=6 convention used by weekend_days in the registry data.
// Do not compare time.Weekday() directly against WeekendDays — the two
// use different day-numbering conventions.
func isoWeekday(d time.Time) int {
	return (int(d.Weekday()) + 6) % 7
}

func (e *Exchange) isWeekend(dateStr string) bool {
	d, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		return false // validateDateFormat should catch this before
	}
	day := isoWeekday(d)
	for _, wd := range e.WeekendDays {
		if day == wd {
			return true
		}
	}
	return false
}

// ──────────────────────────────────────────────────────────────
// Public API — holiday queries
// ──────────────────────────────────────────────────────────────

// IsHoliday returns true if the market is fully closed on this date.
// Includes weekends and explicit/generated holidays.
func (e *Exchange) IsHoliday(dateStr string) bool {
	if e.isWeekend(dateStr) {
		return true
	}
	return e.statusByDate[dateStr] == string(StatusClosed)
}

// IsEarlyClose returns true if this date has an early close.
func (e *Exchange) IsEarlyClose(dateStr string) bool {
	_, ok := e.earlyCloseTimeByDate[dateStr]
	return ok
}

// EarlyCloseTime returns the early close time for this date, or empty string.
func (e *Exchange) EarlyCloseTime(dateStr string) string {
	return e.earlyCloseTimeByDate[dateStr]
}

// ──────────────────────────────────────────────────────────────
// Public API — status
// ──────────────────────────────────────────────────────────────

// StatusAt returns the full session status at a specific date and time.
//
// Returns an error if date or time format is invalid.
//
// Checks in order:
//  1. Weekend → closed
//  2. Full holiday → closed
//  3. Early close day and time >= early_close_time → closed
//  4. Lunch break → lunch_break
//  5. Before regular open → pre_market
//  6. After regular close → after_hours
//  7. Otherwise → open (or early_close on early close day)
//
// timeStr (HH:MM) is interpreted as this exchange's LOCAL time (per
// its Timezone field), NOT UTC and not the caller's local time. This
// wrapper does no timezone conversion -- Timezone is exposed for
// informational purposes only and is not read by any status/date
// logic here. If you have a UTC or other-zone timestamp, convert it
// to this exchange's local time yourself before calling StatusAt.
func (e *Exchange) StatusAt(dateStr, timeStr string) (SessionStatus, error) {
	if err := validateDateFormat(dateStr); err != nil {
		return "", err
	}
	if err := validateTimeFormat(timeStr); err != nil {
		return "", err
	}

	// 1. Weekend
	if e.isWeekend(dateStr) {
		return StatusClosed, nil
	}

	// 2. Full holiday
	if e.statusByDate[dateStr] == string(StatusClosed) {
		return StatusClosed, nil
	}

	// 3. Early close day — check if past the early close time
	isEarlyCloseDay := e.IsEarlyClose(dateStr)
	if isEarlyCloseDay {
		closeTime := e.earlyCloseTimeByDate[dateStr]
		if timeStr >= closeTime {
			return StatusClosed, nil
		}
	}

	// 4. Lunch break
	for _, session := range e.Sessions {
		if session.Type == "lunch_break" && session.Open != "" && session.Close != "" {
			if session.Open <= timeStr && timeStr < session.Close {
				return StatusLunchBreak, nil
			}
		}
	}

	// 5. Before regular open
	if timeStr < e.RegularHours.Open {
		return StatusPreMarket, nil
	}

	// 6. After regular close
	if timeStr >= e.RegularHours.Close {
		return StatusAfterHours, nil
	}

	// 7. Within regular hours
	if isEarlyCloseDay {
		return StatusEarlyClose, nil
	}
	return StatusOpen, nil
}

// IsOpen returns true if the market is open for trading at the given moment.
// Convenience wrapper around StatusAt. Defaults timeStr to "10:00".
func (e *Exchange) IsOpen(dateStr string, timeStrs ...string) bool {
	timeStr := "10:00"
	if len(timeStrs) > 0 {
		timeStr = timeStrs[0]
	}
	status, err := e.StatusAt(dateStr, timeStr)
	if err != nil {
		return false
	}
	return status.IsTradingStatus()
}

// ──────────────────────────────────────────────────────────────
// Public API — date navigation
// ──────────────────────────────────────────────────────────────

// NextTradingDay returns the next trading day after the given date.
// Skips weekends and full holidays. Early close days count.
func (e *Exchange) NextTradingDay(dateStr string) (string, error) {
	if err := validateDateFormat(dateStr); err != nil {
		return "", err
	}

	d, _ := time.Parse("2006-01-02", dateStr)
	for i := 0; i < 30; i++ {
		d = d.AddDate(0, 0, 1)
		candidate := d.Format("2006-01-02")
		if !e.IsHoliday(candidate) {
			return candidate, nil
		}
	}
	return "", fmt.Errorf("no trading day found within 30 days after %s", dateStr)
}

// PreviousTradingDay returns the previous trading day before the given date.
// Skips weekends and full holidays. Early close days count.
func (e *Exchange) PreviousTradingDay(dateStr string) (string, error) {
	if err := validateDateFormat(dateStr); err != nil {
		return "", err
	}

	d, _ := time.Parse("2006-01-02", dateStr)
	for i := 0; i < 30; i++ {
		d = d.AddDate(0, 0, -1)
		candidate := d.Format("2006-01-02")
		if !e.IsHoliday(candidate) {
			return candidate, nil
		}
	}
	return "", fmt.Errorf("no trading day found within 30 days before %s", dateStr)
}

// ──────────────────────────────────────────────────────────────
// Public API — metadata
// ──────────────────────────────────────────────────────────────

// HolidayCount returns the number of holidays, optionally filtered by year.
func (e *Exchange) HolidayCount(year ...int) int {
	if len(year) == 0 {
		return len(e.holidayByDate)
	}

	prefix := fmt.Sprintf("%d-", year[0])
	count := 0
	for dateStr := range e.holidayByDate {
		if strings.HasPrefix(dateStr, prefix) {
			count++
		}
	}
	return count
}

// ListHolidays returns a sorted slice of holiday entries.
// Optionally filtered by year.
func (e *Exchange) ListHolidays(year ...int) []HolidayEntry {
	entries := make([]HolidayEntry, 0, len(e.holidayByDate))

	for _, entry := range e.holidayByDate {
		entries = append(entries, entry)
	}

	if len(year) > 0 {
		prefix := fmt.Sprintf("%d-", year[0])
		filtered := entries[:0]
		for _, entry := range entries {
			if strings.HasPrefix(entry.Date, prefix) {
				filtered = append(filtered, entry)
			}
		}
		entries = filtered
	}

	sort.Slice(entries, func(i, j int) bool {
		return entries[i].Date < entries[j].Date
	})

	return entries
}

// ──────────────────────────────────────────────────────────────
// String representation
// ──────────────────────────────────────────────────────────────

// String returns a human-readable representation.
// Implements the fmt.Stringer interface.
func (e *Exchange) String() string {
	return fmt.Sprintf("%s (%s)", e.Name, e.Code)
}