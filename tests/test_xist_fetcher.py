"""XIST fetcher: a non-PDF response is a FetchError, not a ParseError; the
fetcher tries the current year's PDF URL, then the next year's."""
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
    assert req.call_count == 6  # 2 candidate years x the 3 retry attempts
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
    assert extract.call_count == 2  # one PDF per candidate year
    # both candidates returned the same 2026 text; dates are de-duplicated
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


def test_404_on_every_candidate_url_is_source_missing_and_not_retried():
    err, calls = _fetch_with_http(404)
    assert isinstance(err, ufe.SourceMissingError) and "HTTP 404" in str(err)
    assert calls == 2  # current and next year, once each


def test_robots_disallow_is_source_missing():
    f = ufe.XISTFetcher()
    with mock.patch.object(f, "_check_robots_allowed", return_value=False):
        with pytest.raises(ufe.SourceMissingError) as exc:
            f.fetch()
    assert "robots.txt" in str(exc.value)


def test_503_is_flaky_and_retried():
    err, calls = _fetch_with_http(503)
    assert type(err) is ufe.FetchError
    assert calls == 6  # 2 candidate years x 3 attempts



URL_2031 = "https://www.borsaistanbul.com/files/equity-market-2031-holiday-schedule.pdf"
URL_2032 = "https://www.borsaistanbul.com/files/equity-market-2032-holiday-schedule.pdf"


@pytest.fixture
def year_2031():
    """Pin the fetcher's current year to 2031 for the whole test."""
    with mock.patch.object(ufe.XISTFetcher, "_current_year", return_value=2031):
        yield


def _pdf_text(year, *lines):
    return "\n".join(
        [f"BORSA ISTANBUL A.S. EQUITY MARKET {year} HOLIDAY SCHEDULE", *lines]
    )


def _serve(f, pdfs):
    """Patch f so each candidate URL returns pdfs[year] (None means 404)."""
    def request():
        year = f.source_url.split("equity-market-")[1][:4]
        if pdfs.get(year) is None:
            f._missing_reason = "HTTP 404"
            return None
        return b"%PDF-1.4 " + year.encode()

    return (
        mock.patch.object(f, "_make_binary_request", side_effect=request),
        mock.patch.object(
            f, "_extract_pdf_text", side_effect=lambda b: pdfs[b.decode()[-4:]]
        ),
    )


def test_candidate_urls_are_the_current_and_next_year(year_2031):
    f = ufe.XISTFetcher()
    assert f.candidate_urls() == [URL_2031, URL_2032]
    assert f.source_url == URL_2031


def test_fetch_requests_the_current_year_first_then_the_next(year_2031):
    f = ufe.XISTFetcher()
    f.rate_limiter = mock.Mock()
    with mock.patch.object(f, "_check_robots_allowed", return_value=True), \
            mock.patch.object(f, "_record_manifest"), \
            mock.patch("requests.get", return_value=_Resp(404)) as get:
        with pytest.raises(ufe.SourceMissingError):
            f.fetch()
    assert [c.args[0] for c in get.call_args_list] == [URL_2031, URL_2032]


def test_current_year_gone_next_year_present_uses_next_year(year_2031):
    f = ufe.XISTFetcher()
    pdfs = {"2032": _pdf_text(2032, "January 1, 2032 Thursday New Year")}
    req, extract = _serve(f, pdfs)
    with req, extract:
        data = f.fetch()
    assert [h.date for h in data.holidays] == ["2032-01-01"]
    assert data.source_urls == [URL_2032]


def test_both_years_present_are_merged(year_2031):
    f = ufe.XISTFetcher()
    pdfs = {
        "2031": _pdf_text(2031, "October 29, 2031 Wednesday Republic Day"),
        "2032": _pdf_text(2032, "January 1, 2032 Thursday New Year"),
    }
    req, extract = _serve(f, pdfs)
    with req, extract:
        data = f.fetch()
    assert [h.date for h in data.holidays] == ["2031-10-29", "2032-01-01"]
    assert data.source_urls == [URL_2031, URL_2032]
