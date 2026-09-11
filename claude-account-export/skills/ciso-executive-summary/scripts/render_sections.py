"""Render TINEXTA HTML report sections as high-res PNGs for PPTX embedding."""
from playwright.sync_api import sync_playwright
import os

HTML_PATH = "/home/claude/TinextaCyber_CISO_ExecSummary.html"
OUT_DIR = "/home/claude/pptx_sections"
os.makedirs(OUT_DIR, exist_ok=True)

# Each section corresponds to a PPTX slide
# We'll render the full page, then clip regions
SECTIONS = [
    # slide3: KPI row + Spider + Profile + Domain bars (top of report)
    {"name": "s3_exec_summary", "clip": {"x": 0, "y": 0, "width": 1340, "height": 820}},
    # slide4: Inherent Risk + Risks table
    {"name": "s4_open_risks", "clip": {"x": 0, "y": 820, "width": 1340, "height": 550}},
    # slide5: Euronext Controls + Perimeter Matrix
    {"name": "s5_controls_perimeter", "clip": {"x": 0, "y": 1370, "width": 1340, "height": 700}},
    # slide6: Critical Findings + DORA/Actions
    {"name": "s6_findings_actions", "clip": {"x": 0, "y": 2070, "width": 1340, "height": 520}},
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 3000})
    page.goto(f"file://{os.path.abspath(HTML_PATH)}", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    
    # Full page screenshot first
    page.screenshot(path=f"{OUT_DIR}/full_page.png", full_page=True)
    
    # Get page height for accurate clipping
    height = page.evaluate("document.body.scrollHeight")
    print(f"Page height: {height}px")
    
    # Screenshot each section by scrolling and clipping
    for sec in SECTIONS:
        page.screenshot(
            path=f"{OUT_DIR}/{sec['name']}.png",
            clip=sec["clip"]
        )
        print(f"  ✅ {sec['name']}.png")
    
    browser.close()

print(f"\n✅ All sections rendered to {OUT_DIR}/")
