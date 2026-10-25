#!/usr/bin/env python3
"""
test_export_parquet.py — tests for tools/export_parquet.py (ADR 0012 sections 1, 4, 5, 6, 7).

The exporter writes five tables, one Parquet file each. These tests read the
committed files back with pyarrow and check that:

  * the files exist, one per table, and nothing else at the root is Parquet;
  * the schema (names, order, types, nullability) is the one section 4 sets,
    written out below rather than taken from the exporter;
  * row counts match calendar.json, and every value equals the value in the
    committed CSV export (cross-format consistency);
  * absent values are real nulls, never empty strings;
  * the footer carries exchange_calendar.version and exchange_calendar.table;
  * --check is a logical comparison: it catches a changed value, type,
    nullability, row or metadata key, and it accepts a file rewritten with a
    different compression or row-group size.

pyarrow is a requirement of this suite: a missing pyarrow fails it, it does not
skip it. Alteration and failure cases run on copies under tmp_path; nothing
here modifies the repo.

Run:
    python3 -m pytest tests/test_export_parquet.py -v
"""

import copy
import csv
import datetime
import io
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import export_parquet  # noqa: E402
import export_sql  # noqa: E402

TABLES = list(export_parquet.TABLE_NAMES)

# What ADR 0012 section 4 says, written out here so these tests do not trust the
# exporter's own table. (name, Arrow type as text, nullable). A column that is
# NOT NULL in the SQL export (2a) is required here; the rest are nullable.
SPEC = {
    "exchanges": [
        ("code", "string", False), ("name", "string", False), ("mic", "string", False),
        ("country_code", "string", False), ("timezone", "string", False),
        ("weekend_day_1", "int16", False), ("weekend_day_2", "int16", False),
        ("regular_open", "string", False), ("regular_close", "string", False),
        ("generation_start", "date32[day]", False), ("generation_end", "date32[day]", False),
    ],
    "sessions": [
        ("exchange_code", "string", False), ("type", "string", False), ("seq", "int16", False),
        ("open", "string", True), ("close", "string", True), ("at", "string", True),
    ],
    "holidays": [
        ("exchange_code", "string", False), ("date", "date32[day]", False),
        ("name", "string", False), ("status", "string", False), ("origin", "string", False),
        ("seq", "int16", False), ("early_close_time", "string", True),
        ("delayed_open_time", "string", True), ("predicted", "bool", True),
        ("weekend_exception", "bool", True), ("source_url", "string", True),
    ],
    "ad_hoc_closures": [
        ("exchange_code", "string", False), ("date", "date32[day]", False),
        ("seq", "int16", False), ("name", "string", False), ("status", "string", False),
        ("early_close_time", "string", True), ("source_url", "string", False),
    ],
    "confidence": [
        ("exchange_code", "string", False), ("year", "int16", False), ("level", "string", False),
        ("source", "string", False), ("last_verified", "date32[day]", True),
        ("note", "string", True),
    ],
}
TIME_COLUMNS = {
    "exchanges": ["regular_open", "regular_close"],
    "sessions": ["open", "close", "at"],
    "holidays": ["early_close_time", "delayed_open_time"],
    "ad_hoc_closures": ["early_close_time"],
    "confidence": [],
}
BOOLEANS = {("holidays", "predicted"), ("holidays", "weekend_exception")}


def _path(table):
    return REPO / export_parquet.filename(table)


def _read(table):
    return pq.read_table(_path(table))


def _csv_rows(table):
    text = (REPO / f"exchange_calendar.{table}.csv").read_bytes().decode("utf-8")
    return list(csv.reader(io.StringIO(text, newline="")))


