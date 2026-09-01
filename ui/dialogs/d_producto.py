import pandas as pd
import streamlit as st
from config.database import db
from config.constants import LISTA_RUBROS

@st.dialog("➕ Alta Rápida de Producto", width="large")
def modal_alta_rapida_producto(agregar_al_carrito_fn=None):
    rubros_opt = LISTA_RUBROS
    
    try:
        res_prov = db.table("PROVEEDORES").select("Razon_Social").execute().data
        prov_opt = [p["Razon_Social"] for p in res_prov] if res_prov else ["Genérico"]
    except Exception:
        prov_opt = ["Genérico"]

    with st.form("form_alta_producto_rapido", clear_on_submit=False):
        c_alta1, c_alta2 = st.columns(2)
        
        with c_alta1:
            id_nuevo = st.text_input("Código / ID Producto*", key="alta_rap_id").strip()
            nombre_nuevo = st.text_input("Descripción / Nombre*", key="alta_rap_nom").strip()
            marca_nueva = st.text_input("Marca", key="alta_rap_marca").strip()
            rubro_nuevo = st.selectbox("Rubro", options=rubros_opt, key="alta_rap_rubro")
            prov_seleccionado = st.selectbox("Proveedor", options=prov_opt, key="alta_rap_prov")
            
        with c_alta2:
            stock_ini = st.number_input("Stock Inicial", min_value=0, value=0, step=1, key="alta_rap_stock")
            costo_ini = st.number_input("Precio Costo ($)", min_value=0.0, value=0.0, step=10.0, key="alta_rap_costo")
            p1 = st.number_input("Precio Lista 1 ($)*", min_value=0.0, value=0.0, step=10.0, key="alta_rap_p1")
            p2 = st.number_input("Precio Lista 2 ($)", min_value=0.0, value=0.0, step=10.0, key="alta_rap_p2")
            p3 = st.number_input("Precio Lista 3 ($)", min_value=0.0, value=0.0, step=10.0, key="alta_rap_p3")
            p4 = st.number_input("Precio Lista 4 ($)", min_value=0.0, value=0.0, step=10.0, key="alta_rap_p4")
            p5 = st.number_input("Precio Lista 5 ($)", min_value=0.0, value=0.0, step=10.0, key="alta_rap_p5")

        st.caption("* Campos obligatorios")
        btn_guardar = st.form_submit_button("💾 Guardar y Añadir a la Compra")

    if btn_guardar:
        if not id_nuevo or not nombre_nuevo or p1 <= 0:
            st.error("Por favor, completa los campos obligatorios (ID, Nombre y Precio 1 > 0).")
        else:
            nuevo_prod = {
                "ID_Producto": id_nuevo,
                "Nombre": nombre_nuevo,
                "Rubro": rubro_nuevo if rubro_nuevo != "" else "OTROS",
                "Marca": marca_nueva if marca_nueva != "" else None,
                "Stock_Actual": int(stock_ini),
                "Precio_Costo": float(costo_ini),
                "Precio_1": float(p1),
                "Precio_2": float(p2),
                "Precio_3": float(p3),
                "Precio_4": float(p4),
                "Precio_5": float(p5),
                "ID_Proveedor": prov_seleccionado if prov_seleccionado != "Genérico" else None,
                "Stock_Min": 0,
                "Stock_Max": 0,
                "Imagen": None,
                "Estado": "ACTIVO"
            }
            
            try:
                db.table("PRODUCTOS").insert(nuevo_prod).execute()
                
                if 'df_prod' in st.session_state: 
                    del st.session_state['df_prod']
                
                if agregar_al_carrito_fn:
                    pm_nuevo = pd.Series(nuevo_prod)
                    agregar_al_carrito_fn(pm_nuevo)
                
                st.success("🎉 ¡Producto guardado y añadido a la compra!")
                st.rerun()
            except Exception as e:
                st.error(f"Error técnico al guardar: {e}")
