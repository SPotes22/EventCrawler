<!-- hash:bfa3279fdea5bae37a1262f2ff7d9460fed247fca31222dfaf1c49440f5ce3ac -->
<!-- stack:generic -->
# 📋 Code Review: fb_search.py

**Archivo:** `fb_search.py`
**Stack:** GENERIC
**Fecha:** 2025-08-17 18:10:47
**Líneas de código:** 229
**Tokens utilizados:** 4257

---

```python
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

OUTPUT_FILE = "eventos_fb.csv"
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
    for idx, block in enumerate(blocks):
        try:
            title_element = block.find_element(By.XPATH, ".//a[@aria-label]")
            title = title_element.get_attribute("aria-label")

            link_element = block.find_element(By.XPATH, ".//a[@href and contains(@href, 'eid=')]")
            link = link_element.get_attribute("href")

            eventos.append({"title": title, "link": link})
            print(f"✅ Evento {idx + 1}: {title}")
        except Exception as e:
            print(f"⚠️ Error al extraer evento {idx + 1}: {e}")
    return eventos


def scrape_layout_a():
    eventos = []
    blocks = driver.find_elements(By.XPATH, "//div[contains(@class,'du4w35lb')]")
    print(f"🔎 Layout A detectado → {len(blocks)} bloques encontrados")
    for idx, block in enumerate(blocks):
        try:
            title_element = block.find_element(By.XPATH, ".//a[@aria-label]")
            title = title_element.get_attribute("aria-label")

            link_element = block.find_element(By.XPATH, ".//a[@href and contains(@href, 'eid=')]")
            link = link_element.get_attribute("href")

            eventos.append({"title": title, "link": link})
            print(f"✅ Evento {idx + 1}: {title}")
        except Exception as e:
            print(f"⚠️ Error al extraer evento {idx + 1}: {e}")
    return eventos


def scrape_events():
    # Intenta el Layout B primero, si no encuentra nada, intenta Layout A
    eventos = scrape_layout_b()
    if not eventos:
        eventos = scrape_layout_a()
    return eventos


# ============================
# SEARCH
# ============================
def search_and_scrape(keyword, city):
    search_query = f"{keyword} en {city}"
    print(f"🔎 Buscando: {search_query}")
    driver.get(f"https://www.facebook.com/search/events/?q={search_query}")
    time.sleep(5)  # Espera a que cargue la página

    scroll_until_end()
    eventos = scrape_events()
    return eventos


# ============================
# CSV
# ============================
def write_to_csv(eventos, filename=OUTPUT_FILE):
    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "link", "keyword", "city"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Escribir encabezado solo si el archivo está vacío
        if csvfile.tell() == 0:
            writer.writeheader()

        for evento in eventos:
            writer.writerow(evento)


# ============================
# MAIN
# ============================
def main():
    login_facebook()
    all_events = []
    for keyword in KEYWORDS:
        for city in CITIES:
            events = search_and_scrape(keyword, city)
            # Añadir keyword y city a cada evento para el CSV
            for event in events:
                event["keyword"] = keyword
                event["city"] = city
            all_events.extend(events)

    write_to_csv(all_events)
    print(f"✅ Se encontraron {len(all_events)} eventos y se guardaron en {OUTPUT_FILE}")
    driver.quit()


if __name__ == "__main__":
    main()
```

### Resumen
El código es un script de scraping web que utiliza Selenium para automatizar la búsqueda de eventos en Facebook basados en una lista de palabras clave y ciudades. Inicia sesión en Facebook, realiza búsquedas, extrae información de los eventos encontrados (título y enlace) y guarda los resultados en un archivo CSV.

### Funcionalidades principales
1.  **Login**: Inicia sesión en Facebook usando credenciales almacenadas en variables de entorno.
2.  **Búsqueda**: Realiza búsquedas de eventos en Facebook combinando palabras clave y ciudades.
3.  **Scroll infinito**: Simula el scroll de la página para cargar más resultados.
4.  **Scraping**: Extrae el título y el enlace de cada evento encontrado. Tiene lógica para adaptarse a dos posibles layouts de Facebook (A y B).
5.  **Guardado en CSV**: Guarda los resultados en un archivo CSV, incluyendo el título del evento, el enlace, la palabra clave y la ciudad.

### Arquitectura y patrones (específicos para generic)
*   **Modularidad**: El código está dividido en funciones lógicas (login, scroll, scraping, search, csv writing), lo que facilita su mantenimiento y reutilización.
*   **Configuración centralizada**: Las configuraciones (credenciales, palabras clave, ciudades, nombre del archivo de salida) se definen al principio del script, lo que facilita su modificación.  Usa `dotenv` para gestionar las credenciales, una práctica recomendada.
*   **Manejo de errores**: Utiliza bloques `try...except` para manejar posibles errores durante el login y el scraping.
*   **Adaptación a cambios en el layout**: Implementa dos scrapers (`scrape_layout_a` y `scrape_layout_b`) y una lógica para determinar cuál usar (`scrape_events`). Esto intenta mitigar el impacto de los cambios en la estructura HTML de Facebook.
*   **Separación de responsabilidades:** Cada función tiene una tarea específica.  Por ejemplo, `create_driver` solo crea el driver de Selenium, `login_facebook` solo se encarga del login, etc.

