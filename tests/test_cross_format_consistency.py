#!/usr/bin/env python3
"""
test_cross_format_consistency.py — ADR 0012 section 1: "One shape, three formats."

Each of the five tables is committed as SQL, CSV and Parquet. This test loads
the same table from

  1. exchange_calendar.sqlite.sql   (executed into an in-memory SQLite database)
  2. exchange_calendar.<table>.csv  (the RFC 4180 dialect, read with the csv module)
  3. exchange_calendar.<table>.parquet (read with pyarrow.parquet.read_table)

and requires identical row counts, identical columns, and identical values in
identical row order. The three formats store the same value differently, so each
cell is first normalized by its column kind:

    null      SQLite None      CSV ""              Parquet None        -> None
    bool      SQLite 1 / 0     CSV "true"/"false"  Parquet True/False  -> True / False
    int       SQLite 74        CSV "74"            Parquet 74          -> 74
    date      SQLite "2025-01-01"  CSV "2025-01-01"  Parquet date(2025, 1, 1) -> "2025-01-01"
    str       text in all three                                        -> the text

The normalizers are strict. A representation outside the list above (CSV "True",
SQLite 2 for a boolean, a Parquet datetime where a date belongs) is an error,
not something to coerce, and an empty string in SQLite or Parquet is not a null.
The column kinds are written out in this file and checked against the Parquet
schema, the SQLite declared types and the CSV header; they are not read from
the exporters.

The self-tests at the end alter one source at a time and require the comparison
to notice, so a passing run means something.

Run:
    python3 -m pytest tests/test_cross_format_consistency.py -v
"""

import csv
import datetime
import io
import json
import re
import sqlite3
from pathlib import Path

import pytest

import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent

# (column, kind) per table, in ADR 0012 section 5 order. Kinds: str, int, date, bool.
KINDS = {
    "exchanges": [
        ("code", "str"), ("name", "str"), ("mic", "str"), ("country_code", "str"),
        ("timezone", "str"), ("weekend_day_1", "int"), ("weekend_day_2", "int"),
        ("regular_open", "str"), ("regular_close", "str"),
        ("generation_start", "date"), ("generation_end", "date"),
    ],
    "sessions": [
        ("exchange_code", "str"), ("type", "str"), ("seq", "int"),
        ("open", "str"), ("close", "str"), ("at", "str"),
    ],
    "holidays": [
        ("exchange_code", "str"), ("date", "date"), ("name", "str"), ("status", "str"),
        ("origin", "str"), ("seq", "int"), ("early_close_time", "str"),
        ("delayed_open_time", "str"), ("predicted", "bool"), ("weekend_exception", "bool"),
        ("source_url", "str"),
    ],
    "ad_hoc_closures": [
        ("exchange_code", "str"), ("date", "date"), ("seq", "int"), ("name", "str"),
        ("status", "str"), ("early_close_time", "str"), ("source_url", "str"),
    ],
    "confidence": [
        ("exchange_code", "str"), ("year", "int"), ("level", "str"), ("source", "str"),
        ("last_verified", "date"), ("note", "str"),
    ],
}
TABLES = list(KINDS)

ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
CSV_INT = re.compile(r"-?(0|[1-9]\d*)")


class NormalizationError(ValueError):
    """A value is not in the representation its format uses for its kind."""


# ---------------------------------------------------------------------------
# Normalization: every format's cell -> one comparable Python value
# ---------------------------------------------------------------------------

def _iso_text(text):
    """An ISO-8601 calendar date, spelled exactly YYYY-MM-DD, or an error."""
    if not isinstance(text, str) or not ISO_DATE.fullmatch(text):
        raise NormalizationError(f"not YYYY-MM-DD text: {text!r}")
    try:
        if datetime.date.fromisoformat(text).isoformat() != text:
            raise ValueError
    except ValueError:
        raise NormalizationError(f"not a calendar date: {text!r}") from None
    return text


def normalize_sqlite(kind, value):
    if value is None:
        return None
    if kind == "bool":
        if type(value) is int and value in (0, 1):
            return value == 1
        raise NormalizationError(f"SQLite boolean must be integer 0 or 1, got {value!r}")
    if kind == "int":
        if type(value) is int:
            return value
        raise NormalizationError(f"SQLite integer expected, got {value!r}")
    if kind == "date":
        return _iso_text(value)
    if type(value) is str:
        return value  # "" stays "": it is not a null (ADR section 7)
    raise NormalizationError(f"SQLite text expected, got {value!r}")


