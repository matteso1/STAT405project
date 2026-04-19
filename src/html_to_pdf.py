#!/usr/bin/env python3
"""
html_to_pdf.py: Render an HTML file to PDF via headless Chromium.

Used to produce `presentation.pdf` (from revealjs) and `report.pdf`
(from the plain-HTML report) without needing LaTeX. Playwright's
chromium-headless-shell downloads itself into the user cache on first
run, so no sudo is required.

Usage:
    python html_to_pdf.py INPUT.html OUTPUT.pdf [--reveal] \
        [--format Letter|A4] [--landscape]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--reveal", action="store_true",
                   help="Load with ?print-pdf query (revealjs print mode).")
    p.add_argument("--format", default="Letter")
    p.add_argument("--landscape", action="store_true")
    p.add_argument("--margin", default="0.4in")
    args = p.parse_args()

    from playwright.sync_api import sync_playwright

    src = Path(args.input).resolve()
    if not src.exists():
        sys.exit(f"not found: {src}")
    url = src.as_uri()
    if args.reveal:
        url += "?print-pdf"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle")
        # Let fonts and images settle. revealjs also needs a moment to build
        # the print layout once we've passed ?print-pdf.
        page.wait_for_timeout(1500)
        pdf_bytes = page.pdf(
            format=args.format,
            landscape=args.landscape,
            margin={"top": args.margin, "bottom": args.margin,
                    "left": args.margin, "right": args.margin},
            print_background=True,
        )
        browser.close()

    Path(args.output).write_bytes(pdf_bytes)
    sz_kb = os.path.getsize(args.output) / 1024
    print(f"wrote {args.output} ({sz_kb:.1f} KB)")


if __name__ == "__main__":
    main()
