package exchangecalendar_test

import (
	"testing"

	exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"
)

// ──────────────────────────────────────────────────────────────
// SessionStatus constants
// ──────────────────────────────────────────────────────────────

func TestSessionStatusConstants(t *testing.T) {
	tests := []struct {
		name     string
		status   exchangecalendar.SessionStatus
		expected string
	}{
		{"Closed", exchangecalendar.StatusClosed, "closed"},
		{"PreMarket", exchangecalendar.StatusPreMarket, "pre_market"},
		{"Open", exchangecalendar.StatusOpen, "open"},
		{"EarlyClose", exchangecalendar.StatusEarlyClose, "early_close"},
		{"AfterHours", exchangecalendar.StatusAfterHours, "after_hours"},
		{"LunchBreak", exchangecalendar.StatusLunchBreak, "lunch_break"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if string(tt.status) != tt.expected {
				t.Errorf("expected %q, got %q", tt.expected, string(tt.status))
			}
		})
	}
}

// ──────────────────────────────────────────────────────────────
// String method
// ──────────────────────────────────────────────────────────────

func TestSessionStatusString(t *testing.T) {
	if exchangecalendar.StatusOpen.String() != "open" {
		t.Errorf("expected 'open', got %q", exchangecalendar.StatusOpen.String())
	}
	if exchangecalendar.StatusClosed.String() != "closed" {
		t.Errorf("expected 'closed', got %q", exchangecalendar.StatusClosed.String())
	}
	if exchangecalendar.StatusEarlyClose.String() != "early_close" {
		t.Errorf("expected 'early_close', got %q", exchangecalendar.StatusEarlyClose.String())
	}
}

// ──────────────────────────────────────────────────────────────
// IsValid
// ──────────────────────────────────────────────────────────────

func TestSessionStatusIsValid(t *testing.T) {
	validStatuses := []exchangecalendar.SessionStatus{
		exchangecalendar.StatusClosed,
		exchangecalendar.StatusPreMarket,
		exchangecalendar.StatusOpen,
		exchangecalendar.StatusEarlyClose,
		exchangecalendar.StatusAfterHours,
		exchangecalendar.StatusLunchBreak,
	}

	for _, status := range validStatuses {
		if !status.IsValid() {
			t.Errorf("expected %q to be valid", status)
		}
	}

	invalidStatuses := []exchangecalendar.SessionStatus{
		"",
		"bogus",
		"OPEN", // case-sensitive — must use ParseSessionStatus for case-insensitive
		"Closed",
	}

	for _, status := range invalidStatuses {
		if status.IsValid() {
			t.Errorf("expected %q to be invalid", status)
		}
	}
}

// ──────────────────────────────────────────────────────────────
// IsTradingStatus
// ──────────────────────────────────────────────────────────────

func TestSessionStatusIsTradingStatus(t *testing.T) {
	tradingStatuses := []exchangecalendar.SessionStatus{
		exchangecalendar.StatusOpen,
		exchangecalendar.StatusEarlyClose,
	}

	for _, status := range tradingStatuses {
		if !status.IsTradingStatus() {
			t.Errorf("expected %q to be a trading status", status)
		}
	}

	nonTradingStatuses := []exchangecalendar.SessionStatus{
		exchangecalendar.StatusClosed,
		exchangecalendar.StatusPreMarket,
		exchangecalendar.StatusAfterHours,
		exchangecalendar.StatusLunchBreak,
	}

	for _, status := range nonTradingStatuses {
		if status.IsTradingStatus() {
			t.Errorf("expected %q to not be a trading status", status)
		}
	}
}

// ──────────────────────────────────────────────────────────────
// ParseSessionStatus
// ──────────────────────────────────────────────────────────────

func TestParseSessionStatus(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected exchangecalendar.SessionStatus
	}{
		{"lowercase", "open", exchangecalendar.StatusOpen},
		{"uppercase", "OPEN", exchangecalendar.StatusOpen},
		{"mixed case", "Open", exchangecalendar.StatusOpen},
		{"with spaces", " early_close ", exchangecalendar.StatusEarlyClose},
		{"closed", "closed", exchangecalendar.StatusClosed},
		{"pre_market", "PRE_MARKET", exchangecalendar.StatusPreMarket},
		{"after_hours", "After_Hours", exchangecalendar.StatusAfterHours},
		{"lunch_break", "LUNCH_BREAK", exchangecalendar.StatusLunchBreak},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			status, err := exchangecalendar.ParseSessionStatus(tt.input)
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if status != tt.expected {
				t.Errorf("expected %q, got %q", tt.expected, status)
			}
		})
	}
}

func TestParseSessionStatusInvalid(t *testing.T) {
	invalidInputs := []string{
		"",
		"bogus",
		"trading",
		"open_market",
		
	}

	for _, input := range invalidInputs {
		_, err := exchangecalendar.ParseSessionStatus(input)
		if err == nil {
			t.Errorf("expected error for input %q", input)
		}
	}
}

func TestParseSessionStatusEmptyString(t *testing.T) {
	_, err := exchangecalendar.ParseSessionStatus("")
	if err == nil {
		t.Error("expected error for empty string")
	}
}

// ──────────────────────────────────────────────────────────────
// MustParseSessionStatus
// ──────────────────────────────────────────────────────────────

func TestMustParseSessionStatusValid(t *testing.T) {
	status := exchangecalendar.MustParseSessionStatus("open")
	if status != exchangecalendar.StatusOpen {
		t.Errorf("expected open, got %q", status)
	}
}

func TestMustParseSessionStatusPanics(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for invalid status")
		}
	}()

	exchangecalendar.MustParseSessionStatus("bogus")
}

// ──────────────────────────────────────────────────────────────
// AllSessionStatuses
// ──────────────────────────────────────────────────────────────

func TestAllSessionStatuses(t *testing.T) {
	statuses := exchangecalendar.AllSessionStatuses()

	if len(statuses) != 6 {
		t.Errorf("expected 6 statuses, got %d", len(statuses))
	}

	// Verify all are unique
	seen := make(map[exchangecalendar.SessionStatus]bool)
	for _, status := range statuses {
		if seen[status] {
			t.Errorf("duplicate status: %q", status)
		}
		seen[status] = true
	}

	// Verify all are valid
	for _, status := range statuses {
		if !status.IsValid() {
			t.Errorf("invalid status in AllSessionStatuses: %q", status)
		}
	}
}

// ──────────────────────────────────────────────────────────────
// TradingStatuses
// ──────────────────────────────────────────────────────────────

func TestTradingStatuses(t *testing.T) {
	statuses := exchangecalendar.TradingStatuses()

	if len(statuses) != 2 {
		t.Errorf("expected 2 trading statuses, got %d", len(statuses))
	}

	expected := []exchangecalendar.SessionStatus{
		exchangecalendar.StatusOpen,
		exchangecalendar.StatusEarlyClose,
	}

	for i, status := range statuses {
		if status != expected[i] {
			t.Errorf("position %d: expected %q, got %q", i, expected[i], status)
		}
	}
}

// ──────────────────────────────────────────────────────────────
// NonTradingStatuses
// ──────────────────────────────────────────────────────────────

func TestNonTradingStatuses(t *testing.T) {
	statuses := exchangecalendar.NonTradingStatuses()

	if len(statuses) != 4 {
		t.Errorf("expected 4 non-trading statuses, got %d", len(statuses))
	}

	for _, status := range statuses {
		if status.IsTradingStatus() {
			t.Errorf("non-trading status %q is marked as trading", status)
		}
	}
}