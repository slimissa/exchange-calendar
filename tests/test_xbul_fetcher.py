"""Tests for XBULFetcher (tools/update_from_exchange.py) — fixture and mocks only.

Fixture: tests/fixtures/xbul_calendar.html is a reconstruction of the
div.calendar element of the rendered bse-sofia.bg trading calendar (2026),
with a little surrounding markup. It was rebuilt from a terminal capture of
the reconnaissance extract: the structure, the weekend and holiday classes,
the titles and the weekday cells marked "holiday" come from that capture,
but the data-URI background images and inline colours were dropped, and the
legend after the calendar was cut off in the capture. It is not a
byte-for-byte copy of the page. The fetcher was not run against the live
page when these tests were written.

No test touches the network: render_js and the robots.txt check are mocked.
"""
import datetime
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import fetch_render  # noqa: E402
import update_from_exchange as updater  # noqa: E402

FIXTURE = (ROOT / "tests" / "fixtures" / "xbul_calendar.html").read_text(encoding="utf-8")
PAGE_URL = "https://www.bse-sofia.bg/en/trading-calendar"


def _fetch(html=None, render_side_effect=None):
    """Run XBULFetcher.fetch() with render_js mocked."""
    fetcher = updater.XBULFetcher()
    render = mock.Mock(return_value=html, side_effect=render_side_effect)
    with mock.patch.object(fetch_render, "render_js", render), \
         mock.patch.object(updater.ExchangeFetcher, "_check_robots_allowed",
                           return_value=True):
        data = fetcher.fetch()
    return fetcher, data, render


def test_xbul_parses_holidays():
    fetcher, data, render = _fetch(FIXTURE)

    by_date = {h.date: h.name for h in data.holidays}
    assert by_date["2026-01-01"] == "New Year's Day"
    assert by_date["2026-01-02"] == "Government decision related to the Euro introduction"
    assert by_date["2026-04-10"] == "Good Friday"
    assert by_date["2026-04-13"] == "Easter Monday"
    assert by_date["2026-05-01"] == "Labour Day"
    assert by_date["2026-05-06"] == "St. George's Day"
    assert by_date["2026-12-24"] == "Christmas Eve"
    assert by_date["2026-12-25"] == "Christmas Day"
    # weekday holiday cells with no title: named "Holiday", nothing inferred
    for date in ("2026-04-03", "2026-04-06", "2026-05-25",
                 "2026-09-07", "2026-12-28", "2026-12-31"):
        assert by_date[date] == "Holiday"
    assert len(data.holidays) == 16
    render.assert_called_once_with(PAGE_URL, "#calendar_container table", timeout=90)


def test_xbul_shape():
    _, data, _ = _fetch(FIXTURE)

    assert data.mic == "XBUL"
    assert data.timezone == "Europe/Sofia"
    assert data.source_urls == [PAGE_URL]
    for entry in data.holidays:
        d = entry.to_dict()
        assert {"date", "name", "status", "source_url"} <= set(d)
        assert d["status"] == "closed"
        assert d["source_url"] == PAGE_URL


def test_xbul_blocked_on_empty_dom():
    with pytest.raises(updater.ParseError) as excinfo:
        _fetch("<html></html>")
    assert str(excinfo.value).startswith("BLOCKED:")


def test_xbul_skips_non_holiday_days():
    fetcher, data, _ = _fetch(FIXTURE)
    dates = {h.date for h in data.holidays}

    # <td class="">5</td> in January is an ordinary Monday
    assert '<td class="">5</td>' in FIXTURE
    assert "2026-01-05" not in dates
    # weekends are marked "holiday" by the page but are not recorded
    assert "2026-01-03" not in dates and "2026-01-04" not in dates
    assert all(datetime.date.fromisoformat(d).weekday() < 5 for d in dates)
    # titled weekend holidays are reported, not recorded
    assert "2026-12-26 Second Christmas Day" in fetcher.last_note
    assert "2026-12-26" not in dates
    # the "today" cell (a Sunday here) is not a holiday entry
    assert "2026-11-08" not in dates


@pytest.mark.parametrize("old, new", [
    ('id="div_year_header">2026<', 'id="div_year_header">Year<'),
    ("<div class=\"name\">March</div>", "<div class=\"name\">Marc</div>"),
    # a title on a cell the page does not mark as a holiday is ambiguous
    ('<td class="">5</td>', '<td class="" title="Mystery">5</td>'),
])
def test_xbul_blocked_on_ambiguous_dom(old, new):
    html = FIXTURE.replace(old, new, 1)
    assert html != FIXTURE
    with pytest.raises(updater.ParseError) as excinfo:
        _fetch(html)
    assert str(excinfo.value).startswith("BLOCKED:")


def test_xbul_blocked_when_render_times_out():
    err = fetch_render.RenderTimeout("selector not found")
    with pytest.raises(updater.FetchError) as excinfo:
        _fetch(render_side_effect=err)
    assert str(excinfo.value).startswith("BLOCKED:")
    assert "selector not found" in str(excinfo.value)