def normalize_csv(kind, cell):
    if type(cell) is not str:
        raise NormalizationError(f"CSV cell must be text, got {cell!r}")
    if cell == "":
        return None
    if kind == "bool":
        if cell in ("true", "false"):
            return cell == "true"
        raise NormalizationError(f'CSV boolean must be "true" or "false", got {cell!r}')
    if kind == "int":
        if CSV_INT.fullmatch(cell):
            return int(cell)
        raise NormalizationError(f"CSV integer expected, got {cell!r}")
    if kind == "date":
        return _iso_text(cell)
    return cell


def normalize_parquet(kind, value):
    if value is None:
        return None
    if kind == "bool":
        if type(value) is bool:
            return value
        raise NormalizationError(f"Parquet boolean expected, got {value!r}")
    if kind == "int":
        if type(value) is int:
            return value
        raise NormalizationError(f"Parquet integer expected, got {value!r}")
    if kind == "date":
        if type(value) is datetime.date:  # not datetime.datetime
            return value.isoformat()
        raise NormalizationError(f"Parquet date expected, got {value!r}")
    if type(value) is str:
        return value  # "" stays "": it is not a null (ADR section 7)
    raise NormalizationError(f"Parquet string expected, got {value!r}")


NORMALIZERS = {"sqlite": normalize_sqlite, "csv": normalize_csv, "parquet": normalize_parquet}


# ---------------------------------------------------------------------------
# Loading the three sources
# ---------------------------------------------------------------------------

def columns(table):
    return [name for name, _ in KINDS[table]]


def load_sqlite(db, table):
    """(columns, rows) in primary-key order, which is the ADR section 5 row order."""
    info = list(db.execute(f"PRAGMA table_info({table})"))
    names = [row[1] for row in info]
    pk = [row[1] for row in sorted((r for r in info if r[5]), key=lambda r: r[5])]
    order = f" ORDER BY {', '.join(pk)}" if pk else ""
    rows = [tuple(r) for r in db.execute(f"SELECT {', '.join(names)} FROM {table}{order}")]
    return names, rows


def load_csv(table):
    text = (REPO / f"exchange_calendar.{table}.csv").read_bytes().decode("utf-8")
    records = list(csv.reader(io.StringIO(text, newline="")))
    return records[0], [tuple(r) for r in records[1:]]


def load_parquet(table):
    parquet = pq.read_table(REPO / f"exchange_calendar.{table}.parquet")
    names = parquet.schema.names
    rows = list(zip(*(parquet.column(n).to_pylist() for n in names))) if parquet.num_rows else []
    return names, rows


@pytest.fixture(scope="module")
def sqlite_db():
    db = sqlite3.connect(":memory:")
    db.executescript((REPO / "exchange_calendar.sqlite.sql").read_bytes().decode("utf-8"))
    yield db
    db.close()


@pytest.fixture(scope="module")
def loaded(sqlite_db):
    """{table: {"sqlite": (columns, rows), "csv": ..., "parquet": ...}}"""
    return {t: {"sqlite": load_sqlite(sqlite_db, t), "csv": load_csv(t), "parquet": load_parquet(t)}
            for t in TABLES}


# ---------------------------------------------------------------------------
# The comparison: returns problems, so the self-tests can assert it notices
# ---------------------------------------------------------------------------

def compare(table, sources):
    """Why the three sources of one table disagree; an empty list means they agree."""
    problems = []
    names = columns(table)
    for fmt, (cols, _) in sources.items():
        if list(cols) != names:
            problems.append(f"{fmt} columns {list(cols)} != {names}")
    counts = {fmt: len(rows) for fmt, (_, rows) in sources.items()}
    if len(set(counts.values())) != 1:
        problems.append(f"row counts differ: {counts}")
    if problems:
        return problems

    normalized = {}
    for fmt, (_, rows) in sources.items():
        out = []
        for number, row in enumerate(rows, start=1):
            if len(row) != len(names):
                problems.append(f"{fmt} row {number}: {len(row)} cells, expected {len(names)}")
                continue
            try:
                out.append(tuple(NORMALIZERS[fmt](kind, cell)
                                 for (_, kind), cell in zip(KINDS[table], row)))
            except NormalizationError as exc:
                problems.append(f"{fmt} row {number}: {exc}")
        normalized[fmt] = out
    if problems:
        return problems[:5]

    reference = normalized["sqlite"]
    for fmt in ("csv", "parquet"):
        for number, (want, got) in enumerate(zip(reference, normalized[fmt]), start=1):
            for (name, _), a, b in zip(KINDS[table], want, got):
                if a != b or type(a) is not type(b):
                    problems.append(f"{fmt} row {number} {name}: {b!r}, sqlite has {a!r}")
                    break
            if len(problems) >= 5:
                return problems
    return problems


