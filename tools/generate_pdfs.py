#!/usr/bin/env python3
"""Regenerate the downloadable PDFs from the print-ready HTML pages.

The resume / cv / portfolio2026 pages are hand-built to print cleanly (each has
its own ``@page`` / ``@media print`` rules). This renders them to
``assets/pdf/*.pdf`` with headless Chrome (via Playwright, reusing the system
Chrome install -- no ``playwright install`` needed) so the PDFs always match the
current HTML/CSS, then mirrors exactly those three PDFs into ``~/Downloads``.

Two render modes:
  * "single" (cv, portfolio2026): one ``page.pdf()`` call; page size comes from
    the page's own ``@page`` CSS.
  * "paged"  (resume): each ``.page`` block is printed to its own
    content-height sheet and the sheets are merged, so a 2-block resume is
    exactly 2 pages no matter how tall each block grows. This mirrors how the
    original committed PDF was built (its two pages have different heights).

Usage:
    python tools/generate_pdfs.py                 # regenerate all three
    python tools/generate_pdfs.py resume cv       # regenerate only some

Requires: playwright (+ a system Chrome/Edge), pypdf.
Exit codes: 0 = ok, 2 = bad args, 3 = missing dependency / no browser.
"""
import io
import math
import shutil
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSET_PDF_DIR = ROOT / "assets" / "pdf"
DOWNLOADS_DIR = pathlib.Path.home() / "Downloads"
ZERO = {"top": "0", "right": "0", "bottom": "0", "left": "0"}

# page directory -> render job
JOBS = {
    "resume": dict(
        out="Dongsik_Yoon_Resume.pdf", mode="paged",
        selector=".page", width="210mm",
    ),
    "cv": dict(
        out="Dongsik_Yoon_CV.pdf", mode="single",
        opts=dict(prefer_css_page_size=True, print_background=True),
    ),
    "portfolio2026": dict(
        out="Dongsik_Yoon_Portfolio.pdf", mode="single",
        opts=dict(prefer_css_page_size=True, print_background=True, margin=ZERO),
    ),
}


def launch(pw):
    """Reuse an installed Chrome/Edge; fall back to Playwright's chromium."""
    last = None
    for kwargs in ({"channel": "chrome"}, {"channel": "msedge"}, {}):
        try:
            return pw.chromium.launch(headless=True, **kwargs)
        except Exception as e:            # noqa: BLE001 - try the next option
            last = e
    raise SystemExit(f"could not launch a Chromium-based browser: {last}")


def _open(page, src):
    page.goto(src.as_uri(), wait_until="networkidle")
    page.evaluate("() => document.fonts.ready")   # let web fonts settle
    page.wait_for_timeout(250)


def render_single(page, src, opts):
    _open(page, src)
    return page.pdf(**opts)


def render_paged(page, src, selector, width):
    """Print each `selector` block to its own content-height sheet, merged."""
    from pypdf import PdfReader, PdfWriter
    _open(page, src)
    page.emulate_media(media="print")             # measure in print layout
    page.wait_for_timeout(150)
    heights = page.eval_on_selector_all(
        selector, "els => els.map(e => e.getBoundingClientRect().height * 25.4 / 96)")
    if not heights:
        raise SystemExit(f"no '{selector}' blocks found in {src}")
    writer = PdfWriter()
    for i, h_mm in enumerate(heights):
        page.eval_on_selector_all(
            selector, "(els, i) => els.forEach((e, j) => e.style.display = (j === i ? '' : 'none'))", i)
        buf = page.pdf(width=width, height=f"{math.ceil(h_mm) + 1}mm",
                       print_background=True, margin=ZERO)
        for pg in PdfReader(io.BytesIO(buf)).pages:
            writer.add_page(pg)
    page.eval_on_selector_all(selector, "els => els.forEach(e => e.style.display = '')")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def main(argv):
    which = argv or list(JOBS)
    bad = [w for w in which if w not in JOBS]
    if bad:
        print(f"unknown page(s) {bad}; choose from {list(JOBS)}", file=sys.stderr)
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed (pip install playwright)", file=sys.stderr)
        return 3

    out = ASSET_PDF_DIR
    out.mkdir(parents=True, exist_ok=True)
    mirror_to_downloads = DOWNLOADS_DIR.is_dir()

    with sync_playwright() as pw:
        browser = launch(pw)
        page = browser.new_page()
        for name in which:
            job = JOBS[name]
            src = (ROOT / name / "index.html").resolve()
            if not src.exists():
                print(f"  ! {name}: {src} not found, skipping", file=sys.stderr)
                continue
            if job["mode"] == "paged":
                data = render_paged(page, src, job["selector"], job["width"])
            else:
                data = render_single(page, src, job["opts"])
            target = out / job["out"]
            target.write_bytes(data)
            print(f"  + {name} -> {target}")
            if mirror_to_downloads:
                local_target = DOWNLOADS_DIR / job["out"]
                shutil.copyfile(target, local_target)
                print(f"      copied -> {local_target}")
            else:
                print(f"      skipped local copy: {DOWNLOADS_DIR} not found", file=sys.stderr)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
