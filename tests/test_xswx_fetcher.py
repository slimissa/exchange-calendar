"""Tests for XSWXFetcher (tools/update_from_exchange.py) — fixture and mocks only.

Fixture: tests/fixtures/xswx_calendar.html is the
div.six-dynamic__trading-and-settlement-calendar element of the rendered SIX
page (reconnaissance extract of 2026-11-07) plus the markup just before it.
It is the only source of the DOM structure used here: the fetcher was not
run against the live page in the session that wrote these tests. The
fixture was rebuilt from a terminal capture of the extract: the trailing
`window.six.labels` script (cut off in the capture) is not included.

No test touches the network: render_js and the robots.txt check are mocked.
"""
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import fetch_render  # noqa: E402
import update_from_exchange as updater  # noqa: E402

FIXTURE = (ROOT / "tests" / "fixtures" / "xswx_calendar.html").read_text(encoding="utf-8")
PAGE_URL = ("https://www.six-group.com/en/market-data/news-tools/"
            "trading-currency-holiday-calendar.html")


def _fetch(html=None, render_side_effect=None):
    """Run XSWXFetcher.fetch() with render_js mocked."""
    fetcher = updater.XSWXFetcher()
    render = mock.Mock(return_value=html, side_effect=render_side_effect)
    with mock.patch.object(fetch_render, "render_js", render), \
         mock.patch.object(updater.ExchangeFetcher, "_check_robots_allowed",
                           return_value=True):
        data = fetcher.fetch()
    return fetcher, data, render


def test_xswx_fetcher_parses_holidays():
    _, data, render = _fetch(FIXTURE)

    by_date = {h.date: h.name for h in data.holidays}
    assert len(data.holidays) == 10
    assert by_date["2026-01-01"] == "New Year's Day"
    assert by_date["2026-04-03"] == "Good Friday"
    assert by_date["2026-12-25"] == "Christmas"
    assert sorted(by_date) == [
        "2026-01-01", "2026-01-02", "2026-04-03", "2026-04-06", "2026-05-01",
        "2026-05-14", "2026-05-25", "2026-12-24", "2026-12-25", "2026-12-31",
    ]
    render.assert_called_once_with(PAGE_URL, "[class*=calendar]", timeout=90)


def test_xswx_fetcher_shape():
    _, data, _ = _fetch(FIXTURE)

    assert data.mic == "XSWX"
    assert data.source_urls == [PAGE_URL]
    assert data.early_closes == []
    for entry in data.holidays:
        d = entry.to_dict()
        assert {"date", "name", "status", "source_url"} <= set(d)
        assert d["status"] == "closed"
        assert d["source_url"] == PAGE_URL


@pytest.mark.parametrize("old, new", [
    # the h3 names the currency calendar
    ("<h3>Market Holidays of the Swiss Stock Exchange</h3>",
     "<h3>Currency Holiday Calendar</h3>"),
    # the currency tab is the checked one
    ('value="$(element.name)0" checked=""', 'value="$(element.name)0"'),
])
def test_xswx_fetcher_skips_currency_tab(old, new):
    html = FIXTURE.replace(old, new)
    if old.startswith("value="):
        html = html.replace('value="$(element.name)1"',
                            'value="$(element.name)1" checked=""')
    assert html != FIXTURE
    with pytest.raises(updater.ParseError) as excinfo:
        _fetch(html)
    assert str(excinfo.value).startswith("BLOCKED:")
    assert "Trading Holiday Calendar" in str(excinfo.value)


def test_xswx_fetcher_blocked_on_empty_dom():
    with pytest.raises(updater.ParseError) as excinfo:
        _fetch("<html></html>")
    assert str(excinfo.value).startswith("BLOCKED:")


def test_xswx_fetcher_handles_2027_if_present():
    # The fixture only has the default year (2026); the selector offers 2027.
    fetcher, data, _ = _fetch(FIXTURE)

    assert {h.date[:4] for h in data.holidays} == {"2026"}
    assert "2027" in fetcher.last_note
    assert "not loaded" in fetcher.last_note


def test_xswx_fetcher_blocked_when_render_times_out():
    err = fetch_render.RenderTimeout("selector not found")
    with pytest.raises(updater.FetchError) as excinfo:
        _fetch(render_side_effect=err)
    assert str(excinfo.value).startswith("BLOCKED:")
    assert "selector not found" in str(excinfo.value)


def test_xswx_fetcher_skips_inconsistent_rows():
    # 01.01.2026 is a Thursday: a row that says Tue is skipped, not trusted.
    html = FIXTURE.replace("<span>Thu</span></div>"
                           '<div class="rt-td bold left-align" role="gridcell" '
                           'style="flex: 120 0 auto; width: 120px; max-width: 120px;">'
                           "<span>01.01.2026</span>",
                           "<span>Tue</span></div>"
                           '<div class="rt-td bold left-align" role="gridcell" '
                           'style="flex: 120 0 auto; width: 120px; max-width: 120px;">'
                           "<span>01.01.2026</span>", 1)
    assert html != FIXTURE
    fetcher, data, _ = _fetch(html)

    assert len(data.holidays) == 9
    assert "2026-01-01" not in {h.date for h in data.holidays}
    assert "1 row(s) skipped" in fetcher.last_note
