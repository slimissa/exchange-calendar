#!/usr/bin/env python3
"""
fetch_render.py — Render fetcher: read pages that plain fetchers cannot.

Phase 3, Session 1. Three modes, one fallback contract.

Modes
-----
js
    A JavaScript single-page application. The holiday table is built
    client-side, so the raw HTTP body has no data. Headless Chromium (via
    Playwright) loads the page, waits for ``wait_selector`` (a CSS selector
    that proves the holiday table rendered), and returns ``page.content()``.
    Raises ``RenderTimeout`` if the selector never appears.

pdf
    A PDF visual grid with no per-date text labels. The PDF is downloaded,
    the requested pages are rasterized at 200 DPI (PyMuPDF) and Tesseract
    reads each image. The page texts are concatenated. Raises ``OCRFailure``
    if the PDF cannot be downloaded or Tesseract returns nothing for every
    page.

auto
    Try ``js`` (only when a selector is given), then ``pdf``, then give up
    with ``blocked``.

Fallback contract
-----------------
This module never silently succeeds. If the page cannot be read, it returns
`BLOCKED` with a reason. A fetcher that returns an empty holiday list is
worse than no fetcher.

``render_or_block`` never raises. It returns ``(text, status)`` with status
``"ok"`` (non-empty text), ``"blocked"`` (the page could not be read; reason
on stderr) or ``"error"`` (a bug or a missing dependency, not a property of
the page). Empty text is never reported as ``"ok"``.

Limits (read before trusting the output)
----------------------------------------
* OCR returns the text Tesseract sees. It does not see colour. A calendar
  that marks holidays only by cell fill (the XATH case in ADR 0010 D2)
  yields day numbers without any holiday marker; text from this module is
  raw material for a parser, not a holiday list.
* The module extracts text. It adds no dates to any exchange JSON and is not
  wired into ``tools/update_from_exchange.py`` (Session 2, after
  calibration).
* Playwright, pytesseract and PyMuPDF are imported lazily, inside the
  functions that need them, so importing this module and running
  ``--dry-run`` need none of them.

CLI
---
    python3 tools/fetch_render.py --url URL --mode {js,pdf,auto} \\
        --selector CSS [--dry-run] [--verbose]

Exit codes: 0 text extracted, 1 blocked, 2 usage error, 3 unexpected failure.
"""

from __future__ import annotations

import argparse
import logging
import sys
import urllib.request
from typing import Optional

log = logging.getLogger("fetch_render")

OCR_DPI = 200
DEFAULT_PAGE_RANGE = (0, 3)
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_USAGE = 2
EXIT_FAILURE = 3


class RenderTimeout(Exception):
    """The wait selector did not appear within the timeout."""


class OCRFailure(Exception):
    """The PDF could not be downloaded, or OCR produced no text."""


# ---------------------------------------------------------------------------
# js path
# ---------------------------------------------------------------------------

