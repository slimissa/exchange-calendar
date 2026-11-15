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
