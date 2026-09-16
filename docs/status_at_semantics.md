# `status_at` semantics for extended hours

## Rule

`status_at(date, time)` returns:

- `CLOSED` if the date is a weekend, holiday, or outside all configured
  sessions.
- `PRE_MARKET` **only** if the exchange declares a `pre_market` session in
  its `extended_hours` config and `time` falls inside that window.
- `AFTER_HOURS` **only** if the exchange declares an `after_hours` session
  and `time` falls inside that window.
- `LUNCH_BREAK` if `time` falls inside a configured `lunch_break` session.
- `OPEN` for times inside `regular_hours` not covered by a break.
- `EARLY_CLOSE` on early-close days before the early-close time.

## Why this changed

Prior to v2.1.10, all four wrappers returned `PRE_MARKET` or
`AFTER_HOURS` for any time before regular open or after regular close,
regardless of whether the exchange declared those sessions. For the ~70
exchanges in this registry with empty `extended_hours`, that reported
sessions that do not exist — Xetra at 07:00 returned `PRE_MARKET` even
though Xetra does not trade pre-market.

## Impact

- **No public API change** — enum values and method signatures are the
  same.
- **Behavior change** — `status_at` between midnight and regular open, or
  after regular close, now returns `CLOSED` for exchanges without extended
  hours.
- **`is_open` is unaffected** — it already returned `false` for
  `PRE_MARKET`/`AFTER_HOURS`, so its answers do not change.
- **Consumers** that relied on `status_at` to distinguish "before open"
  from "closed" must check the exchange's `extended_hours` config, or use
  `is_open`.

## Exchange config examples

- `XNYS`: declares both `pre_market` (04:00–09:30) and `after_hours`
  (16:00–20:00). `status_at("2025-07-07", "08:00")` → `PRE_MARKET`.
  `status_at("2025-07-07", "17:00")` → `AFTER_HOURS`.
- `XETR`: no `extended_hours`. `status_at("2025-07-07", "07:00")` →
  `CLOSED`. `status_at("2025-07-07", "18:00")` → `CLOSED`.

## See also

- `docs/exchange_schema.md` — `extended_hours` field reference
- Wrapper READMEs — per-language `status_at` documentation
