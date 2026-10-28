package exchangecalendar_test

import (
	"encoding/json"
	"strings"
	"testing"

	exchangecalendar "github.com/slimissa/exchange-calendar/wrappers/go"
)

const datedExchange = `{
  "code": "XTST", "name": "Test Exchange", "mic": "XTST", "timezone": "Asia/Tokyo",
  "regular_hours": %s,
  "holidays": {"explicit": [], "generated": []}
}`

func loadDated(t *testing.T, hours string) (*exchangecalendar.Exchange, error) {
	t.Helper()
	var data exchangecalendar.ExchangeData
	if err := json.Unmarshal([]byte(strings.Replace(datedExchange, "%s", hours, 1)), &data); err != nil {
		return nil, err
	}
	return exchangecalendar.NewExchange(data)
}

const datedList = `[
  {"effective_from": "2024-11-05", "open": "09:00", "close": "15:30"},
  {"effective_from": "1997-01-01", "open": "09:00", "close": "15:00"}
]`

func TestDatedRegularHoursLoad(t *testing.T) {
	e, err := loadDated(t, datedList)
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if e.RegularHours.Close != "15:30" {
		t.Errorf("current close = %q, want 15:30", e.RegularHours.Close)
	}
	if len(e.RegularHoursHistory) != 2 || e.RegularHoursHistory[0].EffectiveFrom != "1997-01-01" {
		t.Errorf("history not sorted oldest first: %+v", e.RegularHoursHistory)
	}
}

func TestRegularHoursOn(t *testing.T) {
	e, err := loadDated(t, datedList)
	if err != nil {
		t.Fatal(err)
	}
	for date, want := range map[string]string{
		"1980-01-01": "15:00", "2020-06-02": "15:00", "2024-11-04": "15:00",
		"2024-11-05": "15:30", "2026-01-05": "15:30",
	} {
		got, err := e.RegularHoursOn(date)
		if err != nil || got.Close != want {
			t.Errorf("%s: close = %q (err %v), want %s", date, got.Close, err, want)
		}
	}
	if _, err := e.RegularHoursOn("2024-13-45"); err == nil {
		t.Error("expected an error for a bad date")
	}
}

func TestStatusAtUsesTheHoursOfThatDate(t *testing.T) {
	e, err := loadDated(t, datedList)
	if err != nil {
		t.Fatal(err)
	}
	if got, _ := e.StatusAt("2020-06-02", "15:10"); got != exchangecalendar.StatusClosed {
		t.Errorf("2020 at 15:10 = %v, want closed", got)
	}
	if got, _ := e.StatusAt("2025-06-03", "15:10"); got != exchangecalendar.StatusOpen {
		t.Errorf("2025 at 15:10 = %v, want open", got)
	}
}

func TestSingleRegularHoursObjectStillLoads(t *testing.T) {
	e, err := loadDated(t, `{"open": "09:00", "close": "15:30"}`)
	if err != nil {
		t.Fatal(err)
	}
	got, _ := e.RegularHoursOn("1990-01-02")
	if got.Close != "15:30" || len(e.RegularHoursHistory) != 0 {
		t.Errorf("single object: close %q, history %v", got.Close, e.RegularHoursHistory)
	}
}

func TestMalformedRegularHoursListsAreRejected(t *testing.T) {
	if _, err := loadDated(t, `[]`); err == nil {
		t.Error("empty list accepted")
	}
	if _, err := loadDated(t, `[{"open": "09:00", "close": "15:00"}]`); err == nil {
		t.Error("entry without effective_from accepted")
	}
	if _, err := loadDated(t, `[{"effective_from": "2024-01-01", "open": "16:00", "close": "09:00"}]`); err == nil {
		t.Error("open after close accepted")
	}
}
