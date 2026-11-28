#!/usr/bin/env bash
# tools/local_gate.sh — the one local gate (session 4b11.1).
#
# Shared by scripts/release.sh (which calls it with the target version),
# CI (validate.yml, job "local-gate") and work sessions ("full gate").
# Extracted unchanged from release.sh: same commands, same order.
#
# Usage:
#   bash tools/local_gate.sh [VERSION]
#   DRY_RUN=1 bash tools/local_gate.sh 2.39.0    # print, do not run
#
# VERSION is the release whose claims tools/check_release_claims.py checks.
# Without it, the top CHANGELOG heading is used when it is a version; when
# the top is [Unreleased] the claims check is skipped, with a line saying so.
#
# Exits non-zero at the first failing command.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DRY_RUN="${DRY_RUN:-0}"
VERSION="${1:-}"

say()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
run() {
    if [[ "$DRY_RUN" == "1" ]]; then
        printf '\033[1;33m  [dry-run]\033[0m %s\n' "$*"
    else
        "$@"
    fi
}

if [[ -z "$VERSION" ]]; then
    TOP="$(grep -m1 '^## \[' CHANGELOG.md | sed -E 's/^## \[([^]]+)\].*/\1/')"
    if [[ "$TOP" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        VERSION="$TOP"
    fi
fi

say "Running local gate"

run python3 tools/validate.py
ok "validate.py"

run python3 tools/check_country_codes.py --quiet
ok "check_country_codes.py"

if [[ -n "$VERSION" ]]; then
    run python3 tools/check_release_claims.py "$VERSION"
    ok "check_release_claims.py"
else
    ok "check_release_claims.py skipped: CHANGELOG top is not a version"
fi

run python3 tools/check_mojibake.py
ok "check_mojibake.py"

run python3 tools/check_mic_codes.py
ok "check_mic_codes.py"

run python3 tools/check_snapshot_freshness.py
ok "check_snapshot_freshness.py"

run python3 tools/check_stale_verifications.py
ok "check_stale_verifications.py"

run python3 tools/check_stale_year_urls.py
ok "check_stale_year_urls.py"

run python3 tools/check_doc_links.py
ok "check_doc_links.py"

run python3 tools/gen_readme_table.py --check
ok "gen_readme_table.py --check"

run python3 tools/check_wrapper_snapshot.py
ok "check_wrapper_snapshot.py"

run bash tools/check_cross_language.sh
ok "check_cross_language.sh"

run python3 tools/migrate_sessions.py --check --quiet
ok "migrate_sessions.py --check"

run python3 tools/derive_confidence.py --check --quiet
ok "derive_confidence.py --check"

# Check 6, hours evidence (ADR 0014; blocking for reference_compared under
# ADR 0015). Added in 4b13: it ran in no gate before.
run python3 tools/check_verification.py
ok "check_verification.py"

# Recheck dates (ADR 0016 R14, session 4e2): an overdue recheck_date turns the
# gate red; one 14 days away or less warns. It ran only as a CI step before.
run python3 tools/check_recheck_dates.py
ok "check_recheck_dates.py"

run python3 tools/check_fetcher_freshness.py
ok "check_fetcher_freshness.py"

run python3 -m pytest tests/ -q
ok "pytest"

run bash -c 'cd wrappers/javascript && npm ci && npm test'
ok "JavaScript wrapper tests"

run bash -c 'cd wrappers/go && go test ./...'
ok "Go wrapper tests"

run bash -c 'cd wrappers/rust && cargo test --quiet'
ok "Rust wrapper tests"
