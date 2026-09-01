# ui/views/v_proveedores.py
import pandas as pd
import streamlit as st
from services.proveedores_service import (
    actualizar_proveedor,
    generar_siguiente_id_proveedor,
    guardar_proveedor,
    obtener_proveedores,
)


def render_modulo_proveedores(db, lista_rubros: list = None):
    st.title("🚚 Gestión de Proveedores")

    if lista_rubros is None:
        lista_rubros = []

    df_prov = obtener_proveedores(db)

    tab1, tab2, tab3 = st.tabs(
        ["🔍 Explorador", "➕ Nuevo Proveedor", "✏️ Modificar"]
    )

    # -----------------------------------------------------------------
    # PESTAÑA 1: EXPLORADOR Y LISTADO
    # -----------------------------------------------------------------
    with tab1:
        st.subheader("Lista de Proveedores")
        busqueda_prov = st.text_input(
            "🔍 Filtrar por Nombre, CUIT o Rubro:", key="txt_buscar_prov"
        )

        df_filtrado = df_prov.copy()
        if busqueda_prov and not df_prov.empty:
            b_txt = busqueda_prov.lower()
            df_filtrado = df_prov[
                df_prov.apply(
                    lambda row: b_txt
                    in str(row.get("Razon_Social", "")).lower()
                    or b_txt in str(row.get("CUIT", "")).lower()
                    or b_txt in str(row.get("Rubros_Asociados", "")).lower(),
                    axis=1,
                )
            ]

        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    # -----------------------------------------------------------------
    # PESTAÑA 2: NUEVO PROVEEDOR
    # -----------------------------------------------------------------
    with tab2:
        nuevo_id = generar_siguiente_id_proveedor(df_prov)
        st.info(f"ID Sugerido: {nuevo_id}")

        with st.form("form_nuevo_prov", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                razon_social = st.text_input("Razón Social")
                cuit = st.text_input("CUIT (Formato: XX-XXXXXXXX-X)")
                direccion = st.text_input("Dirección")
            with col2:
                telefono = st.text_input("Teléfono")
                condicion = st.selectbox(
                    "Condición Fiscal",
                    ["Responsable Inscripto", "Monotributo", "Exento"],
                )

            rubros_seleccionados = st.multiselect(
                "Asociar Rubros", lista_rubros
            )

            btn_guardar = st.form_submit_button("Guardar Proveedor")

            if btn_guardar:
                datos_nuevo = {
                    "ID_Proveedor": nuevo_id,
                    "Razon_Social": razon_social,
                    "Rubros_Asociados": ", ".join(rubros_seleccionados),
                    "CUIT": cuit,
                    "Condicion_Fiscal": condicion,
                    "Direccion": direccion,
                    "Telefono": telefono,
                }

                exito, msj = guardar_proveedor(db, datos_nuevo, df_prov)
                if exito:
                    st.success(msj)
                    st.rerun()
                else:
                    st.error(msj)

    # -----------------------------------------------------------------
    # PESTAÑA 3: MODIFICAR PROVEEDOR
    # -----------------------------------------------------------------
    with tab3:
        if not df_prov.empty and "Razon_Social" in df_prov.columns:
            lista_razones = df_prov["Razon_Social"].dropna().tolist()
            prov_seleccionado = st.selectbox(
                "Seleccionar proveedor a editar",
                lista_razones,
                key="sb_mod_prov",
            )

            datos = df_prov[
                df_prov["Razon_Social"] == prov_seleccionado
            ].iloc[0]

            with st.form("form_modificar_prov"):
                col1, col2 = st.columns(2)
                with col1:
                    razon_social_mod = st.text_input(
                        "Razón Social", value=str(datos.get("Razon_Social", ""))
                    )
                    cuit_mod = st.text_input(
                        "CUIT", value=str(datos.get("CUIT", ""))
                    )
                    direccion_mod = st.text_input(
                        "Dirección", value=str(datos.get("Direccion", ""))
                    )
                with col2:
                    telefono_mod = st.text_input(
                        "Teléfono", value=str(datos.get("Telefono", ""))
                    )

                    cond_actual = datos.get(
                        "Condicion_Fiscal", "Responsable Inscripto"
                    )
                    opciones_cond = [
                        "Responsable Inscripto",
                        "Monotributo",
                        "Exento",
                    ]
                    idx_cond = (
                        opciones_cond.index(cond_actual)
                        if cond_actual in opciones_cond
                        else 0
                    )

                    condicion_mod = st.selectbox(
                        "Condición Fiscal", opciones_cond, index=idx_cond
                    )

                    # Recuperar rubros previamente guardados
                    raw_rubros = str(datos.get("Rubros_Asociados", ""))
                    rubros_defecto = [
                        r.strip()
                        for r in raw_rubros.split(",")
                        if r.strip() in lista_rubros
                    ]
                    rubros_mod = st.multiselect(
                        "Rubros", lista_rubros, default=rubros_defecto
                    )

                btn_mod = st.form_submit_button("Actualizar Proveedor")

                if btn_mod:
                    datos_actualizados = {
                        "Razon_Social": razon_social_mod,
                        "Rubros_Asociados": ", ".join(rubros_mod),
                        "CUIT": cuit_mod,
                        "Condicion_Fiscal": condicion_mod,
                        "Direccion": direccion_mod,
                        "Telefono": telefono_mod,
                    }

                    exito, msj = actualizar_proveedor(
                        db, str(datos["ID_Proveedor"]), datos_actualizados
                    )
                    if exito:
                        st.success(msj)
                        st.rerun()
                    else:
                        st.error(msj)
        else:
            st.info("No hay proveedores disponibles para modificar.")
