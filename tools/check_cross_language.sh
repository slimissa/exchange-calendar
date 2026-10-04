#!/usr/bin/env bash
# Verify that all four wrappers answer the fixture's queries identically.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

run_and_capture() {
    local name="$1"; shift
    "$@" > "$TMP/$name.json" 2>"$TMP/$name.err" || {
        echo "FAIL: $name runner exited non-zero" >&2
        cat "$TMP/$name.err" >&2
        return 1
    }
}

echo "Running Python runner..."
run_and_capture python python3 tools/cross_lang/run_python.py
echo "Running JavaScript runner..."
run_and_capture javascript node tools/cross_lang/run_javascript.js

if [[ -f wrappers/rust/examples/cross_lang.rs ]]; then
    echo "Running Rust runner..."
    run_and_capture rust bash -c 'cd wrappers/rust && cargo run --quiet --example cross_lang 2>/dev/null'
else
    echo "SKIP: Rust runner not present (wrappers/rust/examples/cross_lang.rs)"
fi

if [[ -d wrappers/go/cmd/cross_lang ]]; then
    echo "Running Go runner..."
    run_and_capture go bash -c 'cd wrappers/go && go run ./cmd/cross_lang 2>/dev/null'
else
    echo "SKIP: Go runner not present (wrappers/go/cmd/cross_lang)"
fi

status=0
for lang in javascript rust go; do
    [[ -f "$TMP/$lang.json" ]] || continue
    if ! diff -q "$TMP/python.json" "$TMP/$lang.json" >/dev/null; then
        echo "MISMATCH: python vs $lang" >&2
        diff "$TMP/python.json" "$TMP/$lang.json" >&2 || true
        status=1
    else
        echo "OK: python == $lang"
    fi
done

if (( status == 0 )); then
    echo "OK: all four wrappers agree on every fixture query"
fi
exit $status
