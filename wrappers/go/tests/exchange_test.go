package exchangecalendar_test

import (
	"testing"

	exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"
)

// ──────────────────────────────────────────────────────────────
// Helper: create a test Exchange
// ──────────────────────────────────────────────────────────────

func createTestExchange() *exchangecalendar.Exchange {
	data := exchangecalendar.ExchangeData{
		Code:     "TEST",
		Name:     "Test Exchange",
		MIC:      "TEST",
		Timezone: "Europe/London",
		RegularHours: exchangecalendar.RegularHours{
			Open:  "09:00",
			Close: "17:00",
		},
		Holidays: exchangecalendar.HolidaysData{
			Explicit: []exchangecalendar.HolidayEntry{
				{
					Date:   "2025-01-01",
					Name:   "New Year's Day",
					Status: string(exchangecalendar.StatusClosed),
				},
				{
					Date:           "2025-07-03",
					Name:           "Early Close Day",
					Status:         string(exchangecalendar.StatusEarlyClose),
					EarlyCloseTime: "13:00",
				},
			},
			Generated: []exchangecalendar.HolidayEntry{},
		},
		GenerationRange: []string{"2025-01-01", "2025-12-31"},
	}

	return exchangecalendar.MustNewExchange(data)
}

func createRealXNYS() *exchangecalendar.Exchange {
	data := exchangecalendar.ExchangeData{
		Code:     "XNYS",
		Name:     "New York Stock Exchange",
		MIC:      "XNYS",
		Timezone: "America/New_York",
		RegularHours: exchangecalendar.RegularHours{
			Open:  "09:30",
			Close: "16:00",
		},
		Holidays: exchangecalendar.HolidaysData{
			Explicit: []exchangecalendar.HolidayEntry{
				{Date: "2025-01-01", Name: "New Year's Day", Status: "closed"},
				{Date: "2025-07-03", Name: "Day before Independence Day", Status: "early_close", EarlyCloseTime: "13:00"},
				{Date: "2025-07-04", Name: "Independence Day", Status: "closed"},
			},
			Generated: []exchangecalendar.HolidayEntry{},
		},
	}

	return exchangecalendar.MustNewExchange(data)
}

func createRealXSAU() *exchangecalendar.Exchange {
	data := exchangecalendar.ExchangeData{
		Code:        "XSAU",
		Name:        "Saudi Stock Exchange (Tadawul)",
		MIC:         "XSAU",
		Timezone:    "Asia/Riyadh",
		WeekendDays: []int{4, 5}, // Friday, Saturday (Monday=0)
		RegularHours: exchangecalendar.RegularHours{
			Open:  "10:00",
			Close: "15:00",
		},
		Holidays: exchangecalendar.HolidaysData{
			Explicit:  []exchangecalendar.HolidayEntry{},
			Generated: []exchangecalendar.HolidayEntry{},
		},
	}

	return exchangecalendar.MustNewExchange(data)
}

// ──────────────────────────────────────────────────────────────
// Constructor validation
// ──────────────────────────────────────────────────────────────

func TestNewExchangeValid(t *testing.T) {
	e := createTestExchange()

	if e.Code != "TEST" {
		t.Errorf("expected code TEST, got %q", e.Code)
	}
	if e.Name != "Test Exchange" {
		t.Errorf("expected name 'Test Exchange', got %q", e.Name)
	}
	if e.MIC != "TEST" {
		t.Errorf("expected MIC TEST, got %q", e.MIC)
	}
	if e.Timezone != "Europe/London" {
		t.Errorf("expected timezone Europe/London, got %q", e.Timezone)
	}
	if e.RegularHours.Open != "09:00" || e.RegularHours.Close != "17:00" {
		t.Errorf("regular hours wrong: %+v", e.RegularHours)
	}
}

func TestNewExchangeMissingCode(t *testing.T) {
	data := exchangecalendar.ExchangeData{
		Name:         "Missing Code",
		MIC:          "TEST",
		Timezone:     "Europe/London",
		RegularHours: exchangecalendar.RegularHours{Open: "09:00", Close: "17:00"},
		Holidays:     exchangecalendar.HolidaysData{},
	}

	_, err := exchangecalendar.NewExchange(data)
	if err == nil {
		t.Error("expected error for missing code")
	}
}

