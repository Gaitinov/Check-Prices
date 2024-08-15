import logging
import time
from playwright.sync_api import sync_playwright


def setup_driver_ozon(url, max_attempts=3):
    attempt = 0
    while attempt < max_attempts:
        try:
            logging.info("Attempt from Ozon %s: Driver launched", attempt + 1)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True,
                                                     args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(
                    viewport={"width": 1280, "height": 1024},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                page.goto(url, timeout=45000)
                page.wait_for_load_state("networkidle", timeout=60000)
                page.wait_for_timeout(10000)

                if page.is_visible("button#reload-button"):
                    logging.info("Reload button is visible, clicking.")
                    page.click("button#reload-button")
                    page.wait_for_load_state("networkidle", timeout=60000)

                page.wait_for_timeout(5000)
                stock_status = page.is_visible('[data-widget="webOutOfStock"]')
                if stock_status:
                    return "webOutOfStock"
                page.wait_for_timeout(10000)

                html = page.content()
                logging.info("Data from Ozon retrieved.")
                return html
        except Exception as e:
            logging.error(
                "Error occurred while fetching data from Ozon on attempt %s: %s",
                attempt + 1,
                str(e),
            )
            time.sleep(5)
            attempt += 1

    logging.error("All attempts failed. Data from Ozon not retrieved.")
    return None
