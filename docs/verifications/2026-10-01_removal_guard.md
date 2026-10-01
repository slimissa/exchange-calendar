# Removal guard — verification (2026-10-01)

## Tests added
- `test_update_blocked_by_holiday_removal` — enum member exists.
- `test_update_not_blocked_when_holiday_added` — no false positive.
- `test_update_not_blocked_when_new_exchange` — empty old → no removals.

## Aligned tests
3 fixtures in `test_update_from_exchange.py` asserted pre-v2.7.0
mirror semantics. Now assert BLOCKED_BY_REMOVAL.

## Stage-1 fix
```
-    d.mkdir(exist_ok=True)
+    d.mkdir(parents=True, exist_ok=True)
```

## Workflow fix
Before: `--dry-run` → `git diff` always empty → no PR.
After:  writes; blocked removals summarized in PR body.

## Regression diff v2.6.0 → v2.7.0
```
```

## Dry-run acceptance
```
41
```
