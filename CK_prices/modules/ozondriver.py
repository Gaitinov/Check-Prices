import logging
import time
from playwright.sync_api import sync_playwright


def setup_driver_ozon(url, max_attempts=3):
    attempt = 0
    while attempt < max_attempts:
        try:
            logging.info(f"Attempt {attempt + 1}: Driver launched")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.goto(url, timeout=45000)
                page.wait_for_load_state("networkidle")

                if page.is_visible("button#reload-button"):
                    logging.info("Reload button is visible, clicking.")
                    page.click("button#reload-button")

                if not page.wait_for_selector(
                    "#section-description", state="attached", timeout=50000
                ):
                    logging.error(
                        "Timeout error: '#section-description' selector not found within the given timeframe."
                    )
                    raise Exception("Selector '#section-description' not found")

                # Ensuring the targeted section is in view
                page.eval_on_selector(
                    "#section-description", "element => element.scrollIntoView()"
                )
                html = page.content()
                return html
        except Exception as e:
            logging.error(
                f"Error occurred while fetching data from Ozon on attempt {attempt + 1}: {str(e)}"
            )
            time.sleep(5)
            attempt += 1

    logging.error("All attempts failed. Data not retrieved.")
    return None
