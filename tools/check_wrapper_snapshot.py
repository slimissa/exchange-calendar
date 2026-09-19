#!/usr/bin/env python3
"""
check_wrapper_snapshot.py — Flags a stale (or missing) bundled copy of
calendar.json inside the Python wrapper package.

wrappers/python/exchange_calendar/calendar.json is a *copy* of the
registry built from exchanges/ by tools/build.py, shipped inside the
Python wrapper package so `pip install` users get a working registry
without needing exchanges/ or tools/ at all. Nothing keeps that copy in
sync automatically: if exchanges/*.json changes and someone forgets to
re-run the packaging step, the wrapper silently ships an old registry.

This script rebuilds the registry in-memory (via tools/build.py's own
`build_registry()` / `write_registry()` functions -- not by shelling out,
so the comparison is exact and uses only the stdlib) into a temp file,
then compares it byte-for-byte against the wrapper's bundled copy.

Usage:
    check_wrapper_snapshot.py [--exchanges-dir PATH] [--wrapper-path PATH]

Defaults:
    exchanges-dir = "exchanges"
    wrapper-path  = "wrappers/python/exchange_calendar/calendar.json"

Exit codes:
    0 — The wrapper's calendar.json is byte-for-byte identical to a fresh
        build from exchanges/
    1 — The wrapper's calendar.json differs from a fresh build, or is
        missing entirely
    2 — A prerequisite is absent: the exchanges/ directory doesn't
        exist, or tools/build.py can't be imported, or the rebuild
        itself fails (e.g. malformed exchange JSON)

To fix a stale or missing copy, run `make package` (see the Makefile),
or equivalently:
    python3 tools/build.py
    cp calendar.json wrappers/python/exchange_calendar/calendar.json
"""

import difflib
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"

DEFAULT_EXCHANGES_DIR = "exchanges"
DEFAULT_WRAPPER_PATH = "wrappers/python/exchange_calendar/calendar.json"


def _import_build_module():
    """Import tools/build.py's build_registry/write_registry functions.

    Returns (build_registry, write_registry) or raises ImportError.
    """
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    import build as build_module  # tools/build.py

    return build_module.build_registry, build_module.write_registry


def rebuild_to_temp(exchanges_dir):
    """Build the registry from exchanges_dir and write it to a fresh temp
    file. Returns the Path to that temp file.

    Raises FileNotFoundError if exchanges_dir doesn't exist, ImportError
    if tools/build.py can't be imported, or ValueError if the build
    itself fails (propagated from build_registry).
    """
    exchanges_dir = Path(exchanges_dir)
    if not exchanges_dir.exists():
        raise FileNotFoundError(f"exchanges directory not found: {exchanges_dir}")

    build_registry, write_registry = _import_build_module()

    registry = build_registry(exchanges_dir)  # may raise ValueError

    fd, tmp_name = tempfile.mkstemp(prefix="calendar_", suffix=".json")
    os.close(fd)
    tmp_path = Path(tmp_name)
    write_registry(registry, tmp_path)
    return tmp_path


def diff_summary(fresh_path, wrapper_path):
    """Return a short human-readable summary of how two files differ:
    size difference plus a count of differing lines from a unified diff.
    """
    fresh_bytes = fresh_path.read_bytes()
    wrapper_bytes = wrapper_path.read_bytes()

    size_delta = len(wrapper_bytes) - len(fresh_bytes)

    try:
        fresh_lines = fresh_bytes.decode("utf-8").splitlines(keepends=True)
        wrapper_lines = wrapper_bytes.decode("utf-8").splitlines(keepends=True)
        diff = list(difflib.unified_diff(wrapper_lines, fresh_lines, n=0))
        changed_lines = sum(
            1 for line in diff
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        )
        diff_line_note = f"{changed_lines} differing line(s) (unified diff, wrapper vs fresh build)"
    except UnicodeDecodeError:
        diff_line_note = "not UTF-8 text; line-level diff unavailable"

    return (
        f"wrapper copy size: {len(wrapper_bytes)} bytes; "
        f"fresh build size: {len(fresh_bytes)} bytes; "
        f"delta: {size_delta:+d} bytes. {diff_line_note}."
    )


def run_check(exchanges_dir=None, wrapper_path=None):
    """Returns (exit_code, report_lines)."""
    exchanges_dir = Path(exchanges_dir if exchanges_dir is not None else DEFAULT_EXCHANGES_DIR)
    wrapper_path = Path(wrapper_path if wrapper_path is not None else DEFAULT_WRAPPER_PATH)

    report = [
        f"Exchanges dir: {exchanges_dir}",
        f"Wrapper copy:  {wrapper_path}",
    ]

    tmp_path = None
    try:
        try:
            tmp_path = rebuild_to_temp(exchanges_dir)
        except FileNotFoundError as exc:
            report.append(f"ERROR: {exc}")
            return 2, report
        except ImportError as exc:
            report.append(f"ERROR: could not import tools/build.py: {exc}")
            return 2, report
        except ValueError as exc:
            report.append(f"ERROR: rebuilding calendar.json failed: {exc}")
            return 2, report

        if not wrapper_path.exists():
            report.append(
                f"FAIL: wrapper copy is missing: {wrapper_path}. "
                f"Run `make package` (or `python3 tools/build.py && "
                f"cp calendar.json {wrapper_path}`) to create it."
            )
            return 1, report

        fresh_bytes = tmp_path.read_bytes()
        wrapper_bytes = wrapper_path.read_bytes()

        if fresh_bytes == wrapper_bytes:
            report.append(
                f"OK: {wrapper_path} is byte-for-byte identical to a fresh build "
                f"({len(fresh_bytes)} bytes)."
            )
            return 0, report

        report.append(f"FAIL: {wrapper_path} is stale (differs from a fresh build).")
        report.append(diff_summary(tmp_path, wrapper_path))
        report.append(
            "Run `make package` (or `python3 tools/build.py && "
            f"cp calendar.json {wrapper_path}`) to sync it."
        )
        return 1, report
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()


def main(argv):
    exchanges_dir = None
    wrapper_path = None

    args = list(argv[1:])
    i = 0
    while i < len(args):
        if args[i] == "--exchanges-dir" and i + 1 < len(args):
            exchanges_dir = args[i + 1]
            i += 2
        elif args[i] == "--wrapper-path" and i + 1 < len(args):
            wrapper_path = args[i + 1]
            i += 2
        else:
            i += 1

    exit_code, report = run_check(exchanges_dir, wrapper_path)
    for line in report:
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
