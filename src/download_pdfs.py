"""Download Article IV PDFs from IMF publication pages.

Reads data/article_iv_links.csv (one row per publication page),
visits each page with Playwright, finds the PDF download link,
and saves it to data/raw/{country}_{year}.pdf.
"""

import csv
import time
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LINKS_CSV = DATA_DIR / "article_iv_links.csv"


def load_links() -> list[dict]:
    with open(LINKS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_filename(country: str, year: str) -> str:
    """Make a clean filename like 'turkey_2018.pdf'."""
    clean = country.lower().replace(" ", "_")
    return f"{clean}_{year}.pdf"


def find_pdf_url(page) -> str | None:
    """Find the main PDF download URL on a publication page."""
    # IMF publication pages have anchor tags pointing to .pdf files
    # We pick the first one that looks like the staff report
    links = page.eval_on_selector_all(
        "a",
        """elements => elements.map(el => ({text: el.innerText.trim(), href: el.href}))"""
    )
    for link in links:
        href = link["href"]
        if href and href.lower().endswith(".pdf"):
            return href
    return None


def download_pdf(context, pdf_url: str, out_path: Path) -> bool:
    """Use Playwright's request API to download a PDF (passes Akamai)."""
    try:
        response = context.request.get(pdf_url, timeout=60000)
        if response.ok:
            out_path.write_bytes(response.body())
            return True
        else:
            print(f"      HTTP {response.status}")
            return False
    except Exception as e:
        print(f"      ERROR: {e}")
        return False


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_links()
    print(f"Loaded {len(rows)} publication links")

    success = 0
    failed = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for i, row in enumerate(rows, 1):
            country, year, url = row["country"], row["year"], row["url"]
            out_path = RAW_DIR / safe_filename(country, year)

            # Skip if already downloaded
            if out_path.exists():
                print(f"[{i}/{len(rows)}] {country} {year}: already exists, skipping")
                success += 1
                continue

            print(f"[{i}/{len(rows)}] {country} {year}: visiting page...")
            try:
                page.goto(url, timeout=60000)
                page.wait_for_timeout(3000)

                pdf_url = find_pdf_url(page)
                if not pdf_url:
                    print(f"      no PDF link found")
                    failed.append((country, year, "no PDF link"))
                    continue

                print(f"      downloading {pdf_url[-60:]}")
                if download_pdf(context, pdf_url, out_path):
                    size_kb = out_path.stat().st_size // 1024
                    print(f"      saved ({size_kb} KB)")
                    success += 1
                else:
                    failed.append((country, year, "download failed"))
            except Exception as e:
                print(f"      ERROR: {e}")
                failed.append((country, year, str(e)[:80]))

            time.sleep(1.5)  # be polite to imf.org

        browser.close()

    print(f"\n=== Summary ===")
    print(f"Success: {success} / {len(rows)}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for c, y, reason in failed:
            print(f"  {c} {y}: {reason}")


if __name__ == "__main__":
    main()