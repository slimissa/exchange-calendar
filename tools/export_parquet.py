#!/usr/bin/env python3
"""
tools/export_parquet.py

Export calendar.json as Parquet, per ADR 0012 (sections 1, 4, 5, 6 and 7).
Each of the five tables is one file at the repository root:

    exchange_calendar.exchanges.parquet
    exchange_calendar.sessions.parquet
    exchange_calendar.holidays.parquet
    exchange_calendar.ad_hoc_closures.parquet
    exchange_calendar.confidence.parquet

The columns are the table's column list from ADR section 5. The rows are the
rows tools/export_sql.py builds, so the Parquet, CSV and SQL exports cannot
disagree.

Types (ADR section 4):

    dates                         date32 (Parquet DATE)
    times                         string, "HH:MM" (never a Parquet TIME)
    seq, year, weekend_day_1/2    int16 (SQL SMALLINT)
    predicted, weekend_exception  bool
    everything else               string (exchange_code is a plain string,
                                  not a dictionary type)

A column that is NOT NULL in the SQL export is a required field; every other
column is nullable. An absent value is a real Parquet null, never an empty
string; the exporter exits 2 if a string column holds "".

Footer metadata, two keys: exchange_calendar.version (calendar.json
meta.version) and exchange_calendar.table (the table name). The version is in
the footer, so a version bump rewrites all five files. Compression is snappy,
one row group, pyarrow defaults for everything else.

--check compares logical content, not bytes. pyarrow writes the same bytes for
the same table except the version digits in the footer's created_by string, so
a byte comparison would need an exact pyarrow pin and every bump would
regenerate the files. Instead --check reads the committed file, rebuilds the
table from the registry, and requires pyarrow.Table.equals(...,
check_metadata=True): same field names, order, types and nullability, same
values row for row, and the same exchange_calendar.* footer keys. Compression,
row-group layout, encodings and created_by are not compared.

pyarrow is a build-time dependency of this tool only (requirements.txt,
pyarrow>=22.0). The wrappers stay dependency-free.

Usage:
    python3 tools/export_parquet.py                       Write all five files
    python3 tools/export_parquet.py -t holidays           Write one table's file
    python3 tools/export_parquet.py -t sessions --stdout  Write one table's bytes to stdout
    python3 tools/export_parquet.py --check               Exit 1 if a file is stale
    python3 tools/export_parquet.py -r /tmp/test.json     Use another registry

Exit codes:
    0  success, or --check matched every file
    1  --check found a mismatch
    2  fatal: bad input, missing registry, invalid data, pyarrow not installed
    3  --check found a committed file missing

Every guard runs before any file is written. Output is deterministic: no wall
clock, sorted rows.
"""
from __future__ import annotations

