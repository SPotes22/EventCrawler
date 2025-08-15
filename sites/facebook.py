# scraper/sites/facebook.py
from scraper.utils.browser import init_driver
from time import sleep

def scrape_facebook(query="eventos en Pereira"):
    driver = init_driver()
    eventos = []

    try:
        driver.get(f"https://www.facebook.com/search/events?q={query}")
        sleep(5)  # Esperar que cargue (luego optimizar con WebDriverWait)

        # TODO: Ajustar selectores reales según layout actual
        cards = driver.find_elements("css selector", "[data-testid='event_card']")
        for card in cards:
            try:
                nombre = card.find_element("css selector", ".event-name").text
                fecha = card.find_element("css selector", ".event-date").text
                descripcion = card.find_element("css selector", ".event-description").text
                costo = "No especificado"  # FB casi nunca lo pone
                redes = driver.current_url

                eventos.append({
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "fecha": fecha,
                    "costo": costo,
                    "redes": redes
                })
            except:
                continue
    finally:
        driver.quit()

    return eventos

