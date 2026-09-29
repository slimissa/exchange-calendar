#!/usr/bin/env bash
#
# release.sh — cut a release for the exchange-calendar registry.
#
# Runs through: static preflight (orphan variables, workflow coverage,
# manifest precondition) →
# preconditions → version bump → rebuild → local gate (incl. release
# claims) → commit → push → poll CI → tag → push tag.
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

# Workflows the release waits on. Single source of truth: the poll loop
# below iterates this array, and check_workflows_covered() fails if a
# per-push workflow exists that is not listed here.
POLLED_WORKFLOWS=(
    "validate.yml"
    "rust-verify.yml"
)

# Files the release commit touches. Used by `git add` below and by
# check_workflows_covered() to decide which path-filtered push workflows
# can fire on the release commit.
RELEASE_FILES=(
    VERSION README.md CHANGELOG.md
    calendar.json wrappers/python/exchange_calendar/calendar.json
)

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

# Detect template variables that were renamed but not updated everywhere.
# A heredoc referencing an undefined variable only fails at expansion time,
# not parse time, which can be after the tree has been mutated. Ported from
# ISO 3166 v1.6.7 (scripts/release.sh). Scans the whole script, not only
# heredocs.
check_no_orphan_variables() {
    local orphans
    orphans="$(grep -nE '\$\{[A-Z_]+\}|\$[A-Z_]{3,}' scripts/release.sh \
        | grep -vE '^\s*#' \
        | grep -oE '\$\{?[A-Z_]+' \
        | sort -u \
        | while read -r v; do
            v="${v#\$}"
            v="${v#\{}"
            # A variable is defined if it appears as assignment anywhere.
            if ! grep -qE "(^|\s)${v}=" scripts/release.sh; then
                echo "$v"
            fi
        done || true)"

    if [[ -n "$orphans" ]]; then
        echo "orphan variables (defined nowhere, expanded somewhere):" >&2
        echo "$orphans" | sed 's/^/  /' >&2
        die "release script references undefined variables"
    fi
}

