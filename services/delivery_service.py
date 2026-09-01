import streamlit as st
from config.database import db

@st.cache_data(ttl=600)
def cargar_puntos_reparto():
    """
    Recupera los puntos de reparto guardados en Supabase.
    Retorna un diccionario: {"Nombre del punto": (lat, lng), ...}
    """
    try:
        data = db.table("puntos_reparto").select("*").execute().data
        puntos = {}
        for p in data:
            puntos[p['nombre']] = (float(p['latitud']), float(p['longitud']))
        return puntos
    except Exception as e:
        st.error(f"Error al cargar puntos de reparto desde la base de datos: {e}")
        return {}