import argparse
import datetime
import io
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_sql  # noqa: E402  (shared flattening, guards and column lists)

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError as exc:  # pragma: no cover - exercised through a subprocess in the tests
    if __name__ == "__main__":
        print(f"ERROR: pyarrow is required for this tool: {exc}", file=sys.stderr)
        print("Install with: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(2)
    raise

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
REGISTRY_PATH: Path = PROJECT_ROOT / "calendar.json"

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_FATAL = 2
EXIT_MISSING = 3

ExportError = export_sql.ExportError

TABLE_NAMES: tuple[str, ...] = tuple(t.name for t in export_sql.TABLES)
COMPRESSION = "snappy"

META_VERSION_KEY = "exchange_calendar.version"
META_TABLE_KEY = "exchange_calendar.table"

# Stored as 0/1 in the shared rows; written as bool (ADR section 7).
BOOLEAN_COLUMNS: frozenset[tuple[str, str]] = frozenset(
    {("holidays", "predicted"), ("holidays", "weekend_exception")}
)


def filename(table: str) -> str:
    return f"exchange_calendar.{table}.parquet"


def expected_filenames(tables: Optional[list[str]] = None) -> list[str]:
    """Every file name for the given tables (default all), in write order."""
    return [filename(t) for t in (tables or TABLE_NAMES)]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

def arrow_type(table: str, col: export_sql.Col) -> pa.DataType:
    if col.kind == "date":
        return pa.date32()
    if col.kind == "smallint":
        return pa.bool_() if (table, col.name) in BOOLEAN_COLUMNS else pa.int16()
    return pa.string()  # varchar and char; times are text (ADR section 6)


def build_schema(table: export_sql.Table, version: str) -> pa.Schema:
    """The schema for one table, footer metadata attached."""
    fields = [pa.field(c.name, arrow_type(table.name, c), nullable=c.nullable) for c in table.cols]
    return pa.schema(fields).with_metadata({
        META_VERSION_KEY.encode(): version.encode("utf-8"),
        META_TABLE_KEY.encode(): table.name.encode("utf-8"),
    })


# ---------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------

def convert(table: str, col: export_sql.Col, value: object) -> object:
    """One shared-row value as the Python value pyarrow stores for its column."""
    where = f"{table}.{col.name}"
    if value is None:
        return None
    if (table, col.name) in BOOLEAN_COLUMNS:
        if isinstance(value, bool) or value not in (0, 1):
            raise ExportError(f"{where}: expected 0 or 1, got {value!r}")
        return value == 1
    if col.kind == "date":
        try:
            return datetime.date.fromisoformat(value)
        except (TypeError, ValueError):
            raise ExportError(f"{where}: not an ISO date: {value!r}") from None
    if col.kind == "smallint":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ExportError(f"{where}: expected an integer, got {value!r}")
        if not -32768 <= value <= 32767:
            raise ExportError(f"{where}: {value} does not fit int16")
        return value
    if isinstance(value, str):
        if value == "":
            raise ExportError(f"{where}: empty string (ADR section 7: absent values are null)")
        return value
    raise ExportError(f"{where}: cannot write {value!r}")


def build_table(table: export_sql.Table, rows: list[tuple], version: str) -> pa.Table:
    schema = build_schema(table, version)
    arrays = []
    for index, (col, field) in enumerate(zip(table.cols, schema)):
        values = [convert(table.name, col, row[index]) for row in rows]
        if not field.nullable and any(v is None for v in values):
            raise ExportError(f"{table.name}.{col.name}: null in a required column")
        arrays.append(pa.array(values, type=field.type))
    return pa.Table.from_arrays(arrays, schema=schema)


def build_tables(registry: dict) -> dict[str, pa.Table]:
    """{table: pyarrow Table}. Runs the SQL exporter's guards, then ours."""
    rows = export_sql.build_tables(registry)  # raises ExportError on any bad data
    version = registry["meta"]["version"]
    return {t.name: build_table(t, rows[t.name], version) for t in export_sql.TABLES}


def render(table: pa.Table) -> bytes:
    buf = io.BytesIO()
    pq.write_table(table, buf, compression=COMPRESSION)
    return buf.getvalue()


def generate(registry_path: Path) -> tuple[dict[str, pa.Table], dict[str, bytes]]:
    """({table: Table}, {file name: bytes}) for all five tables. Guards run first."""
    registry = export_sql.load_registry(registry_path)
    tables = build_tables(registry)
    return tables, {filename(name): render(tbl) for name, tbl in tables.items()}


def generate_all(registry_path: Path) -> dict[str, bytes]:
    """{file name: bytes} for all five files. Runs every guard first."""
    return generate(registry_path)[1]


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def _describe(field: pa.Field) -> str:
    return f"{field.type}{'' if field.nullable else ' not null'}"


def compare(committed: pa.Table, expected: pa.Table) -> list[str]:
    """Why two tables differ, as short messages; an empty list means they are equal.

    The messages explain; the verdict is pyarrow.Table.equals with metadata checked.
    """
    problems: list[str] = []
    c_names, e_names = committed.schema.names, expected.schema.names
    if c_names != e_names:
        problems.append(f"columns {c_names} != expected {e_names}")
    else:
        for c_field, e_field in zip(committed.schema, expected.schema):
            if not c_field.equals(e_field):
                problems.append(f"column {c_field.name}: {_describe(c_field)}, expected {_describe(e_field)}")

    c_meta = {k.decode(): v.decode("utf-8", "replace") for k, v in (committed.schema.metadata or {}).items()}
    e_meta = {k.decode(): v.decode("utf-8") for k, v in (expected.schema.metadata or {}).items()}
    for key in sorted(set(c_meta) | set(e_meta)):
        if c_meta.get(key) != e_meta.get(key):
            problems.append(f"metadata {key}: {c_meta.get(key)!r}, expected {e_meta.get(key)!r}")

    if committed.num_rows != expected.num_rows:
        problems.append(f"{committed.num_rows} rows, expected {expected.num_rows}")
    elif not problems:
        for name in e_names:
            got, want = committed.column(name).to_pylist(), expected.column(name).to_pylist()
            if got != want:
                row = next(i for i, (a, b) in enumerate(zip(got, want)) if a != b)
                problems.append(f"column {name} row {row + 1}: {got[row]!r}, expected {want[row]!r}")
                break

    if not problems and not committed.equals(expected, check_metadata=True):
        problems.append("tables differ")  # equals() is stricter than the checks above
    return problems


# ---------------------------------------------------------------------------
# Writing and checking
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def check_files(tables: dict[str, pa.Table], names: list[str]) -> int:
    """Read each committed file and compare it logically with the regenerated table."""
    by_file = {filename(t): tbl for t, tbl in tables.items()}
    missing: list[str] = []
    mismatched: dict[str, list[str]] = {}
    for name in names:
        committed_path = PROJECT_ROOT / name
        if not committed_path.exists():
            missing.append(name)
            continue
        try:
            committed = pq.read_table(committed_path)
        except (pa.ArrowException, OSError) as exc:
            mismatched[name] = [f"unreadable: {exc}"]
            continue
        problems = compare(committed, by_file[name])
        if problems:
            mismatched[name] = problems

    for name, problems in mismatched.items():
        print(f"  MISMATCH {name}", file=sys.stderr)
        for problem in problems[:5]:
            print(f"    {problem}", file=sys.stderr)
    for name in missing:
        print(f"  MISSING  {name}", file=sys.stderr)
    if mismatched or missing:
        print("Run 'python3 tools/export_parquet.py' to regenerate.", file=sys.stderr)
    if missing:
        return EXIT_MISSING
    if mismatched:
        return EXIT_MISMATCH
    print(f"{len(names)} Parquet file(s) match the registry.")
    return EXIT_OK


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export calendar.json as Parquet, one file per table.",
        epilog="Exit codes: 0 ok, 1 --check mismatch, 2 fatal, 3 committed file missing.",
    )
    parser.add_argument("--registry", "-r", type=Path, default=REGISTRY_PATH,
                        help=f"Path to calendar.json (default: {REGISTRY_PATH})")
    parser.add_argument("--table", "-t", choices=list(TABLE_NAMES) + ["all"], default="all",
                        help="One table or all (default: all)")
    parser.add_argument("--stdout", action="store_true",
                        help="Write one table's Parquet bytes to stdout (needs --table)")
    parser.add_argument("--check", action="store_true",
                        help="Exit 0 if committed files match logically, 1 if any differ, 3 if any missing")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    tables_wanted = list(TABLE_NAMES) if args.table == "all" else [args.table]
    names = expected_filenames(tables_wanted)
    if args.stdout and args.table == "all":
        print("ERROR: --stdout requires one --table", file=sys.stderr)
        return EXIT_FATAL
    if args.stdout and args.check:
        print("ERROR: --check and --stdout are mutually exclusive", file=sys.stderr)
        return EXIT_FATAL

    try:
        tables, files = generate(args.registry)
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_FATAL

    if args.check:
        return check_files(tables, names)
    if args.stdout:
        data = files[filename(args.table)]
        out = getattr(sys.stdout, "buffer", None)
        if out is None:
            print("ERROR: stdout is not binary", file=sys.stderr)
            return EXIT_FATAL
        out.write(data)
        out.flush()
        return EXIT_OK

    try:
        for name in names:
            _atomic_write(PROJECT_ROOT / name, files[name])
        for table in tables_wanted:
            print(f"Wrote {filename(table)} ({tables[table].num_rows} rows)", file=sys.stderr)
    except OSError as exc:
        print(f"ERROR: write failed: {exc}", file=sys.stderr)
        return EXIT_FATAL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
