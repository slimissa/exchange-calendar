#!/usr/bin/env python3
"""
tools/export_sql.py

Export calendar.json as SQL for four dialects, per ADR 0012 (sections 2, 2a
and 5):

    exchange_calendar.sql              ANSI SQL-92 baseline
    exchange_calendar.postgresql.sql   PostgreSQL
    exchange_calendar.mysql.sql        MySQL 8.0.16 or later
    exchange_calendar.sqlite.sql       SQLite 3.37 or later (STRICT)

Five tables in dependency order: exchanges (parent), then sessions,
holidays, ad_hoc_closures and confidence. Each file drops and recreates
them, then inserts one row per statement. The SQLite, PostgreSQL and MySQL
files wrap the INSERT block in a transaction; the ANSI file does not.

Usage:
    python3 tools/export_sql.py                       Write all four files
    python3 tools/export_sql.py -d sqlite             Write one file
    python3 tools/export_sql.py -d mysql --stdout     Print one dialect
    python3 tools/export_sql.py --check               Exit 1 if a file is stale
    python3 tools/export_sql.py -r /tmp/test.json     Use another registry

Exit codes:
    0  success, or --check matched every file
    1  --check found a mismatch
    2  fatal: bad input, missing registry, invalid data, failed guard
    3  --check found a committed file missing

Every guard runs before any file is written. Output is deterministic: LF
line endings, UTF-8 without a BOM, a trailing newline, code-point sorting,
no wall clock.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path
from typing import Callable, Optional

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
REGISTRY_PATH: Path = PROJECT_ROOT / "calendar.json"
REPOSITORY_URL: str = "https://github.com/slimissa/exchange-calendar"

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_FATAL = 2
EXIT_MISSING = 3

DIALECTS: tuple[str, ...] = ("ansi", "postgresql", "mysql", "sqlite")
DIALECT_FILES: dict[str, str] = {
    "ansi": "exchange_calendar.sql",
    "postgresql": "exchange_calendar.postgresql.sql",
    "mysql": "exchange_calendar.mysql.sql",
    "sqlite": "exchange_calendar.sqlite.sql",
}

# Closed enums, copied from schema.json. tests/test_export_sql.py asserts that
# these still equal the schema.
SESSION_TYPES = ("regular", "pre_market", "post_market", "lunch_break", "auction", "halt")
HOLIDAY_STATUSES = ("closed", "early_close", "delayed_open", "special_session")
AD_HOC_STATUSES = ("closed", "early_close")
CONFIDENCE_LEVELS = ("high", "medium", "low")
CONFIDENCE_SOURCES = ("fetcher", "manual", "predicted")
ORIGINS = ("explicit", "generated")

LIMITATION = "Drops and recreates these five tables. Not safe if other tables reference them."


class ExportError(Exception):
    """Raised for any fatal condition; main() turns it into exit code 2."""


# ---------------------------------------------------------------------------
# CHECK definitions (ADR 0012, section 2a). Each check carries the SQL text
# and the equivalent Python predicate, so the generator can refuse to emit a
# row that the database would reject.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Check:
    suffix: str
    sql: Callable[[str], str]
    holds: Callable[[object], bool]
    sqlite_only: bool = False


def c1(lo: int, hi: int) -> Check:
    return Check(
        "_length",
        lambda c: f"LENGTH({c}) BETWEEN {lo} AND {hi}",
        lambda v: isinstance(v, str) and lo <= len(v) <= hi,
    )


def c2(values: tuple) -> Check:
    def sql(c: str) -> str:
        if all(isinstance(v, int) for v in values):
            return f"{c} IN ({', '.join(str(v) for v in values)})"
        return f"{c} IN ({','.join(_quote(v) for v in values)})"

    return Check("", sql, lambda v: v in values and not isinstance(v, bool))


def c3(lo: int, hi: Optional[int] = None) -> Check:
    def sql(c: str) -> str:
        return f"{c} BETWEEN {lo} AND {hi}" if hi is not None else f"{c} >= {lo}"

    def holds(v: object) -> bool:
        return (
            isinstance(v, int) and not isinstance(v, bool)
            and v >= lo and (hi is None or v <= hi)
        )

    return Check("_range", sql, holds)


def _iso_date(v: object) -> bool:
    if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return False
    try:
        return _date.fromisoformat(v).isoformat() == v
    except ValueError:
        return False


def _hhmm(v: object) -> bool:
    return (
        isinstance(v, str) and len(v) == 5 and v[2] == ":"
        and "00" <= v[0:2] <= "23" and "00" <= v[3:5] <= "59"
    )


C4 = Check(
    "_date",
    lambda c: f"{c} GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date({c}) = {c}",
    _iso_date,
    sqlite_only=True,
)
C5 = Check(
    "_time",
    lambda c: (
        f"LENGTH({c})=5 AND SUBSTR({c},3,1)=':' AND SUBSTR({c},1,2) BETWEEN '00' AND '23' "
        f"AND SUBSTR({c},4,2) BETWEEN '00' AND '59'"
    ),
    _hhmm,
)


# ---------------------------------------------------------------------------
# Table definitions (ADR 0012, sections 2, 2a and 5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Col:
    name: str
    kind: str                      # varchar, char, smallint, date
    size: Optional[int] = None
    nullable: bool = True
    check: Optional[Check] = None
    ascii_only: bool = False

    def sql_type(self, dialect: str) -> str:
        if dialect == "sqlite":
            return "INTEGER" if self.kind == "smallint" else "TEXT"
        if self.kind == "varchar":
            return f"VARCHAR({self.size})"
        if self.kind == "char":
            return f"CHAR({self.size})"
        if self.kind == "smallint":
            return "SMALLINT"
        return "DATE"


@dataclass(frozen=True)
class Table:
    name: str
    cols: tuple[Col, ...]
    pk: tuple[str, ...]
    unique: tuple[str, ...] = ()

    @property
    def col_names(self) -> list[str]:
        return [c.name for c in self.cols]


_EXCHANGE_CODE = Col("exchange_code", "varchar", 4, nullable=False)
_TIME = dict(kind="varchar", size=5, check=C5)

EXCHANGES = Table(
    "exchanges",
    (
        Col("code", "varchar", 4, False, c1(4, 4), ascii_only=True),
        Col("name", "varchar", 255, False),
        Col("mic", "char", 4, False, c1(4, 4), ascii_only=True),
        Col("country_code", "char", 2, False, c1(2, 2), ascii_only=True),
        Col("timezone", "varchar", 64, False),
        Col("weekend_day_1", "smallint", None, False, c3(0, 6)),
        Col("weekend_day_2", "smallint", None, False, c3(0, 6)),
        Col("regular_open", nullable=False, **_TIME),
        Col("regular_close", nullable=False, **_TIME),
        Col("generation_start", "date", None, False, C4),
        Col("generation_end", "date", None, False, C4),
    ),
    pk=("code",),
    unique=("mic",),
)

SESSIONS = Table(
    "sessions",
    (
        _EXCHANGE_CODE,
        Col("type", "varchar", 16, False, c2(SESSION_TYPES)),
        Col("seq", "smallint", None, False, c3(1)),
        Col("open", **_TIME),
        Col("close", **_TIME),
        Col("at", **_TIME),
    ),
    pk=("exchange_code", "type", "seq"),
)

HOLIDAYS = Table(
    "holidays",
    (
        _EXCHANGE_CODE,
        Col("date", "date", None, False, C4),
        Col("name", "varchar", 255, False),
        Col("status", "varchar", 16, False, c2(HOLIDAY_STATUSES)),
        Col("origin", "varchar", 16, False, c2(ORIGINS)),
        Col("seq", "smallint", None, False, c3(1)),
        Col("early_close_time", **_TIME),
        Col("delayed_open_time", **_TIME),
        Col("predicted", "smallint", None, True, c2((0, 1))),
        Col("weekend_exception", "smallint", None, True, c2((0, 1))),
        Col("source_url", "varchar", 2048),
    ),
    pk=("exchange_code", "date", "origin", "seq"),
)

AD_HOC_CLOSURES = Table(
    "ad_hoc_closures",
    (
        _EXCHANGE_CODE,
        Col("date", "date", None, False, C4),
        Col("seq", "smallint", None, False, c3(1)),
        Col("name", "varchar", 255, False),
        Col("status", "varchar", 16, False, c2(AD_HOC_STATUSES)),
        Col("early_close_time", **_TIME),
        Col("source_url", "varchar", 2048, False),
    ),
    pk=("exchange_code", "date", "seq"),
)

CONFIDENCE = Table(
    "confidence",
    (
        _EXCHANGE_CODE,
        Col("year", "smallint", None, False),
        Col("level", "varchar", 8, False, c2(CONFIDENCE_LEVELS)),
        Col("source", "varchar", 32, False, c2(CONFIDENCE_SOURCES)),
        Col("last_verified", "date", None, True, C4),
        Col("note", "varchar", 4096),
    ),
    pk=("exchange_code", "year"),
)

# Dependency order: the parent first, then its children.
TABLES: tuple[Table, ...] = (EXCHANGES, SESSIONS, HOLIDAYS, AD_HOC_CLOSURES, CONFIDENCE)


# ---------------------------------------------------------------------------
# Loading and row building
# ---------------------------------------------------------------------------

def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def load_registry(path: Path) -> dict:
    if not path.exists():
        raise ExportError(f"Registry not found: {path}")
    try:
        registry = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExportError(f"Cannot read registry {path}: {exc}") from exc
    if not isinstance(registry, dict):
        raise ExportError("Registry root is not an object")
    meta = registry.get("meta")
    if not isinstance(meta, dict) or not isinstance(meta.get("version"), str) or not meta["version"]:
        raise ExportError("meta.version is missing or not a string")
    if not isinstance(registry.get("exchanges"), list) or not registry["exchanges"]:
        raise ExportError("'exchanges' is missing or not a non-empty list")
    return registry


def _need(obj: dict, key: str, where: str):
    if not isinstance(obj, dict) or key not in obj or obj[key] is None:
        raise ExportError(f"{where}: required field '{key}' is missing")
    return obj[key]


def _flag(value: object, where: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    raise ExportError(f"{where}: expected true, false or absent, got {value!r}")


def build_tables(registry: dict) -> dict[str, list[tuple]]:
    """Flatten the registry into five row lists, sorted per ADR 0012 section 5."""
    exchanges: list[tuple] = []
    sessions: list[tuple] = []
    holidays: list[tuple] = []
    closures: list[tuple] = []
    confidence: list[tuple] = []

    for ex in registry["exchanges"]:
        code = _need(ex, "code", "exchange")
        where = f"exchange {code}"
        weekend = _need(ex, "weekend_days", where)
        hours = _need(ex, "regular_hours", where)
        gen = _need(ex, "generation_range", where)
        if len(weekend) != 2 or len(gen) != 2:
            raise ExportError(f"{where}: weekend_days and generation_range must have two items")
        exchanges.append((
            code, _need(ex, "name", where), _need(ex, "mic", where),
            _need(ex, "country_code", where), _need(ex, "timezone", where),
            weekend[0], weekend[1], _need(hours, "open", where), _need(hours, "close", where),
            gen[0], gen[1],
        ))

        seen: dict[tuple, int] = {}
        for s in _need(ex, "sessions", where):
            stype = _need(s, "type", where)
            key = (stype,)
            seen[key] = seen.get(key, 0) + 1
            sessions.append((
                code, stype, seen[key],
                s.get("open"), s.get("close"), s.get("at"),
            ))

        hol = _need(ex, "holidays", where)
        explicit = hol.get("explicit", [])
        generated = hol.get("generated", [])
        overlap = sorted({h["date"] for h in explicit} & {h["date"] for h in generated})
        if overlap:
            raise ExportError(
                f"{where}: holidays.explicit and holidays.generated overlap on "
                f"{len(overlap)} date(s), first {overlap[0]}"
            )
        seen = {}
        for origin, group in (("explicit", explicit), ("generated", generated)):
            for h in group:
                key = (h["date"], origin)
                seen[key] = seen.get(key, 0) + 1
                holidays.append((
                    code, _need(h, "date", where), _need(h, "name", where),
                    _need(h, "status", where), origin, seen[key],
                    h.get("early_close_time"), h.get("delayed_open_time"),
                    _flag(h.get("predicted"), f"{where} {h['date']} predicted"),
                    _flag(h.get("weekend_exception"), f"{where} {h['date']} weekend_exception"),
                    h.get("source_url"),
                ))

        seen = {}
        for a in _need(ex, "ad_hoc_closures", where):
            key = (a["date"],)
            seen[key] = seen.get(key, 0) + 1
            closures.append((
                code, _need(a, "date", where), seen[key], _need(a, "name", where),
                _need(a, "status", where), a.get("early_close_time"),
                _need(a, "source_url", where),
            ))

        for year, entry in _need(ex, "confidence", where).items():
            if not re.fullmatch(r"\d{4}", year):
                raise ExportError(f"{where}: confidence key {year!r} is not a four-digit year")
            confidence.append((
                code, int(year), _need(entry, "level", where), _need(entry, "source", where),
                entry.get("last_verified"), entry.get("note"),
            ))

    tables = {
        "exchanges": sorted(exchanges, key=lambda r: (r[0],)),
        "sessions": sorted(sessions, key=lambda r: (r[0], r[1], r[2])),
        "holidays": sorted(holidays, key=lambda r: (r[0], r[1], r[4], r[5])),
        "ad_hoc_closures": sorted(closures, key=lambda r: (r[0], r[1], r[2])),
        "confidence": sorted(confidence, key=lambda r: (r[0], r[1])),
    }
    _guard(tables)
    return tables


_UNSAFE = re.compile(r"[\x00-\x1f\x7f\\]")


def _guard(tables: dict[str, list[tuple]]) -> None:
    """Generator guards. Nothing is written until every one of them passes."""
    for table in TABLES:
        rows = tables[table.name]
        idx = {c.name: i for i, c in enumerate(table.cols)}

        # Primary key and unique constraints (the schema guarantees neither).
        for label, names in (("primary key", table.pk),) + (
            (("unique", table.unique),) if table.unique else ()
        ):
            seen: set[tuple] = set()
            for row in rows:
                key = tuple(row[idx[n]] for n in names)
                if key in seen:
                    raise ExportError(f"{table.name}: duplicate {label} {names} = {key}")
                seen.add(key)

        for row in rows:
            where = f"{table.name} {tuple(row[idx[n]] for n in table.pk)}"
            for col, value in zip(table.cols, row):
                if value is None:
                    if not col.nullable:
                        raise ExportError(f"{where}: {col.name} is NOT NULL but empty")
                    continue
                if isinstance(value, str):
                    if value == "":
                        raise ExportError(f"{where}: {col.name} is an empty string")
                    if _UNSAFE.search(value):
                        raise ExportError(
                            f"{where}: {col.name} holds a backslash or control character"
                        )
                    if col.ascii_only and not value.isascii():
                        raise ExportError(f"{where}: {col.name} is not ASCII: {value!r}")
                    if col.size is not None and len(value) > col.size:
                        raise ExportError(
                            f"{where}: {col.name} is {len(value)} characters, bound is {col.size}"
                        )
                if col.kind == "smallint" and not (
                    isinstance(value, int) and not isinstance(value, bool)
                    and -32768 <= value <= 32767
                ):
                    raise ExportError(f"{where}: {col.name} is not a SMALLINT: {value!r}")
                if col.kind in ("varchar", "char") and not isinstance(value, str):
                    raise ExportError(f"{where}: {col.name} is not text: {value!r}")
                if col.check is not None and not col.check.holds(value):
                    raise ExportError(
                        f"{where}: {col.name} = {value!r} would fail its CHECK"
                    )


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return _quote(value)
    return str(int(value))


def _create_table(table: Table, dialect: str) -> list[str]:
    lines = [f"CREATE TABLE {table.name} ("]
    items: list[str] = []
    for col in table.cols:
        not_null = " NOT NULL" if not col.nullable else ""
        items.append(f"    {col.name} {col.sql_type(dialect)}{not_null}")
    items.append(f"    PRIMARY KEY ({', '.join(table.pk)})")
    for name in table.unique:
        items.append(f"    UNIQUE ({name})")
    if table.name != "exchanges":
        items.append(
            f"    CONSTRAINT fk_{table.name}_exchange FOREIGN KEY (exchange_code) "
            "REFERENCES exchanges (code) ON DELETE NO ACTION ON UPDATE NO ACTION"
        )
    for col in table.cols:
        chk = col.check
        if chk is None or (chk.sqlite_only and dialect != "sqlite"):
            continue
        items.append(
            f"    CONSTRAINT chk_{table.name}_{col.name}{chk.suffix} CHECK ({chk.sql(col.name)})"
        )
    lines.append(",\n".join(items))
    if dialect == "mysql":
        lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;")
    elif dialect == "sqlite":
        lines.append(") STRICT;")
    else:
        lines.append(");")
    return lines


_DIALECT_NOTES = {
    "ansi": [
        "Dialect: ANSI SQL-92 baseline. No transaction wrapper.",
    ],
    "postgresql": [
        "Dialect: PostgreSQL. The INSERT block runs in one transaction.",
    ],
    "mysql": [
        "Dialect: MySQL 8.0.16 or later (earlier 8.0 parses CHECK and ignores it).",
        "InnoDB, utf8mb4_bin. DDL commits implicitly, so the transaction starts",
        "after the CREATE statements and wraps the INSERT block.",
    ],
    "sqlite": [
        "Dialect: SQLite 3.37 or later (STRICT tables).",
        "PRAGMA foreign_keys=ON is the first statement, before any BEGIN, because",
        "the setting is per connection and a no-op inside a transaction.",
    ],
}


def render(dialect: str, registry: dict, tables: dict[str, list[tuple]]) -> str:
    """Render one dialect as text (LF line endings, trailing newline)."""
    if dialect not in DIALECTS:
        raise ExportError(f"Unknown dialect: {dialect}")
    version = registry["meta"]["version"]
    counts = {t.name: len(tables[t.name]) for t in TABLES}
    out: list[str] = [
        "-- exchange-calendar registry: SQL export",
        f"-- Source: calendar.json v{version}",
        f"-- Repository: {REPOSITORY_URL}",
        "-- Generated by tools/export_sql.py. Do not edit; regenerate instead.",
    ]
    out += [f"-- {line}" for line in _DIALECT_NOTES[dialect]]
    out += [
        f"-- {LIMITATION}",
        "-- Tables: " + ", ".join(t.name for t in TABLES),
        "-- Rows: " + ", ".join(f"{n} {c}" for n, c in counts.items()),
        "",
    ]
    if dialect == "sqlite":
        out += ["PRAGMA foreign_keys=ON;", ""]

    for table in reversed(TABLES):
        out.append(f"DROP TABLE IF EXISTS {table.name};")
    out.append("")
    for table in TABLES:
        out += _create_table(table, dialect)
        out.append("")

    if dialect == "postgresql":
        out += [
            "-- Alternative for additive loading (do not DROP first). Append a conflict",
            "-- clause to an INSERT; stale rows from an older version persist:",
        ]
        for t in TABLES:
            out.append(
                f"--   INSERT INTO {t.name} (...) VALUES (...) "
                f"ON CONFLICT ({', '.join(t.pk)}) DO NOTHING;"
            )
        out.append("")

    wrapper = {"postgresql": ("BEGIN;", "COMMIT;"), "mysql": ("START TRANSACTION;", "COMMIT;"),
               "sqlite": ("BEGIN;", "COMMIT;")}.get(dialect)
    if wrapper:
        out.append(wrapper[0])
    for table in TABLES:
        cols = ", ".join(table.col_names)
        for row in tables[table.name]:
            values = ", ".join(_literal(v) for v in row)
            out.append(f"INSERT INTO {table.name} ({cols}) VALUES ({values});")
    if wrapper:
        out.append(wrapper[1])
    out.append("")

    out.append("-- Row counts")
    out += [f"--   {t.name}: {counts[t.name]}" for t in TABLES]
    return "\n".join(out) + "\n"


def generate_all(registry_path: Path) -> dict[str, bytes]:
    """Return {dialect: file bytes}. Runs every guard first."""
    registry = load_registry(registry_path)
    tables = build_tables(registry)
    return {d: render(d, registry, tables).encode("utf-8") for d in DIALECTS}


# ---------------------------------------------------------------------------
# Writing and checking
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def check_files(contents: dict[str, bytes], dialects: list[str]) -> int:
    """Regenerate into a temp dir, then byte-compare with the committed files."""
    tmp = Path(tempfile.mkdtemp(prefix="export_sql_check_"))
    missing: list[str] = []
    mismatched: list[str] = []
    try:
        for d in dialects:
            name = DIALECT_FILES[d]
            _atomic_write(tmp / name, contents[d])
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
        print("Run 'python3 tools/export_sql.py' to regenerate.", file=sys.stderr)
    if missing:
        return EXIT_MISSING
    if mismatched:
        return EXIT_MISMATCH
    print(f"{len(dialects)} SQL file(s) match the registry.")
    return EXIT_OK


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export calendar.json as SQL (ANSI, PostgreSQL, MySQL, SQLite).",
        epilog="Exit codes: 0 ok, 1 --check mismatch, 2 fatal, 3 committed file missing.",
    )
    parser.add_argument("--registry", "-r", type=Path, default=REGISTRY_PATH,
                        help=f"Path to calendar.json (default: {REGISTRY_PATH})")
    parser.add_argument("--dialect", "-d", choices=list(DIALECTS) + ["all"], default="all",
                        help="One dialect or all (default: all)")
    parser.add_argument("--stdout", action="store_true",
                        help="Write to stdout instead of files (requires one dialect)")
    parser.add_argument("--check", action="store_true",
                        help="Exit 0 if committed files match, 1 if any differ, 3 if any missing")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    dialects = list(DIALECTS) if args.dialect == "all" else [args.dialect]
    if args.stdout and args.dialect == "all":
        print("ERROR: --stdout requires one --dialect", file=sys.stderr)
        return EXIT_FATAL
    if args.stdout and args.check:
        print("ERROR: --check and --stdout are mutually exclusive", file=sys.stderr)
        return EXIT_FATAL

    try:
        contents = generate_all(args.registry)
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_FATAL

    if args.check:
        return check_files(contents, dialects)
    if args.stdout:
        sys.stdout.write(contents[dialects[0]].decode("utf-8"))
        return EXIT_OK

    registry = load_registry(args.registry)
    tables = build_tables(registry)
    total = sum(len(rows) for rows in tables.values())
    try:
        for d in dialects:
            path = PROJECT_ROOT / DIALECT_FILES[d]
            _atomic_write(path, contents[d])
            print(f"Wrote {path.name} ({len(tables['exchanges'])} exchanges, {total} rows)",
                  file=sys.stderr)
    except OSError as exc:
        print(f"ERROR: write failed: {exc}", file=sys.stderr)
        return EXIT_FATAL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
