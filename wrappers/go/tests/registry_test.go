package exchangecalendar_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"
)

// ──────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────

func createTestRegistryData() exchangecalendar.ExchangeData {
	return exchangecalendar.ExchangeData{
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
				{Date: "2025-01-01", Name: "New Year's Day", Status: "closed"},
			},
			Generated: []exchangecalendar.HolidayEntry{},
		},
	}
}

func writeTestRegistryFile(t *testing.T) string {
	t.Helper()

	tmpDir := t.TempDir()
	registryPath := filepath.Join(tmpDir, "calendar.json")

	data := map[string]interface{}{
		"meta": map[string]interface{}{
			"version":        "1.0.0",
			"exchange_count": 1,
		},
		"exchanges": []exchangecalendar.ExchangeData{
			createTestRegistryData(),
		},
	}

	raw, err := json.Marshal(data)
	if err != nil {
		t.Fatalf("failed to marshal test data: %v", err)
	}

	if err := os.WriteFile(registryPath, raw, 0644); err != nil {
		t.Fatalf("failed to write test file: %v", err)
	}

	return registryPath
}

func writeInvalidJSONFile(t *testing.T) string {
	t.Helper()

	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "invalid.json")
	os.WriteFile(path, []byte("{invalid json"), 0644)
	return path
}

func writeDuplicateCodeFile(t *testing.T) string {
	t.Helper()

	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "duplicates.json")

	exchange1 := createTestRegistryData()
	exchange2 := createTestRegistryData() // same code "TEST"

	data := map[string]interface{}{
		"meta": map[string]interface{}{
			"version":        "1.0.0",
			"exchange_count": 2,
		},
		"exchanges": []exchangecalendar.ExchangeData{exchange1, exchange2},
	}

	raw, _ := json.Marshal(data)
	os.WriteFile(path, raw, 0644)
	return path
}

// ──────────────────────────────────────────────────────────────
// LoadRegistry
// ──────────────────────────────────────────────────────────────

func TestLoadRegistryValid(t *testing.T) {
	path := writeTestRegistryFile(t)

	registry, err := exchangecalendar.LoadRegistry(path)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if registry.Version != "1.0.0" {
		t.Errorf("expected version 1.0.0, got %q", registry.Version)
	}
	if registry.ExchangeCount != 1 {
		t.Errorf("expected 1 exchange, got %d", registry.ExchangeCount)
	}
	if registry.Len() != 1 {
		t.Errorf("expected Len() == 1, got %d", registry.Len())
	}
}

func TestLoadRegistryMissingFile(t *testing.T) {
	_, err := exchangecalendar.LoadRegistry("/nonexistent/path/calendar.json")
	if err == nil {
		t.Error("expected error for missing file")
	}
}

func TestLoadRegistryEmptyPath(t *testing.T) {
	_, err := exchangecalendar.LoadRegistry("")
	if err == nil {
		t.Error("expected error for empty path")
	}
}

func TestLoadRegistryInvalidJSON(t *testing.T) {
	path := writeInvalidJSONFile(t)

	_, err := exchangecalendar.LoadRegistry(path)
	if err == nil {
		t.Error("expected error for invalid JSON")
	}
}

func TestLoadRegistryDuplicateCodes(t *testing.T) {
	path := writeDuplicateCodeFile(t)

	_, err := exchangecalendar.LoadRegistry(path)
	if err == nil {
		t.Error("expected error for duplicate codes")
	}
}

func TestLoadRegistryNoExchanges(t *testing.T) {
	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "empty.json")

	data := map[string]interface{}{
		"meta": map[string]interface{}{
			"version":        "1.0.0",
			"exchange_count": 0,
		},
		"exchanges": []exchangecalendar.ExchangeData{},
	}

	raw, _ := json.Marshal(data)
	os.WriteFile(path, raw, 0644)

	_, err := exchangecalendar.LoadRegistry(path)
	if err == nil {
		t.Error("expected error for empty exchanges")
	}
}

// ──────────────────────────────────────────────────────────────
// MustLoadRegistry
// ──────────────────────────────────────────────────────────────

func TestMustLoadRegistryValid(t *testing.T) {
	path := writeTestRegistryFile(t)

	registry := exchangecalendar.MustLoadRegistry(path)
	if registry == nil {
		t.Error("expected non-nil registry")
	}
}

