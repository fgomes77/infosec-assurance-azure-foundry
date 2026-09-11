"""Convert an HTML CISO Executive Summary to PDF using Playwright/Chromium.
Usage: python3 html_to_pdf.py <input.html> <output.pdf>
"""
from playwright.sync_api import sync_playwright
import sys, os

html_path = sys.argv[1]
pdf_path = sys.argv[2]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"file://{os.path.abspath(html_path)}", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    page.pdf(
        path=pdf_path,
        format="A3",
        landscape=True,
        print_background=True,
        margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
    )
    browser.close()
    print(f"✅ PDF saved → {pdf_path}")
