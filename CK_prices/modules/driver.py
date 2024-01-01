import logging
from playwright.sync_api import sync_playwright
import time as tm

def setup_driver(url):
    try:
        logging.info('Драйвер запушен')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url)
            tm.sleep(5)
            html = page.content()
            return html
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")