# ---------------------------------------------------------------------------
# The column kinds are right
# ---------------------------------------------------------------------------

PARQUET_KIND = {"string": "str", "int16": "int", "date32[day]": "date", "bool": "bool"}
SQLITE_AFFINITY = {"str": {"TEXT"}, "date": {"TEXT"}, "int": {"INTEGER"}, "bool": {"INTEGER"}}


class TestColumnKinds:
    def test_all_five_tables(self):
        assert TABLES == ["exchanges", "sessions", "holidays", "ad_hoc_closures", "confidence"]

    @pytest.mark.parametrize("table", TABLES)
    def test_kinds_match_the_parquet_schema(self, table):
        schema = pq.read_table(REPO / f"exchange_calendar.{table}.parquet").schema
        assert [(f.name, PARQUET_KIND[str(f.type)]) for f in schema] == KINDS[table]

    @pytest.mark.parametrize("table", TABLES)
    def test_kinds_match_the_sqlite_declared_types(self, table, sqlite_db):
        info = list(sqlite_db.execute(f"PRAGMA table_info({table})"))
        assert [r[1] for r in info] == columns(table)
        for row, (name, kind) in zip(info, KINDS[table]):
            assert row[2] in SQLITE_AFFINITY[kind], f"{table}.{name}: {row[2]} for a {kind}"

    @pytest.mark.parametrize("table", TABLES)
    def test_kinds_match_the_csv_header(self, table):
        assert load_csv(table)[0] == columns(table)


# ---------------------------------------------------------------------------
# The three formats agree
# ---------------------------------------------------------------------------

class TestCrossFormat:
    @pytest.mark.parametrize("table", TABLES)
    def test_row_counts_match(self, table, loaded):
        counts = {fmt: len(rows) for fmt, (_, rows) in loaded[table].items()}
        assert len(set(counts.values())) == 1, counts

    def test_row_counts_match_calendar_json(self, loaded):
        registry = json.loads((REPO / "calendar.json").read_text(encoding="utf-8"))
        ex = registry["exchanges"]
        want = {
            "exchanges": len(ex),
            "sessions": sum(len(e["sessions"]) for e in ex),
            "holidays": sum(len(e["holidays"]["explicit"]) + len(e["holidays"].get("generated", []))
                            for e in ex),
            "ad_hoc_closures": sum(len(e["ad_hoc_closures"]) for e in ex),
            "confidence": sum(len(e["confidence"]) for e in ex),
        }
        for table in TABLES:
            for fmt, (_, rows) in loaded[table].items():
                assert len(rows) == want[table], f"{table} {fmt}"

    def test_the_comparison_is_not_vacuous(self, loaded):
        for table in ("exchanges", "sessions", "holidays", "confidence"):
            assert len(loaded[table]["sqlite"][1]) > 0
        assert len(loaded["holidays"]["sqlite"][1]) > 3000

    @pytest.mark.parametrize("table", TABLES)
    def test_columns_are_identical(self, table, loaded):
        for fmt, (cols, _) in loaded[table].items():
            assert list(cols) == columns(table), fmt

    @pytest.mark.parametrize("table", TABLES)
    def test_every_value_matches_row_for_row(self, table, loaded):
        assert compare(table, loaded[table]) == []

    def test_nulls_exist_and_agree_in_all_three(self, loaded):
        """Each null-bearing column has real nulls, and the formats agree on where."""
        names = columns("holidays")
        for column in ("early_close_time", "predicted", "weekend_exception", "source_url"):
            index = names.index(column)
            kind = dict(KINDS["holidays"])[column]
            positions = {
                fmt: [i for i, row in enumerate(rows) if NORMALIZERS[fmt](kind, row[index]) is None]
                for fmt, (_, rows) in loaded["holidays"].items()
            }
            assert positions["sqlite"], column
            assert positions["sqlite"] == positions["csv"] == positions["parquet"], column

    def test_booleans_agree_including_false(self, loaded):
        index = columns("holidays").index("predicted")
        seen = {
            fmt: {NORMALIZERS[fmt]("bool", row[index]) for row in rows}
            for fmt, (_, rows) in loaded["holidays"].items()
        }
        assert seen["sqlite"] == seen["csv"] == seen["parquet"] == {None, True, False}


