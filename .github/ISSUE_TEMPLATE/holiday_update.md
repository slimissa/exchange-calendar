---
name: Holiday Update
about: Report an error or update in an existing exchange calendar
title: "Update [Exchange Name] ([MIC Code]): [holiday/date/status]"
labels: bug, data
assignees: ""
---

## Exchange

- **MIC Code:** [XXXX — e.g., XNYS]
- **Exchange Name:** [e.g., New York Stock Exchange]

## Type of Update

- [ ] Date is incorrect
- [ ] Holiday is missing
- [ ] Holiday should be removed
- [ ] Status is wrong (closed vs. early_close)
- [ ] Early close time is wrong
- [ ] Weekend observation rule is wrong
- [ ] Substitute holiday is wrong
- [ ] Source URL is broken
- [ ] Other: [describe]

## Current Data

```json
{
  "date": "YYYY-MM-DD",
  "name": "Current Entry Name",
  "status": "closed",
  "early_close_time": null,
  "source_url": "https://current-source-url"
}
```

## Proposed Change

```json
{
  "date": "YYYY-MM-DD",
  "name": "Proposed Entry Name",
  "status": "closed",
  "early_close_time": null,
  "source_url": "https://proposed-source-url"
}
```

## Why This Change Is Needed

[Explain the error. Include dates, weekday names, and the specific rule that applies.]

Example:

> July 4, 2026 falls on a Saturday. Under NYSE Rule 7.2, the market observes
> the holiday on Friday, July 3, 2026. The current data incorrectly lists
> July 4 as the closure date.

## Official Source

- **URL:** [Link to official exchange page]
- **Date accessed:** [YYYY-MM-DD]
- **Relevant text:** [Quote or screenshot of the official calendar showing the correct date]

## Verification

- [ ] I have checked the official exchange calendar
- [ ] I have verified the weekday of the date in question
- [ ] I have confirmed whether the exchange observes weekend shifts
- [ ] I have confirmed the correct status (closed vs. early_close)
- [ ] I have confirmed the early close time (if applicable)

## Impact

- **Current behavior:** [What the registry currently returns for this date]
- **Correct behavior:** [What it should return]

## Related Exchanges

If this holiday is shared across multiple exchanges, list them:

- [ ] XNYS (New York Stock Exchange)
- [ ] XNAS (NASDAQ)
- [ ] Other: [list]

## Additional Notes

[Any context that helps reviewers understand the issue]