func TestNewExchangeMissingName(t *testing.T) {
	data := exchangecalendar.ExchangeData{
		Code:         "TEST",
		MIC:          "TEST",
		Timezone:     "Europe/London",
		RegularHours: exchangecalendar.RegularHours{Open: "09:00", Close: "17:00"},
		Holidays:     exchangecalendar.HolidaysData{},
	}

	_, err := exchangecalendar.NewExchange(data)
	if err == nil {
		t.Error("expected error for missing name")
	}
}

func TestNewExchangeCodeMismatchMIC(t *testing.T) {
	data := exchangecalendar.ExchangeData{
		Code:         "TEST",
		Name:         "Test",
		MIC:          "OTHER",
		Timezone:     "Europe/London",
		RegularHours: exchangecalendar.RegularHours{Open: "09:00", Close: "17:00"},
		Holidays:     exchangecalendar.HolidaysData{},
	}

	_, err := exchangecalendar.NewExchange(data)
	if err == nil {
		t.Error("expected error for code/MIC mismatch")
	}
}

func TestNewExchangeMissingHours(t *testing.T) {
	data := exchangecalendar.ExchangeData{
		Code:     "TEST",
		Name:     "Test",
		MIC:      "TEST",
		Timezone: "Europe/London",
		Holidays: exchangecalendar.HolidaysData{},
	}

	_, err := exchangecalendar.NewExchange(data)
	if err == nil {
		t.Error("expected error for missing regular hours")
	}
}

func TestNewExchangeInvalidTimeFormat(t *testing.T) {
	data := exchangecalendar.ExchangeData{
		Code:         "TEST",
		Name:         "Test",
		MIC:          "TEST",
		Timezone:     "Europe/London",
		RegularHours: exchangecalendar.RegularHours{Open: "9am", Close: "17:00"},
		Holidays:     exchangecalendar.HolidaysData{},
	}

	_, err := exchangecalendar.NewExchange(data)
	if err == nil {
		t.Error("expected error for invalid time format")
	}
}

func TestNewExchangeOpenAfterClose(t *testing.T) {
	data := exchangecalendar.ExchangeData{
		Code:         "TEST",
		Name:         "Test",
		MIC:          "TEST",
		Timezone:     "Europe/London",
		RegularHours: exchangecalendar.RegularHours{Open: "17:00", Close: "09:00"},
		Holidays:     exchangecalendar.HolidaysData{},
	}

	_, err := exchangecalendar.NewExchange(data)
	if err == nil {
		t.Error("expected error for open after close")
	}
}

// ──────────────────────────────────────────────────────────────
// Holiday detection
// ──────────────────────────────────────────────────────────────

func TestIsHolidayNewYearsDay(t *testing.T) {
	e := createTestExchange()

	if !e.IsHoliday("2025-01-01") {
		t.Error("expected 2025-01-01 to be a holiday")
	}
}

func TestIsHolidayRegularDay(t *testing.T) {
	e := createTestExchange()

	if e.IsHoliday("2025-03-14") {
		t.Error("expected 2025-03-14 (Friday) to not be a holiday")
	}
}

func TestIsHolidayWeekend(t *testing.T) {
	e := createTestExchange()

	if !e.IsHoliday("2025-03-15") { // Saturday
		t.Error("expected Saturday to be a holiday")
	}
	if !e.IsHoliday("2025-03-16") { // Sunday
		t.Error("expected Sunday to be a holiday")
	}
}

func TestIsHolidayEarlyCloseNotFullHoliday(t *testing.T) {
	e := createTestExchange()

	if e.IsHoliday("2025-07-03") {
		t.Error("expected early close day to not be a full holiday")
	}
}

// ──────────────────────────────────────────────────────────────
// Early close detection
// ──────────────────────────────────────────────────────────────

func TestIsEarlyClose(t *testing.T) {
	e := createTestExchange()

	if !e.IsEarlyClose("2025-07-03") {
		t.Error("expected 2025-07-03 to be early close")
	}
	if e.IsEarlyClose("2025-07-04") {
		t.Error("expected 2025-07-04 to not be early close")
	}
}

func TestEarlyCloseTime(t *testing.T) {
	e := createTestExchange()

	time := e.EarlyCloseTime("2025-07-03")
	if time != "13:00" {
		t.Errorf("expected 13:00, got %q", time)
	}

	empty := e.EarlyCloseTime("2025-07-04")
	if empty != "" {
		t.Errorf("expected empty string, got %q", empty)
	}
}

