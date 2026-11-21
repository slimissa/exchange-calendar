package exchangecalendar

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

)

// Registry represents a loaded exchange calendar registry.
//
// The struct is immutable after construction. All exported fields are
// read-only by convention.
type Registry struct {
	Version       string
	ExchangeCount int

	// Unexported map for O(1) lookup
	exchanges map[string]*Exchange
}

// registryData represents the raw JSON structure of calendar.json.
type registryData struct {
	Meta      metaData       `json:"meta"`
	Exchanges []ExchangeData `json:"exchanges"`
}

// metaData represents the meta block in calendar.json.
type metaData struct {
	Version       string `json:"version"`
	ExchangeCount int    `json:"exchange_count"`
}

func (r *Registry) Sessions(mic string) []Session {
	ex, err := r.Get(mic)
	if err != nil {
		return nil
	}
	return ex.Sessions
}

// intervalSessionTypes are the session types the registry-level IsOpen
// counts as trading intervals. lunch_break is spanned, not an interval;
// auction and halt are points.
var intervalSessionTypes = map[string]bool{"pre_market": true, "regular": true, "post_market": true}

// IsOpen reports whether the exchange is in any interval session
// (pre_market, regular or post_market) at the given local time on the
// given date.
//
// The registry contract, the same in all four wrappers: weekends, closed
// holidays and ad hoc rows whose status is "closed" are closed; an ad hoc
// early close or delayed open is not a full closure. early_close_time is
// ignored and lunch_break is spanned (it is not an interval). On a
// delayed_open day the regular session opens at delayed_open_time. For
// regular hours with early closes and lunch breaks, use Exchange.IsOpen.
func (r *Registry) IsOpen(mic, date, timeStr string) bool {
	ex, err := r.Get(mic)
	if err != nil {
		return false
	}
	if validateDateFormat(date) != nil || ex.IsHoliday(date) {
		return false
	}
	for _, s := range ex.Sessions {
		if !intervalSessionTypes[s.Type] {
			continue
		}
		open, cl := s.Open, s.Close
		if s.Type == "regular" {
			// The regular session follows the hours in force on this date
			// (regular_hours may be a dated list).
			hours := ex.hoursOn(date)
			open, cl = hours.Open, hours.Close
			if d := ex.DelayedOpenTime(date); d != "" {
				open = d
			}
		}
		if open != "" && cl != "" && open <= timeStr && timeStr < cl {
			return true
		}
	}
	return false
}

// LoadRegistry loads and parses the registry from a JSON file.
//
// Returns an error if:
//   - The file does not exist
//   - The file is not valid JSON
//   - The registry structure is invalid
//   - Any exchange data is malformed
//
// Example:
//
//	registry, err := LoadRegistry("calendar.json")
//	if err != nil {
//	    log.Fatal(err)
//	}
func LoadRegistry(path string) (*Registry, error) {
	if path == "" {
		return nil, fmt.Errorf("registry: path must not be empty")
	}

	absPath, err := filepath.Abs(path)
	if err != nil {
		return nil, fmt.Errorf("registry: failed to resolve path: %w", err)
	}

	data, err := os.ReadFile(absPath)
	if err != nil {
		return nil, fmt.Errorf("registry: failed to read file: %w", err)
	}

	var raw registryData
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("registry: invalid JSON: %w", err)
	}

	return NewRegistry(raw)
}

// MustLoadRegistry loads the registry or panics on error.
//
// Use only with known-valid files.
func MustLoadRegistry(path string) *Registry {
	registry, err := LoadRegistry(path)
	if err != nil {
		panic(err)
	}
	return registry
}

