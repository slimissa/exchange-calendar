"""live_fetcher_check: FetchError is WARN (flaky source), ParseError is FAIL."""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import live_fetcher_check as lfc  # noqa: E402
from update_from_exchange import (  # noqa: E402
    FetchError, ParseError, RateLimitError, ValidationError,
)


class Fake:
    name = "Fake Exchange"
    source_url = "https://example.invalid"

    def __init__(self, outcome):
        self.outcome = outcome

    def fetch(self):
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def _data(n):
    return SimpleNamespace(holidays=[SimpleNamespace(date="2026-01-01")] * n)


def test_fetch_error_is_warn():
    r = lfc.check_fetcher("XIST", Fake(FetchError("not a PDF (bytes=24)")))
    assert r["status"] == "WARN" and "FetchError" in r["reason"]


def test_rate_limit_error_is_warn():
    assert lfc.check_fetcher("XIST", Fake(RateLimitError("429")))["status"] == "WARN"


def test_parse_error_is_fail_although_it_subclasses_fetch_error():
    assert issubclass(ParseError, FetchError)
    r = lfc.check_fetcher("XIST", Fake(ParseError("No holidays found")))
    assert r["status"] == "FAIL" and "ParseError" in r["reason"]


def test_validation_error_is_fail():
    assert lfc.check_fetcher("XIST", Fake(ValidationError("bad date")))["status"] == "FAIL"


def test_unexpected_exception_is_fail():
    assert lfc.check_fetcher("XIST", Fake(KeyError("x")))["status"] == "FAIL"


def test_no_holidays_is_fail_and_holidays_is_pass():
    assert lfc.check_fetcher("XIST", Fake(_data(0)))["status"] == "FAIL"
    assert lfc.check_fetcher("XIST", Fake(None))["status"] == "FAIL"
    assert lfc.check_fetcher("XIST", Fake(_data(3)))["status"] == "PASS"


def _run_main(monkeypatch, capsys, outcomes):
    fakes = {m: Fake(o) for m, o in outcomes.items()}

    class Reg:
        def list_available(self):
            return list(fakes)

        def get(self, mic):
            return fakes[mic]

    monkeypatch.setattr(lfc, "ExchangeFetcherRegistry", Reg)
    monkeypatch.setattr(sys, "argv", ["live_fetcher_check.py"])
    code = lfc.main()
    return code, capsys.readouterr().out


def test_exit_code_warn_passes_and_fail_fails(monkeypatch, capsys):
    code, out = _run_main(monkeypatch, capsys, {"AAAA": _data(2), "XIST": FetchError("not a PDF")})
    assert code == 0
    assert "XIST    WARN" in out and "1 warned, 0 failed" in out

    code, out = _run_main(
        monkeypatch, capsys,
        {"AAAA": _data(2), "XIST": FetchError("x"), "BBBB": ParseError("page changed")},
    )
    assert code == 1
    assert "BBBB    FAIL" in out and "1 warned, 1 failed" in out