# Every workflow that fires on a push to main must be in POLLED_WORKFLOWS,
# otherwise the release can be tagged while that workflow is red or still
# running. *.yml.disabled files are not enumerated. Fails closed: an
# unparseable workflow or a missing PyYAML is an error, not a pass.
# A push workflow with a `paths:` filter only counts when at least one
# RELEASE_FILES entry matches it (a workflow that cannot fire on the release
# commit has no run to poll). Prints WARN when a polled workflow cannot fire.
check_workflows_covered() {
    local classified kind wf found d triggers_seen
    classified="$(python3 - "${RELEASE_FILES[@]}" <<'PY'
import fnmatch, re, sys
from pathlib import Path

RELEASE_FILES = sys.argv[1:]

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required for the workflow-coverage check (pip install pyyaml)")

def triggers(doc):
    # YAML 1.1 loads a bare `on:` key as boolean True.
    on = doc.get("on", doc.get(True))
    if on is None:
        raise ValueError("no 'on:' block")
    if isinstance(on, str):
        return {on: None}
    if isinstance(on, list):
        return {k: None for k in on}
    if isinstance(on, dict):
        return on
    raise ValueError("unrecognised 'on:' shape")

def fires_on_main_push(trig):
    if "push" not in trig:
        return False
    cfg = trig["push"]
    if not isinstance(cfg, dict):
        return True
    if cfg.get("branches") is not None:
        return any(fnmatch.fnmatch("main", pat) for pat in cfg["branches"])
    if cfg.get("branches-ignore") is not None:
        return not any(fnmatch.fnmatch("main", pat) for pat in cfg["branches-ignore"])
    if "tags" in cfg or "tags-ignore" in cfg:
        return False  # tag-only filter: branch pushes do not trigger it
    return True

def glob_re(pat):
    out, i = "", 0
    while i < len(pat):
        if pat.startswith("**", i):
            out += ".*"; i += 2
        elif pat[i] == "*":
            out += "[^/]*"; i += 1
        elif pat[i] == "?":
            out += "[^/]"; i += 1
        else:
            out += re.escape(pat[i]); i += 1
    return re.compile("^" + out + "$")

def fires_on_release_commit(trig):
    cfg = trig["push"]
    if not isinstance(cfg, dict):
        return True
    paths, ignore = cfg.get("paths"), cfg.get("paths-ignore")
    if paths is not None:
        if any(p.startswith("!") for p in paths):
            return True  # negation patterns not evaluated: assume it fires
        return any(glob_re(p).match(f) for p in paths for f in RELEASE_FILES)
    if ignore is not None:
        return any(not any(glob_re(p).match(f) for p in ignore)
                   for f in RELEASE_FILES)
    return True

files = sorted(list(Path(".github/workflows").glob("*.yml"))
               + list(Path(".github/workflows").glob("*.yaml")))
for f in files:
    try:
        trig = triggers(yaml.safe_load(f.read_text(encoding="utf-8")))
    except Exception as exc:
        sys.exit("cannot classify %s: %s" % (f.name, exc))
    if not fires_on_main_push(trig):
        kind = "OTHER"
    elif fires_on_release_commit(trig):
        kind = "PUSH"
    else:
        kind = "PATHFILTERED"
    print(kind, f.name, ",".join(str(k) for k in trig))
PY
)" || die "workflow-coverage check could not run"

    while read -r kind wf triggers_seen; do
        [[ -n "$kind" ]] || continue
        found=0
        for d in "${POLLED_WORKFLOWS[@]}"; do
            [[ "$d" == "$wf" ]] && found=1
        done
        if [[ "$kind" == "OTHER" ]]; then
            ok "$wf: not per-push (on: $triggers_seen), not required in poll list"
            continue
        fi
        if [[ "$kind" == "PATHFILTERED" ]]; then
            if [[ "$found" -eq 1 ]]; then
                printf '\033[1;33m  WARN\033[0m %s is polled but its push paths filter matches no RELEASE_FILES entry; it will not run on the release commit and the poll will time out\n' "$wf"
            else
                ok "$wf: push-triggered but path-filtered, cannot fire on release commit"
            fi
            continue
        fi
        [[ "$found" -eq 1 ]] \
            || die "per-push workflow $wf is not in POLLED_WORKFLOWS; add it to the array"
        ok "$wf: per-push, in poll list"
    done <<< "$classified"
}

# ── arguments ──────────────────────────────────────────────────────
[[ -n "$VERSION" ]] || die "usage: $0 <x.y.z>   (e.g. 2.3.0)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "version must be x.y.z, got: $VERSION"

cd "$(git rev-parse --show-toplevel)"
ROOT="$(pwd)"
say "Releasing exchange-calendar v$VERSION (dry_run=$DRY_RUN)"

# Fail early if the target version has no entry in the claims manifest.
# Ported from ISO 3166 v1.6.6. Catches a missing manifest entry at
# preflight, before the version bump and rebuild mutate the tree.
check_manifest_has_version() {
    local manifest="$ROOT/tools/release_claims.json"
    [[ -f "$manifest" ]] || die "claims manifest not found: $manifest"
    if ! python3 - "$manifest" "$VERSION" <<'PYINNER'
import json, sys
path, version = sys.argv[1], sys.argv[2]
sys.exit(0 if version in json.load(open(path)) else 1)
PYINNER
    then
        die "version $VERSION missing from tools/release_claims.json"
    fi
    ok "claims manifest has entry for $VERSION"
}

# ── static preflight ───────────────────────────────────────────────
# File-only checks; they need no git state and run before anything mutates
# the tree.
say "Static preflight"

check_no_orphan_variables
ok "no orphan variables in release.sh"

check_workflows_covered
check_manifest_has_version

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

run python3 tools/check_release_claims.py "$VERSION"
ok "check_release_claims.py"

run python3 -m pytest tests/ -q
ok "pytest"

# ── commit + push ──────────────────────────────────────────────────
say "Committing release"

run git add "${RELEASE_FILES[@]}"

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
# Gate on the workflows listed in POLLED_WORKFLOWS. check_workflows_covered()
# (static preflight) fails the release if a per-push workflow is missing.
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

for wf in "${POLLED_WORKFLOWS[@]}"; do
    poll_workflow "$wf"
done

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