// ──────────────────────────────────────────────────────────────
// Status at specific times
// ──────────────────────────────────────────────────────────────

func TestStatusAtOpen(t *testing.T) {
	e := createTestExchange()

	status, err := e.StatusAt("2025-03-14", "10:00")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != exchangecalendar.StatusOpen {
		t.Errorf("expected open, got %q", status)
	}
}

func TestStatusAtWeekend(t *testing.T) {
	e := createTestExchange()

	status, err := e.StatusAt("2025-03-15", "10:00")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != exchangecalendar.StatusClosed {
		t.Errorf("expected closed, got %q", status)
	}
}

func TestStatusAtHoliday(t *testing.T) {
	e := createTestExchange()

	status, err := e.StatusAt("2025-01-01", "10:00")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != exchangecalendar.StatusClosed {
		t.Errorf("expected closed, got %q", status)
	}
}

func TestStatusAtPreMarket(t *testing.T) {
	e := createTestExchange()

	status, err := e.StatusAt("2025-03-14", "08:00")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != exchangecalendar.StatusPreMarket {
		t.Errorf("expected pre_market, got %q", status)
	}
}

func TestStatusAtAfterHours(t *testing.T) {
	e := createTestExchange()

	status, err := e.StatusAt("2025-03-14", "18:00")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != exchangecalendar.StatusAfterHours {
		t.Errorf("expected after_hours, got %q", status)
	}
}

func TestStatusAtEarlyCloseBeforeClose(t *testing.T) {
	e := createTestExchange()

	status, err := e.StatusAt("2025-07-03", "10:00")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != exchangecalendar.StatusEarlyClose {
		t.Errorf("expected early_close, got %q", status)
	}
}

func TestStatusAtEarlyCloseAfterClose(t *testing.T) {
	e := createTestExchange()

	status, err := e.StatusAt("2025-07-03", "13:30")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != exchangecalendar.StatusClosed {
		t.Errorf("expected closed, got %q", status)
	}
}

func TestStatusAtEarlyCloseExactClose(t *testing.T) {
	e := createTestExchange()

	status, err := e.StatusAt("2025-07-03", "13:00")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != exchangecalendar.StatusClosed {
		t.Errorf("expected closed, got %q", status)
	}
}

func TestStatusAtInvalidDate(t *testing.T) {
	e := createTestExchange()

	_, err := e.StatusAt("2025/01/01", "10:00")
	if err == nil {
		t.Error("expected error for invalid date")
	}
}

func TestStatusAtInvalidTime(t *testing.T) {
	e := createTestExchange()

	_, err := e.StatusAt("2025-03-14", "10am")
	if err == nil {
		t.Error("expected error for invalid time")
	}
}

// ──────────────────────────────────────────────────────────────
// IsOpen
// ──────────────────────────────────────────────────────────────

func TestIsOpenRegularHours(t *testing.T) {
	e := createTestExchange()

	if !e.IsOpen("2025-03-14", "10:00") {
		t.Error("expected open at 10:00")
	}
}

func TestIsOpenDefaultTime(t *testing.T) {
	e := createTestExchange()

	if !e.IsOpen("2025-03-14") {
		t.Error("expected open at default time 10:00")
	}
}

func TestIsOpenEarlyClose(t *testing.T) {
	e := createTestExchange()

	if !e.IsOpen("2025-07-03", "10:00") {
		t.Error("expected open during early close before close time")
	}
}

func TestIsOpenAfterEarlyClose(t *testing.T) {
	e := createTestExchange()

	if e.IsOpen("2025-07-03", "13:30") {
		t.Error("expected closed after early close time")
	}
}

func TestIsOpenHoliday(t *testing.T) {
	e := createTestExchange()

	if e.IsOpen("2025-01-01", "10:00") {
		t.Error("expected closed on holiday")
	}
}

func TestIsOpenWeekend(t *testing.T) {
	e := createTestExchange()

	if e.IsOpen("2025-03-15", "10:00") {
		t.Error("expected closed on weekend")
	}
}

// ──────────────────────────────────────────────────────────────
// Date navigation
// ──────────────────────────────────────────────────────────────

func TestNextTradingDayRegular(t *testing.T) {
	e := createTestExchange()

	next, err := e.NextTradingDay("2025-03-14")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if next != "2025-03-17" { // Friday -> Monday
		t.Errorf("expected 2025-03-17, got %q", next)
	}
}

