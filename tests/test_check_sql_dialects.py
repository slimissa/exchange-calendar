#!/usr/bin/env python3
"""
test_check_sql_dialects.py — tests for tools/check_sql_dialects.py.

These need no database server and no database driver, so they run in the
ordinary test job. The real PostgreSQL and MySQL execution is the
`check-sql-execution` job in .github/workflows/validate.yml, which runs the
script itself against service containers.

The verification logic is exercised here with a SQLite-backed Engine that loads
the committed SQLite export. That proves the checker passes on good data and
fails on missing rows, altered rows and constraints that are not enforced.

Run:
    python3 -m pytest tests/test_check_sql_dialects.py -v
"""

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import check_sql_dialects as csd  # noqa: E402
import export_sql  # noqa: E402


def _read(name):
    return (REPO / name).read_bytes().decode("utf-8")


@pytest.fixture(scope="module")
def registry():
    return json.loads((REPO / "calendar.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tables(registry):
    return export_sql.build_tables(registry)


@pytest.fixture(scope="module")
def counts(registry):
    return csd.expected_counts(registry)


class SqliteEngine(csd.Engine):
    """Stands in for a server: the committed SQLite export, foreign keys on."""

    name = "SQLite"

    def __init__(self):
        self.conn = sqlite3.connect(":memory:", isolation_level=None)
        self.load_script(_read("exchange_calendar.sqlite.sql"))
        self.conn.execute("PRAGMA foreign_keys=ON")

    def version(self):
        return "SQLite " + sqlite3.sqlite_version

    def load_script(self, text):
        self.conn.executescript(text)
        return len(csd.split_statements(text))

    def query(self, sql):
        return self.conn.execute(sql).fetchall()

    def attempt(self, sql):
        self.conn.execute("BEGIN")
        try:
            self.conn.execute(sql)
            return True
        except sqlite3.Error:
            return False
        finally:
            self.conn.execute("ROLLBACK")


@pytest.fixture
def engine():
    return SqliteEngine()


# ---------------------------------------------------------------------------
# split_statements
# ---------------------------------------------------------------------------

class TestSplitStatements:
    def test_basic_split_and_trailing_statement(self):
        assert csd.split_statements("SELECT 1; SELECT 2;\nSELECT 3") == ["SELECT 1", "SELECT 2", "SELECT 3"]

    def test_semicolon_inside_a_string_is_kept(self):
        assert csd.split_statements("INSERT INTO t VALUES ('a;b'); SELECT 1;") == [
            "INSERT INTO t VALUES ('a;b')", "SELECT 1"]

    def test_doubled_quote_does_not_end_the_string(self):
        sql = "INSERT INTO t VALUES ('it''s; fine'); SELECT 1;"
        assert csd.split_statements(sql) == ["INSERT INTO t VALUES ('it''s; fine')", "SELECT 1"]

    def test_comments_are_dropped_even_with_semicolons(self):
        sql = "-- header; not a statement\nSELECT 1; -- trailing; note\nSELECT 2;\n-- footer\n"
        assert csd.split_statements(sql) == ["SELECT 1", "SELECT 2"]

    def test_dashes_inside_a_string_are_not_a_comment(self):
        assert csd.split_statements("SELECT '-- not a comment';") == ["SELECT '-- not a comment'"]

    def test_empty_and_comment_only_input(self):
        assert csd.split_statements("") == [] and csd.split_statements("-- only a comment\n") == []

    @pytest.mark.parametrize("name,wrapped", [
        ("exchange_calendar.postgresql.sql", 2), ("exchange_calendar.mysql.sql", 2), ("exchange_calendar.sql", 0),
    ])
    def test_real_files_split_into_the_expected_statements(self, name, wrapped, counts):
        statements = csd.split_statements(_read(name))
        assert len(statements) == 10 + sum(counts.values()) + wrapped

    @pytest.mark.parametrize("name", ["exchange_calendar.postgresql.sql", "exchange_calendar.mysql.sql"])
    def test_every_insert_survives_the_split_unchanged(self, name):
        text = _read(name)
        from_lines = [l[:-1] for l in text.splitlines() if l.startswith("INSERT INTO")]
        from_split = [s for s in csd.split_statements(text) if s.startswith("INSERT INTO")]
        assert from_split == from_lines


# ---------------------------------------------------------------------------
# parse_uri, defaults, retry, normalise
# ---------------------------------------------------------------------------

class TestUris:
    def test_defaults(self):
        pg = csd.parse_uri(csd.DEFAULT_POSTGRES_URI, ("postgresql",), 5432)
        my = csd.parse_uri(csd.DEFAULT_MYSQL_URI, ("mysql",), 3306)
        assert (pg.host, pg.port, pg.user, pg.password, pg.database) == ("localhost", 5432, "postgres", "postgres", "postgres")
        assert (my.host, my.port, my.user, my.password, my.database) == ("127.0.0.1", 3306, "root", "root", "mysql")

    def test_documented_defaults_are_exact(self):
        assert csd.DEFAULT_POSTGRES_URI == "postgresql://postgres:postgres@localhost:5432/postgres"
        assert csd.DEFAULT_MYSQL_URI == "mysql://root:root@127.0.0.1:3306/mysql"

    def test_percent_encoded_password_and_default_port(self):
        p = csd.parse_uri("mysql://me:p%40ss%3Aword@db.example/x", ("mysql",), 3306)
        assert (p.user, p.password, p.port, p.host, p.database) == ("me", "p@ss:word", 3306, "db.example", "x")

    @pytest.mark.parametrize("uri", ["http://h/x", "mysql:///x", "postgresql://u:p@h:notaport/x"])
    def test_bad_uris_are_fatal(self, uri):
        with pytest.raises(csd.CheckError):
            csd.parse_uri(uri, ("postgresql",), 5432)


class TestRetry:
    def _clock(self):
        state = {"now": 0.0, "slept": []}

        def sleep(s):
            state["slept"].append(s)
            state["now"] += s

        return state, sleep, lambda: state["now"]

    def test_retries_until_it_connects(self):
        state, sleep, clock = self._clock()
        calls = {"n": 0}

        def connect():
            calls["n"] += 1
            if calls["n"] < 4:
                raise OSError("still booting")
            return "conn"

        assert csd.connect_with_retry(connect, "x", 60, interval=2, sleep=sleep, clock=clock) == "conn"
        assert calls["n"] == 4 and state["slept"] == [2, 2, 2]

    def test_gives_up_after_the_wait_and_says_so(self):
        state, sleep, clock = self._clock()

        def connect():
            raise OSError("refused")

        with pytest.raises(csd.CheckError) as err:
            csd.connect_with_retry(connect, "PostgreSQL at h:1", 5, interval=2, sleep=sleep, clock=clock)
        assert "PostgreSQL at h:1" in str(err.value) and "refused" in str(err.value)
        assert sum(state["slept"]) >= 5 - 2

    def test_zero_wait_tries_exactly_once(self):
        state, sleep, clock = self._clock()
        calls = {"n": 0}

        def connect():
            calls["n"] += 1
            raise OSError("no")

        with pytest.raises(csd.CheckError):
            csd.connect_with_retry(connect, "x", 0, sleep=sleep, clock=clock)
        assert calls["n"] == 1 and state["slept"] == []

    def test_a_check_error_is_never_retried(self):
        state, sleep, clock = self._clock()
        calls = {"n": 0}

        def connect():
            calls["n"] += 1
            raise csd.CheckError("driver missing")

        with pytest.raises(csd.CheckError):
            csd.connect_with_retry(connect, "x", 60, sleep=sleep, clock=clock)
        assert calls["n"] == 1 and state["slept"] == []


def test_normalise_turns_dates_into_iso_strings():
    import datetime
    assert csd.normalise(datetime.date(2026, 3, 2)) == "2026-03-02"
    assert csd.normalise("x") == "x" and csd.normalise(3) == 3 and csd.normalise(None) is None


def test_expected_counts_match_the_exporters_rows(counts, tables):
    assert counts == {t: len(rows) for t, rows in tables.items()}
    assert counts["ad_hoc_closures"] == 0


# ---------------------------------------------------------------------------
# verify(): the checker passes on good data and fails on bad data
# ---------------------------------------------------------------------------

class TestVerify:
    def test_clean_load_has_no_problems(self, engine, tables, counts):
        assert csd.verify(engine, tables, counts) == []

    def test_probes_cover_every_constraint_family(self, tables):
        labels = " | ".join(l for l, _, _ in csd.constraint_probes(tables["exchanges"][0][0]))
        for word in ("foreign key", "primary key", "NOT NULL", "CHECK", "time", "calendar date", "ad_hoc_closures"):
            assert word in labels

    def test_a_missing_row_is_reported_as_a_count_and_a_content_problem(self, engine, tables, counts):
        engine.conn.execute("DELETE FROM confidence WHERE rowid = (SELECT MIN(rowid) FROM confidence)")
        problems = csd.verify(engine, tables, counts)
        assert any("confidence: 360 rows stored, calendar.json has 361" in p for p in problems)
        assert any(p.startswith("confidence: stored rows differ") for p in problems)

    def test_an_altered_value_is_reported(self, engine, tables, counts):
        engine.conn.execute("UPDATE holidays SET name = name || ' (edited)' WHERE rowid = 1")
        problems = csd.verify(engine, tables, counts)
        assert problems and all(p.startswith("holidays: stored rows differ") for p in problems)

    def test_an_extra_row_is_reported(self, engine, tables, counts):
        engine.conn.execute("INSERT INTO ad_hoc_closures (exchange_code, date, seq, name, status, source_url) "
                            "VALUES ('XNYS', '2099-01-01', 1, 'x', 'closed', 'u')")
        problems = csd.verify(engine, tables, counts)
        assert any("ad_hoc_closures: 1 rows stored, calendar.json has 0" in p for p in problems)

    def test_unenforced_foreign_keys_are_detected(self, engine, tables, counts):
        engine.conn.execute("PRAGMA foreign_keys=OFF")
        problems = csd.verify(engine, tables, counts)
        assert problems == ["constraint probe failed: foreign key rejects an unknown exchange "
                            "(engine accepted it)"]

    def test_probes_always_roll_back(self, engine, tables, counts):
        before = {t: engine.query(f"SELECT COUNT(*) FROM {t}")[0][0] for t in csd.TABLE_NAMES}
        csd.verify(engine, tables, counts)
        assert {t: engine.query(f"SELECT COUNT(*) FROM {t}")[0][0] for t in csd.TABLE_NAMES} == before

    def test_check_engine_prints_progress_and_returns_no_problems(self, engine, tables, counts, capsys):
        problems = csd.check_engine(engine, _read("exchange_calendar.sqlite.sql"), tables, counts)
        out = capsys.readouterr().out
        assert problems == [] and "SQLite: OK (exchanges 74" in out


# ---------------------------------------------------------------------------
# Rule 7: a server that cannot be reached is a failure, never a skip
# ---------------------------------------------------------------------------

DEAD = ["--postgres-uri", "postgresql://u:p@127.0.0.1:1/x", "--mysql-uri", "mysql://u:p@127.0.0.1:1/x",
        "--wait-seconds", "0"]


class TestRule7:
    def test_unreachable_servers_exit_2(self, capsys):
        assert csd.main(DEAD) == 2
        err = capsys.readouterr().err
        assert err.count("ERROR:") == 2

    def test_unreachable_via_the_command_line_exits_2(self):
        proc = subprocess.run([sys.executable, str(REPO / "tools/check_sql_dialects.py")] + DEAD,
                              capture_output=True, text=True)
        assert proc.returncode == 2 and "ERROR:" in proc.stderr

    @pytest.mark.parametrize("module,engine_cls,uri", [
        ("psycopg2", "PostgresEngine", "postgresql://u:p@127.0.0.1:1/x"),
        ("pymysql", "MysqlEngine", "mysql://u:p@127.0.0.1:1/x"),
    ])
    def test_a_missing_driver_is_fatal_and_says_how_to_fix_it(self, monkeypatch, module, engine_cls, uri):
        monkeypatch.setitem(sys.modules, module, None)  # makes `import module` raise ImportError
        with pytest.raises(csd.CheckError) as err:
            getattr(csd, engine_cls)(uri, 0)
        assert "requirements-dev.txt" in str(err.value)

    def test_a_missing_sql_file_is_fatal(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(csd, "PROJECT_ROOT", tmp_path)
        assert csd.main(DEAD + ["--registry", str(REPO / "calendar.json")]) == 2
        assert "missing SQL file" in capsys.readouterr().err

    def test_a_missing_registry_is_fatal(self, tmp_path, capsys):
        assert csd.main(DEAD + ["--registry", str(tmp_path / "none.json")]) == 2

    def test_module_imports_without_drivers(self):
        src = (REPO / "tools/check_sql_dialects.py").read_text(encoding="utf-8")
        top_level = [l for l in src.splitlines() if re.match(r"^(import|from) ", l)]
        assert not [l for l in top_level if "psycopg2" in l or "pymysql" in l]


# ---------------------------------------------------------------------------
# Dependencies and workflow wiring
# ---------------------------------------------------------------------------

class TestWiring:
    def test_drivers_are_dev_only(self):
        runtime = (REPO / "requirements.txt").read_text().lower()
        dev = (REPO / "requirements-dev.txt").read_text().lower()
        assert "psycopg2" not in runtime and "pymysql" not in runtime
        assert "psycopg2" in dev and "pymysql" in dev

    def test_sqlglot_is_a_runtime_requirement_the_ci_installs(self):
        assert "sqlglot" in (REPO / "requirements.txt").read_text()

    def test_workflow_runs_the_drift_gate_and_the_execution_job(self):
        wf = (REPO / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        assert "name: Check SQL exports" in wf
        assert "python3 tools/export_sql.py --check" in wf
        assert "check-sql-execution:" in wf
        assert "python3 tools/check_sql_dialects.py" in wf
        assert "postgres:15" in wf and "mysql:8.0" in wf
        assert "requirements-dev.txt" in wf
