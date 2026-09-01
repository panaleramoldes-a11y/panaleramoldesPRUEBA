import re
from math import radians, cos, sin, asin, sqrt

def extraer_coords_desde_link(link: str):
    """Busca el patrón @-XX.XXXX,-YY.YYYY en un enlace de Google Maps."""
    if not link:
        return None
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None

def obtener_coordenadas(link_maps: str):
    """Alias/Envoltorio para extracción de coordenadas."""
    return extraer_coords_desde_link(link_maps)

def calcular_distancia_haversine(p1: tuple, p2: tuple) -> float:
    """
    Calcula la distancia en kilómetros entre dos coordenadas (lat, lng)
    utilizando la fórmula de Haversine.
    """
    if not p1 or not p2:
        return 0.0

    lat1, lon1 = p1
    lat2, lon2 = p2

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radio de la Tierra en km
    return c * r
