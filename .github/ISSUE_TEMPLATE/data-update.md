---
name: Exchange Calendar Data Update
about: Report incorrect or missing exchange calendar data
title: '[DATA UPDATE] '
labels: ['data-update', 'needs-review', 'priority-review']
assignees: 'slimissa'
projects: ['exchange-calendar']
---

<!--
================================================================================
 EXCHANGE CALENDAR DATA UPDATE REQUEST
================================================================================

Thank you for helping improve the Exchange Calendar Registry!

This template is for reporting:
  • Incorrect holiday dates
  • Missing holidays
  • Wrong early close times
  • Incorrect trading hours
  • Outdated information
  • New exchange additions

For bugs in the tooling (update_from_exchange.py, validators, etc.),
please use the Bug Report template instead.

Before submitting:
  1. Search existing issues to avoid duplicates
  2. Verify the information against the official exchange website
  3. Provide as much detail as possible
  
================================================================================
-->

## 🔍 Exchange Information

<!-- Replace with the correct information -->

| Field | Value |
|-------|-------|
| **Exchange Name** | <!-- e.g., New York Stock Exchange --> |
| **MIC Code** | <!-- e.g., XNYS (4-letter ISO 10383 code) --> |
| **Country** | <!-- e.g., United States --> |
| **Timezone** | <!-- e.g., America/New_York (IANA format) --> |
| **Official Website** | <!-- e.g., https://www.nyse.com --> |

## 📊 Update Type

<!-- Select the type of update by checking the appropriate box -->

- [ ] **New Holiday** - A holiday that is missing from the registry
- [ ] **Incorrect Date** - A holiday with the wrong date
- [ ] **Removed Holiday** - A holiday that no longer applies
- [ ] **Early Close** - Missing or incorrect early close time
- [ ] **Delayed Open** - Missing or incorrect delayed open time
- [ ] **Trading Hours** - Incorrect regular trading hours
- [ ] **New Exchange** - Request to add a new exchange
- [ ] **Other** - Something else (describe below)

## 📝 Detailed Information

### Holiday Details (if applicable)

<!-- Fill out for holiday-related updates -->

| Field | Value |
|-------|-------|
| **Holiday Name** | <!-- e.g., Juneteenth National Independence Day --> |
| **Date** | <!-- Format: YYYY-MM-DD, e.g., 2026-06-19 --> |
| **Status** | <!-- closed / early_close / delayed_open --> |
| **Early Close Time** | <!-- If applicable, e.g., 13:00 (24-hour format) --> |
| **Delayed Open Time** | <!-- If applicable, e.g., 11:00 (24-hour format) --> |
| **Year(s) Affected** | <!-- e.g., 2025, 2026, 2027 --> |
| **Recurring?** | <!-- Yes/No - if yes, describe pattern --> |

### Current Data (if correcting)

<!-- Show what's currently in the registry -->

```json
{
  "date": "CURRENT_DATE_IN_REGISTRY",
  "name": "CURRENT_NAME_IN_REGISTRY",
  "status": "CURRENT_STATUS_IN_REGISTRY"
}
```

### Corrected Data

<!-- Show what the data should be -->

```json
{
  "date": "CORRECTED_DATE",
  "name": "CORRECTED_NAME",
  "status": "CORRECTED_STATUS"
}
```

## 🔗 Source Information

<!-- CRITICAL: Provide official sources to verify the update -->

### Primary Source

<!-- Official exchange website or regulatory announcement -->

- **URL**: <!-- https://... -->
- **Date Accessed**: <!-- YYYY-MM-DD -->
- **Relevant Quote/Text**: 
  ```
  <!-- Paste the relevant text from the source -->
  ```

### Additional Sources (optional)

<!-- Secondary sources to corroborate the information -->

| Source | URL | Date Accessed |
|--------|-----|---------------|
| <!-- e.g., Regulatory filing --> | <!-- https://... --> | <!-- YYYY-MM-DD --> |
| <!-- e.g., News announcement --> | <!-- https://... --> | <!-- YYYY-MM-DD --> |
| <!-- e.g., Exchange press release --> | <!-- https://... --> | <!-- YYYY-MM-DD --> |

## ⚠️ Impact Assessment

<!-- Help us understand the impact of this update -->

### Severity

- [ ] **Critical** - Affects trading decisions or compliance
- [ ] **High** - Incorrect data for major exchange
- [ ] **Medium** - Minor inaccuracy
- [ ] **Low** - Cosmetic or documentation only

### Affected Components

<!-- Check all that apply -->

- [ ] **Registry Data** - `exchanges/*.json`
- [ ] **Python Wrapper** - `wrappers/python/`
- [ ] **JavaScript Wrapper** - `wrappers/javascript/`
- [ ] **Go Wrapper** - `wrappers/go/`
- [ ] **Rust Wrapper** - `wrappers/rust/`
- [ ] **Build Artifact** - `calendar.json`
- [ ] **Documentation** - `README.md`, `CHANGELOG.md`
- [ ] **Validation Tool** - `tools/validate.py`
- [ ] **Update Tool** - `tools/update_from_exchange.py`

### Affected Users

<!-- Who is impacted by this update? -->

- [ ] All users (major holiday on major exchange)
- [ ] Users of specific exchange
- [ ] Users in specific region
- [ ] Users of specific wrapper
- [ ] Limited impact

## 🔄 Proposed Changes

<!-- If you know what changes are needed, describe them here -->

### File Changes

<!-- List files that need to be modified -->

```
1. exchanges/XNYS.json - Update holiday date
2. calendar.json - Rebuild with updated data
3. CHANGELOG.md - Document the change
```

### Code Changes (if needed)

<!-- If tooling changes are required -->

```python
# Example: Update fetcher logic
def parse_holiday_date(self, date_str, year):
    # Add new date format
    pass
```

## ✅ Verification Checklist

<!-- Confirm you've completed these steps -->

- [ ] I have searched for existing issues about this update
- [ ] I have verified the information against official sources
- [ ] I have provided source URLs for verification
- [ ] I have included the correct date format (YYYY-MM-DD)
- [ ] I have identified all affected years
- [ ] I have checked if this is a recurring holiday
- [ ] I have noted any early close or delayed open times

## 📎 Additional Context

<!-- Any other information that might be helpful -->

### Screenshots (if applicable)

<!-- Drag and drop screenshots here -->

### Historical Context

<!-- Any relevant historical information about this holiday or change -->

### Related Issues

<!-- Link to related issues or PRs -->

- Related: #
- Blocked by: #
- Blocks: #

### Suggested Fix

<!-- If you have a suggested fix, describe it here -->

## 🏷️ Metadata

<!-- Internal use - do not edit -->

- **Submitted by**: <!-- @username -->
- **Submitted at**: <!-- Auto-filled -->
- **Priority**: <!-- Set by maintainers -->
- **Assigned to**: <!-- Set by maintainers -->
- **Milestone**: <!-- Set by maintainers -->

---

<!--
================================================================================
THANK YOU FOR YOUR CONTRIBUTION!

Your report helps maintain the accuracy and reliability of the
Exchange Calendar Registry for the entire quantitative finance community.

After submission:
  1. Maintainers will review within 2-3 business days
  2. The update will be verified against official sources
  3. If approved, it will be included in the next release
  4. You will be notified of the outcome

For urgent issues, please contact:
  - Email: maintainers@exchange-calendar.dev
  - GitHub: @slimissa
  
================================================================================
-->
```