func TestMustLoadRegistryPanics(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for missing file")
		}
	}()

	exchangecalendar.MustLoadRegistry("/nonexistent/path/calendar.json")
}

// ──────────────────────────────────────────────────────────────
// Exchange lookup
// ──────────────────────────────────────────────────────────────

func TestExchangeLookup(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	exchange := registry.Exchange("TEST")
	if exchange == nil {
		t.Fatal("expected exchange, got nil")
	}
	if exchange.Code != "TEST" {
		t.Errorf("expected code TEST, got %q", exchange.Code)
	}
}

func TestExchangeLookupCaseInsensitive(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	exchange := registry.Exchange("test")
	if exchange == nil {
		t.Fatal("expected exchange for lowercase code, got nil")
	}
	if exchange.Code != "TEST" {
		t.Errorf("expected code TEST, got %q", exchange.Code)
	}
}

func TestExchangeNotFoundReturnsNil(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	exchange := registry.Exchange("XXXX")
	if exchange != nil {
		t.Error("expected nil for unknown code")
	}
}

func TestExchangeEmptyCodeReturnsNil(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	exchange := registry.Exchange("")
	if exchange != nil {
		t.Error("expected nil for empty code")
	}
}

func TestGetReturnsExchange(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	exchange, err := registry.Get("TEST")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exchange == nil {
		t.Fatal("expected exchange, got nil")
	}
}

func TestGetReturnsError(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	_, err := registry.Get("XXXX")
	if err == nil {
		t.Error("expected error for unknown code")
	}
}

func TestHasReturnsBool(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	if !registry.Has("TEST") {
		t.Error("expected Has(TEST) to be true")
	}
	if registry.Has("XXXX") {
		t.Error("expected Has(XXXX) to be false")
	}
}

// ──────────────────────────────────────────────────────────────
// Listing
// ──────────────────────────────────────────────────────────────

func TestCodes(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	codes := registry.Codes()
	if len(codes) != 1 {
		t.Fatalf("expected 1 code, got %d", len(codes))
	}
	if codes[0] != "TEST" {
		t.Errorf("expected TEST, got %q", codes[0])
	}
}

func TestNames(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	names := registry.Names()
	if len(names) != 1 {
		t.Fatalf("expected 1 name, got %d", len(names))
	}
	if names[0] != "Test Exchange" {
		t.Errorf("expected 'Test Exchange', got %q", names[0])
	}
}

func TestListExchanges(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	exchanges := registry.ListExchanges()
	if len(exchanges) != 1 {
		t.Fatalf("expected 1 exchange, got %d", len(exchanges))
	}
	if exchanges[0].Code != "TEST" {
		t.Errorf("expected code TEST, got %q", exchanges[0].Code)
	}
}

func TestStringRepresentation(t *testing.T) {
	registry := exchangecalendar.MustLoadRegistry(writeTestRegistryFile(t))

	s := registry.String()
	if s == "" {
		t.Error("expected non-empty string")
	}
}

// ──────────────────────────────────────────────────────────────
// Multiple exchanges
// ──────────────────────────────────────────────────────────────

func TestMultipleExchangesSorted(t *testing.T) {
	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "multi.json")

	exchangeB := createTestRegistryData()
	exchangeB.Code = "ZED"
	exchangeB.Name = "Zed Exchange"
	exchangeB.MIC = "ZED"

	exchangeA := createTestRegistryData()
	exchangeA.Code = "ALPHA"
	exchangeA.Name = "Alpha Exchange"
	exchangeA.MIC = "ALPHA"

	data := map[string]interface{}{
		"meta": map[string]interface{}{
			"version":        "1.0.0",
			"exchange_count": 2,
		},
		"exchanges": []exchangecalendar.ExchangeData{exchangeB, exchangeA},
	}

	raw, _ := json.Marshal(data)
	os.WriteFile(path, raw, 0644)

	registry := exchangecalendar.MustLoadRegistry(path)

	codes := registry.Codes()
	if len(codes) != 2 {
		t.Fatalf("expected 2 codes, got %d", len(codes))
	}
	if codes[0] != "ALPHA" {
		t.Errorf("expected ALPHA first, got %q", codes[0])
	}
	if codes[1] != "ZED" {
		t.Errorf("expected ZED second, got %q", codes[1])
	}
}