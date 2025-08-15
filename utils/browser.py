# scraper/utils/browser.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scraper.config import SELENIUM_DRIVER_PATH, HEADLESS

def init_driver():
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(executable_path=SELENIUM_DRIVER_PATH, options=chrome_options)
    return driver