### Posibles mejoras
1.  **Manejo de excepciones más robusto**:  En los bloques `except`, sería útil registrar el error en un archivo de log y continuar con el proceso, en lugar de simplemente imprimirlo. Esto permitiría una mejor depuración y evitaría que el script se detenga por errores inesperados.
2.  **Refactorización de `scrape_events`**:  La función `scrape_events` es un ejemplo de  *Feature Envy*.  Debería haber una función general para encontrar los bloques, y las funciones `scrape_layout_a` y `scrape_layout_b` deberían enfocarse en la extracción de datos *dentro* de esos bloques.
3.  **Mejorar la detección del "fin de resultados"**: El scroll infinito actual se basa en detectar el "End of results" o en detectar que la altura de la página no cambia.  Estos métodos no son muy confiables.  Podría ser mejor implementar un sistema de paginación (si Facebook lo permite) o un sistema que detecte si se han cargado nuevos eventos en un cierto periodo de tiempo.
4.  **Paralelización**: El script podría ser más rápido si se paralelizaran las búsquedas (por ejemplo, usando `multiprocessing` o `threading`). Esto permitiría buscar en múltiples ciudades y con múltiples palabras clave al mismo tiempo.
5.  **Uso de proxies**:  Para evitar ser bloqueado por Facebook, se podría usar una lista de proxies rotatorios.
6.  **Configuración más flexible**: Considerar usar un archivo de configuración (YAML o JSON) para almacenar las palabras clave, ciudades y otras opciones de configuración. Esto facilitaría la modificación de la configuración sin necesidad de editar el código.
7.  **Implementar un sistema de reintentos**: Si una búsqueda falla (por ejemplo, debido a un error de red), se podría implementar un sistema de reintentos automáticos.
8.  **Agregar logging**: Implementar un sistema de logging adecuado en lugar de solo `print` statements. Esto haría que la depuración y el monitoreo del script sean mucho más fáciles.
9.  **Más inteligencia en la detección de layouts**: Facebook puede cambiar su layout con frecuencia.  Una alternativa a tener scrapers específicos para layouts A y B sería usar un modelo de machine learning para detectar el layout y adaptar el scraping dinámicamente.  Esto sería una mejora mucho más compleja, pero también mucho más robusta.
10. **Watchdog Timer**: Incluir un watchdog timer para la espera manual del 2FA. Si el usuario no completa el 2FA en un tiempo razonable (definido en la variable `WATCHDOG_TIMEOUT`), el script debe terminar, previniendo bloqueos indefinidos.

### Problemas de seguridad
1.  **Almacenamiento de credenciales**: Aunque las credenciales se cargan desde variables de entorno, es importante asegurarse de que estas variables de entorno no se almacenen en el código fuente ni se compartan accidentalmente. Es crucial tener cuidado al versionar el código y al desplegarlo.
2.  **Posible bloqueo por Facebook**: Facebook puede detectar y bloquear el script si se realizan demasiadas solicitudes en un corto período de tiempo.  El uso de proxies y la implementación de un retraso aleatorio entre las solicitudes pueden ayudar a mitigar este riesgo.
3.  **Vulnerabilidades de Selenium**:  Es importante mantener Selenium y el driver del navegador actualizados para evitar posibles vulnerabilidades de seguridad.

### Recomendaciones para GENERIC
1.  **Abstracción de scrapers**:  Crear una clase base abstracta `Scraper` con métodos para `login`, `scroll`, `extract_data`, y una clase hija para cada sitio web que se desea scrapear.  Esto facilita la adición de nuevos sitios web.
2.  **Sistema de plugins**:  Implementar un sistema de plugins para los scrapers.  Esto permitiría a los usuarios agregar sus propios scrapers sin necesidad de modificar el código principal.
3.  **Interfaz de usuario**:  Proporcionar una interfaz de usuario (GUI o CLI) para configurar las búsquedas, las credenciales y otras opciones.
4.  **Sistema de colas de mensajes**:  Utilizar un sistema de colas de mensajes (por ejemplo, RabbitMQ o Celery) para distribuir las tareas de scraping entre múltiples máquinas.  Esto permitiría escalar el script para scrapear grandes cantidades de datos.
5.  **Orquestación de contenedores**:  Empaquetar el script en un contenedor Docker y utilizar un sistema de orquestación de contenedores (por ejemplo, Kubernetes) para gestionarlo. Esto facilita el despliegue y la gestión del script en un entorno de producción.
6.  **Monitorización**:  Implementar un sistema de monitorización para supervisar el script y detectar posibles problemas.  Esto podría incluir la monitorización del uso de la CPU, el uso de la memoria, el tiempo de ejecución, y la tasa de errores.
7.  **Sistema de alertas**:  Implementar un sistema de alertas para notificar a los usuarios cuando ocurran errores o cuando el script detecte algo inusual.
8.  **Versionado de la API de scraping**:  Almacenar el XPATH selector en una base de datos con versionado. Crear una capa API que gestione el scraper para evitar despliegues en caso de que Facebook cambie el DOM.
9. **Integración con servicios de resolución de CAPTCHAs**: Implementar la resolución automática de CAPTCHAs utilizando servicios como 2Captcha o Anti-Captcha para evitar interrupciones en el proceso de scraping.

En resumen, el código proporcionado es un buen punto de partida para un proyecto de scraping web.  Implementando las mejoras y recomendaciones mencionadas, se puede convertir en una solución robusta, escalable y fácil de mantener.


---
✅ Sin cambios significativos - Última revisión 2025-08-17 18:13:08

---
✅ Sin cambios significativos - Última revisión 2025-08-17 18:13:37