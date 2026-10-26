#!/usr/bin/env python3
"""
test_export_csv.py — tests for tools/export_csv.py (ADR 0012 sections 3, 5, 6, 7).

The exporter writes five tables in four dialects, 20 files. These tests read
the committed files back with Python's csv module and check that:

  * every dialect parses to the same rows, and those rows equal the rows of
    the committed SQLite export (cross-format consistency);
  * the header row is the section 5 column list;
  * nulls are empty fields, booleans are true or false, quoting is minimal;
  * only the Excel dialect starts with a BOM;
  * the formula guard, determinism and --check behave.

Alteration and failure cases run on copies under tmp_path; nothing here
modifies the repo.

Run:
    python3 -m pytest tests/test_export_csv.py -v
"""

import copy
import csv
import functools
import hashlib
import io
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

import export_csv  # noqa: E402
import export_sql  # noqa: E402

TABLES = list(export_csv.TABLE_NAMES)
DIALECTS = list(export_csv.DIALECTS)
ALL = [(t, d) for t in TABLES for d in DIALECTS]
ids = [f"{t}-{d.key}" for t, d in ALL]
BOM = b"\xef\xbb\xbf"
# What ADR 0012 section 3 says, written out here so these tests do not trust the exporter's own table.
SPEC = {"rfc": (",", False), "excel": (",", True), "european": (";", False), "tsv": ("\t", False)}


def _delim(d):
    return SPEC[d.key][0]


def _bom(d):
    return SPEC[d.key][1]


def _path(table, dialect):
    return REPO / export_csv.filename(table, dialect)


@functools.lru_cache(maxsize=None)
def _parse(table, dialect_key):
    dialect = next(d for d in DIALECTS if d.key == dialect_key)
    delimiter, bom = SPEC[dialect_key]
    text = _path(table, dialect).read_bytes().decode("utf-8-sig" if bom else "utf-8")
    return list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))


