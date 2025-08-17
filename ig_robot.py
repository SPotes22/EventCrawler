from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time, os, csv, re
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sys

# ================================
# Configuración y variables globales
# ================================
load_dotenv()
IG_USER = os.getenv("IG_USER")
IG_PASS = os.getenv("IG_PASS")

class ProgressBar:
    def __init__(self, total_time=600):  # 10 minutos por defecto
        self.total_time = total_time
        self.start_time = time.time()
        self.width = 50
    
    def update(self, current_posts=0, events_found=0):
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.total_time, 1.0)
        filled = int(progress * self.width)
        bar = '█' * filled + '-' * (self.width - filled)
        
        remaining = max(0, self.total_time - elapsed)
        mins, secs = divmod(int(remaining), 60)
        
        sys.stdout.write(f'\r[{bar}] {progress*100:.1f}% | Posts: {current_posts} | Eventos: {events_found} | {mins:02d}:{secs:02d}')
        sys.stdout.flush()
        
        return elapsed >= self.total_time
    
    def finish(self):
        sys.stdout.write('\n')

# ================================
# KEYWORDS PARA DETECTAR EVENTOS
# ================================
EVENT_KEYWORDS = [
    # Tipos de eventos
    'evento', 'concierto', 'festival', 'tributo', 'presentacion', 'presentación',
    'show', 'espectaculo', 'espectáculo', 'función', 'funcion', 'obra',
    'conferencia', 'taller', 'curso', 'seminario', 'exposicion', 'exposición',
    'feria', 'mercado', 'bazar', 'venta', 'lanzamiento', 'estreno',
    'competencia', 'torneo', 'concurso', 'festival', 'fiesta', 'celebracion', 'celebración',
    'encuentro', 'reunion', 'reunión', 'congreso', 'simposio',
    'teatro', 'danza', 'baile', 'musical', 'opera', 'ópera',
    'rock', 'jazz', 'salsa', 'reggae', 'pop', 'vallenato', 'bambuco',
    
    # Palabras de tiempo/programación
    'proximo', 'próximo', 'este', 'mañana', 'hoy', 'viernes', 'sabado', 'sábado', 'domingo',
    'lunes', 'martes', 'miercoles', 'miércoles', 'jueves',
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
    'agenda', 'programacion', 'programación', 'lineup', 'line-up', 'line up',
    'entrada', 'boleta', 'ticket', 'reserva', 'inscripcion', 'inscripción',
    'gratis', 'libre', 'abierto', 'publico', 'público',
    
    # Lugares específicos de Pereira/Risaralda
    'plaza', 'parque', 'coliseo', 'teatro', 'centro', 'salon', 'salón',
    'auditorio', 'estadio', 'polideportivo', 'cultural', 'biblioteca',
    'pereira', 'dosquebradas', 'santa rosa', 'risaralda', 'eje cafetero',
    'plaza civica', 'cívica', 'victoria', 'bolivar', 'bolívar',
    'unicentro', 'megacentro', 'circunvalar'
]

DATE_INDICATORS = [
    # Patrones de fecha
    r'\d{1,2}\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
    r'\d{1,2}/\d{1,2}/\d{2,4}',
    r'\d{1,2}-\d{1,2}-\d{2,4}',
    r'(?:viernes|sábado|sabado|domingo|lunes|martes|miércoles|miercoles|jueves)\s+\d{1,2}',
    r'\d{1,2}\s+(?:y|al)\s+\d{1,2}',
    r'(?:hoy|mañana|manana|este|proximo|próximo)\s+(?:viernes|sábado|sabado|domingo)',
    r'\d{1,2}:\d{2}',  # Horas
    r'\d{1,2}\s*(?:am|pm|AM|PM)'
]

