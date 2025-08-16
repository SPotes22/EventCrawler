# Facebook Events Scraper

Scraper en Python con **Selenium** que obtiene eventos públicos en Facebook entre diferentes layouts de interfaz.

## Funcionalidad
- Login automático con credenciales guardadas en `.env`.
- Manejo de 2FA manual (espera hasta 60s).
- Autodetección de layout:
  - **Layout B** → resultados de búsqueda (`search/events`).
  - **Layout C** → dashboard de eventos desde la barra lateral.
- Scroll automático hasta final de resultados.
- Guardado en `eventos.csv` con columnas:
  - `DIA`, `NOMBRE_EVENTO`, `DESCRIPCION`, `ENLACE`.

## Requisitos
- Python 3.10+
- Google Chrome + chromedriver
- Librerías:
```
  pip install selenium python-dotenv
```

Configuración

Crear archivo .env:
```
FB_EMAIL=tu_correo
FB_PASSWORD=tu_password
```

Asegurarse de que .env está en .gitignore.

Uso
```
python scraper.py
```

Los eventos se guardarán en eventos.csv.
