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