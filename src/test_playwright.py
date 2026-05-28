"""Test whether Playwright can bypass IMF's Akamai bot protection."""

from playwright.sync_api import sync_playwright


def main() -> None:
    """Open an IMF country page with a real browser and check the result."""
    url = "https://www.imf.org/en/countries/GRC"

    with sync_playwright() as p:
        # Launch a real Chromium browser (headless = no visible window)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating to {url} ...")
        page.goto(url, timeout=60000)

        # Wait a moment for any JS / bot checks to complete
        page.wait_for_timeout(3000)

        # Get the page title and content length
        title = page.title()
        content = page.content()

        print(f"\n--- Result ---")
        print(f"Page title: {title}")
        print(f"HTML length: {len(content):,} characters")

        # Check if we got blocked or got real content
        if "Access Denied" in content or len(content) < 5000:
            print("STATUS: Likely BLOCKED")
        else:
            print("STATUS: Likely SUCCESS")
            # Count how many "Article IV" mentions appear
            count = content.count("Article IV")
            print(f"'Article IV' mentions on page: {count}")

        browser.close()


if __name__ == "__main__":
    main()