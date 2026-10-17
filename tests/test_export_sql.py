#!/usr/bin/env python3
"""
test_export_sql.py — tests for tools/export_sql.py (ADR 0012 sections 2, 2a, 5).

Tier 1 loads the committed SQLite file (and the ANSI file) into an in-memory
SQLite database and exercises keys, foreign keys, CHECKs, NULL handling and
STRICT typing. Tier 2 parses the PostgreSQL, MySQL and ANSI files with
sqlglot. The cross-dialect test extracts every literal from those three
files and compares it, as a multiset, with the rows SQLite actually holds.
sqlglot is required: if it cannot be imported the tests fail, they are not
skipped.

Tier 3 (real PostgreSQL/MySQL execution) runs on GitHub Actions
ubuntu-latest, which ships both preinstalled but stopped. Starts them
in-script.

Alteration and failure cases run on copies under tmp_path; nothing here
modifies the repo.

Run:
    python3 -m pytest tests/test_export_sql.py -v
"""

import copy
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import export_sql  # noqa: E402

try:
    import sqlglot
    from sqlglot import expressions as exp
except ImportError:  # the tests below fail on this, they do not skip
    sqlglot = None
    exp = None

TABLE_NAMES = ["exchanges", "sessions", "holidays", "ad_hoc_closures", "confidence"]
PK_ORDER = {
    "exchanges": "code",
    "sessions": "exchange_code, type, seq",
    "holidays": "exchange_code, date, origin, seq",
    "ad_hoc_closures": "exchange_code, date, seq",
    "confidence": "exchange_code, year",
}


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

def _read(name: str) -> str:
    return (REPO / name).read_bytes().decode("utf-8")