@pytest.fixture(scope="module")
def registry():
    return json.loads((REPO / "calendar.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sql_tables(registry):
    return export_sql.build_tables(registry)


@pytest.fixture(scope="module")
def live_counts(sql_tables):
    return {t: len(rows) for t, rows in sql_tables.items()}


@pytest.fixture(scope="module")
def sqlite_db():
    db = sqlite3.connect(":memory:")
    db.executescript((REPO / "exchange_calendar.sqlite.sql").read_bytes().decode("utf-8"))
    yield db
    db.close()


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


def _adr_columns():
    adr = (REPO / "docs/decisions/0012-export-shapes.md").read_text(encoding="utf-8")
    block = adr.split("### 5. Column order")[1].split("### 6.")[0]
    out = {}
    for chunk in re.split(r"\n- (?=`)", block):
        m = re.match(r"`?(\w+)`: (.*)", chunk.strip().lstrip("- "), re.S)
        if m and m.group(1) in TABLES:
            out[m.group(1)] = re.findall(r"`(\w+)`", m.group(2).split("\n\n")[0])
    return out


# ---------------------------------------------------------------------------
# Files and dialects
# ---------------------------------------------------------------------------

class TestFilesAndDialects:
    def test_twenty_files_exist_and_nothing_else_matches(self):
        on_disk = sorted(
            p.name for p in REPO.glob("exchange_calendar.*") if p.suffix in (".csv", ".tsv")
        )
        assert on_disk == sorted(export_csv.expected_filenames())
        assert len(on_disk) == 20

    def test_names_for_the_holidays_table(self):
        names = {export_csv.filename("holidays", d) for d in DIALECTS}
        assert names == {
            "exchange_calendar.holidays.csv",
            "exchange_calendar.holidays.excel.csv",
            "exchange_calendar.holidays.european.csv",
            "exchange_calendar.holidays.tsv",
        }

    def test_dialect_table_matches_the_adr_and_the_sibling(self):
        assert [(d.key, d.delimiter, d.bom, d.suffix) for d in DIALECTS] == [
            ("rfc", ",", False, ".csv"),
            ("excel", ",", True, ".excel.csv"),
            ("european", ";", False, ".european.csv"),
            ("tsv", "\t", False, ".tsv"),
        ]

    def test_gitattributes_covers_sql_csv_and_tsv(self):
        rules = {}
        for line in (REPO / ".gitattributes").read_text().splitlines():
            pattern, *attrs = line.split()
            rules[pattern] = attrs
        # Match by attribute, not by whole line, so a rule may carry more
        # (the TSV rule adds whitespace=-blank-at-eol).
        for pattern in ("*.sql", "*.csv", "*.tsv"):
            assert "text" in rules[pattern]
            assert "eol=lf" in rules[pattern]
        assert "whitespace=-blank-at-eol" in rules["*.tsv"]

    def test_boolean_columns_are_exactly_the_zero_one_columns_of_the_sql_tables(self):
        zero_one = {
            (t.name, c.name)
            for t in export_sql.TABLES for c in t.cols
            if c.check is not None and c.check.sql("x") == "x IN (0, 1)"
        }
        assert set(export_csv.BOOLEAN_COLUMNS) == zero_one


# ---------------------------------------------------------------------------
# Round trip, headers, parity
# ---------------------------------------------------------------------------

class TestRoundTrip:
    @pytest.mark.parametrize("table,dialect", ALL, ids=ids)
    def test_row_count_equals_the_live_calendar(self, table, dialect, live_counts):
        assert len(_parse(table, dialect.key)) == live_counts[table] + 1

    @pytest.mark.parametrize("table,dialect", ALL, ids=ids)
    def test_header_is_the_section_5_column_list(self, table, dialect):
        assert _parse(table, dialect.key)[0] == _adr_columns()[table]
        assert _adr_columns()[table] == next(t for t in export_sql.TABLES if t.name == table).col_names

    @pytest.mark.parametrize("table", TABLES)
    def test_all_four_dialects_parse_to_the_same_rows(self, table):
        reference = _parse(table, "rfc")
        for d in DIALECTS[1:]:
            assert _parse(table, d.key) == reference, d.key

    @pytest.mark.parametrize("table", TABLES)
    def test_rows_equal_the_sqlite_export(self, table, sqlite_db):
        cols = next(t for t in export_sql.TABLES if t.name == table).col_names
        want = []
        for row in sqlite_db.execute(f"SELECT {', '.join(cols)} FROM {table} ORDER BY rowid"):
            want.append([export_csv.render_cell(table, c, v) for c, v in zip(cols, row)])
        assert _parse(table, "rfc")[1:] == want

    def test_ad_hoc_closures_files_are_a_header_and_nothing_else(self):
        header = _adr_columns()["ad_hoc_closures"]
        for d in DIALECTS:
            data = _path("ad_hoc_closures", d).read_bytes()
            body = data[3:] if _bom(d) else data
            assert body == (_delim(d).join(header) + "\n").encode("utf-8")

    def test_non_ascii_names_survive_every_dialect(self):
        for d in DIALECTS:
            assert "Deutsche Börse".encode("utf-8") in _path("exchanges", d).read_bytes()
            assert "Battle of Boyacá".encode("utf-8") in _path("holidays", d).read_bytes()


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

class TestFormatting:
    @pytest.mark.parametrize("table", TABLES)
    def test_nulls_are_empty_fields_and_never_a_word(self, table, sql_tables):
        nulls = sum(1 for row in sql_tables[table] for v in row if v is None)
        cells = [c for row in _parse(table, "rfc")[1:] for c in row]
        assert sum(1 for c in cells if c == "") == nulls
        assert not {c for c in cells if c.lower() in ("none", "null", "nan")}

    def test_booleans_are_true_or_false(self):
        header = _parse("holidays", "rfc")[0]
        rows = _parse("holidays", "rfc")[1:]
        for column in ("predicted", "weekend_exception"):
            values = Counter(r[header.index(column)] for r in rows)
            assert set(values) <= {"true", "false", ""}, values
        predicted = Counter(r[header.index("predicted")] for r in rows)
        assert predicted["true"] == 226 and predicted["false"] == 73

    def test_dates_times_and_integers_are_plain_text(self):
        checks = {
            "date": r"\d{4}-\d{2}-\d{2}", "generation_start": r"\d{4}-\d{2}-\d{2}",
            "generation_end": r"\d{4}-\d{2}-\d{2}", "last_verified": r"\d{4}-\d{2}-\d{2}",
            "open": r"\d{2}:\d{2}", "close": r"\d{2}:\d{2}", "at": r"\d{2}:\d{2}",
            "regular_open": r"\d{2}:\d{2}", "regular_close": r"\d{2}:\d{2}",
            "early_close_time": r"\d{2}:\d{2}", "delayed_open_time": r"\d{2}:\d{2}",
            "seq": r"\d+", "year": r"\d{4}", "weekend_day_1": r"\d", "weekend_day_2": r"\d",
        }
        seen = set()
        for table in TABLES:
            rows = _parse(table, "rfc")
            for column, pattern in checks.items():
                if column in rows[0]:
                    i = rows[0].index(column)
                    seen.add(column)
                    for r in rows[1:]:
                        assert r[i] == "" or re.fullmatch(pattern, r[i]), (table, column, r[i])
        assert seen == set(checks)

    @pytest.mark.parametrize("table,dialect", ALL, ids=ids)
    def test_lf_endings_and_one_trailing_newline(self, table, dialect, live_counts):
        data = _path(table, dialect).read_bytes()
        assert b"\r" not in data
        assert data.endswith(b"\n") and not data.endswith(b"\n\n")
        assert data.count(b"\n") == live_counts[table] + 1

    @pytest.mark.parametrize("table,dialect", ALL, ids=ids)
    def test_quoting_is_minimal(self, table, dialect):
        """Data holds no double quote or newline, so every quote pair wraps a delimiter."""
        rows = _parse(table, dialect.key)
        cells = [c for r in rows for c in r]
        assert not [c for c in cells if '"' in c or "\n" in c or "\r" in c]
        data = _path(table, dialect).read_bytes()
        needing = sum(1 for c in cells if _delim(dialect) in c)
        assert data.count(b'"') == 2 * needing

    def test_a_comma_name_is_quoted_only_where_the_delimiter_is_a_comma(self):
        name = next(r[2] for r in _parse("holidays", "rfc")[1:] if "," in r[2])
        quoted, bare = f'"{name}"'.encode(), name.encode()
        for d in DIALECTS:
            data = _path("holidays", d).read_bytes()
            if _delim(d) == ",":
                assert quoted in data
            else:
                assert bare in data and quoted not in data

    def test_only_the_excel_dialect_has_a_bom_and_only_one(self):
        for table, d in ALL:
            data = _path(table, d).read_bytes()
            assert data.startswith(BOM) == _bom(d), (table, d.key)
            assert data.count(BOM) == (1 if _bom(d) else 0), (table, d.key)

    def test_delimiters(self):
        for table in TABLES:
            for d in DIALECTS:
                first = _path(table, d).read_bytes().decode("utf-8-sig" if _bom(d) else "utf-8").split("\n")[0]
                assert first.split(_delim(d)) == _adr_columns()[table]
        assert ";" in _path("exchanges", DIALECTS[2]).read_text(encoding="utf-8").split("\n")[0]
        assert "\t" in _path("exchanges", DIALECTS[3]).read_text(encoding="utf-8").split("\n")[0]
        assert "," not in _path("exchanges", DIALECTS[2]).read_text(encoding="utf-8").split("\n")[0]


# ---------------------------------------------------------------------------
# Determinism and the committed files
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_two_runs_have_identical_sha256_for_all_20_files(self):
        a = export_csv.generate_all(REPO / "calendar.json")
        b = export_csv.generate_all(REPO / "calendar.json")
        assert len(a) == 20
        assert {n: hashlib.sha256(v).hexdigest() for n, v in a.items()} == \
               {n: hashlib.sha256(v).hexdigest() for n, v in b.items()}

    @pytest.mark.parametrize("table,dialect", ALL, ids=ids)
    def test_committed_file_equals_fresh_output(self, table, dialect):
        fresh = export_csv.generate_all(REPO / "calendar.json")[export_csv.filename(table, dialect)]
        assert _path(table, dialect).read_bytes() == fresh

    def test_exporter_is_checksummed_and_outputs_are_not(self):
        files = json.loads((REPO / "checksums.json").read_text())["files"]
        assert "tools/export_csv.py" in files
        assert not [f for f in files if f.endswith((".csv", ".tsv"))]

    def test_output_does_not_depend_on_the_registry_version(self, tmp_path, registry):
        """CSV carries no version, so a version bump must not change a byte."""
        bumped = _mutated(registry, lambda d: d["meta"].__setitem__("version", "9.9.9"))
        out = export_csv.generate_all(_write_registry(tmp_path, bumped))
        assert out == export_csv.generate_all(REPO / "calendar.json")


# ---------------------------------------------------------------------------
# Formula guard and inherited guards (all on copies)
# ---------------------------------------------------------------------------

def _set_exchange_name(value):
    return lambda d: _exchange(d, "XNYS").__setitem__("name", value)


def _set_holiday_name(value):
    return lambda d: _exchange(d, "XNYS")["holidays"]["explicit"][0].__setitem__("name", value)


def _set_source_url(value):
    return lambda d: _exchange(d, "XNYS")["holidays"]["explicit"][0].__setitem__("source_url", value)


def _set_note(value):
    def fn(d):
        ex = _exchange(d, "XNYS")
        year = sorted(ex["confidence"])[0]
        ex["confidence"][year]["note"] = value
    return fn


def _add_ad_hoc(value):
    return lambda d: _exchange(d, "XNYS")["ad_hoc_closures"].append(
        {"date": "2099-06-01", "name": value, "status": "closed", "source_url": "https://e.org/x"}
    )


class TestFormulaGuard:
    @pytest.fixture
    def run(self, tmp_path, monkeypatch, registry, capsys):
        monkeypatch.setattr(export_csv, "PROJECT_ROOT", tmp_path)

        def _run(mutate):
            code = export_csv.main(["-r", str(_write_registry(tmp_path, _mutated(registry, mutate)))])
            assert not [p for p in tmp_path.iterdir() if p.suffix in (".csv", ".tsv", ".tmp")], \
                "a guard failure must not leave files behind"
            return code, capsys.readouterr().err

        return _run

    @pytest.mark.parametrize("lead", ["=", "+", "-", "@"])
    @pytest.mark.parametrize("where", [_set_exchange_name, _set_holiday_name, _set_source_url,
                                       _set_note, _add_ad_hoc],
                             ids=["exchange-name", "holiday-name", "source-url", "confidence-note", "ad-hoc-name"])
    def test_a_leading_formula_character_exits_2(self, run, lead, where):
        code, err = run(where(lead + "SUM(A1:A9)"))
        assert code == 2 and "spreadsheet" in err

    def test_the_character_must_lead_the_field(self, tmp_path, registry):
        for value in ("A=B", "Day+1", "Re-open", "mail@x"):
            data = _mutated(registry, _set_holiday_name(value))
            export_csv.generate_all(_write_registry(tmp_path, data))

    def test_every_dialect_is_guarded_because_the_check_runs_before_rendering(self, tmp_path, registry):
        data = _mutated(registry, _set_holiday_name("=1+1"))
        with pytest.raises(export_csv.ExportError):
            export_csv.generate_all(_write_registry(tmp_path, data))

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda d: d["exchanges"].append(copy.deepcopy(_exchange(d, "XNYS"))),
            lambda d: _exchange(d, "XNYS")["holidays"]["explicit"][0].__setitem__("status", "bogus"),
            lambda d: _exchange(d, "XNYS").__setitem__("mic", "X\u00d1YS"),
            lambda d: _exchange(d, "XNYS").__setitem__("name", ""),
            lambda d: _exchange(d, "XNYS").pop("timezone"),
        ],
    )
    def test_the_sql_exporters_guards_apply_here_too(self, run, mutate):
        assert run(mutate)[0] == 2

    def test_non_ascii_names_are_not_a_problem(self, tmp_path, registry):
        data = _mutated(registry, _set_exchange_name("Bourse \u00c9t\u00e9"))
        out = export_csv.generate_all(_write_registry(tmp_path, data))
        assert "Bourse \u00c9t\u00e9".encode("utf-8") in out["exchange_calendar.exchanges.excel.csv"]


