import logging
import time
from playwright.sync_api import sync_playwright


def setup_driver_kaspi(url, max_attempts=3):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"

    for attempt in range(1, max_attempts + 1):
        try:
            logging.info(f"Kaspi attempt {attempt}/{max_attempts}")
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--start-maximized"
                    ]
                )

                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1366, "height": 768},
                    locale="ru-RU"
                )

                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                    window.chrome = {
                        runtime: {},
                    };
                """)

                page = context.new_page()

                page.on("dialog", lambda dialog: dialog.dismiss())

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=80000)
                    page.wait_for_selector("body", state="attached", timeout=20000)

                    for selector in ['div.popup', 'button.close', 'div.cookie-banner']:
                        try:
                            page.click(selector, timeout=3000)
                        except:
                            pass

                    page.wait_for_function("""() => {
                        return document.querySelector('h1.item__heading') && 
                               document.querySelector('div.sellers-table');
                    }""", timeout=45000)

                    return page.content()

                except Exception as nav_error:
                    logging.error(f"Navigation error: {str(nav_error)}")
                    raise

        except Exception as e:
            logging.error(f"Attempt {attempt} failed: {str(e)}")
            time.sleep(10 + attempt * 2)

    logging.error("All Kaspi attempts exhausted")
    return None