# ================================
# Función para detectar si es un evento
# ================================
def is_event_post(text):
    """Determina si un post contiene información de eventos"""
    if not text or len(text.strip()) < 30:  # Posts muy cortos no son eventos
        return False
    
    text_lower = text.lower()
    
    # Contador de indicadores de evento
    event_score = 0
    
    # 1. Buscar keywords de eventos (peso 2)
    event_keywords_found = sum(1 for keyword in EVENT_KEYWORDS if keyword in text_lower)
    event_score += event_keywords_found * 2
    
    # 2. Buscar patrones de fecha (peso 3)
    date_patterns_found = sum(1 for pattern in DATE_INDICATORS if re.search(pattern, text, re.IGNORECASE))
    event_score += date_patterns_found * 3
    
    # 3. Buscar menciones múltiples (indica colaboración/evento - peso 1)
    mentions = len(re.findall(r'@\w+', text))
    if mentions >= 3:
        event_score += 2
    
    # 4. Buscar hashtags de eventos (peso 2)
    event_hashtags = ['#evento', '#concierto', '#festival', '#show', '#pereira', '#dosquebradas']
    hashtag_score = sum(1 for hashtag in event_hashtags if hashtag in text_lower)
    event_score += hashtag_score * 2
    
    # 5. Palabras de llamada a la acción (peso 1)
    action_words = ['acompañanos', 'acompáñanos', 'ven', 'asiste', 'participa', 'inscribete', 'reserva']
    action_score = sum(1 for word in action_words if word in text_lower)
    event_score += action_score
    
    # Umbral mínimo para considerar que es un evento
    return event_score >= 5

# ================================
# Configuración Selenium
# ================================
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

driver = setup_driver()
wait = WebDriverWait(driver, 15)

# ================================
# Login mejorado
# ================================
def instagram_login():
    print("🔑 Iniciando login en Instagram...")
    
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        wait.until(EC.presence_of_element_located((By.NAME, "username")))

        user_input = driver.find_element(By.NAME, "username")
        pass_input = driver.find_element(By.NAME, "password")

        user_input.clear()
        user_input.send_keys(IG_USER)
        time.sleep(1)
        pass_input.clear()
        pass_input.send_keys(IG_PASS)
        time.sleep(1)

        pass_input.submit()
        time.sleep(5)
        
        # Verificar y manejar 2FA
        current_url = driver.current_url
        if "challenge" in current_url or "two_factor" in current_url or current_url.endswith("2F"):
            print("⚠️ Detectado 2FA, intentando bypass...")
            skip_common_popups()
        
        # Verificar login exitoso
        wait.until(EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, "nav")),
            EC.presence_of_element_located((By.CSS_SELECTOR, "main"))
        ))
        print("✅ Login exitoso")
        skip_common_popups()
            
    except Exception as e:
        print(f"❌ Error en login: {e}")
        driver.quit()
        exit(1)

def skip_common_popups():
    for _ in range(3):
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = btn.text.lower().strip()
                if any(skip in btn_text for skip in ['not now', 'ahora no', 'dismiss', 'cerrar']):
                    btn.click()
                    time.sleep(2)
                    break
            time.sleep(2)
        except:
            break

# ================================
# Extractor de información mejorado
# ================================
def extract_event_info(text):
    """Extrae información específica de eventos del texto"""
    event_data = {
        'menciones': [],
        'lugar': '',
        'fecha': '',
        'hora': '',
        'hashtags': []
    }
    
    # Extraer menciones (@usuario)
    mentions = re.findall(r'@([a-zA-Z0-9_.]+)', text)
    event_data['menciones'] = mentions
    
    # Extraer hashtags
    hashtags = re.findall(r'#([a-zA-Z0-9_ÑñÁáÉéÍíÓóÚúÜü]+)', text)
    event_data['hashtags'] = hashtags
    
    # Buscar fechas con mayor precisión
    date_patterns = [
        r'(?:viernes|sábado|sabado|domingo|lunes|martes|miércoles|miercoles|jueves)\s+\d{1,2}\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
        r'\d{1,2}\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
        r'\d{1,2}/\d{1,2}/\d{2,4}',
        r'\d{1,2}-\d{1,2}-\d{2,4}',
        r'(?:viernes|sábado|sabado|domingo|lunes|martes|miércoles|miercoles|jueves)\s+\d{1,2}',
        r'\d{1,2}\s+(?:y|al)\s+\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
        r'(?:próximo|proximo|este)\s+(?:viernes|sábado|sabado|domingo|lunes|martes|miércoles|miercoles|jueves)'
    ]
    
    for pattern in date_patterns:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            event_data['fecha'] = matches.group(0).strip()
            break
    
    # Buscar horas con mayor precisión
    time_patterns = [
        r'\d{1,2}:\d{2}\s*(?:am|pm|AM|PM|a\.?m\.?|p\.?m\.?)',
        r'\d{1,2}\s*(?:am|pm|AM|PM|a\.?m\.?|p\.?m\.?)',
        r'(?:desde\s+las\s+|a\s+partir\s+de\s+las\s+|a\s+las\s+)\d{1,2}(?::\d{2})?',
        r'\d{1,2}(?::\d{2})?\s*(?:h|hrs|horas)'
    ]
    
    for pattern in time_patterns:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            event_data['hora'] = matches.group(0).strip()
            break
    
    # Buscar lugares con mayor precisión
    lugar_patterns = [
        r'(?:plaza|parque|centro|teatro|coliseo|estadio|auditorio|salon|salón)\s+[a-zA-ZÀ-ÿ\s]{3,30}',
        r'(?:en\s+|@\s*)?(?:plaza\s+cívica|plaza\s+civica|plaza\s+bolivar|plaza\s+bolívar)',
        r'(?:pereira|dosquebradas|santa\s+rosa\s+de\s+cabal)',
        r'(?:unicentro|megacentro|circunvalar)',
        r'(?:biblioteca|museo|casa\s+de\s+cultura)'
    ]
    
    for pattern in lugar_patterns:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            event_data['lugar'] = matches.group(0).strip()
            break
    
    return event_data

