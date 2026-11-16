"""XIST fetcher: a non-PDF response is a FetchError, not a ParseError."""
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import update_from_exchange as ufe  # noqa: E402


@pytest.fixture(autouse=True)
def no_sleep():
    with mock.patch.object(ufe.time, "sleep"):
        yield


def test_non_pdf_response_raises_fetch_error_and_is_retried():
    f = ufe.XISTFetcher()
    with mock.patch.object(
        f, "_make_binary_request", return_value=b"<html>Access Denied</html>"
    ) as req, mock.patch.object(f, "_extract_pdf_text") as extract:
        with pytest.raises(ufe.FetchError) as exc:
            f.fetch()
    assert not isinstance(exc.value, ufe.ParseError)
    assert "not a PDF" in str(exc.value)
    assert req.call_count == 3  # the existing retry runs all three attempts
    extract.assert_not_called()  # the parser never saw the HTML


def test_pdf_header_reaches_the_parser():
    f = ufe.XISTFetcher()
    text = (
        "BORSA ISTANBUL EQUITY MARKET 2026 HOLIDAY SCHEDULE\n"
        "1 January 2026 Thursday New Year\n"
        "23 April 2026 Thursday National Sovereignty Day\n"
    )
    with mock.patch.object(
        f, "_make_binary_request", return_value=b"%PDF-1.4\n..."
    ), mock.patch.object(f, "_extract_pdf_text", return_value=text) as extract:
        data = f.fetch()
    extract.assert_called_once()
    assert [h.date for h in data.holidays] == ["2026-01-01", "2026-04-23"]


def test_pdf_with_no_holidays_is_still_a_parse_error():
    f = ufe.XISTFetcher()
    with mock.patch.object(
        f, "_make_binary_request", return_value=b"%PDF-1.4\n..."
    ), mock.patch.object(f, "_extract_pdf_text", return_value=""):
        with pytest.raises(ufe.ParseError):
            f.fetch()


class _Resp:
    def __init__(self, status, content=b""):
        self.status_code, self.content = status, content

    def raise_for_status(self):
        import requests
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code}", response=self)


def _fetch_with_http(status):
    f = ufe.XISTFetcher()
    f.rate_limiter = mock.Mock()
    with mock.patch.object(f, "_check_robots_allowed", return_value=True), \
            mock.patch.object(f, "_record_manifest"), \
            mock.patch("requests.get", return_value=_Resp(status)) as get:
        try:
            f.fetch()
        except Exception as e:  # noqa: BLE001
            return e, get.call_count
    return None, get.call_count


def test_404_on_the_year_specific_url_is_source_missing_and_not_retried():
    err, calls = _fetch_with_http(404)
    assert isinstance(err, ufe.SourceMissingError) and "HTTP 404" in str(err)
    assert calls == 1


def test_robots_disallow_is_source_missing():
    f = ufe.XISTFetcher()
    with mock.patch.object(f, "_check_robots_allowed", return_value=False):
        with pytest.raises(ufe.SourceMissingError) as exc:
            f.fetch()
    assert "robots.txt" in str(exc.value)


def test_503_is_flaky_and_retried():
    err, calls = _fetch_with_http(503)
    assert type(err) is ufe.FetchError
    assert calls == 3
