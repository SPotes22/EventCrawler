import time
import csv
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================
# CONFIG
# ============================
load_dotenv()
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")

OUTPUT_FILE = "eventos.csv"
KEYWORDS = ["concierto", "feria", "conmemoriacion", "tributo", "fumaton"]
CITIES = ["pereira", "santarosa", "dosquebradas"]

WATCHDOG_TIMEOUT = 30  

# ============================
# SELENIUM SETUP
# ============================
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    return webdriver.Chrome(options=chrome_options)

driver = create_driver()
wait = WebDriverWait(driver, 15)


# ============================
# LOGIN
# ============================
def login_facebook():
    driver.get("https://www.facebook.com/")
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        pass_input = driver.find_element(By.ID, "pass")
        email_input.send_keys(FB_EMAIL)
        pass_input.send_keys(FB_PASSWORD)
        pass_input.send_keys(Keys.RETURN)
        print("✅ Login exitoso")
        time.sleep(8)

        # Si pide 2FA → esperar intervención manual
        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(),'Inicio') or contains(text(),'Home')]")
                ),
                60,
            )
        except:
            print("⚠️ Esperando que completes 2FA manualmente...")
            time.sleep(60)
    except Exception as e:
        print("⚠️ Ya estabas logueado o falló login:", e)


# ============================
# SCROLL
# ============================
def scroll_until_end():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(3)

        try:
            driver.find_element(By.XPATH, "//span[contains(text(),'End of results')]")
            print("📍 Fin de resultados detectado")
            break
        except:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("📍 No crece el scroll, detenemos")
            break
        last_height = new_height


# ============================
# SCRAPERS
# ============================
def scrape_layout_b():
    eventos = []
    blocks = driver.find_elements(By.XPATH, "//div[contains(@class,'x1qjc9v5')]")
    print(f"🔎 Layout B detectado → {len(blocks)} bloques encontrados")
    for idx, block in enumerate(blocks, start=1):
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
            print(f"   ➡️ [{idx}] {nombre}")
            eventos.append([dia, nombre, desc, enlace])
    return eventos


def scrape_layout_c():
    eventos = []
    cards = driver.find_elements(By.XPATH, "//div[contains(@class,'x1xmf6yo')]")
    print(f"🔎 Layout C detectado → {len(cards)} tarjetas encontradas")
    for idx, card in enumerate(cards, start=1):
        try:
            dia = card.find_element(By.XPATH, ".//span").text
        except:
            dia = ""

        try:
            nombre = card.find_element(By.XPATH, ".//strong").text
            enlace = card.find_element(By.XPATH, ".//a").get_attribute("href")
        except:
            nombre = ""
            enlace = ""

        try:
            desc = card.find_element(By.XPATH, ".//div[contains(@class,'x1iorvi4')]").text
        except:
            desc = ""

        if nombre:
            print(f"   ➡️ [{idx}] {nombre}")
            eventos.append([dia, nombre, desc, enlace])
    return eventos


def detect_layout():
    try:
        driver.find_element(By.XPATH, "//span[text()='Events']")
        return "B"
    except:
        pass
    try:
        driver.find_element(By.XPATH, "//div[contains(@class,'x1xmf6yo')]")
        return "C"
    except:
        return "UNKNOWN"


# ============================
# WATCHDOG (auto retry)
# ============================
last_activity_time = time.time()
retry_count = 0

def update_watchdog():
    global last_activity_time
    last_activity_time = time.time()

def check_watchdog():
    return time.time() - last_activity_time > WATCHDOG_TIMEOUT

def restart_driver():
    global driver, wait, retry_count
    retry_count += 1
    try:
        driver.quit()
    except:
        pass
    print(f"🔄 Reiniciando driver... (intentos: {retry_count})")
    driver = create_driver()
    wait = WebDriverWait(driver, 15)
    login_facebook()


# ============================
# MAIN
# ============================
login_facebook()
total_eventos = 0

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["DIA", "NOMBRE_EVENTO", "DESCRIPCION", "ENLACE"])

    for kw in KEYWORDS:
        for city in CITIES:
            print(f"\n🚀 Buscando: {kw} en {city} | Reintentos: {retry_count} | Eventos acumulados: {total_eventos}")
            url = f"https://www.facebook.com/search/events?q={kw}%20{city}"
            driver.get(url)
            time.sleep(5)

            layout = detect_layout()
            print(f"👉 Detectado layout: {layout}")

            if layout == "B":
                scroll_until_end()
                eventos = scrape_layout_b()
            elif layout == "C":
                eventos = scrape_layout_c()
            else:
                print("⚠️ Layout no reconocido, skip.")
                eventos = []

            for ev in eventos:
                update_watchdog()
                writer.writerow(ev)
                total_eventos += 1

            # watchdog
            if check_watchdog():
                print("⏰ 30s sin actividad → reiniciando driver/login...")
                restart_driver()

driver.quit()
print(f"\n✅ Scraping terminado. Guardado en {OUTPUT_FILE} | Total eventos: {total_eventos} | Reintentos: {retry_count}")

