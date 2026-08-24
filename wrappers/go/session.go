package exchangecalendar

import (
	"fmt"
	"strings"
)

// SessionStatus represents the operational state of an exchange at a point in time.
//
// This is the canonical status vocabulary for the entire QuantOS ecosystem.
// All language wrappers must map to the same semantic states.
//
// The zero value is an empty string and is invalid. Always use one of the
// exported constants.
type SessionStatus string

const (
	// StatusClosed indicates the market is closed (weekend, holiday, or outside all hours).
	StatusClosed SessionStatus = "closed"

	// StatusPreMarket indicates pre-market trading (before regular hours).
	StatusPreMarket SessionStatus = "pre_market"

	// StatusOpen indicates regular trading hours.
	StatusOpen SessionStatus = "open"

	// StatusEarlyClose indicates an early close day, before the early close time.
	StatusEarlyClose SessionStatus = "early_close"

	// StatusAfterHours indicates after-hours trading (after regular hours).
	StatusAfterHours SessionStatus = "after_hours"

	// StatusLunchBreak indicates an intraday break (exchanges with lunch pauses).
	StatusLunchBreak SessionStatus = "lunch_break"
)

// String returns the string value of the status.
// Implements the fmt.Stringer interface.
func (s SessionStatus) String() string {
	return string(s)
}

// IsValid returns true if the status is one of the defined constants.
func (s SessionStatus) IsValid() bool {
	switch s {
	case StatusClosed, StatusPreMarket, StatusOpen, StatusEarlyClose, StatusAfterHours, StatusLunchBreak:
		return true
	default:
		return false
	}
}

// IsTradingStatus returns true if the status represents a state where
// trading is currently possible (regular hours or early close before close time).
func (s SessionStatus) IsTradingStatus() bool {
	return s == StatusOpen || s == StatusEarlyClose
}

// ParseSessionStatus converts a string to a SessionStatus.
//
// The input is case-insensitive and trimmed of surrounding whitespace.
// Returns an error if the string does not match any known status.
//
// Example:
//
//	status, err := ParseSessionStatus("OPEN")
//	if err != nil {
//	    log.Fatal(err)
//	}
//	fmt.Println(status) // "open"
func ParseSessionStatus(value string) (SessionStatus, error) {
	normalized := strings.ToLower(strings.TrimSpace(value))

	switch normalized {
	case string(StatusClosed):
		return StatusClosed, nil
	case string(StatusPreMarket):
		return StatusPreMarket, nil
	case string(StatusOpen):
		return StatusOpen, nil
	case string(StatusEarlyClose):
		return StatusEarlyClose, nil
	case string(StatusAfterHours):
		return StatusAfterHours, nil
	case string(StatusLunchBreak):
		return StatusLunchBreak, nil
	default:
		return "", fmt.Errorf("unknown session status: %q (valid: closed, pre_market, open, early_close, after_hours, lunch_break)", value)
	}
}

// MustParseSessionStatus converts a string to a SessionStatus or panics.
//
// Use this only when the input is known to be valid (e.g., hardcoded
// constants in tests or registry data that has already been validated).
// For user input, use ParseSessionStatus and handle the error.
func MustParseSessionStatus(value string) SessionStatus {
	status, err := ParseSessionStatus(value)
	if err != nil {
		panic(err)
	}
	return status
}

// AllSessionStatuses returns all valid statuses in a stable order.
func AllSessionStatuses() []SessionStatus {
	return []SessionStatus{
		StatusClosed,
		StatusPreMarket,
		StatusOpen,
		StatusEarlyClose,
		StatusAfterHours,
		StatusLunchBreak,
	}
}

// TradingStatuses returns only statuses where trading is possible.
func TradingStatuses() []SessionStatus {
	return []SessionStatus{
		StatusOpen,
		StatusEarlyClose,
	}
}

// NonTradingStatuses returns only statuses where trading is not possible.
func NonTradingStatuses() []SessionStatus {
	return []SessionStatus{
		StatusClosed,
		StatusPreMarket,
		StatusAfterHours,
		StatusLunchBreak,
	}
}