#!/usr/bin/env python3
"""
tools/check_sql_dialects.py

Tier 3 for the SQL exports (ADR 0012): execute exchange_calendar.postgresql.sql
against a real PostgreSQL server and exchange_calendar.mysql.sql against a real
MySQL server, then verify what the engines actually stored.

Parsing with sqlglot (tests/test_export_sql.py) cannot show that an engine
accepts the syntax, escapes the strings the same way, or enforces the keys and
CHECKs. This script can.

After each load it checks:
  1. row counts of the five tables equal the counts in calendar.json;
  2. every stored row equals the row the exporter derives from calendar.json
     (this covers quote escaping and non-ASCII text);
  3. the engine enforces the constraints: a foreign key, a primary key, NOT
     NULL, a CHECK, a time CHECK and an invalid calendar date are all
     rejected, and a valid synthetic ad_hoc_closures row is accepted. Each
     probe runs inside a transaction that is rolled back.

Usage:
    python3 tools/check_sql_dialects.py
    python3 tools/check_sql_dialects.py --postgres-uri postgresql://u:p@host:5432/db
    python3 tools/check_sql_dialects.py --mysql-uri mysql://u:p@host:3306/db
    python3 tools/check_sql_dialects.py --wait-seconds 120

Defaults point at the standard local servers (the CI service containers):
    postgresql://postgres:postgres@localhost:5432/postgres
    mysql://root:root@127.0.0.1:3306/mysql

WARNING: each file DROPs and recreates exchanges, sessions, holidays,
ad_hoc_closures and confidence in the target database. Point it at a
disposable database. The MySQL default is the `mysql` schema, which is fine for
a throwaway CI container but not for a server you care about.

Connecting is retried until --wait-seconds elapses, because service containers
boot slowly. A server that never answers is a failure, never a skip.

Drivers (requirements-dev.txt): psycopg2 and PyMySQL. They are imported only
when a connection is made, so this module imports without them.

Exit codes:
    0  both engines loaded the file and every check passed
    1  an engine was reached but a check failed
    2  fatal: cannot connect, driver missing, unreadable input
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_sql  # noqa: E402

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_POSTGRES_URI = "postgresql://postgres:postgres@localhost:5432/postgres"
DEFAULT_MYSQL_URI = "mysql://root:root@127.0.0.1:3306/mysql"
DEFAULT_WAIT_SECONDS = 60.0
RETRY_INTERVAL = 2.0

EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_FATAL = 2

TABLE_NAMES = [t.name for t in export_sql.TABLES]


class CheckError(Exception):
    """A fatal condition (exit 2): no connection, no driver, unreadable input."""


# ---------------------------------------------------------------------------
# Small pure helpers (unit-tested without a database)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ParsedUri:
    host: str
    port: int
    user: str
    password: str
    database: str


def parse_uri(uri: str, schemes: tuple[str, ...], default_port: int) -> ParsedUri:
    parts = urlparse(uri)
    if parts.scheme not in schemes:
        raise CheckError(f"URI scheme must be one of {', '.join(schemes)}: {uri!r}")
    if not parts.hostname:
        raise CheckError(f"URI has no host: {uri!r}")
    try:
        port = parts.port or default_port
    except ValueError as exc:
        raise CheckError(f"URI has an invalid port: {uri!r}") from exc
    return ParsedUri(
        host=parts.hostname,
        port=port,
        user=unquote(parts.username or ""),
        password=unquote(parts.password or ""),
        database=unquote(parts.path.lstrip("/")),
    )


def split_statements(text: str) -> list[str]:
    """Split SQL text on semicolons that are outside strings and comments.

    Handles `--` line comments and single-quoted strings with doubled quotes.
    The exporter never emits backslashes or other quoting forms (it refuses
    them), so nothing else needs handling.
    """
    statements: list[str] = []
    buf: list[str] = []
    in_string = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if in_string:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and text[i + 1] == "'":
                    buf.append("'")
                    i += 1
                else:
                    in_string = False
        elif ch == "'":
            in_string = True
            buf.append(ch)
        elif ch == "-" and text.startswith("--", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def connect_with_retry(
    connect: Callable[[], object],
    label: str,
    wait_seconds: float,
    interval: float = RETRY_INTERVAL,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
):
    """Call connect() until it works or wait_seconds pass. CheckError is not retried."""
    deadline = clock() + max(wait_seconds, 0.0)
    attempt = 0
    while True:
        attempt += 1
        try:
            return connect()
        except CheckError:
            raise
        except Exception as exc:  # driver errors differ per engine
            if clock() >= deadline:
                raise CheckError(
                    f"cannot connect to {label} after {attempt} attempt(s): {exc}"
                ) from exc
            sleep(interval)


def normalise(value: object) -> object:
    """Make a driver value comparable with the exporter's row values."""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def expected_counts(registry: dict) -> dict[str, int]:
    """Row counts straight from calendar.json, independent of the exporter."""
    ex = registry["exchanges"]
    return {
        "exchanges": len(ex),
        "sessions": sum(len(e["sessions"]) for e in ex),
        "holidays": sum(
            len(e["holidays"].get("explicit", [])) + len(e["holidays"].get("generated", []))
            for e in ex
        ),
        "ad_hoc_closures": sum(len(e["ad_hoc_closures"]) for e in ex),
        "confidence": sum(len(e["confidence"]) for e in ex),
    }


# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------

class Engine:
    """What the verifier needs from a database connection."""

    name = "engine"

    def version(self) -> str:
        raise NotImplementedError

    def load_script(self, text: str) -> int:
        """Execute the whole file; return the number of statements."""
        raise NotImplementedError

    def query(self, sql: str) -> list[tuple]:
        raise NotImplementedError

    def attempt(self, sql: str) -> bool:
        """Run sql inside a transaction that is always rolled back.

        Returns True if the engine accepted it, False if it rejected it.
        """
        raise NotImplementedError

    def close(self) -> None:
        pass


class PostgresEngine(Engine):
    name = "PostgreSQL"

    def __init__(self, uri: str, wait_seconds: float):
        target = parse_uri(uri, ("postgresql", "postgres"), 5432)

        def connect():
            try:
                import psycopg2
            except ImportError as exc:
                raise CheckError(
                    "psycopg2 is not installed; run: pip install -r requirements-dev.txt"
                ) from exc
            conn = psycopg2.connect(
                host=target.host, port=target.port, user=target.user,
                password=target.password, dbname=target.database, connect_timeout=5,
            )
            conn.autocommit = True
            return conn

        self._conn = connect_with_retry(connect, f"PostgreSQL at {target.host}:{target.port}", wait_seconds)
        import psycopg2  # noqa: F401  (already importable here)

        self._psycopg2 = psycopg2

    def version(self) -> str:
        return str(self.query("SELECT version()")[0][0]).split(",")[0]

    def load_script(self, text: str) -> int:
        with self._conn.cursor() as cur:
            cur.execute(text)  # no parameters: psycopg2 does no % processing
        return len(split_statements(text))

    def query(self, sql: str) -> list[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())

    def attempt(self, sql: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute("BEGIN")
            try:
                cur.execute(sql)
                return True
            except self._psycopg2.Error:
                return False
            finally:
                cur.execute("ROLLBACK")

    def close(self) -> None:
        self._conn.close()


class MysqlEngine(Engine):
    name = "MySQL"

    def __init__(self, uri: str, wait_seconds: float):
        target = parse_uri(uri, ("mysql",), 3306)

        def connect():
            try:
                import pymysql
            except ImportError as exc:
                raise CheckError(
                    "PyMySQL is not installed; run: pip install -r requirements-dev.txt"
                ) from exc
            return pymysql.connect(
                host=target.host, port=target.port, user=target.user,
                password=target.password, database=target.database or None,
                charset="utf8mb4", autocommit=True, connect_timeout=5,
            )

        self._conn = connect_with_retry(connect, f"MySQL at {target.host}:{target.port}", wait_seconds)
        import pymysql

        self._pymysql = pymysql

    def version(self) -> str:
        return "MySQL " + str(self.query("SELECT VERSION()")[0][0])

    def load_script(self, text: str) -> int:
        statements = split_statements(text)
        with self._conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)  # no parameters: PyMySQL does no % processing
        return len(statements)

    def query(self, sql: str) -> list[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())

    def attempt(self, sql: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute("START TRANSACTION")
            try:
                cur.execute(sql)
                return True
            except self._pymysql.MySQLError:
                return False
            finally:
                cur.execute("ROLLBACK")

    def close(self) -> None:
        self._conn.close()


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def constraint_probes(code: str) -> list[tuple[str, str, bool]]:
    """(label, SQL, should_be_accepted). Valid in PostgreSQL, MySQL and SQLite."""
    holiday = (
        "INSERT INTO holidays (exchange_code, date, name, status, origin, seq) "
        "VALUES ('{c}', '{d}', 'Probe', '{s}', 'explicit', 1)"
    )
    return [
        ("foreign key rejects an unknown exchange",
         "INSERT INTO sessions (exchange_code, type, seq) VALUES ('ZZZZ', 'regular', 1)", False),
        ("primary key rejects a duplicate exchange",
         f"INSERT INTO exchanges SELECT * FROM exchanges WHERE code = '{code}'", False),
        ("NOT NULL rejects a missing confidence level",
         f"INSERT INTO confidence (exchange_code, year, level, source) VALUES ('{code}', 2099, NULL, 'manual')",
         False),
        ("CHECK rejects an unknown holiday status", holiday.format(c=code, d="2099-01-01", s="bogus"), False),
        ("CHECK rejects an impossible time",
         f"INSERT INTO sessions (exchange_code, type, seq, open) VALUES ('{code}', 'halt', 1, '25:00')", False),
        ("an impossible calendar date is rejected", holiday.format(c=code, d="2026-02-30", s="closed"), False),
        ("a valid holiday row is accepted", holiday.format(c=code, d="2099-01-01", s="closed"), True),
        ("a valid ad_hoc_closures row is accepted",
         "INSERT INTO ad_hoc_closures (exchange_code, date, seq, name, status, early_close_time, source_url) "
         f"VALUES ('{code}', '2099-06-01', 1, 'Probe', 'closed', NULL, 'https://example.org/probe')", True),
    ]


def verify(engine: Engine, tables: dict[str, list[tuple]], counts: dict[str, int]) -> list[str]:
    """Return a list of problems; empty means every check passed."""
    problems: list[str] = []

    for table in export_sql.TABLES:
        stored_n = int(engine.query(f"SELECT COUNT(*) FROM {table.name}")[0][0])
        if stored_n != counts[table.name]:
            problems.append(
                f"{table.name}: {stored_n} rows stored, calendar.json has {counts[table.name]}"
            )

    for table in export_sql.TABLES:
        cols = ", ".join(table.col_names)
        stored = Counter(
            tuple(normalise(v) for v in row) for row in engine.query(f"SELECT {cols} FROM {table.name}")
        )
        wanted = Counter(tuple(row) for row in tables[table.name])
        if stored != wanted:
            missing = sum((wanted - stored).values())
            extra = sum((stored - wanted).values())
            sample = next(iter(wanted - stored), None) or next(iter(stored - wanted), None)
            problems.append(
                f"{table.name}: stored rows differ from the exporter's rows "
                f"({missing} missing, {extra} unexpected); first difference: {sample}"
            )

    code = tables["exchanges"][0][0]
    for label, sql, should_accept in constraint_probes(code):
        accepted = engine.attempt(sql)
        if accepted != should_accept:
            problems.append(
                f"constraint probe failed: {label} "
                f"(engine {'accepted' if accepted else 'rejected'} it)"
            )
    return problems


def check_engine(engine: Engine, sql_text: str, tables: dict, counts: dict) -> list[str]:
    print(f"{engine.name}: {engine.version()}")
    n = engine.load_script(sql_text)
    print(f"{engine.name}: executed {n} statements")
    problems = verify(engine, tables, counts)
    if not problems:
        shown = ", ".join(f"{t} {counts[t]}" for t in TABLE_NAMES)
        print(f"{engine.name}: OK ({shown}; rows, escaping and constraints verified)")
    return problems


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute the PostgreSQL and MySQL exports on real servers and verify them.",
        epilog="Exit codes: 0 ok, 1 a check failed, 2 fatal (cannot connect, driver missing).",
    )
    parser.add_argument("--postgres-uri", default=DEFAULT_POSTGRES_URI,
                        help=f"PostgreSQL URI (default: {DEFAULT_POSTGRES_URI})")
    parser.add_argument("--mysql-uri", default=DEFAULT_MYSQL_URI,
                        help=f"MySQL URI (default: {DEFAULT_MYSQL_URI})")
    parser.add_argument("--wait-seconds", type=float, default=DEFAULT_WAIT_SECONDS,
                        help="How long to retry connecting while a server boots "
                             f"(default: {DEFAULT_WAIT_SECONDS:g})")
    parser.add_argument("--registry", "-r", type=Path, default=PROJECT_ROOT / "calendar.json",
                        help="Path to calendar.json")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        registry = export_sql.load_registry(args.registry)
        tables = export_sql.build_tables(registry)
        counts = expected_counts(registry)
        sql = {}
        for dialect in ("postgresql", "mysql"):
            path = PROJECT_ROOT / export_sql.DIALECT_FILES[dialect]
            if not path.exists():
                raise CheckError(f"missing SQL file: {path}")
            sql[dialect] = path.read_bytes().decode("utf-8")
    except (export_sql.ExportError, CheckError, OSError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_FATAL

    jobs = [
        ("postgresql", lambda: PostgresEngine(args.postgres_uri, args.wait_seconds)),
        ("mysql", lambda: MysqlEngine(args.mysql_uri, args.wait_seconds)),
    ]
    fatal = False
    failed = False
    for dialect, make in jobs:
        try:
            engine = make()
        except CheckError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            fatal = True
            continue
        try:
            problems = check_engine(engine, sql[dialect], tables, counts)
        except Exception as exc:  # the engine rejected part of the file
            print(f"FAIL: {engine.name} could not execute {export_sql.DIALECT_FILES[dialect]}: {exc}",
                  file=sys.stderr)
            failed = True
            continue
        finally:
            engine.close()
        for problem in problems:
            print(f"FAIL: {engine.name}: {problem}", file=sys.stderr)
        failed = failed or bool(problems)

    if fatal:
        return EXIT_FATAL
    return EXIT_CHECK_FAILED if failed else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
