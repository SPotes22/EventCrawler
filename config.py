# scraper/config.py
from datetime import datetime, timedelta

# Configuración de fechas
HOY = datetime.now()
FECHA_INICIO = HOY - timedelta(days=180)  # 6 meses atrás
FECHA_FIN = HOY

# Opciones de Selenium
SELENIUM_DRIVER_PATH = "/path/to/chromedriver"
HEADLESS = True
TIMEOUT = 10