@pytest.fixture(scope="module")
def registry():
    return json.loads((REPO / "calendar.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def live_counts(registry):
    ex = registry["exchanges"]
    return {
        "exchanges": len(ex),
        "sessions": sum(len(e["sessions"]) for e in ex),
        "holidays": sum(
            len(e["holidays"]["explicit"]) + len(e["holidays"]["generated"]) for e in ex
        ),
        "ad_hoc_closures": sum(len(e["ad_hoc_closures"]) for e in ex),
        "confidence": sum(len(e["confidence"]) for e in ex),
    }


@pytest.fixture(scope="module")
def sqlite_base():
    db = sqlite3.connect(":memory:")
    db.executescript(_read("exchange_calendar.sqlite.sql"))
    yield db
    db.close()


@pytest.fixture(scope="module")
def ansi_db():
    db = sqlite3.connect(":memory:")
    db.executescript(_read("exchange_calendar.sql"))
    yield db
    db.close()


@pytest.fixture
def db(sqlite_base):
    """A writable copy of the loaded SQLite database, foreign keys on."""
    copy_db = sqlite3.connect(":memory:")
    sqlite_base.backup(copy_db)
    copy_db.execute("PRAGMA foreign_keys=ON")
    yield copy_db
    copy_db.close()


def _rejects(db, sql, params=(), fragment=""):
    with pytest.raises(sqlite3.IntegrityError) as err:
        db.execute(sql, params)
    assert fragment in str(err.value), str(err.value)


HOLIDAY_SQL = (
    "INSERT INTO holidays (exchange_code, date, name, status, origin, seq) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)
AD_HOC_SQL = (
    "INSERT INTO ad_hoc_closures (exchange_code, date, seq, name, status, "
    "early_close_time, source_url) VALUES (?, ?, ?, ?, ?, ?, ?)"
)
AD_HOC_OK = ("XNYS", "2099-06-01", 1, "Synthetic closure", "closed", None, "https://example.org/x")


def _write_registry(tmp_path, data, name="registry.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def _mutated(registry, fn):
    data = copy.deepcopy(registry)
    fn(data)
    return data


def _exchange(data, code):
    return next(e for e in data["exchanges"] if e["code"] == code)


# ---------------------------------------------------------------------------
# Tier 1: SQLite execution
# ---------------------------------------------------------------------------

class TestSqliteLoad:
    def test_row_counts_equal_live_calendar(self, sqlite_base, live_counts):
        for table in TABLE_NAMES:
            n = sqlite_base.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert n == live_counts[table], table

    def test_file_leaves_foreign_keys_on(self):
        fresh = sqlite3.connect(":memory:")
        assert fresh.execute("PRAGMA foreign_keys").fetchone()[0] == 0
        fresh.executescript(_read("exchange_calendar.sqlite.sql"))
        assert fresh.execute("PRAGMA foreign_keys").fetchone()[0] == 1

    def test_pragma_precedes_any_transaction(self):
        lines = [l for l in _read("exchange_calendar.sqlite.sql").splitlines() if l and not l.startswith("--")]
        assert lines[0] == "PRAGMA foreign_keys=ON;"
        assert lines.index("BEGIN;") > 0

    @pytest.mark.parametrize("table", ["sessions", "holidays", "confidence"])
    def test_foreign_key_rejects_orphan(self, db, table):
        if table == "sessions":
            sql, args = "INSERT INTO sessions (exchange_code, type, seq) VALUES (?, 'regular', 1)", ("ZZZZ",)
        elif table == "holidays":
            sql, args = HOLIDAY_SQL, ("ZZZZ", "2099-01-01", "Orphan", "closed", "explicit", 1)
        else:
            sql, args = ("INSERT INTO confidence (exchange_code, year, level, source) "
                         "VALUES (?, 2099, 'high', 'manual')"), ("ZZZZ",)
        _rejects(db, sql, args, "FOREIGN KEY constraint failed")

    def test_foreign_key_off_without_pragma_accepts_orphan(self, sqlite_base):
        """Why the tests set the pragma: without it an orphan row goes in."""
        other = sqlite3.connect(":memory:")
        sqlite_base.backup(other)
        other.execute("PRAGMA foreign_keys=OFF")
        other.execute(HOLIDAY_SQL, ("ZZZZ", "2099-01-01", "Orphan", "closed", "explicit", 1))

    @pytest.mark.parametrize(
        "label,sql,args,constraint",
        [
            ("C1", "INSERT INTO exchanges (code, name, mic, country_code, timezone, weekend_day_1, "
                   "weekend_day_2, regular_open, regular_close, generation_start, generation_end) "
                   "VALUES ('XX', 'Bad', 'XXXX', 'US', 'UTC', 5, 6, '09:30', '16:00', '2026-01-01', '2026-12-31')",
             (), "chk_exchanges_code_length"),
            ("C2", HOLIDAY_SQL, ("XNYS", "2099-01-01", "Bad status", "bogus", "explicit", 1),
             "chk_holidays_status"),
            ("C2-origin", HOLIDAY_SQL, ("XNYS", "2099-01-01", "Bad origin", "closed", "other", 1),
             "chk_holidays_origin"),
            ("C3-seq", HOLIDAY_SQL, ("XNYS", "2099-01-01", "Bad seq", "closed", "explicit", 0),
             "chk_holidays_seq_range"),
            ("C4", HOLIDAY_SQL, ("XNYS", "2099-02-30", "Bad date", "closed", "explicit", 1),
             "chk_holidays_date_date"),
            ("C5", "INSERT INTO sessions (exchange_code, type, seq, open) VALUES ('XNYS', 'halt', 1, '25:00')",
             (), "chk_sessions_open_time"),
        ],
    )
    def test_check_rejection_per_category(self, db, label, sql, args, constraint):
        _rejects(db, sql, args, f"CHECK constraint failed: {constraint}")

    def test_weekend_day_bound(self, db):
        _rejects(db, "UPDATE exchanges SET weekend_day_1 = 7 WHERE code = 'XNYS'", (),
                 "chk_exchanges_weekend_day_1_range")

    def test_boolean_check(self, db):
        _rejects(db, "UPDATE holidays SET predicted = 2 WHERE rowid = 1", (), "chk_holidays_predicted")

    def test_invalid_calendar_date_rejected_by_c4(self, db):
        """2026-02-30 matches the GLOB shape; date() normalises it, so equality fails."""
        _rejects(db, HOLIDAY_SQL, ("XNYS", "2026-02-30", "Feb 30", "closed", "explicit", 1),
                 "chk_holidays_date_date")
        _rejects(db, "UPDATE confidence SET last_verified = '2026-02-30' WHERE rowid = 1", (),
                 "chk_confidence_last_verified_date")
        _rejects(db, AD_HOC_SQL, ("XNYS", "2026-02-30", 1, "x", "closed", None, "u"),
                 "chk_ad_hoc_closures_date_date")

    @pytest.mark.parametrize("bad", ["2026-1-5", "abcd-ef-gh", "2026/01/05", "20260105"])
    def test_malformed_dates_rejected(self, db, bad):
        _rejects(db, HOLIDAY_SQL, ("XNYS", bad, "Bad", "closed", "explicit", 1), "CHECK constraint failed")

    def test_valid_date_accepted(self, db):
        db.execute(HOLIDAY_SQL, ("XNYS", "2026-03-02", "Fine", "closed", "explicit", 1))

    def test_nullable_note_on_confidence(self, sqlite_base, registry):
        with_note = sum(1 for e in registry["exchanges"] for c in e["confidence"].values() if "note" in c)
        total = sum(len(e["confidence"]) for e in registry["exchanges"])
        assert 0 < with_note < total
        null_notes = sqlite_base.execute("SELECT COUNT(*) FROM confidence WHERE note IS NULL").fetchone()[0]
        assert null_notes == total - with_note

    def test_null_accepted_in_nullable_column_and_rejected_in_required(self, db):
        db.execute("INSERT INTO confidence (exchange_code, year, level, source, last_verified, note) "
                   "VALUES ('XNYS', 2099, 'high', 'manual', NULL, NULL)")
        _rejects(db, "INSERT INTO confidence (exchange_code, year, level, source) "
                     "VALUES ('XNYS', 2098, NULL, 'manual')", (), "NOT NULL constraint failed: confidence.level")

    def test_boolean_values_are_one_zero_or_null(self, sqlite_base):
        vals = {r[0] for r in sqlite_base.execute("SELECT DISTINCT predicted FROM holidays")}
        assert vals == {0, 1, None}

    def test_strict_rejects_wrong_storage_type(self, db):
        _rejects(db, "INSERT INTO sessions (exchange_code, type, seq) VALUES ('XNYS', 'halt', 'abc')",
                 (), "cannot store TEXT value in INTEGER column")

    def test_tables_are_strict(self):
        sql = _read("exchange_calendar.sqlite.sql")
        assert sql.count(") STRICT;") == 5

    def test_sessions_with_two_auctions_get_seq_one_and_two(self, sqlite_base):
        rows = sqlite_base.execute(
            "SELECT seq FROM sessions WHERE exchange_code = 'XASX' AND type = 'auction' ORDER BY seq"
        ).fetchall()
        assert rows == [(1,), (2,)]

    def test_non_ascii_names_are_kept(self, sqlite_base):
        names = [r[0] for r in sqlite_base.execute("SELECT name FROM exchanges")]
        assert any(not n.isascii() for n in names)

    @pytest.mark.parametrize("table", TABLE_NAMES)
    def test_ansi_and_sqlite_loads_yield_identical_rows(self, sqlite_base, ansi_db, table):
        q = f"SELECT * FROM {table} ORDER BY {PK_ORDER[table]}"
        assert ansi_db.execute(q).fetchall() == sqlite_base.execute(q).fetchall()

    def test_ansi_file_sets_no_pragma_and_no_transaction(self):
        sql = _read("exchange_calendar.sql")
        assert "PRAGMA" not in sql and "BEGIN" not in sql and "COMMIT" not in sql


class TestAdHocClosures:
    """Empty today (0 rows). A synthetic insert covers its PK, FK and CHECKs."""

    def test_table_is_empty_in_live_data(self, sqlite_base):
        assert sqlite_base.execute("SELECT COUNT(*) FROM ad_hoc_closures").fetchone()[0] == 0

    def test_valid_row_accepted(self, db):
        db.execute(AD_HOC_SQL, AD_HOC_OK)
        assert db.execute("SELECT COUNT(*) FROM ad_hoc_closures").fetchone()[0] == 1

    def test_primary_key_rejects_duplicate_and_allows_next_seq(self, db):
        db.execute(AD_HOC_SQL, AD_HOC_OK)
        _rejects(db, AD_HOC_SQL, AD_HOC_OK, "UNIQUE constraint failed")
        db.execute(AD_HOC_SQL, AD_HOC_OK[:2] + (2,) + AD_HOC_OK[3:])

    def test_foreign_key_rejects_unknown_exchange(self, db):
        _rejects(db, AD_HOC_SQL, ("ZZZZ",) + AD_HOC_OK[1:], "FOREIGN KEY constraint failed")

    @pytest.mark.parametrize(
        "change,constraint",
        [
            ({4: "bogus"}, "chk_ad_hoc_closures_status"),
            ({4: "delayed_open"}, "chk_ad_hoc_closures_status"),
            ({5: "25:61"}, "chk_ad_hoc_closures_early_close_time_time"),
            ({2: 0}, "chk_ad_hoc_closures_seq_range"),
            ({1: "2026-02-30"}, "chk_ad_hoc_closures_date_date"),
        ],
    )
    def test_checks(self, db, change, constraint):
        row = list(AD_HOC_OK)
        for i, v in change.items():
            row[i] = v
        _rejects(db, AD_HOC_SQL, tuple(row), f"CHECK constraint failed: {constraint}")

    def test_source_url_is_required(self, db):
        _rejects(db, AD_HOC_SQL, AD_HOC_OK[:6] + (None,), "NOT NULL constraint failed")

    def test_name_has_no_check_and_accepts_non_ascii_and_short_text(self, db):
        db.execute(AD_HOC_SQL, ("XNYS", "2099-06-02", 1, "Ñ", "closed", None, "u"))


# ---------------------------------------------------------------------------
# Tier 2 and cross-dialect: sqlglot
# ---------------------------------------------------------------------------

PARSE_DIALECTS = {
    "exchange_calendar.postgresql.sql": "postgres",
    "exchange_calendar.mysql.sql": "mysql",
    "exchange_calendar.sql": None,
}
WRAPPED = {"exchange_calendar.postgresql.sql": 2, "exchange_calendar.mysql.sql": 2, "exchange_calendar.sql": 0}


@pytest.fixture(scope="module")
def parsed():
    assert sqlglot is not None, "sqlglot must be installed (requirements.txt): this test must not skip"
    out = {}
    for name, read in PARSE_DIALECTS.items():
        out[name] = [e for e in sqlglot.parse(_read(name), read=read) if e is not None
                     and not isinstance(e, exp.Semicolon)]
    return out


def test_sqlglot_is_importable():
    assert sqlglot is not None, "sqlglot must be installed (requirements.txt): this test must not skip"


class TestParseOnly:
    @pytest.mark.parametrize("name", list(PARSE_DIALECTS))
    def test_statement_counts(self, parsed, live_counts, name):
        stmts = parsed[name]
        rows = sum(live_counts.values())
        assert Counter(type(s).__name__ for s in stmts if not isinstance(s, (exp.Transaction, exp.Commit))) == {
            "Drop": 5, "Create": 5, "Insert": rows,
        }
        assert len(stmts) == 10 + rows + WRAPPED[name]

    @pytest.mark.parametrize("name", ["exchange_calendar.postgresql.sql", "exchange_calendar.mysql.sql"])
    def test_wrapper_surrounds_only_the_insert_block(self, parsed, name):
        kinds = [type(s).__name__ for s in parsed[name]]
        assert kinds[:10] == ["Drop"] * 5 + ["Create"] * 5
        assert kinds[10] == "Transaction" and kinds[-1] == "Commit"
        assert set(kinds[11:-1]) == {"Insert"}


def _node_value(node):
    if isinstance(node, exp.Null):
        return None
    assert isinstance(node, exp.Literal), repr(node)
    return node.this if node.is_string else int(node.this)


def _insert_rows(statements):
    """{table: Counter of (column tuple, value tuple)} from the INSERT statements."""
    out = {t: Counter() for t in TABLE_NAMES}
    for s in statements:
        if not isinstance(s, exp.Insert):
            continue
        table = s.this.this.name
        cols = tuple(c.name for c in s.this.expressions)
        values = tuple(_node_value(v) for v in s.expression.expressions[0].expressions)
        assert len(cols) == len(values)
        out[table][(cols, values)] += 1
    return out


class TestCrossDialect:
    @pytest.mark.parametrize("name", list(PARSE_DIALECTS))
    def test_all_five_tables_match_sqlite_rows(self, parsed, sqlite_base, name):
        from_ast = _insert_rows(parsed[name])
        for table in TABLE_NAMES:
            cols = export_sql_cols(table)
            executed = Counter(
                (tuple(cols), tuple(r))
                for r in sqlite_base.execute(f"SELECT {', '.join(cols)} FROM {table}")
            )
            assert from_ast[table] == executed, f"{name}: {table}"

    def test_ad_hoc_closures_is_compared_even_when_empty(self, parsed, sqlite_base):
        for name in PARSE_DIALECTS:
            assert _insert_rows(parsed[name])["ad_hoc_closures"] == Counter()
        assert sqlite_base.execute("SELECT COUNT(*) FROM ad_hoc_closures").fetchone()[0] == 0


def export_sql_cols(table):
    return next(t for t in export_sql.TABLES if t.name == table).col_names


# ---------------------------------------------------------------------------
# Determinism, shape of the files, and the committed copies
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_two_runs_have_identical_sha256(self):
        a = export_sql.generate_all(REPO / "calendar.json")
        b = export_sql.generate_all(REPO / "calendar.json")
        assert {d: hashlib.sha256(v).hexdigest() for d, v in a.items()} == \
               {d: hashlib.sha256(v).hexdigest() for d, v in b.items()}

    @pytest.mark.parametrize("dialect", export_sql.DIALECTS)
    def test_committed_file_equals_fresh_output(self, dialect):
        fresh = export_sql.generate_all(REPO / "calendar.json")[dialect]
        assert (REPO / export_sql.DIALECT_FILES[dialect]).read_bytes() == fresh

    @pytest.mark.parametrize("dialect", export_sql.DIALECTS)
    def test_lf_utf8_no_bom_trailing_newline(self, dialect):
        data = (REPO / export_sql.DIALECT_FILES[dialect]).read_bytes()
        assert b"\r" not in data
        assert not data.startswith(b"\xef\xbb\xbf")
        assert data.endswith(b"\n") and not data.endswith(b"\n\n")
        data.decode("utf-8")

    def test_gitattributes_covers_sql(self):
        lines = (REPO / ".gitattributes").read_text().splitlines()
        assert "*.sql text eol=lf" in lines

    def test_rows_are_sorted_by_code_point(self, registry):
        tables = export_sql.build_tables(registry)
        codes = [r[0] for r in tables["exchanges"]]
        assert codes == sorted(codes)
        for name in ("sessions", "holidays", "confidence"):
            keys = [(r[0],) + tuple(r[1:2]) for r in tables[name]]
            assert keys == sorted(keys)

    def test_sessions_sort_by_type_then_seq(self, registry):
        rows = [r for r in export_sql.build_tables(registry)["sessions"] if r[0] == "XASX"]
        assert [(r[1], r[2]) for r in rows] == sorted((r[1], r[2]) for r in rows)

    def test_exporter_is_checksummed_and_outputs_are_not(self):
        files = json.loads((REPO / "checksums.json").read_text())["files"]
        assert "tools/export_sql.py" in files
        assert not [f for f in files if f.endswith(".sql")]


class TestHeaders:
    def test_source_line_reads_meta_version_and_nothing_invented(self, registry):
        for dialect in export_sql.DIALECTS:
            text = _read(export_sql.DIALECT_FILES[dialect])
            assert f"-- Source: calendar.json v{registry['meta']['version']}\n" in text
            assert "Updated:" not in text and "Amendment:" not in text

    def test_limitation_sentence_in_every_header(self):
        for dialect in export_sql.DIALECTS:
            head = _read(export_sql.DIALECT_FILES[dialect]).split("\nDROP", 1)[0]
            assert export_sql.LIMITATION in head

    def test_row_count_footer(self, live_counts):
        for dialect in export_sql.DIALECTS:
            text = _read(export_sql.DIALECT_FILES[dialect])
            for table in TABLE_NAMES:
                assert f"--   {table}: {live_counts[table]}\n" in text

    def test_mysql_header_and_table_options(self):
        text = _read("exchange_calendar.mysql.sql")
        assert "8.0.16" in text.split("\nDROP", 1)[0]
        assert text.count("ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;") == 5

    def test_postgresql_commented_conflict_block_has_one_line_per_table(self):
        text = _read("exchange_calendar.postgresql.sql")
        for t in export_sql.TABLES:
            assert f"--   INSERT INTO {t.name} (...) VALUES (...) ON CONFLICT ({', '.join(t.pk)}) DO NOTHING;" in text
        assert "\nON CONFLICT" not in text

    def test_transaction_wrappers_start_after_the_creates(self):
        for name, opener in (("exchange_calendar.sqlite.sql", "BEGIN;"),
                             ("exchange_calendar.postgresql.sql", "BEGIN;"),
                             ("exchange_calendar.mysql.sql", "START TRANSACTION;")):
            text = _read(name)
            first_insert = re.search(r"^INSERT INTO", text, re.M).start()
            last_insert = max(m.start() for m in re.finditer(r"^INSERT INTO", text, re.M))
            assert text.rfind("CREATE TABLE") < text.index("\n" + opener) < first_insert
            assert text.index("\nCOMMIT;") > last_insert

    def test_drop_order_is_children_first_and_create_order_parent_first(self):
        text = _read("exchange_calendar.sql")
        drops = re.findall(r"^DROP TABLE IF EXISTS (\w+);", text, re.M)
        creates = re.findall(r"^CREATE TABLE (\w+) \(", text, re.M)
        assert creates == TABLE_NAMES and drops == TABLE_NAMES[::-1]

    def test_every_child_has_the_decided_foreign_key(self):
        text = _read("exchange_calendar.sql")
        for t in TABLE_NAMES[1:]:
            assert (f"CONSTRAINT fk_{t}_exchange FOREIGN KEY (exchange_code) REFERENCES exchanges (code) "
                    "ON DELETE NO ACTION ON UPDATE NO ACTION") in text

    def test_c4_only_in_sqlite_and_c5_everywhere(self):
        for dialect in export_sql.DIALECTS:
            text = _read(export_sql.DIALECT_FILES[dialect])
            assert ("GLOB" in text) == (dialect == "sqlite")
            assert "SUBSTR(regular_open,3,1)=':'" in text

    def test_no_check_on_any_name_column(self):
        for dialect in export_sql.DIALECTS:
            assert "_name" not in "".join(
                re.findall(r"CONSTRAINT chk_\w+", _read(export_sql.DIALECT_FILES[dialect]))
            )


# ---------------------------------------------------------------------------
# The spec: enums, NOT NULL rule, and schema agreement
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def schema():
    return json.loads((REPO / "schema.json").read_text(encoding="utf-8"))


class TestSchemaAgreement:
    def test_enum_constants_equal_schema_enums(self, schema):
        p = schema["properties"]
        assert list(export_sql.SESSION_TYPES) == p["sessions"]["items"]["properties"]["type"]["enum"]
        assert list(export_sql.HOLIDAY_STATUSES) == \
            p["holidays"]["properties"]["explicit"]["items"]["properties"]["status"]["enum"]
        assert list(export_sql.AD_HOC_STATUSES) == p["ad_hoc_closures"]["items"]["properties"]["status"]["enum"]
        conf = p["confidence"]["additionalProperties"]["properties"]
        assert list(export_sql.CONFIDENCE_LEVELS) == conf["level"]["enum"]
        assert list(export_sql.CONFIDENCE_SOURCES) == conf["source"]["enum"]

    def test_not_null_iff_required_in_schema(self, schema):
        p = schema["properties"]
        required = {
            "exchanges": set(schema["required"]),
            "sessions": set(p["sessions"]["items"]["required"]),
            "holidays": set(p["holidays"]["properties"]["explicit"]["items"]["required"]),
            "ad_hoc_closures": set(p["ad_hoc_closures"]["items"]["required"]),
            "confidence": set(p["confidence"]["additionalProperties"]["required"]),
        }
        # column -> schema field it comes from; exporter-added columns are NOT NULL by definition
        source_field = {
            "exchanges": {"weekend_day_1": "weekend_days", "weekend_day_2": "weekend_days",
                          "regular_open": "regular_hours", "regular_close": "regular_hours",
                          "generation_start": "generation_range", "generation_end": "generation_range"},
        }
        added = {"exchange_code", "origin", "seq", "year"}
        for table in export_sql.TABLES:
            for col in table.cols:
                if col.name in added:
                    assert not col.nullable, (table.name, col.name)
                    continue
                field = source_field.get(table.name, {}).get(col.name, col.name)
                assert col.nullable == (field not in required[table.name]), (table.name, col.name)

    def test_sizes_and_checks_decided_in_the_adr(self):
        by = {(t.name, c.name): c for t in export_sql.TABLES for c in t.cols}
        assert (by["holidays", "status"].size, by["confidence", "level"].size) == (16, 8)
        assert by["exchanges", "name"].check is None and by["holidays", "name"].check is None
        assert by["ad_hoc_closures", "name"].check is None
        assert [c.name for c in export_sql.TABLES[1].cols][:3] == ["exchange_code", "type", "seq"]
        assert "ordinal" not in {c.name for t in export_sql.TABLES for c in t.cols}
        assert {c.name for t in export_sql.TABLES for c in t.cols if c.ascii_only} == {
            "code", "mic", "country_code"}


# ---------------------------------------------------------------------------
# CLI: --check, --stdout, exit codes, and generator guards (all on copies)
# ---------------------------------------------------------------------------

@pytest.fixture
def sandbox(tmp_path, monkeypatch, registry):
    """A registry copy plus freshly generated SQL files, with PROJECT_ROOT redirected."""
    reg = _write_registry(tmp_path, registry)
    for dialect, data in export_sql.generate_all(reg).items():
        (tmp_path / export_sql.DIALECT_FILES[dialect]).write_bytes(data)
    monkeypatch.setattr(export_sql, "PROJECT_ROOT", tmp_path)
    return tmp_path, reg


class TestCheckMode:
    def test_committed_files_pass_check(self):
        proc = subprocess.run([sys.executable, str(REPO / "tools/export_sql.py"), "--check"],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr

    def test_fresh_copy_passes(self, sandbox):
        _, reg = sandbox
        assert export_sql.main(["-r", str(reg), "--check"]) == 0

    def test_altered_file_fails_with_1(self, sandbox, capsys):
        tmp, reg = sandbox
        target = tmp / "exchange_calendar.mysql.sql"
        target.write_bytes(target.read_bytes() + b"-- tampered\n")
        assert export_sql.main(["-r", str(reg), "--check"]) == 1
        assert "exchange_calendar.mysql.sql" in capsys.readouterr().err

    def test_single_changed_byte_is_detected(self, sandbox):
        tmp, reg = sandbox
        target = tmp / "exchange_calendar.sql"
        data = bytearray(target.read_bytes())
        data[-5] ^= 0x01
        target.write_bytes(bytes(data))
        assert export_sql.main(["-r", str(reg), "--check", "-d", "ansi"]) == 1

    def test_crlf_rewrite_is_detected(self, sandbox):
        tmp, reg = sandbox
        target = tmp / "exchange_calendar.sqlite.sql"
        target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
        assert export_sql.main(["-r", str(reg), "--check"]) == 1

    def test_missing_file_fails_with_3_even_if_another_mismatches(self, sandbox):
        tmp, reg = sandbox
        (tmp / "exchange_calendar.postgresql.sql").unlink()
        (tmp / "exchange_calendar.sql").write_bytes(b"-- stale\n")
        assert export_sql.main(["-r", str(reg), "--check"]) == 3

    def test_check_does_not_write_into_the_project_root(self, sandbox):
        tmp, reg = sandbox
        before = sorted(p.name for p in tmp.iterdir())
        export_sql.main(["-r", str(reg), "--check"])
        assert sorted(p.name for p in tmp.iterdir()) == before

    def test_write_mode_creates_all_four_files(self, tmp_path, monkeypatch, registry):
        reg = _write_registry(tmp_path, registry)
        monkeypatch.setattr(export_sql, "PROJECT_ROOT", tmp_path)
        assert export_sql.main(["-r", str(reg)]) == 0
        assert sorted(p.name for p in tmp_path.glob("*.sql")) == sorted(export_sql.DIALECT_FILES.values())
        assert not list(tmp_path.glob("*.tmp"))


class TestCli:
    def test_stdout_single_dialect(self, capsys):
        assert export_sql.main(["-d", "sqlite", "--stdout"]) == 0
        out = capsys.readouterr().out
        assert out.startswith("-- exchange-calendar registry: SQL export\n")
        assert out.encode("utf-8") == (REPO / "exchange_calendar.sqlite.sql").read_bytes()

    def test_stdout_requires_one_dialect(self):
        assert export_sql.main(["--stdout"]) == 2

    def test_check_and_stdout_are_exclusive(self):
        assert export_sql.main(["-d", "mysql", "--stdout", "--check"]) == 2

    def test_missing_registry_is_fatal(self, tmp_path):
        assert export_sql.main(["-r", str(tmp_path / "nope.json")]) == 2

    def test_invalid_json_is_fatal(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        assert export_sql.main(["-r", str(bad)]) == 2

    def test_missing_meta_version_is_fatal(self, tmp_path, registry):
        data = _mutated(registry, lambda d: d["meta"].pop("version"))
        assert export_sql.main(["-r", str(_write_registry(tmp_path, data))]) == 2

    def test_unknown_dialect_rejected_by_argparse(self):
        with pytest.raises(SystemExit) as err:
            export_sql.main(["-d", "oracle"])
        assert err.value.code == 2


class TestGuards:
    """Each guard exits 2 before any file is written."""

    def _run(self, tmp_path, monkeypatch, data):
        monkeypatch.setattr(export_sql, "PROJECT_ROOT", tmp_path)
        code = export_sql.main(["-r", str(_write_registry(tmp_path, data))])
        assert not list(tmp_path.glob("*.sql")), "a guard failure must not leave files behind"
        return code

    def test_generated_explicit_overlap_exits_2(self, tmp_path, monkeypatch, registry, capsys):
        def overlap(d):
            ex = next(e for e in d["exchanges"] if e["holidays"]["generated"])
            g = ex["holidays"]["generated"][0]
            ex["holidays"]["explicit"].append(dict(g, source_url="https://example.org/x"))
        assert self._run(tmp_path, monkeypatch, _mutated(registry, overlap)) == 2
        assert "overlap" in capsys.readouterr().err

    def test_non_ascii_mic_exits_2(self, tmp_path, monkeypatch, registry, capsys):
        def bad(d):
            _exchange(d, "XNYS")["mic"] = "X\u00d1YS"
        assert self._run(tmp_path, monkeypatch, _mutated(registry, bad)) == 2
        assert "not ASCII" in capsys.readouterr().err

    def test_non_ascii_name_is_allowed(self, tmp_path, registry):
        data = _mutated(registry, lambda d: _exchange(d, "XNYS").__setitem__("name", "Bourse \u00c9t\u00e9"))
        out = export_sql.generate_all(_write_registry(tmp_path, data))
        assert "Bourse \u00c9t\u00e9" in out["mysql"].decode("utf-8")

    def test_duplicate_exchange_code_exits_2(self, tmp_path, monkeypatch, registry):
        data = _mutated(registry, lambda d: d["exchanges"].append(copy.deepcopy(_exchange(d, "XNYS"))))
        assert self._run(tmp_path, monkeypatch, data) == 2

    def test_duplicate_mic_exits_2(self, tmp_path, monkeypatch, registry):
        data = _mutated(registry, lambda d: _exchange(d, "XNAS").__setitem__("mic", "XNYS"))
        assert self._run(tmp_path, monkeypatch, data) == 2

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda d: _exchange(d, "XNYS").__setitem__("name", "x" * 256),
            lambda d: _exchange(d, "XNYS").__setitem__("name", "back\\slash"),
            lambda d: _exchange(d, "XNYS").__setitem__("name", "line\nbreak"),
            lambda d: _exchange(d, "XNYS").__setitem__("name", ""),
            lambda d: _exchange(d, "XNYS").__setitem__("timezone", "z" * 65),
            lambda d: _exchange(d, "XNYS")["holidays"]["explicit"][0].__setitem__("status", "bogus"),
            lambda d: _exchange(d, "XNYS")["holidays"]["explicit"][0].__setitem__("date", "2026-02-30"),
            lambda d: _exchange(d, "XNYS")["holidays"]["explicit"][0].__setitem__("predicted", "yes"),
            lambda d: _exchange(d, "XNYS")["regular_hours"].__setitem__("open", "9:30"),
            lambda d: _exchange(d, "XNYS")["weekend_days"].__setitem__(0, 7),
            lambda d: _exchange(d, "XNYS")["confidence"].__setitem__("26", {"level": "high", "source": "manual"}),
            lambda d: _exchange(d, "XNYS").pop("timezone"),
        ],
    )
    def test_invalid_data_exits_2(self, tmp_path, monkeypatch, registry, mutate):
        assert self._run(tmp_path, monkeypatch, _mutated(registry, mutate)) == 2

    def test_duplicate_natural_keys_get_incrementing_seq_not_an_error(self, tmp_path, registry):
        def dup(d):
            ex = _exchange(d, "XNYS")
            ex["holidays"]["explicit"].append(copy.deepcopy(ex["holidays"]["explicit"][0]))
            ex["ad_hoc_closures"].extend([
                {"date": "2099-06-01", "name": "A", "status": "closed", "source_url": "https://e.org/a"},
                {"date": "2099-06-01", "name": "B", "status": "closed", "source_url": "https://e.org/b"},
            ])
        tables = export_sql.build_tables(_mutated(registry, dup))
        first = _exchange(registry, "XNYS")["holidays"]["explicit"][0]["date"]
        seqs = sorted(r[5] for r in tables["holidays"] if r[0] == "XNYS" and r[1] == first and r[4] == "explicit")
        assert seqs == [1, 2]
        assert [r[2] for r in tables["ad_hoc_closures"]] == [1, 2]
