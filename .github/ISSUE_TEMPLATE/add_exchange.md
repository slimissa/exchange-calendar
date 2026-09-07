---
name: Add Exchange
about: Request adding a new exchange calendar to the registry
title: "Add [Exchange Name] ([MIC Code])"
labels: enhancement, exchange
assignees: ""
---

## Exchange Details

- **MIC Code:** [XXXX — 4-character ISO 10383 code, e.g., XNYS]
- **Exchange Name:** [Full official name, e.g., New York Stock Exchange]
- **Time Zone:** [IANA timezone, e.g., America/New_York]
- **Regular Hours:** [open] – [close]
- **Lunch Break:** [Yes/No — if yes, times]
- **Extended Hours:** [Yes/No — if yes, pre-market and after-hours]
- **Half-Day Sessions:** [Yes/No — if yes, dates and early close times]
- **Weekend Observation:** [Does the exchange shift holidays from weekends to weekdays?]
- **Source URL:** [Official exchange page listing holidays]

## Why This Exchange Matters

[Brief explanation of market significance — G7? Emerging market? Regional hub?]

## Holiday Calendar Checklist

Please provide the exchange's official holiday schedule for the next 5 years:

| Year | Holiday | Date | Status (closed / early_close) |
|------|---------|------|-------------------------------|
| 2025 | [Name] | [YYYY-MM-DD] | [closed / early_close] |
| 2026 | [Name] | [YYYY-MM-DD] | [closed / early_close] |
| 2027 | [Name] | [YYYY-MM-DD] | [closed / early_close] |
| 2028 | [Name] | [YYYY-MM-DD] | [closed / early_close] |
| 2029 | [Name] | [YYYY-MM-DD] | [closed / early_close] |

## Holiday Model

Which holiday model does this exchange follow?

- [ ] US weekend adjustment (Saturday→Friday, Sunday→Monday)
- [ ] UK substitute days (Bank Holidays shift to Monday)
- [ ] No substitutes (Germany/Switzerland — holidays on weekends NOT shifted)
- [ ] Open on civil holidays (Euronext/BME — exchange trades on legal holidays)
- [ ] Lunisolar explicit-only (China/Japan/Korea/HK/Singapore)
- [ ] Other: [describe]

## Early Close / Half-Day Rules

If the exchange has half-days:

- **Christmas Eve:** [closed / early_close at HH:MM]
- **New Year's Eve:** [closed / early_close at HH:MM]
- **Other eves:** [describe, e.g., CNY Eve early close]

## Weekend Observation Rules

- Saturday holidays are observed on: [Friday / Monday / Not observed]
- Sunday holidays are observed on: [Monday / Not observed]

## Additional Notes

[Any special cases — national days of mourning, ad-hoc closures, unique rules]

## Checklist

- [ ] I have verified the MIC code from ISO 10383
- [ ] I have verified the timezone from IANA
- [ ] I have verified the holiday dates from the official exchange calendar
- [ ] I have provided a source URL for every holiday
- [ ] I understand that weekend dates should NOT appear in explicit arrays
- [ ] I understand that the exchange may be open on some civil holidays

## Data Submission

If you have already prepared the JSON, paste it below:

```json
{
  "code": "XXXX",
  "name": "Full Exchange Name",
  "mic": "XXXX",
  "timezone": "Continent/City",
  "regular_hours": {
    "open": "09:30",
    "close": "16:00"
  },
  "extended_hours": {},
  "sessions": [],
  "holidays": {
    "explicit": [],
    "recurrence_rules": []
  },
  "ad_hoc_closures": [],
  "generation_range": ["2025-01-01", "2029-12-31"]
}