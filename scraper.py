import os
import time
import csv
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import pickle

# ============================
# CONFIGURACIÓN
# ============================
load_dotenv()
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")
COOKIES_FILE = "fb_cookies.pkl"
CSV_FILE = "eventos_fb.csv"

# Inicializar driver
driver = webdriver.Chrome()

# ============================
# FUNCIONES DE SESIÓN
# ============================
def save_cookies(driver):
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver):
    if not os.path.exists(COOKIES_FILE):
        return False
    with open(COOKIES_FILE, "rb") as f:
        cookies = pickle.load(f)
    driver.get("https://www.facebook.com")
    for cookie in cookies:
        driver.add_cookie(cookie)
    return True

def fb_login_interactivo():
    driver.get("https://www.facebook.com/login")
    time.sleep(5)

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

    input("[*] Si hay captcha/MFA, complétalo y presiona ENTER aquí...")
    save_cookies(driver)
    print("[+] Cookies guardadas para la próxima sesión")

def ensure_logged_in():
    if load_cookies(driver):
        driver.refresh()
        time.sleep(3)
        try:
            driver.find_element(By.XPATH, "//a[contains(@href,'/me/')]")
            print("[+] Sesión restaurada desde cookies")
            return
        except NoSuchElementException:
            print("[-] Cookies inválidas o expiradas, iniciando login...")
    fb_login_interactivo()

# ============================
# FUNCIONES DE SCRAPEO
# ============================
def limpiar_titulo(t):
    if not t:
        return ""
    t = t.strip()
    if t.lower().startswith("profile photo of "):
        t = t[len("profile photo of "):]
    return t

def scrape_eventos():
    eventos = []
    # 🔹 Aquí pegas tu URL de búsqueda de eventos de Facebook
    driver.get("https://www.facebook.com/events/search/?q=concierto%20pereira")
    time.sleep(5)

    cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/events/')]")
    for c in cards:
        try:
            titulo = limpiar_titulo(c.text.split("\n")[0])
            fecha = ""
            lugar = ""
            enlace = c.get_attribute("href")

            partes = c.text.split("\n")
            if len(partes) >= 2:
                fecha = partes[1]
            if len(partes) >= 3:
                lugar = partes[2]

            eventos.append({
                "Título": titulo,
                "Fecha": fecha,
                "Lugar": lugar,
                "Enlace": enlace
            })
        except Exception as e:
            print(f"[-] Error procesando card: {e}")

    return eventos

# ============================
# GUARDAR CSV
# ============================
def guardar_csv(eventos):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Título", "Fecha", "Lugar", "Enlace"])
        writer.writeheader()
        for e in eventos:
            e["Título"] = limpiar_titulo(e["Título"])
            writer.writerow(e)
    print(f"[+] {len(eventos)} eventos guardados en {CSV_FILE}")

# ============================
# MAIN
# ============================
if __name__ == "__main__":
    ensure_logged_in()
    eventos = scrape_eventos()
    guardar_csv(eventos)
    driver.quit()

