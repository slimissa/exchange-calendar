#!/usr/bin/env python3
"""
tools/export_csv.py

Export calendar.json as CSV and TSV, per ADR 0012 (sections 3, 5, 6 and 7).
Each of the five tables is written in four dialects, following the sibling
iso4217 export, so a run writes 20 files at the repository root:

    exchange_calendar.TABLE.csv            RFC 4180: comma, UTF-8, no BOM
    exchange_calendar.TABLE.excel.csv      comma, UTF-8 with a BOM
    exchange_calendar.TABLE.european.csv   semicolon, UTF-8, no BOM
    exchange_calendar.TABLE.tsv            tab, UTF-8, no BOM

where TABLE is exchanges, sessions, holidays, ad_hoc_closures or confidence.
The four dialects differ only in the delimiter and the BOM. The header row is
the table's column list from ADR section 5. The rows are the rows tools/
export_sql.py builds, so the CSV, TSV and SQL exports cannot disagree.

Format rules: UTF-8, LF line endings with a newline after the last record,
minimal quoting (a field is quoted only if it contains the delimiter, a
double quote, CR or LF), an absent value is an empty field, booleans are
`true` or `false`, dates are YYYY-MM-DD and times HH:MM (the text already in
calendar.json).

Formula guard: spreadsheets run a cell that starts with =, +, - or @. The
exporter exits 2 before writing any file if any field in any table does.

Usage:
    python3 tools/export_csv.py                       Write all 20 files
    python3 tools/export_csv.py -t holidays           Write one table's four files
    python3 tools/export_csv.py -t sessions --stdout  Print one table (RFC 4180)
    python3 tools/export_csv.py --check               Exit 1 if a file is stale
    python3 tools/export_csv.py -r /tmp/test.json     Use another registry

Exit codes:
    0  success, or --check matched every file
    1  --check found a mismatch
    2  fatal: bad input, missing registry, invalid data, a failed guard
    3  --check found a committed file missing

Every guard runs before any file is written. Output is deterministic: no
wall clock, code-point sorting, the same bytes on every run.
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_sql  # noqa: E402  (shared flattening, guards and column lists)

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
REGISTRY_PATH: Path = PROJECT_ROOT / "calendar.json"

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_FATAL = 2
EXIT_MISSING = 3

ExportError = export_sql.ExportError

TABLE_NAMES: tuple[str, ...] = tuple(t.name for t in export_sql.TABLES)
BOM = b"\xef\xbb\xbf"

# Stored as 0/1 in the shared rows; written as true/false (ADR section 7).
BOOLEAN_COLUMNS: frozenset[tuple[str, str]] = frozenset(
    {("holidays", "predicted"), ("holidays", "weekend_exception")}
)
FORMULA_LEADS: tuple[str, ...] = ("=", "+", "-", "@")


@dataclass(frozen=True)
class Dialect:
    key: str
    delimiter: str
    bom: bool
    suffix: str


DIALECTS: tuple[Dialect, ...] = (
    Dialect("rfc", ",", False, ".csv"),
    Dialect("excel", ",", True, ".excel.csv"),
    Dialect("european", ";", False, ".european.csv"),
    Dialect("tsv", "\t", False, ".tsv"),
)


def filename(table: str, dialect: Dialect) -> str:
    return f"exchange_calendar.{table}{dialect.suffix}"


def expected_filenames(tables: Optional[list[str]] = None) -> list[str]:
    """Every file name for the given tables (default all), in write order."""
    return [filename(t, d) for t in (tables or TABLE_NAMES) for d in DIALECTS]


# ---------------------------------------------------------------------------
# Cells
# ---------------------------------------------------------------------------

def render_cell(table: str, column: str, value: object) -> str:
    if value is None:
        return ""
    if (table, column) in BOOLEAN_COLUMNS:
        if value not in (0, 1) or isinstance(value, bool):
            raise ExportError(f"{table}.{column}: expected 0 or 1, got {value!r}")
        return "true" if value == 1 else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    raise ExportError(f"{table}.{column}: cannot write {value!r}")


def build_cells(registry: dict) -> dict[str, tuple[list[str], list[list[str]]]]:
    """{table: (header, rows of text)}. Runs the SQL exporter's guards, then ours."""
    tables = export_sql.build_tables(registry)  # raises ExportError on any bad data
    out: dict[str, tuple[list[str], list[list[str]]]] = {}
    for table in export_sql.TABLES:
        header = table.col_names
        rows = [
            [render_cell(table.name, col, value) for col, value in zip(header, row)]
            for row in tables[table.name]
        ]
        out[table.name] = (header, rows)
    _formula_guard(out)
    return out


