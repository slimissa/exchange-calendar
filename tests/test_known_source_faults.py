"""tools/known_source_faults.py (4b4): expiring known-source-fault entries."""
import datetime as dt
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import known_source_faults as ksf  # noqa: E402
import live_fetcher_check as lfc  # noqa: E402

ENTRY = {"mic": "XMAD", "match": r"they fit 2027", "reason": "BME page lists 2027 dates under 2026",
         "evidence": "https://www.bolsasymercados.es/en/bme-exchange/trading/trading-calendar.html: ...",
         "opened": "2026-11-22", "expires": "2027-01-31"}
TODAY = dt.date(2026, 12, 1)


def res(status, reason="", mic="XMAD"):
    return {"mic": mic, "status": status, "attempts": 1, "reason": reason}


def test_matching_failure_is_known_until_expiry():
    r = ksf.apply(res("FAIL", "ParseError: ... they fit 2027 ..."), [ENTRY], TODAY)
    assert r["status"] == "KNOWN" and r["known_fault"]["expires"] == "2027-01-31"
    assert ksf.apply(res("TRANSIENT", "they fit 2027"), [ENTRY], TODAY)["status"] == "KNOWN"
    assert ksf.apply(res("FAIL", "they fit 2027"), [ENTRY], dt.date(2027, 1, 31))["status"] == "KNOWN"


def test_matching_failure_after_expiry_is_fail():
    r = ksf.apply(res("FAIL", "they fit 2027"), [ENTRY], dt.date(2027, 2, 1))
    assert r["status"] == "FAIL" and r["reason"].startswith("known fault expired on 2027-01-31")


def test_a_different_failure_is_fail():
    r = ksf.apply(res("TRANSIENT", "FetchError: Failed to fetch BME Madrid page"), [ENTRY], TODAY)
    assert r["status"] == "FAIL" and "differs from the known fault" in r["reason"]


def test_a_passing_listed_fetcher_warns_to_remove_the_entry():
    r = ksf.apply(res("PASS"), [ENTRY], TODAY)
    assert r["status"] == "PASS" and r["warning"].startswith("fault cleared, remove the entry for XMAD")


def test_unlisted_mic_is_untouched():
    r = res("FAIL", "they fit 2027", mic="XNYS")
    assert ksf.apply(r, [ENTRY], TODAY) is r


@pytest.mark.parametrize("change,msg", [
    ({"expires": "2027-02-01"}, "more than 70 days"),
    ({"expires": "2026-11-21"}, "before opened"),
    ({"evidence": ""}, "missing evidence"),
    ({"match": "("}, "not a regular expression"),
    ({"opened": "22/11/2026"}, "ISO dates"),
    ({"mic": "madrid"}, "not a MIC"),
    ({"extra": 1}, "unknown field"),
])
def test_validation(change, msg):
    assert any(msg in p for p in ksf.problems([dict(ENTRY, **change)]))


def test_seventy_days_exactly_is_allowed_and_duplicates_are_not():
    assert ksf.problems([dict(ENTRY, expires="2027-01-31")]) == []
    assert any("more than one entry" in p for p in ksf.problems([ENTRY, ENTRY]))


def test_the_committed_file_is_valid():
    assert ksf.main(["--check"]) == 0


def test_live_check_reports_known_and_does_not_fail(monkeypatch, capsys, tmp_path):
    faults = tmp_path / "f.json"
    faults.write_text(json.dumps({"faults": [ENTRY]}))

    class Fake:
        name, source_url = "BME", "https://example.invalid"

        def fetch(self):
            raise lfc.ParseError("XMAD: ... they fit 2027. The page contradicts itself")

    class Reg:
        def list_available(self):
            return ["XMAD"]

        def get(self, mic):
            return Fake()

    monkeypatch.setattr(lfc, "ExchangeFetcherRegistry", Reg)
    out_json = tmp_path / "r.json"
    code = lfc.main(["--known-faults", str(faults), "--today", "2026-12-01", "--retry-delay", "0",
                     "--json-out", str(out_json)])
    out = capsys.readouterr().out
    assert code == 0
    assert "XMAD    KNOWN" in out and "1 known source fault(s)" in out
    assert json.loads(out_json.read_text())["results"][0]["known_fault"]["expires"] == "2027-01-31"
    # After expiry the same failure fails the job.
    code = lfc.main(["--known-faults", str(faults), "--today", "2027-02-01", "--retry-delay", "0"])
    assert code == 1


def test_invalid_entries_stop_the_check(monkeypatch, tmp_path):
    faults = tmp_path / "f.json"
    faults.write_text(json.dumps({"faults": [dict(ENTRY, expires="2027-06-01")]}))
    assert lfc.main(["--known-faults", str(faults)]) == 2
