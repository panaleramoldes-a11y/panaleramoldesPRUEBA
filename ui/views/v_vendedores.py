from datetime import datetime
import pandas as pd
import streamlit as st

from services.vendedores_service import (
    actualizar_vendedor,
    calcular_siguiente_id,
    obtener_vendedores,
    registrar_vendedor,
)


def render_vendedores_view():
    st.title("👥 Gestión de Vendedores")

    # Carga de datos
    df_vend = obtener_vendedores()

    tab1, tab2, tab3 = st.tabs(
        ["🔍 Listado", "➕ Nuevo Vendedor", "✏️ Modificar"]
    )

    # -----------------------------------------------------------------
    # TAB 1: LISTADO DE ACTIVOS
    # -----------------------------------------------------------------
    with tab1:
        st.subheader("Personal de Ventas Activo")
        if not df_vend.empty and "Estado" in df_vend.columns:
            df_activos = df_vend[df_vend["Estado"] == "Activo"]
            st.dataframe(df_activos, width="stretch", hide_index=True)
        else:
            st.info("No hay vendedores registrados activos.")

    # -----------------------------------------------------------------
    # TAB 2: NUEVO VENDEDOR
    # -----------------------------------------------------------------
    with tab2:
        with st.form("nuevo_vendedor", clear_on_submit=True):
            nuevo_id = calcular_siguiente_id(df_vend)
            st.info(f"ID Automático: {nuevo_id}")

            col_a, col_b = st.columns(2)

            with col_a:
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")

            with col_b:
                mail = st.text_input("Correo Electrónico")
                url_foto = st.text_input("URL o Nombre de archivo de foto")

            fecha_nac = st.date_input(
                "Fecha de Nacimiento",
                value=datetime(1990, 1, 1),
                min_value=datetime(1900, 1, 1),
            )

            btn_guardar = st.form_submit_button("Registrar Vendedor")

            if btn_guardar:
                if nombre and apellido and mail:
                    exito, mensaje = registrar_vendedor(
                        nuevo_id=nuevo_id,
                        nombre=nombre,
                        apellido=apellido,
                        mail=mail,
                        fecha_nac=fecha_nac,
                        imagen=url_foto,
                    )
                    if exito:
                        st.success(mensaje)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(mensaje)
                else:
                    st.error("Por favor, completá los campos obligatorios.")

    # -----------------------------------------------------------------
    # TAB 3: MODIFICAR VENDEDOR
    # -----------------------------------------------------------------
    with tab3:
        if not df_vend.empty:
            # Generar listado identificable de vendedores
            df_vend_copia = df_vend.copy()
            df_vend_copia["NombreCompleto"] = (
                df_vend_copia["Nombre"].astype(str)
                + " "
                + df_vend_copia["Apellido"].astype(str)
            )

            vendedor_sel = st.selectbox(
                "Seleccionar vendedor a editar",
                options=df_vend_copia["NombreCompleto"].tolist(),
            )

            datos_v = df_vend_copia[
                df_vend_copia["NombreCompleto"] == vendedor_sel
            ].iloc[0]

            with st.form("modificar_vendedor"):
                st.write(
                    f"**Editando Vendedor ID:** {datos_v.get('ID_Vendedor')}"
                )

                col1, col2 = st.columns(2)
                with col1:
                    n_nombre = st.text_input(
                        "Nombre", value=str(datos_v.get("Nombre", ""))
                    )
                    n_apellido = st.text_input(
                        "Apellido", value=str(datos_v.get("Apellido", ""))
                    )
                    n_mail = st.text_input(
                        "Mail", value=str(datos_v.get("Mail", ""))
                    )

                with col2:
                    fecha_raw = datos_v.get("Fecha de Nacimiento")
                    if fecha_raw and pd.notna(fecha_raw):
                        try:
                            fecha_guardada = pd.to_datetime(fecha_raw).date()
                        except Exception:
                            fecha_guardada = datetime(1990, 1, 1).date()
                    else:
                        fecha_guardada = datetime(1990, 1, 1).date()

                    n_fecha_nac = st.date_input(
                        "Fecha de Nacimiento",
                        value=fecha_guardada,
                        min_value=datetime(1900, 1, 1),
                    )

                    estado_actual = str(datos_v.get("Estado", "Activo"))
                    n_estado = st.selectbox(
                        "Estado",
                        ["Activo", "Inactivo"],
                        index=0 if estado_actual == "Activo" else 1,
                    )

                    n_foto = st.text_input(
                        "URL/Archivo de Foto",
                        value=str(datos_v.get("Imagen", "")),
                    )

                btn_modificar = st.form_submit_button("Guardar Cambios")

                if btn_modificar:
                    exito, mensaje = actualizar_vendedor(
                        id_vendedor=datos_v["ID_Vendedor"],
                        nombre=n_nombre,
                        apellido=n_apellido,
                        mail=n_mail,
                        fecha_nac=n_fecha_nac,
                        estado=n_estado,
                        imagen=n_foto,
                    )
                    if exito:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)
        else:
            st.info("No hay vendedores registrados.")