# ================================
# Función mejorada para cerrar modales
# ================================
def close_modal_improved():
    strategies = [
        # SVG close buttons
        (By.CSS_SELECTOR, "svg[aria-label='Cerrar'], svg[aria-label='Close']"),
        # Button close in dialog
        (By.CSS_SELECTOR, "div[role='dialog'] button svg"),
        # Generic close button
        (By.CSS_SELECTOR, "button[type='button'] svg"),
        # X path-based buttons
        (By.XPATH, "//button[contains(@aria-label, 'Cerrar') or contains(@aria-label, 'Close')]")
    ]
    
    for method, selector in strategies:
        try:
            element = driver.find_element(method, selector)
            # Si es SVG, click en el parent button
            if element.tag_name == 'svg':
                parent = element.find_element(By.XPATH, "..")
                if parent.tag_name == 'button':
                    parent.click()
                else:
                    ActionChains(driver).move_to_element(element).click().perform()
            else:
                element.click()
            time.sleep(1)
            return True
        except:
            continue
    
    # Último recurso: ESC
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        return True
    except:
        return False

# ================================
# Reset del driver
# ================================
def reset_driver():
    global driver, wait
    print("\n🔄 Reseteando driver...")
    try:
        driver.quit()
    except:
        pass
    
    time.sleep(5)
    driver = setup_driver()
    wait = WebDriverWait(driver, 15)
    instagram_login()

# ================================
# Scraper principal CON FILTRO DE EVENTOS
# ================================
def scrape_profile_posts(profile_url, profile_name, max_time=600):
    print(f"\n📍 Analizando: {profile_name}")
    
    try:
        driver.get(profile_url)
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(3)
    except Exception as e:
        print(f"❌ Error cargando perfil: {e}")
        return []
    
    eventos_encontrados = []
    progress_bar = ProgressBar(max_time)
    posts_procesados = 0
    eventos_detectados = 0
    
    try:
        while not progress_bar.update(posts_procesados, eventos_detectados):
            # Buscar posts
            post_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
            
            if posts_procesados >= len(post_links):
                # Scroll para cargar más posts
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(4)
                continue
            
            # Procesar siguiente post
            if posts_procesados < len(post_links):
                try:
                    post_link = post_links[posts_procesados]
                    post_url = post_link.get_attribute('href')
                    
                    # Click en el post
                    ActionChains(driver).move_to_element(post_link).click().perform()
                    time.sleep(3)
                    
                    # Extraer texto del post
                    post_text = get_post_text()
                    
                    # *** AQUÍ ESTÁ EL FILTRO CLAVE ***
                    if post_text and is_event_post(post_text):
                        # Solo si ES un evento, extraer toda la información
                        event_data = extract_full_event_data(profile_name, post_url, post_text)
                        if event_data:
                            eventos_encontrados.append(event_data)
                            eventos_detectados += 1
                            print(f"\n🎉 EVENTO DETECTADO #{eventos_detectados}: {post_text[:80]}...")
                    
                    posts_procesados += 1
                    
                    # Cerrar modal
                    close_modal_improved()
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"\n❌ Error en post {posts_procesados}: {e}")
                    close_modal_improved()
                    posts_procesados += 1
                    continue
        
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        try:
            reset_driver()
        except:
            pass
    
    finally:
        progress_bar.finish()
    
    print(f"✅ Análisis completado: {eventos_detectados} eventos de {posts_procesados} posts revisados")
    return eventos_encontrados

