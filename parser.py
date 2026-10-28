import playwright,os
import bs4
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

URL = os.getenv("URL")
USER_DATA_DIR = os.getenv("USER_DATA_DIR")

with sync_playwright() as p:
    # Открытие браузера с launch_persistent_context значит, что мы сохраняем сессии между собой.
    # Нужно чтобы не логиниться каждый раз по новой 
    browser = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False)
    # Это потом замениться на логику получения html или чет другое
    page = browser.new_page()
    page.goto(URL)
    content = page.content()
    page.wait_for_timeout(500)
    locators = page.locator("a.bkk_p").all()
    for locator in locators:
        print("="*50)
        print(locator.locator("text-content").inner_text())
        print("https://v5.animelib.org" + locator.get_attribute("href"))
        
    

    browser.close()
    
    
 
