import logging
from playwright.sync_api import sync_playwright

def setup_driver_ozon(url):
    try:
        logging.info('Драйвер запушен')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url)
            page.wait_for_load_state("networkidle")
            page.click('button#reload-button')
            page.wait_for_selector("#section-description")
            page.eval_on_selector("#section-description", "element => element.scrollIntoView()")
            html = page.content()
            return html
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")

