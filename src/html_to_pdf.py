#!/usr/bin/env python3
# Render HTML to PDF with headless Chromium (Playwright). Used for
# presentation.pdf and report.pdf since we don't have LaTeX set up.

import argparse
import os
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--reveal", action="store_true")
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