# ---------------------------------------------------------------------------
# The normalizers
# ---------------------------------------------------------------------------

class TestNormalizers:
    def test_nulls(self):
        assert normalize_sqlite("str", None) is None
        assert normalize_csv("str", "") is None
        assert normalize_parquet("str", None) is None
        for kind in ("int", "date", "bool"):
            assert normalize_sqlite(kind, None) is None
            assert normalize_csv(kind, "") is None
            assert normalize_parquet(kind, None) is None

    def test_booleans(self):
        assert normalize_sqlite("bool", 1) is True and normalize_sqlite("bool", 0) is False
        assert normalize_csv("bool", "true") is True and normalize_csv("bool", "false") is False
        assert normalize_parquet("bool", True) is True and normalize_parquet("bool", False) is False

    def test_numbers(self):
        assert normalize_sqlite("int", 74) == normalize_csv("int", "74") == normalize_parquet("int", 74) == 74
        assert normalize_csv("int", "0") == 0 and normalize_csv("int", "-3") == -3

    def test_dates(self):
        want = "2025-01-01"
        assert normalize_sqlite("date", "2025-01-01") == want
        assert normalize_csv("date", "2025-01-01") == want
        assert normalize_parquet("date", datetime.date(2025, 1, 1)) == want

    def test_text_is_unchanged(self):
        for fn in (normalize_sqlite, normalize_parquet):
            assert fn("str", "Eid al-Fitr (predicted)") == "Eid al-Fitr (predicted)"
        assert normalize_csv("str", " spaced ") == " spaced "

    def test_an_empty_string_is_not_a_null_in_sqlite_or_parquet(self):
        assert normalize_sqlite("str", "") == ""
        assert normalize_parquet("str", "") == ""

    @pytest.mark.parametrize("fn,kind,value", [
        (normalize_sqlite, "bool", 2), (normalize_sqlite, "bool", True), (normalize_sqlite, "bool", "1"),
        (normalize_sqlite, "int", "74"), (normalize_sqlite, "int", 7.0), (normalize_sqlite, "int", True),
        (normalize_sqlite, "date", "2025-1-1"), (normalize_sqlite, "date", "2025-02-30"),
        (normalize_sqlite, "date", "2025-01-01T00:00:00"), (normalize_sqlite, "str", 5),
        (normalize_csv, "bool", "True"), (normalize_csv, "bool", "1"), (normalize_csv, "bool", "0"),
        (normalize_csv, "int", "07"), (normalize_csv, "int", "7.0"), (normalize_csv, "int", "+7"),
        (normalize_csv, "int", " 7"), (normalize_csv, "date", "01/02/2025"), (normalize_csv, "date", "2025-13-01"),
        (normalize_parquet, "bool", 1), (normalize_parquet, "bool", "true"),
        (normalize_parquet, "int", True), (normalize_parquet, "int", "7"), (normalize_parquet, "int", 7.0),
        (normalize_parquet, "date", "2025-01-01"),
        (normalize_parquet, "date", datetime.datetime(2025, 1, 1)),
        (normalize_parquet, "str", b"bytes"),
    ])
    def test_unexpected_representations_are_rejected(self, fn, kind, value):
        with pytest.raises(NormalizationError):
            fn(kind, value)


# ---------------------------------------------------------------------------
# Self-tests: alter one source, the comparison must notice
# ---------------------------------------------------------------------------

def _copy(sources):
    return {fmt: (list(cols), [tuple(r) for r in rows]) for fmt, (cols, rows) in sources.items()}


def _set(sources, fmt, row, column, value, table="holidays"):
    names = columns(table)
    cols, rows = sources[fmt]
    cells = list(rows[row])
    cells[names.index(column)] = value
    rows[row] = tuple(cells)


def _first_row_where(sources, column, predicate, table="holidays"):
    index = columns(table).index(column)
    return next(i for i, r in enumerate(sources["sqlite"][1]) if predicate(r[index]))


