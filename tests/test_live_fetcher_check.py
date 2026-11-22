"""live_fetcher_check (4b3): PASS / FAIL / TRANSIENT with attempt counts.

Transient = the source had a bad day (FetchError, RateLimitError, requests
timeout / connection error / HTTP 5xx, "no holidays" on an empty or
maintenance page), retried within the run. Deterministic = FAIL at once
(ValidationError, conflicting rows, SourceMissingError, ParseError on a page
with content, HTTP 4xx, unexpected exceptions).
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import live_fetcher_check as lfc  # noqa: E402
from update_from_exchange import (  # noqa: E402
    FetchError, ParseError, RateLimitError, SourceMissingError, ValidationError,
)

CONTENT = "<html><body>" + ("Trading calendar 2026: a real page with content. " * 20) + "</body></html>"
MAINTENANCE = "<html><body><h1>Sitio en mantenimiento</h1>" + ("x " * 300) + "</body></html>"


class Fake:
    """A fetcher whose fetch() reads `page` through _make_request (when given)
    and then returns or raises each outcome in turn."""
    name = "Fake Exchange"
    source_url = "https://example.invalid"

    def __init__(self, *outcomes, page=lfc.UNKNOWN):
        self.outcomes = list(outcomes)
        self.calls = 0
        if page is not lfc.UNKNOWN:
            self._page = page
            self._make_request = lambda: self._page

    def fetch(self):
        if hasattr(self, "_make_request"):
            self._make_request()
        outcome = self.outcomes[min(self.calls, len(self.outcomes) - 1)]
        self.calls += 1
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _data(n):
    return SimpleNamespace(holidays=[SimpleNamespace(date="2026-01-01")] * n)


def run(fake, attempts=3):
    sleeps = []
    r = lfc.check_fetcher("XTST", fake, attempts=attempts, retry_delay=10, sleep=sleeps.append)
    return r, sleeps


# --- classification -----------------------------------------------------------

@pytest.mark.parametrize("exc", [FetchError("Failed to fetch CSX page"), RateLimitError("429"),
                                 requests.exceptions.Timeout("t"), requests.exceptions.ConnectionError("c")])
def test_transient_kinds(exc):
    r, sleeps = run(Fake(exc))
    assert r["status"] == "TRANSIENT" and r["attempts"] == 3
    assert sleeps == [10, 20]  # increasing delay


def test_http_5xx_is_transient_4xx_is_fail():
    def http(code):
        e = requests.exceptions.HTTPError(f"{code}")
        e.response = SimpleNamespace(status_code=code)
        return e
    assert run(Fake(http(503)))[0]["status"] == "TRANSIENT"
    r, sleeps = run(Fake(http(403)))
    assert r["status"] == "FAIL" and r["attempts"] == 1 and sleeps == []


@pytest.mark.parametrize("exc", [
    ValidationError("Invalid data: Duplicate holiday date: 2026-01-01"),
    ParseError("XMAD: conflicting rows for 2026-12-24: closed vs early_close 14:00"),
    SourceMissingError("HTTP 404"),
    ParseError("table header changed"),
    KeyError("x"),
])
def test_deterministic_kinds_fail_at_once(exc):
    r, sleeps = run(Fake(exc, page=CONTENT))
    assert r["status"] == "FAIL" and r["attempts"] == 1 and sleeps == []
    assert type(exc).__name__ in r["reason"]


def test_no_holidays_on_an_empty_or_maintenance_page_is_transient():
    for page in (None, "", "<html><body></body></html>", MAINTENANCE):
        r, _ = run(Fake(ParseError("No holidays found for XMEX"), page=page))
        assert r["status"] == "TRANSIENT", page


def test_no_holidays_on_a_page_with_content_is_fail():
    r, sleeps = run(Fake(ParseError("No holidays found for XTSE"), page=CONTENT))
    assert r["status"] == "FAIL" and r["attempts"] == 1


def test_no_holidays_without_a_recorded_page_is_fail():
    # The fetcher did not read through _make_request: emptiness unknown.
    assert run(Fake(ParseError("No holidays found for XIST")))[0]["status"] == "FAIL"
    assert run(Fake(_data(0)))[0]["status"] == "FAIL"
    assert run(Fake(None))[0]["status"] == "FAIL"


def test_empty_result_on_an_empty_page_is_transient():
    assert run(Fake(_data(0), page=""))[0]["status"] == "TRANSIENT"


def test_pdf_bytes_count_as_content():
    assert not lfc.page_is_empty_or_maintenance(b"%PDF-1.7" + b"\0" * 2000)


# --- retries ------------------------------------------------------------------

def test_transient_then_pass_reports_the_attempt_count():
    r, sleeps = run(Fake(FetchError("x"), _data(4)))
    assert r["status"] == "PASS" and r["attempts"] == 2 and sleeps == [10]


def test_pass_needs_one_attempt():
    r, sleeps = run(Fake(_data(3)))
    assert r["status"] == "PASS" and r["attempts"] == 1 and sleeps == []


def test_transient_then_deterministic_stops_at_the_fail():
    r, _ = run(Fake(FetchError("x"), ValidationError("dup"), page=CONTENT))
    assert r["status"] == "FAIL" and r["attempts"] == 2


# --- main ---------------------------------------------------------------------

def _run_main(monkeypatch, capsys, outcomes, extra=()):
    fakes = {m: Fake(o) for m, o in outcomes.items()}

    class Reg:
        def list_available(self):
            return list(fakes)

        def get(self, mic):
            return fakes[mic]

    monkeypatch.setattr(lfc, "ExchangeFetcherRegistry", Reg)
    code = lfc.main(["--retry-delay", "0", *extra])
    return code, capsys.readouterr().out


def test_exit_code_transient_passes_and_fail_fails(monkeypatch, capsys, tmp_path):
    code, out = _run_main(monkeypatch, capsys, {"AAAA": _data(2), "XCAY": FetchError("Failed to fetch CSX page")})
    assert code == 0
    assert "XCAY    TRANSIENT  3" in out and "1 transient, 0 failed" in out

    out_json = tmp_path / "r.json"
    code, out = _run_main(
        monkeypatch, capsys,
        {"AAAA": _data(2), "XCAY": FetchError("x"), "XMAD": ValidationError("Duplicate holiday date")},
        extra=["--json-out", str(out_json)])
    assert code == 1
    assert "XMAD    FAIL       1" in out and "1 transient, 1 failed" in out
    rows = {r["mic"]: r for r in json.loads(out_json.read_text())["results"]}
    assert rows["XMAD"]["status"] == "FAIL" and rows["XCAY"]["attempts"] == 3