def get_post_text():
    """Extrae el texto del post abierto en modal"""
    try:
        # Esperar a que cargue
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article")))
        time.sleep(2)
        
        # Múltiples selectores para capturar el texto
        text_selectors = [
            "article div div div div h1",  # Posts con descripción larga
            "article h1",                  # Posts simples
            "article div ul li span",      # Comments/descriptions
            "article span[dir='auto']",    # Auto-direction text
            "div[data-testid] span",       # Test ID spans
            "article div span"             # Generic spans in article
        ]
        
        full_text = ""
        
        for selector in text_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    # Solo textos significativos (no botones, no nombres de usuario repetidos)
                    if (text and len(text) > 15 and 
                        not text.lower() in ['like', 'share', 'save', 'see translation', 'reply'] and
                        not text.count(text.split()[0]) > 3):  # No repeticiones
                        full_text += text + " "
            except:
                continue
        
        return full_text.strip()
        
    except:
        return ""

def extract_full_event_data(profile_name, post_url, post_text):
    """Extrae datos completos del evento detectado"""
    try:
        # Información básica del evento
        event_info = extract_event_info(post_text)
        
        # Fecha de publicación
        try:
            time_elem = driver.find_element(By.CSS_SELECTOR, "time")
            post_date = time_elem.get_attribute("datetime") or time_elem.get_attribute("title")
        except:
            post_date = "No disponible"
        
        return {
            'fuente': profile_name,
            'texto': post_text[:500] + ("..." if len(post_text) > 500 else ""),
            'menciones': ', '.join(event_info['menciones']) if event_info['menciones'] else '',
            'lugar': event_info['lugar'],
            'fecha_evento': event_info['fecha'],
            'hora_evento': event_info['hora'],
            'hashtags': ', '.join(event_info['hashtags']) if event_info['hashtags'] else '',
            'link': post_url,
            'fecha_publicacion': post_date
        }
        
    except Exception as e:
        print(f"❌ Error extrayendo datos: {e}")
        return None

# ================================
# Diccionario de perfiles
# ================================
PROFILES_AND_HASHTAGS = {
    "pereiravirtual": "https://www.instagram.com/pereiravirtual/",
    "convivenciaejerockfest": "https://www.instagram.com/convivenciaejerockfest/",
    "secretariaculturapereira": "https://www.instagram.com/secretariaculturapereira/",
    "alcaldiadepereira": "https://www.instagram.com/alcaldiadepereira/",
    "lacanterapereira": "https://www.instagram.com/lacanterapereira/",
    "globos.liz": "https://www.instagram.com/globos.liz/"
}

# ================================
# MAIN EXECUTION
# ================================
def main():
    print("🎯 Instagram Event Hunter v2.0 - Solo Eventos Reales")
    print("=" * 60)
    
    instagram_login()
    
    # CSV con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"eventos_reales_{timestamp}.csv"
    
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Fuente", "Texto", "Menciones", "Lugar", 
            "Fecha_Evento", "Hora_Evento", "Hashtags", 
            "Link", "Fecha_Publicacion"
        ])
        
        total_eventos_reales = 0
        
        for profile_name, profile_url in PROFILES_AND_HASHTAGS.items():
            try:
                eventos = scrape_profile_posts(profile_url, profile_name, max_time=600)
                
                for evento in eventos:
                    writer.writerow([
                        evento['fuente'],
                        evento['texto'],
                        evento['menciones'],
                        evento['lugar'],
                        evento['fecha_evento'],
                        evento['hora_evento'],
                        evento['hashtags'],
                        evento['link'],
                        evento['fecha_publicacion']
                    ])
                
                total_eventos_reales += len(eventos)
                print(f"📊 Total eventos reales encontrados: {total_eventos_reales}")
                
                # Pausa entre perfiles
                time.sleep(15)
                
            except Exception as e:
                print(f"❌ Error en {profile_name}: {e}")
                try:
                    reset_driver()
                    time.sleep(10)
                except:
                    continue
    
    print(f"\n🎉 MISIÓN COMPLETADA!")
    print(f"📄 Archivo: {csv_filename}")
    print(f"🎯 Eventos reales encontrados: {total_eventos_reales}")
    
    driver.quit()

if __name__ == "__main__":
    main()