def _formula_guard(cells: dict[str, tuple[list[str], list[list[str]]]]) -> None:
    for table, (header, rows) in cells.items():
        for number, row in enumerate(rows, start=1):
            for column, text in zip(header, row):
                if text.startswith(FORMULA_LEADS):
                    raise ExportError(
                        f"{table} row {number}: {column} starts with {text[0]!r} "
                        f"(a spreadsheet would run it): {text[:40]!r}"
                    )


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_file(dialect: Dialect, header: list[str], rows: list[list[str]]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.writer(
        buf, delimiter=dialect.delimiter, quotechar='"', doublequote=True,
        quoting=csv.QUOTE_MINIMAL, lineterminator="\n",
    )
    writer.writerow(header)
    writer.writerows(rows)
    data = buf.getvalue().encode("utf-8")
    return BOM + data if dialect.bom else data


def generate(registry_path: Path) -> tuple[dict[str, bytes], dict[str, int]]:
    """({file name: bytes} for all 20 files, {table: row count}). Guards run first."""
    registry = export_sql.load_registry(registry_path)
    cells = build_cells(registry)
    files: dict[str, bytes] = {}
    for table in TABLE_NAMES:
        header, rows = cells[table]
        for dialect in DIALECTS:
            files[filename(table, dialect)] = render_file(dialect, header, rows)
    return files, {table: len(cells[table][1]) for table in TABLE_NAMES}


def generate_all(registry_path: Path) -> dict[str, bytes]:
    """{file name: bytes} for all 20 files. Runs every guard first."""
    return generate(registry_path)[0]


# ---------------------------------------------------------------------------
# Writing and checking
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def check_files(files: dict[str, bytes], names: list[str]) -> int:
    """Regenerate into a temp dir, then byte-compare with the committed files."""
    tmp = Path(tempfile.mkdtemp(prefix="export_csv_check_"))
    missing: list[str] = []
    mismatched: list[str] = []
    try:
        for name in names:
            _atomic_write(tmp / name, files[name])
            committed = PROJECT_ROOT / name
            if not committed.exists():
                missing.append(name)
            elif committed.read_bytes() != (tmp / name).read_bytes():
                mismatched.append(name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for name in mismatched:
        print(f"  MISMATCH {name}", file=sys.stderr)
    for name in missing:
        print(f"  MISSING  {name}", file=sys.stderr)
    if mismatched or missing:
        print("Run 'python3 tools/export_csv.py' to regenerate.", file=sys.stderr)
    if missing:
        return EXIT_MISSING
    if mismatched:
        return EXIT_MISMATCH
    print(f"{len(names)} CSV/TSV file(s) match the registry.")
    return EXIT_OK


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export calendar.json as CSV and TSV (RFC 4180, Excel, European, TSV).",
        epilog="Exit codes: 0 ok, 1 --check mismatch, 2 fatal, 3 committed file missing.",
    )
    parser.add_argument("--registry", "-r", type=Path, default=REGISTRY_PATH,
                        help=f"Path to calendar.json (default: {REGISTRY_PATH})")
    parser.add_argument("--table", "-t", choices=list(TABLE_NAMES) + ["all"], default="all",
                        help="One table or all (default: all). Each table is written in four dialects.")
    parser.add_argument("--stdout", action="store_true",
                        help="Write one table to stdout in the RFC 4180 dialect (needs --table)")
    parser.add_argument("--check", action="store_true",
                        help="Exit 0 if committed files match, 1 if any differ, 3 if any missing")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    tables = list(TABLE_NAMES) if args.table == "all" else [args.table]
    names = expected_filenames(tables)
    if args.stdout and args.table == "all":
        print("ERROR: --stdout requires one --table", file=sys.stderr)
        return EXIT_FATAL
    if args.stdout and args.check:
        print("ERROR: --check and --stdout are mutually exclusive", file=sys.stderr)
        return EXIT_FATAL

    try:
        files, counts = generate(args.registry)
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_FATAL

    if args.check:
        return check_files(files, names)
    if args.stdout:
        data = files[filename(args.table, DIALECTS[0])]
        out = getattr(sys.stdout, "buffer", None)
        if out is not None:
            out.write(data)
            out.flush()
        else:
            sys.stdout.write(data.decode("utf-8"))
        return EXIT_OK

    try:
        for name in names:
            _atomic_write(PROJECT_ROOT / name, files[name])
        for table in tables:
            for dialect in DIALECTS:
                print(f"Wrote {filename(table, dialect)} ({counts[table]} rows)", file=sys.stderr)
    except OSError as exc:
        print(f"ERROR: write failed: {exc}", file=sys.stderr)
        return EXIT_FATAL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