// NewRegistry creates a Registry from raw parsed JSON data.
//
// Returns an error if the structure is invalid or contains duplicates.
func NewRegistry(data registryData) (*Registry, error) {
	if data.Meta.Version == "" {
		return nil, fmt.Errorf("registry: missing meta.version")
	}

	if len(data.Exchanges) == 0 {
		return nil, fmt.Errorf("registry: no exchanges found")
	}

	// Phase 1.6: meta.exchange_count must match the actual list.
	// ExchangeCount is a plain int, so a zero value with a non-empty
	// slice fails here -- that is intentional: either the caller forgot
	// to set it or the data is wrong, and failing loudly beats silently
	// reporting a wrong count.
	if data.Meta.ExchangeCount != len(data.Exchanges) {
		return nil, fmt.Errorf(
			"registry: meta.exchange_count (%d) does not match len(exchanges) (%d)",
			data.Meta.ExchangeCount, len(data.Exchanges),
		)
	}

	registry := &Registry{
		Version:       data.Meta.Version,
		ExchangeCount: data.Meta.ExchangeCount,
		exchanges:     make(map[string]*Exchange, len(data.Exchanges)),
	}

	for _, exchangeData := range data.Exchanges {
		// Check for duplicates
		if _, exists := registry.exchanges[exchangeData.Code]; exists {
			return nil, fmt.Errorf("registry: duplicate exchange code %q", exchangeData.Code)
		}

		exchange, err := NewExchange(exchangeData)
		if err != nil {
			return nil, fmt.Errorf("registry: exchange %q: %w", exchangeData.Code, err)
		}

		registry.exchanges[exchange.Code] = exchange
	}

	return registry, nil
}

// MustNewRegistry creates a Registry from raw data or panics on error.
func MustNewRegistry(data registryData) *Registry {
	registry, err := NewRegistry(data)
	if err != nil {
		panic(err)
	}
	return registry
}

// ──────────────────────────────────────────────────────────────
// Public API — lookup
// ──────────────────────────────────────────────────────────────

// Exchange returns the Exchange with the given MIC code.
// Case-insensitive. Returns nil if not found.
func (r *Registry) Exchange(code string) *Exchange {
	if code == "" {
		return nil
	}
	normalized := toUpper(code)
	return r.exchanges[normalized]
}

// Get returns the Exchange with the given MIC code, or an error.
// Case-insensitive.
func (r *Registry) Get(code string) (*Exchange, error) {
	exchange := r.Exchange(code)
	if exchange == nil {
		available := strings.Join(r.Codes(), ", ")
		return nil, fmt.Errorf("registry: exchange %q not found. Available: %s", code, available)
	}
	return exchange, nil
}

// Has returns true if the given MIC code exists.
// Case-insensitive.
func (r *Registry) Has(code string) bool {
	return r.Exchange(code) != nil
}

// ──────────────────────────────────────────────────────────────
// Public API — listing
// ──────────────────────────────────────────────────────────────

// Codes returns all MIC codes, sorted alphabetically.
func (r *Registry) Codes() []string {
	codes := make([]string, 0, len(r.exchanges))
	for code := range r.exchanges {
		codes = append(codes, code)
	}
	sort.Strings(codes)
	return codes
}

// Names returns all exchange names, sorted by MIC code.
func (r *Registry) Names() []string {
	codes := r.Codes()
	names := make([]string, 0, len(codes))
	for _, code := range codes {
		names = append(names, r.exchanges[code].Name)
	}
	return names
}

// ListExchanges returns all exchanges, sorted by MIC code.
func (r *Registry) ListExchanges() []*Exchange {
	codes := r.Codes()
	exchanges := make([]*Exchange, 0, len(codes))
	for _, code := range codes {
		exchanges = append(exchanges, r.exchanges[code])
	}
	return exchanges
}

// ──────────────────────────────────────────────────────────────
// Public API — convenience
// ──────────────────────────────────────────────────────────────

// Len returns the number of exchanges in the registry.
func (r *Registry) Len() int {
	return len(r.exchanges)
}

// String returns a human-readable representation.
// Implements the fmt.Stringer interface.
func (r *Registry) String() string {
	return fmt.Sprintf("Exchange Calendar Registry v%s (%d exchanges)", r.Version, len(r.exchanges))
}

// ──────────────────────────────────────────────────────────────
// Internal helpers
// ──────────────────────────────────────────────────────────────

func toUpper(s string) string {
	// ASCII-only uppercase conversion (MIC codes are always ASCII)
	b := []byte(s)
	for i := 0; i < len(b); i++ {
		if b[i] >= 'a' && b[i] <= 'z' {
			b[i] -= 32
		}
	}
	return string(b)
}