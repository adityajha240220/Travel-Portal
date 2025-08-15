from playwright.sync_api import sync_playwright
import time

def fetch_html(url: str, headless=True, timeout=30000, retries=3):
    """
    Fetch HTML from a given URL using Playwright with better error handling, 
    retries, and JS-rendered page support.
    """
    attempt = 0
    while attempt < retries:
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=headless)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/114.0.0.0 Safari/537.36" 
                    ),
                    viewport={"width": 1366, "height": 768}
                )
                page = context.new_page()

                # Navigate with proper wait for network idle
                page.goto(url, timeout=timeout)
                page.wait_for_load_state('networkidle')

                html = page.content()

                browser.close()
                return html

        except Exception as e:
            print(f"[Attempt {attempt + 1}/{retries}] Error fetching {url}: {e}")
            attempt += 1
            time.sleep(2)  # Small delay before retry

    return None
