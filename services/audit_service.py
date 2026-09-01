"""
services/audit_service.py
Capa de servicio para la lectura y escritura de eventos de Auditoría.
"""

import pandas as pd
import streamlit as st
from config.database import db


def log_auditoria(tabla: str, accion: str, id_entidad: str, detalles: dict, usuario: str = "Martin"):
    """
    Registra automáticamente un movimiento en la tabla de Auditoría.
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


def obtener_registros_auditoria(
    tabla: str = "Todas",
    accion: str = "Todas",
    usuario: str = "",
    id_entidad: str = "",
    limite: int = 100
) -> pd.DataFrame:
    """
    Consulta la tabla AUDITORIA aplicando filtros dinámicos y formateando el resultado para la UI.
    """
    try:
        query = db.table("AUDITORIA").select("*")

        if tabla and tabla != "Todas":
            query = query.eq("Tabla_Afectada", tabla)

        if accion and accion != "Todas":
            query = query.eq("Accion", accion)

        if usuario and usuario.strip():
            query = query.ilike("Usuario", f"%{usuario.strip()}%")

        if id_entidad and id_entidad.strip():
            query = query.eq("ID_Entidad", id_entidad.strip())

        res = query.order("Fecha_Hora", desc=True).limit(limite).execute()

        if not res.data:
            return pd.DataFrame()

        df_auditoria = pd.DataFrame(res.data)

        if "Fecha_Hora" in df_auditoria.columns:
            df_auditoria["Fecha_Hora"] = pd.to_datetime(
                df_auditoria["Fecha_Hora"]
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

        columnas_ordenadas = [
            "Fecha_Hora",
            "Usuario",
            "Tabla_Afectada",
            "Accion",
            "ID_Entidad",
            "Detalles",
        ]

        for col in columnas_ordenadas:
            if col not in df_auditoria.columns:
                df_auditoria[col] = None

        return df_auditoria[columnas_ordenadas]

    except Exception as e:
        st.error(f"Error al consultar la auditoría: {e}")
        return pd.DataFrame()