class TestSelfCheck:
    def test_unaltered_copy_passes(self, loaded):
        assert compare("holidays", _copy(loaded["holidays"])) == []

    def test_flipped_boolean_in_parquet(self, loaded):
        s = _copy(loaded["holidays"])
        row = _first_row_where(s, "predicted", lambda v: v == 0)
        _set(s, "parquet", row, "predicted", True)
        assert compare("holidays", s)

    def test_flipped_boolean_in_csv(self, loaded):
        s = _copy(loaded["holidays"])
        row = _first_row_where(s, "predicted", lambda v: v == 1)
        _set(s, "csv", row, "predicted", "false")
        assert compare("holidays", s)

    def test_boolean_changed_in_sqlite(self, loaded):
        s = _copy(loaded["holidays"])
        row = _first_row_where(s, "predicted", lambda v: v == 1)
        _set(s, "sqlite", row, "predicted", 0)
        assert compare("holidays", s)

    def test_date_shifted_by_a_day_in_parquet(self, loaded):
        s = _copy(loaded["holidays"])
        _set(s, "parquet", 0, "date", s["parquet"][1][0][columns("holidays").index("date")]
             + datetime.timedelta(days=1))
        assert compare("holidays", s)

    def test_date_changed_in_csv(self, loaded):
        s = _copy(loaded["holidays"])
        _set(s, "csv", 5, "date", "1999-01-01")
        assert compare("holidays", s)

    def test_number_changed_in_sqlite(self, loaded):
        s = _copy(loaded["sessions"])
        _set(s, "sqlite", 0, "seq", 99, table="sessions")
        assert compare("sessions", s)

    def test_null_became_empty_string_in_sqlite(self, loaded):
        s = _copy(loaded["holidays"])
        row = _first_row_where(s, "source_url", lambda v: v is None)
        _set(s, "sqlite", row, "source_url", "")
        assert compare("holidays", s)

    def test_null_became_empty_string_in_parquet(self, loaded):
        s = _copy(loaded["holidays"])
        row = _first_row_where(s, "source_url", lambda v: v is None)
        _set(s, "parquet", row, "source_url", "")
        assert compare("holidays", s)

    def test_value_became_null_in_csv(self, loaded):
        s = _copy(loaded["holidays"])
        row = _first_row_where(s, "source_url", lambda v: v is not None)
        _set(s, "csv", row, "source_url", "")
        assert compare("holidays", s)

    def test_text_changed_in_parquet(self, loaded):
        s = _copy(loaded["exchanges"])
        _set(s, "parquet", 3, "name", s["parquet"][1][3][1] + "!", table="exchanges")
        assert compare("exchanges", s)

    def test_row_dropped_from_csv(self, loaded):
        s = _copy(loaded["confidence"])
        del s["csv"][1][10]
        assert any("row counts differ" in p for p in compare("confidence", s))

    def test_row_added_to_parquet(self, loaded):
        s = _copy(loaded["sessions"])
        s["parquet"][1].append(s["parquet"][1][0])
        assert any("row counts differ" in p for p in compare("sessions", s))

    def test_rows_swapped_in_parquet(self, loaded):
        s = _copy(loaded["holidays"])
        rows = s["parquet"][1]
        rows[0], rows[1] = rows[1], rows[0]
        assert compare("holidays", s)

    def test_column_renamed_in_csv(self, loaded):
        s = _copy(loaded["exchanges"])
        s["csv"][0][1] = "title"
        assert any("csv columns" in p for p in compare("exchanges", s))

    def test_columns_reordered_in_parquet(self, loaded):
        s = _copy(loaded["sessions"])
        s["parquet"][0].reverse()
        assert any("parquet columns" in p for p in compare("sessions", s))

    def test_wrong_representation_is_reported_not_coerced(self, loaded):
        s = _copy(loaded["holidays"])
        row = _first_row_where(s, "predicted", lambda v: v == 1)
        _set(s, "csv", row, "predicted", "True")
        problems = compare("holidays", s)
        assert problems and "CSV boolean" in problems[0]

    def test_datetime_instead_of_date_is_reported(self, loaded):
        s = _copy(loaded["holidays"])
        value = s["parquet"][1][0][columns("holidays").index("date")]
        _set(s, "parquet", 0, "date", datetime.datetime(value.year, value.month, value.day))
        assert any("Parquet date expected" in p for p in compare("holidays", s))
