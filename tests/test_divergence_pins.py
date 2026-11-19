"""The divergence tools refuse to run against unpinned reference libraries.

The pins live in requirements-dev.txt only; tools/divergence_pins.py reads
them from there. 09ab215 regenerated docs/DIVERGENCE.md with
pandas_market_calendars 5.5.0 instead of 5.6.0 because nothing checked.
"""
import io
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import divergence_pins  # noqa: E402
import divergence_report  # noqa: E402
import divergence_test  # noqa: E402

PINS = divergence_pins.read_pins()


def test_requirements_pin_both_libraries_exactly():
    assert set(PINS) == {"exchange_calendars", "pandas_market_calendars"}
    for version in PINS.values():
        assert version and all(part.isdigit() for part in version.split("."))


def test_read_pins_rejects_an_unpinned_library(tmp_path):
    req = tmp_path / "requirements-dev.txt"
    req.write_text("exchange_calendars==4.13.2\npandas_market_calendars\n")
    with pytest.raises(ValueError, match="pandas_market_calendars"):
        divergence_pins.read_pins(req)


def test_read_pins_ignores_comments_and_other_packages(tmp_path):
    req = tmp_path / "requirements-dev.txt"
    req.write_text("# pins\npytest>=8\nexchange-calendars==4.13.2  # EC\n"
                   "pandas_market_calendars==5.6.0\n")
    assert divergence_pins.read_pins(req) == {
        "exchange_calendars": "4.13.2", "pandas_market_calendars": "5.6.0"}


def test_check_passes_on_matching_versions():
    out = io.StringIO()
    assert divergence_pins.check(found=dict(PINS), stream=out) == 0
    assert out.getvalue() == ""


def test_check_exits_2_and_names_both_versions_on_mismatch():
    found = dict(PINS, pandas_market_calendars="5.5.0")
    out = io.StringIO()
    assert divergence_pins.check(found=found, stream=out) == 2
    msg = out.getvalue()
    assert "pandas_market_calendars: installed 5.5.0, pinned " + PINS["pandas_market_calendars"] in msg
    assert "pip install -r requirements-dev.txt" in msg
    assert "exchange_calendars" not in msg  # only the mismatching library is listed


def test_check_reports_a_missing_library():
    found = dict(PINS, exchange_calendars=None)
    out = io.StringIO()
    assert divergence_pins.check(found=found, stream=out) == 2
    assert "exchange_calendars: installed not installed" in out.getvalue()


def _installed(**override):
    versions = dict(PINS, **override)
    return lambda lib: versions[lib]


def test_divergence_test_main_exits_2_before_comparing(capsys):
    with mock.patch.object(divergence_pins.metadata, "version",
                           side_effect=_installed(pandas_market_calendars="5.5.0")), \
            mock.patch.object(divergence_test, "run_exchange") as run, \
            mock.patch.object(divergence_test, "run_exchange_sessions") as run_sessions:
        rc = divergence_test.main(["--exchanges", "XNYS", "--year", "2026",
                                   "--output", "/nonexistent/never-written.json"])
    assert rc == 2
    run.assert_not_called()
    run_sessions.assert_not_called()
    assert "pinned " + PINS["pandas_market_calendars"] in capsys.readouterr().err


def test_divergence_report_main_exits_2_on_installed_mismatch(tmp_path, capsys):
    out = tmp_path / "DIVERGENCE.md"
    with mock.patch.object(divergence_pins.metadata, "version",
                           side_effect=_installed(exchange_calendars="4.12.0")):
        rc = divergence_report.main(["--output", str(out)])
    assert rc == 2
    assert not out.exists()
    assert "exchange_calendars: installed 4.12.0" in capsys.readouterr().err


def test_divergence_report_main_exits_2_on_stale_input(tmp_path, capsys):
    """Matching installed versions are not enough: the input JSON must have
    been produced with the pins too."""
    stale = {"years": [2026], "libraries": dict(PINS, pandas_market_calendars="5.5.0"),
             "exchanges": {}}
    inp = tmp_path / "divergence.json"
    inp.write_text(json.dumps(stale))
    out = tmp_path / "DIVERGENCE.md"
    with mock.patch.object(divergence_pins.metadata, "version", side_effect=_installed()):
        rc = divergence_report.main(["--input", str(inp), "--output", str(out)])
    assert rc == 2
    assert not out.exists()
    assert "recorded in divergence.json 5.5.0" in capsys.readouterr().err
