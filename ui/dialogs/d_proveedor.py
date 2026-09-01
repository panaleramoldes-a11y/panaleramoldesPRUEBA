import re
import pandas as pd
import streamlit as st
from config.database import db
from config.constants import LISTA_RUBROS

@st.dialog("➕ Nuevo Proveedor Rápido")
def abrir_alta_proveedor_rapida():
    try:
        response = db.table("PROVEEDORES").select("*").execute()
        df_prov = pd.DataFrame(response.data)
    except Exception:
        df_prov = pd.DataFrame()
    
    with st.form("form_nuevo_proveedor_rapido", clear_on_submit=True):
        nuevo_id = str(len(df_prov) + 1).zfill(4)
        st.info(f"ID Sugerido: {nuevo_id}")
        
        col1, col2 = st.columns(2)
        with col1:
            razon_social = st.text_input("Razón Social")
            cuit = st.text_input("CUIT (Formato: XX-XXXXXXXX-X)")
            direccion = st.text_input("Dirección")
        with col2:
            telefono = st.text_input("Teléfono")
            condicion = st.selectbox("Condición Fiscal", ["Responsable Inscripto", "Monotributo", "Exento"])
        
        rubros_seleccionados = st.multiselect("Asociar Rubros", LISTA_RUBROS)
        
        btn_guardar = st.form_submit_button("Guardar Proveedor")
        
        if btn_guardar:
            if not re.match(r'^\d{2}-\d{8}-\d{1}$', cuit):
                st.error("Error: El CUIT debe tener formato XX-XXXXXXXX-X")
            elif not df_prov.empty and cuit in df_prov['CUIT'].astype(str).values:
                st.error("Error: Ya existe un proveedor con ese CUIT.")
            else:
                try:
                    db.table("PROVEEDORES").insert({
                        "ID_Proveedor": nuevo_id,
                        "Razon_Social": razon_social,
                        "Rubros_Asociados": ", ".join(rubros_seleccionados),
                        "CUIT": cuit,
                        "Condicion_Fiscal": condicion,
                        "Direccion": direccion,
                        "Telefono": telefono
                    }).execute()
                    st.success("✅ ¡Proveedor cargado exitosamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
