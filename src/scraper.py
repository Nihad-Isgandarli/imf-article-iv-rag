"""Download IMF Article IV consultation PDFs from imf.org.

Reads countries.csv, fetches each country's IMF page,
finds Article IV publication links, and downloads PDFs.
"""

import csv
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
COUNTRIES_CSV = DATA_DIR / "countries.csv"


# Browser-like headers to bypass Cloudflare bot protection
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


def make_session() -> requests.Session:
    """Create a requests Session with browser-like headers."""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def load_countries() -> list[dict]:
    """Read countries.csv and return list of country dicts."""
    with open(COUNTRIES_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fetch_country_page(session: requests.Session, iso3: str) -> str | None:
    """Fetch an IMF country page and return its HTML."""
    url = f"https://www.imf.org/en/countries/{iso3}"
    print(f"  Fetching {url}")
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  ERROR fetching {iso3}: {e}")
        return None


def main() -> None:
    """Test the scraper on the first country in countries.csv."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    countries = load_countries()
    print(f"Loaded {len(countries)} countries from CSV")
    print(f"First country: {countries[0]}")

    # For now, just test fetching the first country's page
    session = make_session()
    first = countries[0]
    print(f"\nTesting fetch for {first['country']} ({first['iso3']})...")

    html = fetch_country_page(session, first["iso3"])
    if html:
        print(f"  SUCCESS: got {len(html):,} characters of HTML")
        print(f"  First 200 chars: {html[:200]}")
    else:
        print(f"  FAILED")


if __name__ == "__main__":
    main()