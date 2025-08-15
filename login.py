import os
import json
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

# Cargar .env
load_dotenv()
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")

# Configurar Chrome
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--headless=new")  # Opcional

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

COOKIES_FILE = "cookies.json"

def save_cookies(driver):
    with open(COOKIES_FILE, "w") as f:
        json.dump(driver.get_cookies(), f)

def load_cookies(driver):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        return True
    return False

def fb_login():
    """Inicia sesión en Facebook y guarda cookies"""
    driver.get("https://www.facebook.com/login")
    time.sleep(2)

    # Campo email
    email_input = driver.find_element(By.ID, "email")
    email_input.clear()
    email_input.send_keys(FB_EMAIL)

    # Campo password
    pass_input = driver.find_element(By.ID, "pass")
    pass_input.clear()
    pass_input.send_keys(FB_PASSWORD)
    pass_input.send_keys(Keys.RETURN)

    time.sleep(5)
    save_cookies(driver)
    print("[+] Sesión iniciada y cookies guardadas")

def ensure_logged_in():
    driver.get("https://www.facebook.com")
    if load_cookies(driver):
        driver.refresh()
        time.sleep(3)
        try:
            driver.find_element(By.XPATH, "//a[contains(@href,'/me/')]")
            print("[+] Sesión restaurada desde cookies")
            return
        except NoSuchElementException:
            print("[-] Cookies inválidas o expiradas, iniciando login manual...")
    fb_login_interactivo()


def fb_login_interactivo():
    """Login manual/automático y guardado de cookies"""
    driver.get("https://www.facebook.com/login")
    time.sleep(10)  # tiempo para rellenar manualmente si hay captcha

    # Si tenemos credenciales en .env, las usamos automáticamente
    if FB_EMAIL and FB_PASSWORD:
        try:
            email_input = driver.find_element(By.ID, "email")
            pass_input = driver.find_element(By.ID, "pass")

            email_input.clear()
            email_input.send_keys(FB_EMAIL)
            pass_input.clear()
            pass_input.send_keys(FB_PASSWORD)
            pass_input.send_keys(Keys.RETURN)

            time.sleep(5)
        except Exception as e:
            print(f"[-] No se pudo loguear automáticamente: {e}")

    input("[*] Si hubo captcha/MFA, complétalo y presiona ENTER aquí...")
    save_cookies(driver)
    print("[+] Cookies guardadas para la próxima sesión")


# ---- Uso ----
ensure_logged_in()

# Aquí seguiría tu scraping...
print("[*] Listo para scrapear")


