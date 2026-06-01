"""Fetch Lebanon 2018 Article IV materials.

No staff report PDF exists for Lebanon 2018, so we combine the
Concluding Statement + Press Release into a single PDF.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright
from fpdf import FPDF


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUT_PATH = RAW_DIR / "lebanon_2018.pdf"

URLS = [
    ("Concluding Statement of the 2018 Article IV Mission",
     "https://www.imf.org/en/News/Articles/2018/02/12/ms021218-lebanon-staff-concluding-statement-of-the-2018-article-iv-mission"),
    ("Press Release: Executive Board Concludes 2018 Article IV Consultation",
     "https://www.imf.org/en/news/articles/2018/06/21/pr18250-imf-executive-board-concludes-article-iv-consultation-with-lebanon"),
]


def fetch_text(page, url):
    page.goto(url, timeout=60000)
    page.wait_for_timeout(3000)
    return page.eval_on_selector("body", "el => el.innerText")


def build_pdf(sections, out_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for title, text in sections:
        pdf.set_font("Helvetica", style="B", size=13)
        pdf.multi_cell(0, 8, title)
        pdf.ln(4)
        pdf.set_font("Helvetica", size=11)
        clean = text.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 5, clean)
        pdf.add_page()
    pdf.output(str(out_path))


def main():
    sections = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for title, url in URLS:
            print(f"Fetching: {title}")
            text = fetch_text(page, url)
            print(f"  Got {len(text):,} characters")
            sections.append((title, text))
        browser.close()

    print("\nBuilding PDF...")
    build_pdf(sections, OUT_PATH)
    size_kb = OUT_PATH.stat().st_size // 1024
    print(f"Saved: {OUT_PATH} ({size_kb} KB)")


if __name__ == "__main__":
    main()