def _cell(table, column, value):
    """A Parquet value as the committed CSV spells it (ADR sections 6 and 7)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)


@pytest.fixture(scope="module")
def registry():
    return json.loads((REPO / "calendar.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sql_tables(registry):
    return export_sql.build_tables(registry)


@pytest.fixture(scope="module")
def expected(registry):
    return export_parquet.build_tables(registry)


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
# Files and schema
# ---------------------------------------------------------------------------

class TestFilesAndSchema:
    def test_five_files_named_per_table(self):
        assert export_parquet.expected_filenames() == [
            "exchange_calendar.exchanges.parquet",
            "exchange_calendar.sessions.parquet",
            "exchange_calendar.holidays.parquet",
            "exchange_calendar.ad_hoc_closures.parquet",
            "exchange_calendar.confidence.parquet",
        ]
        for name in export_parquet.expected_filenames():
            assert (REPO / name).is_file()

    def test_no_other_parquet_files_at_the_root(self):
        assert sorted(p.name for p in REPO.glob("*.parquet")) == sorted(export_parquet.expected_filenames())

    @pytest.mark.parametrize("table", TABLES)
    def test_file_is_parquet(self, table):
        data = _path(table).read_bytes()
        assert data[:4] == b"PAR1" and data[-4:] == b"PAR1"

    @pytest.mark.parametrize("table", TABLES)
    def test_schema_matches_adr_section_4(self, table):
        schema = _read(table).schema
        got = [(f.name, str(f.type), f.nullable) for f in schema]
        assert got == SPEC[table]

    @pytest.mark.parametrize("table", TABLES)
    def test_column_order_is_adr_section_5(self, table):
        assert _read(table).schema.names == _adr_columns()[table]

    def test_the_spec_table_covers_every_adr_column(self):
        adr = _adr_columns()
        assert sorted(adr) == sorted(TABLES)
        for table in TABLES:
            assert [name for name, _, _ in SPEC[table]] == adr[table]

    def test_no_nested_or_dictionary_types(self):
        for table in TABLES:
            for field in _read(table).schema:
                assert not (pa.types.is_nested(field.type) or pa.types.is_dictionary(field.type)), \
                    f"{table}.{field.name}: {field.type}"

    def test_exchange_code_is_a_plain_string(self):
        for table in TABLES[1:]:
            assert _read(table).schema.field("exchange_code").type == pa.string()


# ---------------------------------------------------------------------------
# Round trip and cross-format consistency
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_row_counts_match_calendar_json(self, registry):
        exchanges = registry["exchanges"]
        want = {
            "exchanges": len(exchanges),
            "sessions": sum(len(e["sessions"]) for e in exchanges),
            "holidays": sum(len(e["holidays"]["explicit"]) + len(e["holidays"].get("generated", []))
                            for e in exchanges),
            "ad_hoc_closures": sum(len(e["ad_hoc_closures"]) for e in exchanges),
            "confidence": sum(len(e["confidence"]) for e in exchanges),
        }
        assert {t: _read(t).num_rows for t in TABLES} == want

    def test_row_counts_match_the_sql_export(self, sql_tables):
        for table in TABLES:
            assert _read(table).num_rows == len(sql_tables[table])

    @pytest.mark.parametrize("table", TABLES)
    def test_every_value_equals_the_committed_csv(self, table):
        parquet = _read(table)
        names = parquet.schema.names
        rows = [
            [_cell(table, n, v) for n, v in zip(names, row)]
            for row in zip(*(parquet.column(n).to_pylist() for n in names))
        ]
        csv_rows = _csv_rows(table)
        assert csv_rows[0] == names
        assert rows == csv_rows[1:]

    def test_committed_files_equal_a_fresh_build(self, expected):
        for table in TABLES:
            assert _read(table).equals(expected[table], check_metadata=True), table

    def test_ad_hoc_closures_ships_with_zero_rows_and_its_schema(self):
        parquet = _read("ad_hoc_closures")
        assert parquet.num_rows == 0
        assert parquet.schema.names == _adr_columns()["ad_hoc_closures"]

    def test_a_non_empty_ad_hoc_closures_table_round_trips(self, tmp_path, registry):
        data = _mutated(registry, lambda d: _exchange(d, "XNYS")["ad_hoc_closures"].append(
            {"date": "2099-06-01", "name": "Test closure", "status": "closed",
             "source_url": "https://e.org/x"}))
        reg = _write_registry(tmp_path, data)
        tables, files = export_parquet.generate(reg)
        back = pq.read_table(io.BytesIO(files["exchange_calendar.ad_hoc_closures.parquet"]))
        assert back.to_pylist() == [{
            "exchange_code": "XNYS", "date": datetime.date(2099, 6, 1), "seq": 1,
            "name": "Test closure", "status": "closed", "early_close_time": None,
            "source_url": "https://e.org/x",
        }]


# ---------------------------------------------------------------------------
# Types, nulls and booleans (ADR sections 6 and 7)
# ---------------------------------------------------------------------------

class TestTypesAndNulls:
    @pytest.mark.parametrize("table", TABLES)
    def test_times_are_hhmm_text(self, table):
        parquet = _read(table)
        for column in TIME_COLUMNS[table]:
            assert parquet.schema.field(column).type == pa.string()
            for value in parquet.column(column).to_pylist():
                assert value is None or re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", value), value

    def test_dates_are_python_dates(self):
        for value in _read("holidays").column("date").to_pylist():
            assert type(value) is datetime.date
        for value in _read("exchanges").column("generation_start").to_pylist():
            assert type(value) is datetime.date

    def test_booleans_are_bool_or_null(self):
        parquet = _read("holidays")
        for column in ("predicted", "weekend_exception"):
            assert parquet.schema.field(column).type == pa.bool_()
            assert {type(v) for v in parquet.column(column).to_pylist()} <= {bool, type(None)}

    def test_boolean_counts_match_calendar_json(self, registry):
        explicit = [h for e in registry["exchanges"] for h in e["holidays"]["explicit"]]
        parquet = _read("holidays")
        for column in ("predicted", "weekend_exception"):
            values = parquet.column(column).to_pylist()
            assert values.count(True) == sum(1 for h in explicit if h.get(column) is True)
            assert values.count(False) == sum(1 for h in explicit if h.get(column) is False)
            assert values.count(None) == len(values) - values.count(True) - values.count(False)

    def test_false_is_not_rewritten_to_null(self):
        assert _read("holidays").column("predicted").to_pylist().count(False) > 0

    @pytest.mark.parametrize("table", TABLES)
    def test_no_empty_strings_anywhere(self, table):
        parquet = _read(table)
        for field in parquet.schema:
            if field.type == pa.string():
                assert "" not in parquet.column(field.name).to_pylist(), f"{table}.{field.name}"

    def test_absent_fields_load_as_none_not_empty_string(self, registry):
        holidays = _read("holidays")
        generated = sum(len(e["holidays"].get("generated", [])) for e in registry["exchanges"])
        urls = holidays.column("source_url").to_pylist()
        assert urls.count(None) == generated and generated == 66
        assert "" not in urls
        early = holidays.column("early_close_time").to_pylist()
        assert None in early and "" not in early

    @pytest.mark.parametrize("table", TABLES)
    def test_required_columns_have_no_nulls(self, table):
        parquet = _read(table)
        for field in parquet.schema:
            if not field.nullable:
                assert parquet.column(field.name).null_count == 0, f"{table}.{field.name}"

    def test_integers_are_python_ints(self):
        for value in _read("confidence").column("year").to_pylist():
            assert type(value) is int
        for value in _read("exchanges").column("weekend_day_1").to_pylist():
            assert type(value) is int and 0 <= value <= 6

    def test_convert_rejects_an_empty_string_and_a_bad_boolean(self):
        col = export_sql.EXCHANGES.cols[1]  # name
        with pytest.raises(export_parquet.ExportError):
            export_parquet.convert("exchanges", col, "")
        flag = next(c for c in export_sql.HOLIDAYS.cols if c.name == "predicted")
        for bad in (2, True, "true"):
            with pytest.raises(export_parquet.ExportError):
                export_parquet.convert("holidays", flag, bad)


# ---------------------------------------------------------------------------
# Footer metadata and writer options
# ---------------------------------------------------------------------------

class TestFooterAndWriter:
    @pytest.mark.parametrize("table", TABLES)
    def test_footer_carries_version_and_table(self, table, registry):
        footer = pq.ParquetFile(_path(table)).metadata.metadata
        assert footer[b"exchange_calendar.version"] == registry["meta"]["version"].encode()
        assert footer[b"exchange_calendar.table"] == table.encode()

    @pytest.mark.parametrize("table", TABLES)
    def test_only_two_exchange_calendar_keys(self, table):
        read_back = _read(table).schema.metadata
        assert sorted(read_back) == [b"exchange_calendar.table", b"exchange_calendar.version"]

    @pytest.mark.parametrize("table", TABLES)
    def test_snappy_and_one_row_group(self, table):
        meta = pq.ParquetFile(_path(table)).metadata
        assert meta.num_row_groups == 1
        if meta.num_rows:
            group = meta.row_group(0)
            assert {group.column(i).compression for i in range(group.num_columns)} == {"SNAPPY"}


# ---------------------------------------------------------------------------
# Determinism (logical)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_two_runs_produce_identical_tables(self):
        first, _ = export_parquet.generate(REPO / "calendar.json")
        second, _ = export_parquet.generate(REPO / "calendar.json")
        for table in TABLES:
            assert first[table].equals(second[table], check_metadata=True)

    def test_files_from_two_runs_read_back_equal(self):
        _, a = export_parquet.generate(REPO / "calendar.json")
        _, b = export_parquet.generate(REPO / "calendar.json")
        for name in a:
            assert pq.read_table(io.BytesIO(a[name])).equals(
                pq.read_table(io.BytesIO(b[name])), check_metadata=True)

    def test_rows_are_sorted_by_key(self):
        holidays = _read("holidays")
        keys = list(zip(*(holidays.column(n).to_pylist() for n in ("exchange_code", "date"))))
        assert keys == sorted(keys)
        exchanges = _read("exchanges").column("code").to_pylist()
        assert exchanges == sorted(exchanges)


# ---------------------------------------------------------------------------
# The logical comparison itself
# ---------------------------------------------------------------------------

def _replace(table, name, values):
    i = table.schema.get_field_index(name)
    field = table.schema.field(i)
    return table.set_column(i, field, pa.array(values, type=field.type))


def _flip_boolean(t):
    values = t.column("predicted").to_pylist()
    i = next(n for n, v in enumerate(values) if v is not None)
    values[i] = not values[i]
    return _replace(t, "predicted", values)


def _shift_date(t):
    values = t.column("date").to_pylist()
    values[0] += datetime.timedelta(days=1)
    return _replace(t, "date", values)


def _change_string(t):
    values = t.column("name").to_pylist()
    values[3] += "!"
    return _replace(t, "name", values)


def _null_a_value(t):
    values = t.column("source_url").to_pylist()
    i = next(n for n, v in enumerate(values) if v is not None)
    values[i] = None
    return _replace(t, "source_url", values)


def _change_int(t):
    values = t.column("seq").to_pylist()
    values[0] += 1
    return _replace(t, "seq", values)


def _widen_int(t):
    i = t.schema.get_field_index("seq")
    return t.set_column(i, pa.field("seq", pa.int32(), nullable=False), t.column("seq").cast(pa.int32()))


def _make_nullable(t):
    i = t.schema.get_field_index("exchange_code")
    return t.set_column(i, pa.field("exchange_code", pa.string(), nullable=True), t.column("exchange_code"))


def _to_large_string(t):
    i = t.schema.get_field_index("name")
    return t.set_column(i, pa.field("name", pa.large_string(), nullable=False),
                        t.column("name").cast(pa.large_string()))


def _bump_version(t):
    return t.replace_schema_metadata({**t.schema.metadata, b"exchange_calendar.version": b"9.9.9"})


def _drop_table_key(t):
    meta = dict(t.schema.metadata)
    del meta[b"exchange_calendar.table"]
    return t.replace_schema_metadata(meta)


def _wrong_table_key(t):
    return t.replace_schema_metadata({**t.schema.metadata, b"exchange_calendar.table": b"sessions"})


MUTATIONS = {
    "flipped-boolean": _flip_boolean,
    "shifted-date": _shift_date,
    "changed-string": _change_string,
    "value-nulled": _null_a_value,
    "changed-int": _change_int,
    "int16-widened-to-int32": _widen_int,
    "required-became-nullable": _make_nullable,
    "string-became-large-string": _to_large_string,
    "row-dropped": lambda t: t.slice(1),
    "row-added": lambda t: pa.concat_tables([t, t.slice(0, 1)]),
    "columns-reversed": lambda t: t.select(list(reversed(t.schema.names))),
    "version-changed": _bump_version,
    "table-key-dropped": _drop_table_key,
    "table-key-wrong": _wrong_table_key,
    "metadata-removed": lambda t: t.replace_schema_metadata(None),
}


class TestCompare:
    def test_an_unmodified_table_has_no_problems(self, expected):
        assert export_parquet.compare(expected["holidays"], expected["holidays"]) == []

    def test_the_replace_helper_is_neutral(self, expected):
        t = expected["holidays"]
        same = _replace(t, "name", t.column("name").to_pylist())
        assert same.equals(t, check_metadata=True)  # so a failing mutation test means the mutation worked

    @pytest.mark.parametrize("kind", sorted(MUTATIONS))
    def test_mutation_is_caught(self, expected, kind):
        want = expected["holidays"]  # has every column kind the mutations touch
        mutated = MUTATIONS[kind](want)
        assert not mutated.equals(want, check_metadata=True)
        assert export_parquet.compare(mutated, want), kind

    def test_a_flipped_boolean_is_named_with_its_row(self, expected):
        problems = export_parquet.compare(_flip_boolean(expected["holidays"]), expected["holidays"])
        assert len(problems) == 1 and problems[0].startswith("column predicted row ")

    def test_a_changed_version_is_named(self, expected):
        problems = export_parquet.compare(_bump_version(expected["exchanges"]), expected["exchanges"])
        assert len(problems) == 1
        assert problems[0].startswith("metadata exchange_calendar.version: '9.9.9', expected ")

    def test_byte_level_differences_are_not_differences(self, expected):
        t = expected["holidays"]
        for options in ({"compression": "zstd"}, {"compression": "none"},
                        {"row_group_size": 100}, {"use_dictionary": False}):
            buf = io.BytesIO()
            pq.write_table(t, buf, **options)
            assert export_parquet.compare(pq.read_table(io.BytesIO(buf.getvalue())), t) == [], options


# ---------------------------------------------------------------------------
# CLI and --check (on copies, PROJECT_ROOT redirected)
# ---------------------------------------------------------------------------

@pytest.fixture
def sandbox(tmp_path, monkeypatch, registry):
    reg = _write_registry(tmp_path, registry)
    for name, data in export_parquet.generate_all(reg).items():
        (tmp_path / name).write_bytes(data)
    monkeypatch.setattr(export_parquet, "PROJECT_ROOT", tmp_path)
    return tmp_path, reg


def _rewrite(path, fn, **options):
    table = fn(pq.read_table(path))
    pq.write_table(table, path, **({"compression": "snappy"} | options))


class TestCheckMode:
    def test_committed_files_pass_check(self):
        proc = subprocess.run([sys.executable, str(REPO / "tools/export_parquet.py"), "--check"],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        assert "5 Parquet file(s) match the registry." in proc.stdout

    def test_fresh_copy_passes(self, sandbox):
        _, reg = sandbox
        assert export_parquet.main(["-r", str(reg), "--check"]) == 0

    @pytest.mark.parametrize("table,kind", [
        ("holidays", "flipped-boolean"), ("holidays", "shifted-date"), ("holidays", "changed-string"),
        ("holidays", "value-nulled"), ("sessions", "changed-int"), ("sessions", "int16-widened-to-int32"),
        ("holidays", "required-became-nullable"), ("holidays", "row-dropped"),
        ("holidays", "columns-reversed"), ("holidays", "version-changed"),
        ("holidays", "table-key-dropped"), ("holidays", "metadata-removed"),
    ])
    def test_a_mutated_file_fails_with_1_and_is_named(self, sandbox, capsys, table, kind):
        tmp, reg = sandbox
        _rewrite(tmp / export_parquet.filename(table), MUTATIONS[kind])
        assert export_parquet.main(["-r", str(reg), "--check"]) == 1
        err = capsys.readouterr().err
        assert f"MISMATCH exchange_calendar.{table}.parquet" in err
        assert "Run 'python3 tools/export_parquet.py' to regenerate." in err

    @pytest.mark.parametrize("options", [
        {"compression": "zstd"}, {"compression": "none"}, {"row_group_size": 500},
        {"use_dictionary": False}, {"write_statistics": False},
    ], ids=["zstd", "no-compression", "small-row-groups", "no-dictionary", "no-statistics"])
    def test_a_logically_equal_rewrite_passes(self, sandbox, options):
        tmp, reg = sandbox
        _rewrite(tmp / "exchange_calendar.holidays.parquet", lambda t: t, **options)
        assert export_parquet.main(["-r", str(reg), "--check"]) == 0

    def test_a_version_bump_in_the_registry_makes_every_file_stale(self, sandbox, registry, tmp_path, capsys):
        tmp, _ = sandbox
        data = _mutated(registry, lambda d: d["meta"].__setitem__("version", "9.9.9"))
        reg = _write_registry(tmp, data, name="bumped.json")
        assert export_parquet.main(["-r", str(reg), "--check"]) == 1
        err = capsys.readouterr().err
        assert err.count("MISMATCH exchange_calendar.") == 5
        assert "exchange_calendar.version" in err

    def test_a_changed_registry_value_is_detected(self, sandbox, registry):
        tmp, _ = sandbox
        data = _mutated(registry, lambda d: _exchange(d, "XNYS").__setitem__("name", "New York Stock Exchange X"))
        reg = _write_registry(tmp, data, name="changed.json")
        assert export_parquet.main(["-r", str(reg), "--check"]) == 1

    def test_unreadable_file_fails_with_1(self, sandbox, capsys):
        tmp, reg = sandbox
        (tmp / "exchange_calendar.sessions.parquet").write_bytes(b"not parquet")
        assert export_parquet.main(["-r", str(reg), "--check"]) == 1
        err = capsys.readouterr().err
        assert "MISMATCH exchange_calendar.sessions.parquet" in err and "unreadable" in err

    def test_missing_file_fails_with_3_even_if_another_mismatches(self, sandbox):
        tmp, reg = sandbox
        (tmp / "exchange_calendar.confidence.parquet").unlink()
        _rewrite(tmp / "exchange_calendar.exchanges.parquet", MUTATIONS["changed-string"])
        assert export_parquet.main(["-r", str(reg), "--check"]) == 3

    def test_table_limits_what_check_compares(self, sandbox):
        tmp, reg = sandbox
        (tmp / "exchange_calendar.exchanges.parquet").unlink()
        assert export_parquet.main(["-r", str(reg), "--check", "-t", "holidays"]) == 0
        assert export_parquet.main(["-r", str(reg), "--check", "-t", "exchanges"]) == 3
        (tmp / "exchange_calendar.holidays.parquet").write_bytes(b"x")
        assert export_parquet.main(["-r", str(reg), "--check", "-t", "holidays"]) == 1

    def test_check_does_not_write_into_the_project_root(self, sandbox):
        tmp, reg = sandbox
        before = sorted((p.name, p.read_bytes()) for p in tmp.iterdir())
        export_parquet.main(["-r", str(reg), "--check"])
        assert sorted((p.name, p.read_bytes()) for p in tmp.iterdir()) == before

    def test_write_mode_creates_all_five_files_and_no_temp_files(self, tmp_path, monkeypatch, registry, capsys):
        reg = _write_registry(tmp_path, registry)
        monkeypatch.setattr(export_parquet, "PROJECT_ROOT", tmp_path)
        assert export_parquet.main(["-r", str(reg)]) == 0
        assert sorted(p.name for p in tmp_path.glob("*.parquet")) == sorted(export_parquet.expected_filenames())
        assert not list(tmp_path.glob("*.tmp"))
        assert capsys.readouterr().err.count("Wrote exchange_calendar.") == 5
        assert export_parquet.main(["-r", str(reg), "--check"]) == 0

    def test_write_mode_with_a_table_writes_only_its_file(self, tmp_path, monkeypatch, registry):
        reg = _write_registry(tmp_path, registry)
        monkeypatch.setattr(export_parquet, "PROJECT_ROOT", tmp_path)
        assert export_parquet.main(["-r", str(reg), "-t", "sessions"]) == 0
        assert [p.name for p in tmp_path.glob("*.parquet")] == ["exchange_calendar.sessions.parquet"]


class TestCli:
    def test_stdout_writes_one_table_as_parquet(self, capsysbinary, expected):
        assert export_parquet.main(["-t", "sessions", "--stdout"]) == 0
        out = capsysbinary.readouterr().out
        assert out[:4] == b"PAR1"
        assert pq.read_table(io.BytesIO(out)).equals(_read("sessions"), check_metadata=True)

    def test_short_table_flag(self, capsysbinary):
        assert export_parquet.main(["-t", "confidence", "--stdout"]) == 0
        assert pq.read_table(io.BytesIO(capsysbinary.readouterr().out)).schema.names[:2] == ["exchange_code", "year"]

    def test_stdout_requires_one_table(self):
        assert export_parquet.main(["--stdout"]) == 2

    def test_check_and_stdout_are_exclusive(self):
        assert export_parquet.main(["-t", "holidays", "--stdout", "--check"]) == 2

    def test_missing_registry_is_fatal(self, tmp_path):
        assert export_parquet.main(["-r", str(tmp_path / "nope.json")]) == 2

    def test_invalid_json_is_fatal(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        assert export_parquet.main(["-r", str(bad)]) == 2

    def test_missing_meta_version_is_fatal(self, tmp_path, registry):
        data = _mutated(registry, lambda d: d["meta"].pop("version"))
        assert export_parquet.main(["-r", str(_write_registry(tmp_path, data))]) == 2

    def test_unknown_table_is_rejected_by_argparse(self):
        with pytest.raises(SystemExit) as err:
            export_parquet.main(["-t", "currencies"])
        assert err.value.code == 2

    def test_a_guard_failure_writes_nothing(self, tmp_path, monkeypatch, registry):
        data = _mutated(registry, lambda d: _exchange(d, "XNYS").__setitem__("mic", "XNY\u00c9"))
        reg = _write_registry(tmp_path, data)
        monkeypatch.setattr(export_parquet, "PROJECT_ROOT", tmp_path)
        assert export_parquet.main(["-r", str(reg)]) == 2
        assert not list(tmp_path.glob("*.parquet"))

    def test_without_pyarrow_the_script_exits_2_with_a_message(self):
        blocker = (
            "import sys\n"
            "class Block:\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name == 'pyarrow' or name.startswith('pyarrow.'):\n"
            "            raise ImportError('blocked for the test')\n"
            "sys.meta_path.insert(0, Block())\n"
            "import runpy\n"
            f"sys.argv = ['export_parquet.py', '--check']\n"
            f"runpy.run_path({str(REPO / 'tools/export_parquet.py')!r}, run_name='__main__')\n"
        )
        proc = subprocess.run([sys.executable, "-c", blocker], capture_output=True, text=True)
        assert proc.returncode == 2
        assert "pyarrow is required" in proc.stderr


# ---------------------------------------------------------------------------
# Repository wiring
# ---------------------------------------------------------------------------

class TestWiring:
    def test_gitattributes_marks_parquet_binary(self):
        lines = [l.split() for l in (REPO / ".gitattributes").read_text().splitlines() if l.strip()]
        assert ["*.parquet", "binary"] in lines

    def test_requirements_txt_has_the_pyarrow_floor_and_no_pin(self):
        reqs = (REPO / "requirements.txt").read_text().splitlines()
        assert "pyarrow>=22.0" in reqs
        assert not any(l.startswith("pyarrow==") for l in reqs)

    def test_the_wrapper_does_not_depend_on_pyarrow(self):
        for path in (REPO / "wrappers/python").rglob("*"):
            if path.is_file() and path.suffix in (".py", ".toml", ".cfg", ".txt"):
                assert "pyarrow" not in path.read_text(encoding="utf-8", errors="ignore"), path

    def test_release_script_regenerates_and_ships_the_parquet_files(self):
        text = (REPO / "scripts/release.sh").read_text()
        release_files = text.split("RELEASE_FILES=(")[1].split(")")[0]
        trap = text.split("local files=")[1].split("if git log")[0]
        for name in export_parquet.expected_filenames():
            assert name in release_files, f"{name}: missing from RELEASE_FILES"
            assert name in trap, f"{name}: missing from the cleanup trap"
        sql = text.index("run python3 tools/export_sql.py")
        parquet = text.index("run python3 tools/export_parquet.py")
        assert sql < parquet < text.index("run make package")