func TestNextTradingDaySkipsHoliday(t *testing.T) {
	e := createTestExchange()

	next, err := e.NextTradingDay("2025-06-30")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if next != "2025-07-01" {
		t.Errorf("expected 2025-07-01, got %q", next)
	}
}

func TestPreviousTradingDayRegular(t *testing.T) {
	e := createTestExchange()

	prev, err := e.PreviousTradingDay("2025-03-17")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if prev != "2025-03-14" { // Monday -> Friday
		t.Errorf("expected 2025-03-14, got %q", prev)
	}
}

func TestNextTradingDayInvalidDate(t *testing.T) {
	e := createTestExchange()

	_, err := e.NextTradingDay("invalid-date")
	if err == nil {
		t.Error("expected error for invalid date")
	}
}

// ──────────────────────────────────────────────────────────────
// Metadata
// ──────────────────────────────────────────────────────────────

func TestHolidayCount(t *testing.T) {
	e := createTestExchange()

	count := e.HolidayCount()
	if count != 2 {
		t.Errorf("expected 2 holidays, got %d", count)
	}
}

func TestHolidayCountYearFilter(t *testing.T) {
	e := createTestExchange()

	count := e.HolidayCount(2025)
	if count != 2 {
		t.Errorf("expected 2 holidays in 2025, got %d", count)
	}

	countOther := e.HolidayCount(2026)
	if countOther != 0 {
		t.Errorf("expected 0 holidays in 2026, got %d", countOther)
	}
}

func TestListHolidaysSorted(t *testing.T) {
	e := createTestExchange()

	holidays := e.ListHolidays()
	if len(holidays) != 2 {
		t.Fatalf("expected 2 holidays, got %d", len(holidays))
	}

	if holidays[0].Date > holidays[1].Date {
		t.Errorf("holidays not sorted: %s > %s", holidays[0].Date, holidays[1].Date)
	}
}

func TestListHolidaysYearFilter(t *testing.T) {
	e := createTestExchange()

	holidays := e.ListHolidays(2025)
	if len(holidays) != 2 {
		t.Errorf("expected 2 holidays in 2025, got %d", len(holidays))
	}

	holidaysOther := e.ListHolidays(2026)
	if len(holidaysOther) != 0 {
		t.Errorf("expected 0 holidays in 2026, got %d", len(holidaysOther))
	}
}

// ──────────────────────────────────────────────────────────────
// String representation
// ──────────────────────────────────────────────────────────────

func TestString(t *testing.T) {
	e := createTestExchange()

	s := e.String()
	if s == "" {
		t.Error("expected non-empty string")
	}
}

// ──────────────────────────────────────────────────────────────
// Real exchange data
// ──────────────────────────────────────────────────────────────

func TestRealXNYS(t *testing.T) {
	e := createRealXNYS()

	if !e.IsHoliday("2025-01-01") {
		t.Error("expected New Year's Day to be holiday")
	}
	if !e.IsHoliday("2025-07-04") {
		t.Error("expected Independence Day to be holiday")
	}
	if !e.IsEarlyClose("2025-07-03") {
		t.Error("expected July 3 to be early close")
	}
	if e.EarlyCloseTime("2025-07-03") != "13:00" {
		t.Errorf("expected 13:00, got %q", e.EarlyCloseTime("2025-07-03"))
	}
	if e.IsOpen("2025-07-04", "10:00") {
		t.Error("expected closed on July 4")
	}
	if !e.IsOpen("2025-07-07", "10:00") {
		t.Error("expected open on July 7 (Monday)")
	}
}

// TestRealXSAUIslamicWeekend is a regression test for the wrapper
// hardcoding Saturday/Sunday as the weekend for every exchange,
// regardless of its actual weekend system. XSAU (Saudi) observes a
// Friday/Saturday weekend.
func TestRealXSAUIslamicWeekend(t *testing.T) {
	e := createRealXSAU()

	if !e.IsHoliday("2025-08-22") {
		t.Error("expected Friday 2025-08-22 to be a holiday (weekend)")
	}
	if !e.IsHoliday("2025-08-23") {
		t.Error("expected Saturday 2025-08-23 to be a holiday (weekend)")
	}
	if e.IsHoliday("2025-08-24") {
		t.Error("expected Sunday 2025-08-24 to be a trading day, not a holiday")
	}
}