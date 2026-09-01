"""
ui/views/v_auditoria.py
Vista de la pantalla de Auditoría del Sistema.
"""

import streamlit as st
from services.audit_service import obtener_registros_auditoria


def render_auditoria_view():
    st.title("🛡️ Auditoría del Sistema")
    st.subheader("Historial de Modificaciones y Eventos")

    # --- FILTROS DE BÚSQUEDA ---
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tabla_f = st.selectbox(
            "Tabla Afectada",
            ["Todas", "PRODUCTOS", "CAJA", "VENDEDORES", "COMPRAS_CABECERA"],
            key="sel_tabla",
        )

    with c2:
        accion_f = st.selectbox(
            "Acción",
            ["Todas", "INSERT", "UPDATE", "DELETE"],
            key="sel_accion",
        )

    with c3:
        user_f = st.text_input("Usuario (Filtro parcial)", key="input_user")

    with c4:
        id_f = st.text_input("ID Entidad Exacto", key="input_id")

    # --- EJECUCIÓN Y RENDERIZADO ---
    df_render = obtener_registros_auditoria(
        tabla=tabla_f,
        accion=accion_f,
        usuario=user_f,
        id_entidad=id_f,
        limite=100,
    )

    if not df_render.empty:
        st.dataframe(
            df_render,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Detalles": st.column_config.JsonColumn(
                    "Datos/Cambios 🔍",
                    help="Historial de campos modificados",
                )
            },
        )
    else:
        st.info("No se encontraron registros que coincidan con los criterios de búsqueda.")
