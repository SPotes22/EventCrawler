# scraper/main.py
from scraper.sites.facebook import scrape_facebook
from scraper.utils.filters import filtrar_por_fecha

if __name__ == "__main__":
    print("[*] Iniciando scraping...")
    eventos_fb = scrape_facebook("conciertos Pereira")
    eventos_fb_filtrados = filtrar_por_fecha(eventos_fb)

    print(f"[+] Eventos encontrados: {len(eventos_fb_filtrados)}")
    for e in eventos_fb_filtrados:
        print(e)

