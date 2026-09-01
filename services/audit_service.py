import streamlit as st
from config.database import db

def log_auditoria(tabla: str, accion: str, id_entidad: str, detalles: dict, usuario: str = "Martin"):
    """
    Registra automáticamente el movimiento en la tabla de Auditoría.
    """
    try:
        db.table("AUDITORIA").insert({
            "Tabla_Afectada": tabla,
            "Accion": accion,
            "ID_Entidad": str(id_entidad),
            "Detalles": detalles,
            "Usuario": usuario
        }).execute()
    except Exception as e:
        st.error(f"🚨 Error crítico al guardar en auditoría: {e}")
