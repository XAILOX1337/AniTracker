import playwright,os
import bs4
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin 

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
    page.wait_for_selector("div.fade-2")
    locators = page.locator("div.fade-2").all()
    # Перебор всех div'ов с ссылками на "уведомляемые" тайтлы
    for locator in locators:
        print("="*50)
        print(locator.locator("a").inner_text())
        # Поиск тега "a", в котором есть ссылка 
        href = locator.locator("a").get_attribute("href")
        # Склейка ссылки для избежания ошибок с "+"
        print(urljoin("https://v5.animelib.org", href)) 
        
    

    browser.close()
    
    
 
