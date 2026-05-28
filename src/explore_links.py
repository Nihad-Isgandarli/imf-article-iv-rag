"""Collect Article IV links via IMF search with 50 results/page, then
filter by country name in the URL and by target year range.
"""

import csv
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
URL_SLUG_VARIANTS = {
    "Turkey": ["turkey", "turkiye"],
    "Argentina": ["argentina"],
    "Sri Lanka": ["sri-lanka"],
    "Lebanon": ["lebanon"],
    "Zambia": ["zambia"],
    "Pakistan": ["pakistan"],
    "Ghana": ["ghana"],
    "Egypt": ["egypt", "arab-republic-of-egypt"],
    "Ecuador": ["ecuador"],
    "Switzerland": ["switzerland"],
    "Canada": ["canada"],
    "Korea": ["korea", "republic-of-korea"],
    "Poland": ["poland", "republic-of-poland"],
    "Malaysia": ["malaysia"],
}


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COUNTRIES_CSV = DATA_DIR / "countries.csv"
LINKS_CSV = DATA_DIR / "article_iv_links.csv"


def load_countries() -> list[dict]:
    with open(COUNTRIES_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extract_year(url: str) -> str | None:
    """Extract the Article IV year from the URL slug."""
    m = re.search(r"/([a-z-]+)-(\d{4})-article-iv", url.lower())
    if m:
        return m.group(2)
    return None


def url_matches_country(url: str, country: str) -> bool:
    """Check the URL contains any of this country's known slug variants."""
    url_lower = url.lower()
    variants = URL_SLUG_VARIANTS.get(country, [country.lower().replace(" ", "-")])
    for slug in variants:
        if f"/{slug}-" in url_lower:
            return True
    return False


def collect_for_country(page, country: str) -> list[dict]:
    """Search IMF for one country's Article IV reports, 50 per page."""
    query = f"{country} Article IV Consultation".replace(" ", "%20")
    url = (
        "https://www.imf.org/en/publications/search"
        f"?series=IMF%20Staff%20Country%20Reports"
        f"#q={query}&f-country={country.replace(' ', '%20')}"
        f"&cf-type=COUNTRYREPS,ARTICLE4&sort=date&rows=50"
    )
    print(f"  {country}: searching...")
    page.goto(url, timeout=60000)
    page.wait_for_timeout(8000)

    links = page.eval_on_selector_all(
        "a",
        """elements => elements.map(el => ({text: el.innerText.trim(), href: el.href}))"""
    )

    results = []
    seen = set()
    for link in links:
        href = link["href"]
        if not href or "/cr/issues/" not in href:
            continue
        if "article-iv" not in href.lower():
            continue
        if not url_matches_country(href, country):
            continue
        if href in seen:
            continue
        seen.add(href)
        year = extract_year(href)
        results.append({"country": country, "year": year or "", "url": href})
    return results
def debug_country(page, country: str) -> None:
    """Print ALL Article IV URLs found for a country, no filtering."""
    query = f"{country} Article IV Consultation".replace(" ", "%20")
    url = (
        "https://www.imf.org/en/publications/search"
        f"?series=IMF%20Staff%20Country%20Reports"
        f"#q={query}&f-country={country.replace(' ', '%20')}"
        f"&cf-type=COUNTRYREPS,ARTICLE4&sort=date&rows=50"
    )
    page.goto(url, timeout=60000)
    page.wait_for_timeout(8000)
    links = page.eval_on_selector_all(
        "a",
        """elements => elements.map(el => el.href)"""
    )
    print(f"\n=== {country} ===")
    seen = set()
    for href in links:
        if href and "/cr/issues/" in href and "article-iv" in href.lower():
            if href not in seen:
                seen.add(href)
                print(f"  {href}")


def debug_main() -> None:
    """Debug the countries that returned 0 results."""
    problem_countries = ["Egypt", "Korea", "Poland", "Ukraine", "Canada"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for c in problem_countries:
            debug_country(page, c)
            time.sleep(2)
        browser.close()

def main() -> None:
    countries = load_countries()
    all_links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for c in countries:
            try:
                links = collect_for_country(page, c["country"])
                # Filter by target year range
                y_start, y_end = int(c["year_start"]), int(c["year_end"])
                kept = [l for l in links
                        if l["year"].isdigit() and y_start <= int(l["year"]) <= y_end]
                print(f"    {len(links)} found, {len(kept)} in range {y_start}-{y_end}")
                all_links.extend(kept)
            except Exception as e:
                print(f"    ERROR for {c['country']}: {e}")
            time.sleep(2)

        browser.close()

    with open(LINKS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["country", "year", "url"])
        writer.writeheader()
        writer.writerows(all_links)

    print(f"\n=== Total: {len(all_links)} links in target ranges ===")
    print(f"Saved to {LINKS_CSV}")


if __name__ == "__main__":
    main()
