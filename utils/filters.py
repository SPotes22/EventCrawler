# scraper/utils/filters.py
from scraper.config import FECHA_INICIO, FECHA_FIN
from datetime import datetime

def filtrar_por_fecha(eventos):
    """Recibe lista de diccionarios con clave 'fecha' y filtra por rango."""
    filtrados = []
    for evento in eventos:
        try:
            fecha_evento = datetime.strptime(evento["fecha"], "%Y-%m-%d")
            if FECHA_INICIO <= fecha_evento <= FECHA_FIN:
                filtrados.append(evento)
        except Exception:
            continue
    return filtrados