# ---------------------------------------------------------------------------
# CLI and --check (on copies, PROJECT_ROOT redirected)
# ---------------------------------------------------------------------------

@pytest.fixture
def sandbox(tmp_path, monkeypatch, registry):
    reg = _write_registry(tmp_path, registry)
    for name, data in export_csv.generate_all(reg).items():
        (tmp_path / name).write_bytes(data)
    monkeypatch.setattr(export_csv, "PROJECT_ROOT", tmp_path)
    return tmp_path, reg


class TestCheckMode:
    def test_committed_files_pass_check(self):
        proc = subprocess.run([sys.executable, str(REPO / "tools/export_csv.py"), "--check"],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        assert "20 CSV/TSV file(s) match" in proc.stdout

    def test_fresh_copy_passes(self, sandbox):
        _, reg = sandbox
        assert export_csv.main(["-r", str(reg), "--check"]) == 0

    def test_altered_file_fails_with_1_and_is_named(self, sandbox, capsys):
        tmp, reg = sandbox
        target = tmp / "exchange_calendar.holidays.european.csv"
        target.write_bytes(target.read_bytes() + b"tampered\n")
        assert export_csv.main(["-r", str(reg), "--check"]) == 1
        assert "MISMATCH exchange_calendar.holidays.european.csv" in capsys.readouterr().err

    @pytest.mark.parametrize("edit", [
        lambda b: b[3:],                       # the Excel BOM removed
        lambda b: b.replace(b"\n", b"\r\n"),   # a CRLF rewrite
        lambda b: b + b"\n",                   # an extra trailing newline
        lambda b: b[:-2] + b"X\n",             # one changed byte
    ], ids=["bom-removed", "crlf", "extra-newline", "one-byte"])
    def test_subtle_changes_are_detected(self, sandbox, edit):
        tmp, reg = sandbox
        target = tmp / "exchange_calendar.sessions.excel.csv"
        target.write_bytes(edit(target.read_bytes()))
        assert export_csv.main(["-r", str(reg), "--check"]) == 1

    def test_missing_file_fails_with_3_even_if_another_mismatches(self, sandbox):
        tmp, reg = sandbox
        (tmp / "exchange_calendar.confidence.tsv").unlink()
        (tmp / "exchange_calendar.exchanges.csv").write_bytes(b"stale\n")
        assert export_csv.main(["-r", str(reg), "--check"]) == 3

    def test_table_limits_what_check_compares(self, sandbox):
        tmp, reg = sandbox
        for p in tmp.glob("exchange_calendar.exchanges.*"):
            p.unlink()
        assert export_csv.main(["-r", str(reg), "--check", "-t", "holidays"]) == 0
        assert export_csv.main(["-r", str(reg), "--check", "-t", "exchanges"]) == 3
        (tmp / "exchange_calendar.holidays.tsv").write_bytes(b"x\n")
        assert export_csv.main(["-r", str(reg), "--check", "-t", "holidays"]) == 1

    def test_check_does_not_write_into_the_project_root(self, sandbox):
        tmp, reg = sandbox
        before = sorted(p.name for p in tmp.iterdir())
        export_csv.main(["-r", str(reg), "--check"])
        assert sorted(p.name for p in tmp.iterdir()) == before

    def test_write_mode_creates_all_20_files_and_no_temp_files(self, tmp_path, monkeypatch, registry, capsys):
        reg = _write_registry(tmp_path, registry)
        monkeypatch.setattr(export_csv, "PROJECT_ROOT", tmp_path)
        assert export_csv.main(["-r", str(reg)]) == 0
        written = sorted(p.name for p in tmp_path.iterdir() if p.suffix in (".csv", ".tsv"))
        assert written == sorted(export_csv.expected_filenames())
        assert not list(tmp_path.glob("*.tmp"))
        assert capsys.readouterr().err.count("Wrote exchange_calendar.") == 20

    def test_write_mode_with_a_table_writes_only_its_four_files(self, tmp_path, monkeypatch, registry):
        reg = _write_registry(tmp_path, registry)
        monkeypatch.setattr(export_csv, "PROJECT_ROOT", tmp_path)
        assert export_csv.main(["-r", str(reg), "-t", "sessions"]) == 0
        assert sorted(p.name for p in tmp_path.iterdir() if p.suffix in (".csv", ".tsv")) == \
               sorted(export_csv.expected_filenames(["sessions"]))


class TestCli:
    def test_stdout_writes_the_rfc_dialect_of_one_table(self, capsysbinary):
        assert export_csv.main(["-t", "sessions", "--stdout"]) == 0
        out = capsysbinary.readouterr().out
        assert out == (REPO / "exchange_calendar.sessions.csv").read_bytes()
        assert not out.startswith(BOM)

    def test_short_table_flag(self, capsysbinary):
        assert export_csv.main(["-t", "confidence", "--stdout"]) == 0
        assert capsysbinary.readouterr().out.startswith(b"exchange_code,year,level,source")

    def test_stdout_requires_one_table(self):
        assert export_csv.main(["--stdout"]) == 2

    def test_check_and_stdout_are_exclusive(self):
        assert export_csv.main(["-t", "holidays", "--stdout", "--check"]) == 2

    def test_missing_registry_is_fatal(self, tmp_path):
        assert export_csv.main(["-r", str(tmp_path / "nope.json")]) == 2

    def test_invalid_json_is_fatal(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        assert export_csv.main(["-r", str(bad)]) == 2

    def test_missing_meta_version_is_fatal(self, tmp_path, registry):
        data = _mutated(registry, lambda d: d["meta"].pop("version"))
        assert export_csv.main(["-r", str(_write_registry(tmp_path, data))]) == 2

    def test_unknown_table_is_rejected_by_argparse(self):
        with pytest.raises(SystemExit) as err:
            export_csv.main(["-t", "currencies"])
        assert err.value.code == 2

    def test_command_line_runs_from_the_script(self):
        proc = subprocess.run([sys.executable, str(REPO / "tools/export_csv.py"), "-t", "exchanges", "--stdout"],
                              capture_output=True)
        assert proc.returncode == 0
        assert proc.stdout == (REPO / "exchange_calendar.exchanges.csv").read_bytes()
