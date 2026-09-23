#!/usr/bin/env bash
#
# release.sh — cut a release for the exchange-calendar registry.
#
# Runs through: preconditions → version bump → rebuild → local gate →
# commit → push → poll CI (Validate + Rust Verification) → tag → push tag.
#
# Usage:
#   scripts/release.sh 2.3.0
#   DRY_RUN=1 scripts/release.sh 2.3.0
#
# Preconditions (all enforced):
#   - on main, clean tree, up to date with origin
#   - VERSION differs from the target
#   - CHANGELOG.md already has a "## [<target>]" section
#
# Refuses on any failure. Does not force-push. Never tags a commit whose
# CI has not passed on origin.

set -euo pipefail

VERSION="${1:-}"
DRY_RUN="${DRY_RUN:-0}"
POLL_TIMEOUT="${POLL_TIMEOUT:-900}"   # 15 min
POLL_INTERVAL=15

# ── helpers ────────────────────────────────────────────────────────
say()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }
run() {
    if [[ "$DRY_RUN" == "1" ]]; then
        printf '\033[1;33m  [dry-run]\033[0m %s\n' "$*"
    else
        "$@"
    fi
}

# ── arguments ──────────────────────────────────────────────────────
[[ -n "$VERSION" ]] || die "usage: $0 <x.y.z>   (e.g. 2.3.0)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "version must be x.y.z, got: $VERSION"

cd "$(git rev-parse --show-toplevel)"
ROOT="$(pwd)"
say "Releasing exchange-calendar v$VERSION (dry_run=$DRY_RUN)"

# ── preconditions ──────────────────────────────────────────────────
say "Checking preconditions"

[[ "$(git branch --show-current)" == "main" ]] || die "not on main"
ok "on main"

[[ -z "$(git status --porcelain)" ]] || die "working tree is dirty: $(git status --porcelain | head -1)"
ok "working tree clean"

git fetch origin main --quiet
LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse origin/main)"
[[ "$LOCAL" == "$REMOTE" ]] || die "local main ($LOCAL) is not origin/main ($REMOTE)"
ok "main is up to date with origin"

CURRENT="$(cat VERSION)"
[[ "$CURRENT" != "$VERSION" ]] || die "VERSION is already $VERSION"
ok "VERSION currently $CURRENT, target $VERSION"

grep -q "^## \[$VERSION\]" CHANGELOG.md \
    || die "CHANGELOG.md has no '## [$VERSION]' section — write it first"
ok "CHANGELOG has [${VERSION}] section"

# ── version bump ───────────────────────────────────────────────────
say "Bumping version sites"

run bash -c "echo '$VERSION' > VERSION"
ok "VERSION → $VERSION"

run bash -c "sed -i 's|registry-[0-9.]*-orange|registry-${VERSION}-orange|' README.md"
grep -q "registry-${VERSION}-orange" README.md || die "README badge not updated"
ok "README badge → $VERSION"

# CHANGELOG top entry is already correct (checked above). Verify
# it's still the first dated version heading.
TOP="$(grep -m1 '^## \[' CHANGELOG.md | sed -E 's/^## \[([^]]+)\].*/\1/')"
[[ "$TOP" == "$VERSION" ]] || die "CHANGELOG top entry is $TOP, expected $VERSION"
ok "CHANGELOG top entry = $VERSION"

# ── rebuild artifacts ──────────────────────────────────────────────
say "Rebuilding distribution artifacts"

run python3 tools/build.py
run make package

if [[ "$DRY_RUN" != "1" ]]; then
    # Verify both the root artifact and the wrapper's bundled copy. The
    # wrapper copy is a plain file copy, not a generator output — if
    # `make package` fails silently, the two can disagree and the wheel
    # ships stale data.
    for f in calendar.json wrappers/python/exchange_calendar/calendar.json; do
        V="$(python3 -c "import json; print(json.load(open('$f'))['meta']['version'])")"
        [[ "$V" == "$VERSION" ]] || die "$f meta.version is $V, expected $VERSION"
        ok "$f meta.version = $VERSION"
    done
fi

# ── local gate ─────────────────────────────────────────────────────
say "Running local gate"

run python3 tools/validate.py
ok "validate.py"

run python3 tools/check_country_codes.py --quiet
ok "check_country_codes.py"

run python3 -m pytest tests/ -q
ok "pytest"

# ── commit + push ──────────────────────────────────────────────────
say "Committing release"

run git add VERSION README.md CHANGELOG.md \
        calendar.json wrappers/python/exchange_calendar/calendar.json

if [[ "$DRY_RUN" == "1" ]]; then
    say "DRY RUN — stopping before commit. Would run:"
    echo "    git commit -m 'Release v$VERSION'"
    echo "    git push origin main"
    echo "    (poll CI on the pushed SHA)"
    echo "    git tag -a v$VERSION -m 'Release v$VERSION'"
    echo "    git push --tags"
    exit 0
fi

git commit -m "Release v$VERSION"
SHA="$(git rev-parse HEAD)"
say "Commit: $SHA"

git push origin main
ok "pushed to origin/main"

# ── poll CI ────────────────────────────────────────────────────────
# Gate on Validate and Rust Verification only. Update Exchange Calendar
# Data and Live Fetcher Health Check are schedule-driven and do not run
# on every push; they are not part of the release gate.
say "Polling CI on $SHA (timeout ${POLL_TIMEOUT}s)"

poll_workflow() {
    local workflow="$1"
    local deadline=$(( $(date +%s) + POLL_TIMEOUT ))
    local status="" conclusion=""
    while :; do
        # Query. An empty result set produces "null" for both fields; treat
        # that the same as "no run visible yet" and keep waiting.
        local line
        line="$(gh run list --workflow="$workflow" --commit="$SHA" --limit 1 \
                    --json status,conclusion \
                    --jq '.[0] | "\(.status // "pending") \(.conclusion // "")"' \
                    2>/dev/null || echo "pending ")"
        read -r status conclusion <<< "$line"

        case "$status" in
            completed)
                if [[ "$conclusion" == "success" ]]; then
                    ok "$workflow: $conclusion"
                    return 0
                fi
                die "$workflow finished with conclusion=$conclusion on $SHA"
                ;;
            pending|queued|in_progress|requested|waiting|"")
                : # keep waiting
                ;;
            *)
                die "$workflow: unexpected status=$status on $SHA"
                ;;
        esac
        if (( $(date +%s) > deadline )); then
            die "$workflow: timed out after ${POLL_TIMEOUT}s on $SHA (last status=$status)"
        fi
        sleep "$POLL_INTERVAL"
    done
}

poll_workflow "validate.yml"
poll_workflow "rust-verify.yml"

# ── tag ────────────────────────────────────────────────────────────
say "Tagging (CI green on $SHA)"

git tag -a "v$VERSION" -m "Release v$VERSION"
git push --tags
ok "tagged v$VERSION and pushed"

# ── summary ────────────────────────────────────────────────────────
say "Done."
echo "  Version: v$VERSION"
echo "  Commit:  $SHA"
echo "  Origin:  $(git config --get remote.origin.url)"
echo "  Runs:    gh run list --commit $SHA"
