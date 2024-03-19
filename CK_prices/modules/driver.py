import logging
import time
from playwright.sync_api import sync_playwright

def setup_driver(url, max_attempts=3):
    attempt = 0
    while attempt < max_attempts:
        try:
            logging.info(f"Попытка {attempt + 1} запуска драйвера")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.goto(url, timeout=50000)
                page.wait_for_load_state("networkidle")
                html = page.content()
                return html
        except Exception as e:
            logging.error(f"Произошла ошибка при попытке получить данные с kaspi: {e}")
            time.sleep(5)
            attempt += 1
    logging.error("Превышено количество попыток запуска драйвера")
    return None
