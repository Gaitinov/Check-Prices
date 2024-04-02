import logging
import time
from playwright.sync_api import sync_playwright


def setup_driver_kaspi(url, max_attempts=3):
    attempt = 0
    while attempt < max_attempts:
        try:
            logging.info("Attempt from Kaspi %s: Driver launched", attempt + 1)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.goto(url, timeout=50000)
                page.wait_for_load_state("networkidle")
                html = page.content()
                logging.info("Data from Kaspi retrieved.")
                return html
        except Exception as e:
            logging.error("Error occurred while fetching data from Kaspi: %s", str(e))
            time.sleep(5)
            attempt += 1
    logging.error("All attempts failed. Data from Kaspi not retrieved.")
    return None
