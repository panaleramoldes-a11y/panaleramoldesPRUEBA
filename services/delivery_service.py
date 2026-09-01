"""
services/delivery_service.py
Capa de servicio para la gestión de puntos de reparto y ventas pendientes.
"""

import re
from typing import Dict, List, Optional, Tuple
import streamlit as st
from config.database import db


@st.cache_data(ttl=600)
def cargar_puntos_reparto() -> Dict[str, Tuple[float, float]]:
    """
    Recupera los puntos de reparto guardados en Supabase.
    Retorna un diccionario: {"Nombre del punto": (lat, lng), ...}
    """
    try:
        data = db.table("puntos_reparto").select("*").execute().data
        puntos = {}
        for p in data:
            puntos[p["nombre"]] = (float(p["latitud"]), float(p["longitud"]))
        return puntos
    except Exception as e:
        st.error(f"Error al cargar puntos de reparto desde la base de datos: {e}")
        return {}


def obtener_ventas_reparto() -> List[Dict]:
    """
    Obtiene todas las ventas pendientes cuya forma de entrega es 'Reparto'.
    """
    try:
        res = (
            db.table("VENTAS_PENDIENTES")
            .select("*")
            .eq("Forma_Entrega", "Reparto")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Error al cargar ventas de reparto: {e}")
        return []


def extraer_coords_desde_link(link: str) -> Optional[Tuple[float, float]]:
    """
    Extrae un par de coordenadas (lat, lng) desde un enlace de Google Maps.
    """
    if not link:
        return None
    pattern = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
    match = re.search(pattern, link)
    if match:
        return (float(match.group(1)), float(match.group(2)))
    return None