def render_js(url: str, wait_selector: str, timeout: int = 30) -> str:
    """Load ``url`` in headless Chromium, wait for ``wait_selector``, return HTML.

    Raises RenderTimeout (with the URL and the selector in the message) when
    the selector does not appear within ``timeout`` seconds.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    timeout_ms = int(timeout * 1000)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            try:
                page.goto(url, timeout=timeout_ms)
                page.wait_for_selector(wait_selector, timeout=timeout_ms)
            except (PlaywrightTimeout, TimeoutError) as exc:
                raise RenderTimeout(
                    f"selector {wait_selector!r} not found at {url} "
                    f"within {timeout}s"
                ) from exc
            return page.content()
        finally:
            browser.close()


# ---------------------------------------------------------------------------
# pdf path
# ---------------------------------------------------------------------------

def _download_pdf(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _rasterize_pages(pdf_bytes: bytes, page_range: tuple[int, int]) -> list:
    """Render pages [start, end) at OCR_DPI as PIL images."""
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24.3
    except ImportError:
        import fitz  # older PyMuPDF
    from PIL import Image
    import io

    start, end = page_range
    images = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        end = min(end, doc.page_count)
        for index in range(max(start, 0), end):
            pix = doc[index].get_pixmap(dpi=OCR_DPI)
            images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
    return images


def render_pdf_ocr(
    url: str,
    page_range: tuple[int, int] = DEFAULT_PAGE_RANGE,
    timeout: int = 30,
) -> str:
    """Download a PDF, OCR pages [start, end) at 200 DPI, return the text.

    Raises OCRFailure if the download fails, no page can be rendered, or
    Tesseract returns empty text for every page.
    """
    import pytesseract

    try:
        pdf_bytes = _download_pdf(url, timeout)
    except Exception as exc:  # network, HTTP, DNS, TLS: all the same to the caller
        raise OCRFailure(f"cannot download PDF {url}: {exc}") from exc

    try:
        images = _rasterize_pages(pdf_bytes, page_range)
    except Exception as exc:
        raise OCRFailure(f"cannot render PDF {url}: {exc}") from exc
    if not images:
        raise OCRFailure(f"no pages in range {page_range} for {url}")

    texts = []
    for image in images:
        text = (pytesseract.image_to_string(image) or "").strip()
        if text:
            texts.append(text)
    if not texts:
        raise OCRFailure(
            f"Tesseract returned empty text for all {len(images)} page(s) of {url}"
        )
    return "\n\n".join(texts)


# ---------------------------------------------------------------------------
# dispatcher
# ---------------------------------------------------------------------------

def _render(url: str, mode: str, **kwargs) -> tuple[str, str, str]:
    """Run the requested mode(s). Returns (text, status, reason). Never raises."""
    if mode not in ("js", "pdf", "auto"):
        return "", "error", f"unknown mode {mode!r} (expected js, pdf or auto)"

    selector: Optional[str] = kwargs.get("wait_selector")
    timeout: int = kwargs.get("timeout", 30)
    page_range = kwargs.get("page_range", DEFAULT_PAGE_RANGE)
    reasons: list[str] = []

    if mode in ("js", "auto"):
        if not selector:
            if mode == "js":
                return "", "error", "js mode needs wait_selector"
            reasons.append("js skipped: no wait_selector")
        else:
            try:
                text = render_js(url, selector, timeout=timeout)
                if text and text.strip():
                    return text, "ok", ""
                reasons.append("js: page content empty")
            except RenderTimeout as exc:
                reasons.append(f"js: {exc}")
            except Exception as exc:
                if mode == "js":
                    return "", "error", f"js: {type(exc).__name__}: {exc}"
                reasons.append(f"js error: {type(exc).__name__}: {exc}")

    if mode in ("pdf", "auto"):
        try:
            text = render_pdf_ocr(url, page_range=page_range, timeout=timeout)
            if text and text.strip():
                return text, "ok", ""
            reasons.append("pdf: OCR text empty")
        except OCRFailure as exc:
            reasons.append(f"pdf: {exc}")
        except Exception as exc:
            if mode == "pdf":
                return "", "error", f"pdf: {type(exc).__name__}: {exc}"
            reasons.append(f"pdf error: {type(exc).__name__}: {exc}")

    return "", "blocked", "; ".join(reasons) or "no mode produced text"


def render_or_block(url: str, mode: str, **kwargs) -> tuple[str, str]:
    """Fallback dispatcher. Returns (text, status); never raises.

    kwargs: wait_selector (str), timeout (int), page_range (tuple[int, int]).
    The reason for a non-ok status is logged to stderr.
    """
    text, status, reason = _render(url, mode, **kwargs)
    if status != "ok":
        print(f"BLOCKED {url}: {reason}" if status == "blocked"
              else f"ERROR {url}: {reason}", file=sys.stderr)
    return text, status


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fetch_render.py",
        description="Render a page (JS SPA, PDF grid) and print its text, "
                    "or report BLOCKED with a reason.",
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--mode", required=True, choices=("js", "pdf", "auto"))
    parser.add_argument("--selector", help="CSS selector proving the holiday "
                        "table rendered (required for js; used by auto)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would run; launch nothing")
    parser.add_argument("--verbose", action="store_true")
    return parser


def _dry_run(args: argparse.Namespace) -> None:
    start, end = DEFAULT_PAGE_RANGE
    if args.mode in ("js", "auto") and args.selector:
        print(f"DRY RUN: would launch Playwright for {args.url} "
              f"with selector {args.selector}")
    if args.mode in ("pdf", "auto"):
        print(f"DRY RUN: would download PDF from {args.url} and OCR pages "
              f"{start}-{end} at {OCR_DPI} DPI")


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 on usage errors
        return int(exc.code) if isinstance(exc.code, int) else EXIT_USAGE

    if args.mode == "js" and not args.selector:
        print("usage error: --selector is required with --mode js",
              file=sys.stderr)
        return EXIT_USAGE

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        stream=sys.stderr, format="%(levelname)s %(name)s: %(message)s",
    )

    if args.dry_run:
        _dry_run(args)
        return EXIT_OK

    try:
        text, status, reason = _render(
            args.url, args.mode, wait_selector=args.selector)
    except Exception as exc:  # _render should not raise; belt and braces
        print(f"ERROR {args.url}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_FAILURE

    if status == "ok":
        print(text)
        return EXIT_OK
    if status == "blocked":
        print(f"BLOCKED {args.url}: {reason}")
        return EXIT_BLOCKED
    print(f"ERROR {args.url}: {reason}", file=sys.stderr)
    return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
