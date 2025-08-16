import time
import csv
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================
# CONFIGURACIÓN
# ============================
load_dotenv()
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")
FACEBOOK_EMAIL = FB_EMAIL
FACEBOOK_PASS =  FB_PASSWORD
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"
OUTPUT_FILE = "eventos.csv"

# Keywords
KEYWORDS = ["concierto", "feria", "conmemoriacion", "tributo", "fumaton"]
CITIES = ["pereira", "santarosa", "dosquebradas"]

# === SELENIUM OPTIONS ===
chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)


def login_facebook():
    driver.get("https://www.facebook.com/")
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        pass_input = driver.find_element(By.ID, "pass")
        email_input.send_keys(FACEBOOK_EMAIL)
        pass_input.send_keys(FACEBOOK_PASS)
        pass_input.send_keys(Keys.RETURN)
        print("✅ Login exitoso")
        time.sleep(5)
    except Exception as e:
        print("⚠️ Ya estabas logueado o falló login:", e)


def scroll_until_end():
    """Hace scroll hasta que aparece 'End of results'."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(3)

        try:
            end_text = driver.find_element(By.XPATH, "//span[contains(text(),'End of results')]")
            if end_text:
                print("📍 Llegamos al final de resultados.")
                break
        except:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def scrape_events():
    eventos = []
    event_blocks = driver.find_elements(By.XPATH, "//div[contains(@class,'x1qjc9v5')]")

    for block in event_blocks:
        try:
            dia = block.find_element(By.XPATH, ".//span/span").text
        except:
            dia = ""

        try:
            nombre = block.find_element(By.XPATH, ".//a").text
            enlace = block.find_element(By.XPATH, ".//a").get_attribute("href")
        except:
            nombre = ""
            enlace = ""

        try:
            desc = block.find_element(By.XPATH, ".//span[contains(@class,'x4zkp8e')]").text
        except:
            desc = ""

        if nombre:
            print(f"📌 Copiado evento: {nombre}")
            eventos.append([dia, nombre, desc, enlace])
    return eventos


# === MAIN ===
login_facebook()

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["DIA", "NOMBRE_EVENTO", "DESCRIPCION", "ENLACE"])

    for kw in KEYWORDS:
        for city in CITIES:
            url = f"https://www.facebook.com/search/events?q={kw}%20{city}"
            print(f"\n🔎 Buscando: {kw} en {city}")
            driver.get(url)

            # Esperar filtro "Events"
            try:
                filtro = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Events']")))
                filtro.click()
                time.sleep(3)
            except:
                print("⚠️ No encontré filtro 'Events'")

            # Scroll hasta fin
            scroll_until_end()

            # Scrape
            eventos = scrape_events()
            writer.writerows(eventos)

driver.quit()
print(f"\n✅ Scraping terminado. Guardado en {OUTPUT_FILE}")

