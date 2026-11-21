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

func TestLoadRegistryMismatchedExchangeCount(t *testing.T) {
	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "bad_count.json")
	os.WriteFile(path, []byte(`{
		"meta": {"version": "1.0.0", "exchange_count": 99},
		"exchanges": [{
			"code": "TEST", "name": "Test Exchange", "mic": "TEST",
			"timezone": "Europe/London",
			"regular_hours": {"open": "09:00", "close": "17:00"},
			"holidays": {"explicit": [], "generated": []}
		}]
	}`), 0644)

	_, err := exchangecalendar.LoadRegistry(path)
	if err == nil {
		t.Fatal("expected error for mismatched exchange_count")
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
func TestRealRegistryData(t *testing.T) {
	// Phase 4.7: load the shipped calendar.json and verify known-good values.
	r, err := exchangecalendar.LoadRegistry("../../../calendar.json")
	if err != nil {
		t.Fatalf("load calendar.json: %v", err)
	}

	xnys, err := r.Get("XNYS")
	if err != nil {
		t.Fatal(err)
	}
	if !xnys.IsHoliday("2025-07-04") {
		t.Error("XNYS 2025-07-04 should be a holiday")
	}
	if !xnys.IsEarlyClose("2025-07-03") {
		t.Error("XNYS 2025-07-03 should be an early close")
	}
	if got := xnys.EarlyCloseTime("2025-07-03"); got != "13:00" {
		t.Errorf("XNYS early close time: want 13:00, got %q", got)
	}

	xsau, err := r.Get("XSAU")
	if err != nil {
		t.Fatal(err)
	}
	if !xsau.IsHoliday("2025-08-22") {
		t.Error("XSAU 2025-08-22 (Friday) should be a weekend day")
	}

	xtks, err := r.Get("XTKS")
	if err != nil {
		t.Fatal(err)
	}
	st, err := xtks.StatusAt("2025-07-07", "12:00")
	if err != nil {
		t.Fatal(err)
	}
	if st != exchangecalendar.StatusLunchBreak {
		t.Errorf("XTKS 12:00: want lunch_break, got %v", st)
	}
}

func TestConfidence(t *testing.T) {
	reg, err := exchangecalendar.LoadRegistry("../../../calendar.json")
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	c, ok := reg.Confidence("XBUD", 2026)
	if !ok {
		t.Fatal("XBUD 2026 not found")
	}
	if c.Source != "fetcher" || c.Level != "high" {
		t.Errorf("unexpected: %+v", c)
	}
	if _, ok := reg.Confidence("XNYS", 1980); ok {
		t.Error("1999 should not exist")
	}
}

func TestVerificationKnownMIC(t *testing.T) {
	reg, err := exchangecalendar.LoadRegistry("../../../calendar.json")
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	v := reg.Verification("XSWX")
	if v == nil {
		t.Fatal("XSWX has no verification object")
	}
	switch v.Class {
	case "reference_compared", "source_verified", "single_source", "ci_unreachable":
	default:
		t.Errorf("unexpected class %q", v.Class)
	}
	if v.Basis == "" || v.ReferenceNote == "" || len(v.LastChecked) != 10 {
		t.Errorf("incomplete verification: %+v", v)
	}
	// a copy: changing it does not change the registry
	v.Class = "changed"
	if reg.Verification("XSWX").Class == "changed" {
		t.Error("Verification returned the registry's own object")
	}
	// case-insensitive, like Exchange
	if lower := reg.Verification("xswx"); lower == nil || lower.Class != reg.Verification("XSWX").Class {
		t.Errorf("lower-case lookup differs: %+v", lower)
	}
}

func TestVerificationUnknownMIC(t *testing.T) {
	reg, err := exchangecalendar.LoadRegistry("../../../calendar.json")
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if v := reg.Verification("XXXX"); v != nil {
		t.Errorf("unknown MIC should give nil, got %+v", v)
	}
}

func TestCoverageKnownMIC(t *testing.T) {
	reg, err := exchangecalendar.LoadRegistry("../../../calendar.json")
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	c := reg.Coverage("XKRX")
	if c == nil {
		t.Fatal("XKRX has no coverage object")
	}
	if c.From != "2010-01-01" || c.To != "2029-12-31" {
		t.Errorf("unexpected span %s..%s", c.From, c.To)
	}
	if len(c.Ranges) == 0 || len(c.Sources) == 0 {
		t.Fatalf("incomplete coverage: %+v", c)
	}
	first := c.Sources[0]
	if first.Source != "exchange_calendars" || first.From != "2010-01-01" || first.To != "2024-12-31" {
		t.Errorf("unexpected first source: %+v", first)
	}
	if first.Sampled != nil {
		t.Errorf("sampled should be nil until Phase 4d, got %v", *first.Sampled)
	}
	// a copy: changing it does not change the registry
	c.Sources[0].Source = "changed"
	if reg.Coverage("XKRX").Sources[0].Source == "changed" {
		t.Error("Coverage returned the registry's own object")
	}
	// case-insensitive, like Exchange
	if reg.Coverage("xkrx") == nil {
		t.Error("lowercase MIC should find coverage")
	}
}

func TestCoverageUnknownMIC(t *testing.T) {
	reg, err := exchangecalendar.LoadRegistry("../../../calendar.json")
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if c := reg.Coverage("XXXX"); c != nil {
		t.Errorf("unknown MIC should give nil, got %+v", c)
	}
}

func TestAsOf(t *testing.T) {
	reg, err := exchangecalendar.LoadRegistry("../../../calendar.json")
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	a, _ := reg.AsOf("XBUD", "2026-01-01")
	conf := a["confidence"].(map[string]exchangecalendar.ConfidenceEntry)
	if _, ok := conf["2026"]; ok {
		t.Error("2026 should be filtered out before fetch date")
	}
	b, _ := reg.AsOf("XBUD", "2026-10-03")
	conf2 := b["confidence"].(map[string]exchangecalendar.ConfidenceEntry)
	if _, ok := conf2["2026"]; !ok {
		t.Error("2026 should be present on/after fetch date")
	}
}
// 4c12: a delayed_open day opens at delayed_open_time (shipped calendar.json).
func TestRealRegistryDelayedOpen(t *testing.T) {
	r, err := exchangecalendar.LoadRegistry(filepath.Join("..", "..", "..", "calendar.json"))
	if err != nil {
		t.Fatalf("load calendar.json: %v", err)
	}
	cases := []struct {
		mic, date, at string
		open          bool
	}{
		{"XBSP", "2026-02-18", "11:00", false},
		{"XBSP", "2026-02-18", "12:59", false},
		{"XBSP", "2026-02-18", "13:00", true},
		{"XBSP", "2026-02-18", "14:00", true},
		{"XBDA", "2025-10-02", "10:00", false},
		{"XBDA", "2025-10-02", "12:14", false},
		{"XBDA", "2025-10-02", "12:15", true},
		{"XBDA", "2025-10-02", "13:00", true},
	}
	for _, c := range cases {
		if got := r.IsOpen(c.mic, c.date, c.at); got != c.open {
			t.Errorf("%s %s %s: IsOpen = %v, want %v", c.mic, c.date, c.at, got, c.open)
		}
	}
	xbsp, err := r.Get("XBSP")
	if err != nil {
		t.Fatalf("get XBSP: %v", err)
	}
	if got := xbsp.DelayedOpenTime("2026-02-18"); got != "13:00" {
		t.Errorf("XBSP DelayedOpenTime = %q, want 13:00", got)
	}
}

// (b1) registry contract: any pre_market/regular/post_market interval;
// early_close_time ignored; lunch_break spanned; an ad hoc row closes the day
// only when its status is "closed". Exchange.IsOpen stays the regular session.
func TestRegistryIsOpenContractB1(t *testing.T) {
	r, err := exchangecalendar.LoadRegistry(filepath.Join("..", "..", "..", "calendar.json"))
	if err != nil {
		t.Fatalf("load calendar.json: %v", err)
	}
	cases := []struct {
		mic, date, at              string
		registryOpen, exchangeOpen bool
	}{
		{"XBDA", "2025-10-01", "10:00", true, true},
		{"XBDA", "2025-10-01", "14:00", true, false},
		{"XNYS", "2025-11-28", "14:00", true, false},
		{"XTKS", "2025-07-03", "12:00", true, false},
		{"XNYS", "2025-11-26", "08:00", true, false},
		{"XNYS", "2025-11-26", "17:00", true, false},
		{"XKUW", "2025-06-02", "12:45", false, false},
	}
	for _, c := range cases {
		if got := r.IsOpen(c.mic, c.date, c.at); got != c.registryOpen {
			t.Errorf("registry %s %s %s: IsOpen = %v, want %v", c.mic, c.date, c.at, got, c.registryOpen)
		}
		ex, err := r.Get(c.mic)
		if err != nil {
			t.Fatalf("get %s: %v", c.mic, err)
		}
		if got := ex.IsOpen(c.date, c.at); got != c.exchangeOpen {
			t.Errorf("exchange %s %s %s: IsOpen = %v, want %v", c.mic, c.date, c.at, got, c.exchangeOpen)
		}
	}
}
