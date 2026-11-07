"""Tests for tools/fetch_render.py — all mocked, no network, no live browser.

The four tests that exercise the Playwright and Tesseract paths skip when
the package is missing (pytest.importorskip, per test, so the rest of the
file still runs). The render_or_block tests and the CLI dry-run test never
need either package and always run.

The dates below are synthetic test data (year 2099). This file adds no date
to any exchange JSON.
"""
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import fetch_render  # noqa: E402

URL = "https://example.test/holidays"
SELECTOR = "table.holidays"

FIXTURE_HTML = (
    "<html><body><table class='holidays'>"
    "<tr><td>2099-01-01</td><td>Test Day</td></tr>"
    "</table></body></html>"
)

TEN_DATES = [f"2099-01-{day:02d}" for day in range(1, 11)]
TEN_HOLIDAYS_TEXT = "\n".join(f"{d} Test Holiday {i}" for i, d in enumerate(TEN_DATES, 1))


def _fake_playwright(page):
    """A sync_playwright() replacement whose chromium.launch().new_page() is `page`."""
    playwright = mock.MagicMock()
    browser = playwright.chromium.launch.return_value
    browser.new_page.return_value = page
    factory = mock.MagicMock()
    factory.return_value.__enter__.return_value = playwright
    return factory, playwright


# --- js path ---------------------------------------------------------------

def test_render_js_returns_content():
    pytest.importorskip("playwright")
    page = mock.MagicMock()
    page.content.return_value = FIXTURE_HTML
    factory, playwright = _fake_playwright(page)

    with mock.patch("playwright.sync_api.sync_playwright", factory):
        html = fetch_render.render_js(URL, SELECTOR, timeout=5)

    assert "<table class='holidays'>" in html
    assert "2099-01-01" in html
    page.wait_for_selector.assert_called_once()
    assert page.wait_for_selector.call_args.args[0] == SELECTOR
    playwright.chromium.launch.assert_called_once()


def test_render_js_times_out():
    pw_api = pytest.importorskip("playwright.sync_api")
    page = mock.MagicMock()
    page.wait_for_selector.side_effect = pw_api.TimeoutError("timed out")
    factory, _ = _fake_playwright(page)

    with mock.patch("playwright.sync_api.sync_playwright", factory):
        with pytest.raises(fetch_render.RenderTimeout) as excinfo:
            fetch_render.render_js(URL, SELECTOR, timeout=1)

    assert URL in str(excinfo.value)
    assert SELECTOR in str(excinfo.value)


# --- pdf path --------------------------------------------------------------

def test_render_pdf_ocr_returns_text():
    pytest.importorskip("pytesseract")
    with mock.patch.object(fetch_render, "_download_pdf", return_value=b"%PDF-fake"), \
         mock.patch.object(fetch_render, "_rasterize_pages", return_value=[object()]), \
         mock.patch("pytesseract.image_to_string", return_value=TEN_HOLIDAYS_TEXT):
        text = fetch_render.render_pdf_ocr(URL, page_range=(0, 1))

    for date in TEN_DATES:
        assert date in text


def test_render_pdf_ocr_empty_pdf():
    pytest.importorskip("pytesseract")
    with mock.patch.object(fetch_render, "_download_pdf", return_value=b"%PDF-fake"), \
         mock.patch.object(fetch_render, "_rasterize_pages",
                           return_value=[object(), object(), object()]), \
         mock.patch("pytesseract.image_to_string", return_value="  \n"):
        with pytest.raises(fetch_render.OCRFailure):
            fetch_render.render_pdf_ocr(URL)


# --- dispatcher (always runs) ----------------------------------------------

def test_render_or_block_js_success():
    with mock.patch.object(fetch_render, "render_js", return_value="<table/>") as js:
        result = fetch_render.render_or_block(URL, "js", wait_selector=SELECTOR)

    assert result == ("<table/>", "ok")
    js.assert_called_once()


def test_render_or_block_js_timeout_falls_back_to_pdf():
    with mock.patch.object(fetch_render, "render_js",
                           side_effect=fetch_render.RenderTimeout("t")), \
         mock.patch.object(fetch_render, "render_pdf_ocr",
                           return_value=TEN_HOLIDAYS_TEXT) as pdf:
        result = fetch_render.render_or_block(URL, "auto", wait_selector=SELECTOR)

    assert result == (TEN_HOLIDAYS_TEXT, "ok")
    pdf.assert_called_once()


def test_render_or_block_both_fail_returns_blocked(capsys):
    with mock.patch.object(fetch_render, "render_js",
                           side_effect=fetch_render.RenderTimeout("no table")), \
         mock.patch.object(fetch_render, "render_pdf_ocr",
                           side_effect=fetch_render.OCRFailure("no text")):
        result = fetch_render.render_or_block(URL, "auto", wait_selector=SELECTOR)

    assert result == ("", "blocked")
    stderr = capsys.readouterr().err
    assert "BLOCKED" in stderr and "no table" in stderr and "no text" in stderr


# --- CLI (always runs) -----------------------------------------------------

def test_cli_dry_run_does_not_launch_browser():
    # Make every browser/OCR import fail inside the child process: if
    # --dry-run touched Playwright, Tesseract or PyMuPDF it would crash.
    child = textwrap.dedent(f"""
        import sys
        for name in ("playwright", "playwright.sync_api", "pytesseract",
                     "pymupdf", "fitz"):
            sys.modules[name] = None
        sys.path.insert(0, {str(ROOT / "tools")!r})
        import fetch_render
        sys.exit(fetch_render.main([
            "--dry-run", "--url", "https://example.com",
            "--mode", "js", "--selector", "table",
        ]))
    """)
    proc = subprocess.run([sys.executable, "-c", child],
                          capture_output=True, text=True, timeout=30)

    assert proc.returncode == 0, proc.stderr
    assert ("DRY RUN: would launch Playwright for https://example.com "
            "with selector table") in proc.stdout
