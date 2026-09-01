import pandas as pd
import streamlit as st
from services.cliente_service import ClienteService


def limpiar_val(val):
    """Auxiliar para sanitizar valores vacíos/NaN procedentes del DataFrame."""
    if (
        pd.isna(val)
        or val is None
        or str(val).strip().upper() in ["NAN", "NONE", "NULL"]
    ):
        return ""
    return str(val).strip()


def render_clientes():
    st.header("👥 Gestión de Clientes")

    # 1. Cargar datos desde la capa de servicio
    df_clientes = ClienteService.obtener_todos()
    if df_clientes.empty:
        st.info("No hay datos de clientes para mostrar.")

    # 2. Definir pestañas según el rol
    rol_usuario = st.session_state.get("rol", "Vendedor")
    if rol_usuario == "Administrador":
        nombres_tabs = ["🔍 Explorador", "➕ Nuevo Cliente", "✏️ Modificar"]
    else:
        nombres_tabs = ["➕ Nuevo Cliente", "✏️ Modificar"]

    tabs = st.tabs(nombres_tabs)

    if rol_usuario == "Administrador":
        tab_explorador, tab_nuevo, tab_modificar = tabs
    else:
        tab_explorador = None
        tab_nuevo, tab_modificar = tabs

    # --- TAB 1: EXPLORADOR ---
    if tab_explorador:
        with tab_explorador:
            st.subheader("Buscador de Clientes")
            query = st.text_input(
                "Buscar por nombre, apellido, DNI, CUIT, teléfono o dirección..."
            )
            if query and not df_clientes.empty:
                mask = df_clientes.apply(
                    lambda row: row.astype(str).str.contains(query, case=False).any(),
                    axis=1,
                )
                st.dataframe(df_clientes[mask], use_container_width=True)
            else:
                st.dataframe(df_clientes, use_container_width=True)

    # --- TAB 2: NUEVO CLIENTE ---
    with tab_nuevo:
        with st.form("form_nuevo_cliente"):
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre*")
                apellido = st.text_input("Apellido*")
                dni = st.text_input("DNI", max_chars=8)
                cuit = st.text_input("CUIT", max_chars=13)
                razon_social = st.text_input("Razón Social")
                telefono = st.text_input("Teléfono* (10 dígitos)", max_chars=10)
            with c2:
                dir1 = st.text_input("Dirección 1*")
                link1 = st.text_input("Link Dirección 1")
                dir2 = st.text_input("Dirección 2")
                link2 = st.text_input("Link Dirección 2")
                dir3 = st.text_input("Dirección 3")
                link3 = st.text_input("Link Dirección 3")
                zona = st.selectbox(
                    "Zona*",
                    ["NORTE", "SUR", "CENTRO", "ESTE", "OESTE", "SANLO CHICO"],
                )
                tipo = st.selectbox(
                    "Tipo Cliente",
                    ["CONSUMIDOR FINAL", "MAYORISTA", "EMPRESA/ORGANISMO"],
                )

            submitted = st.form_submit_button("Guardar Cliente")

            if submitted:
                tiene_datos_persona = bool(nombre and apellido)
                tiene_razon_social = bool(razon_social)

                if not (tiene_datos_persona or tiene_razon_social):
                    st.error(
                        "⚠️ Debes completar obligatoriamente el 'Nombre y Apellido' o la 'Razón Social'."
                    )
                elif not all([telefono, dir1]):
                    st.error(
                        "⚠️ El 'Teléfono' y la 'Dirección 1' son campos obligatorios para cualquier cliente."
                    )
                elif (
                    not df_clientes.empty
                    and telefono in df_clientes["Telefono"].astype(str).values
                ):
                    st.error("⚠️ Ya existe un cliente con este teléfono!")
                else:
                    nuevo_cliente = {
                        "Nombre": nombre.upper() if nombre else "N/A",
                        "Apellido": apellido.upper() if apellido else "N/A",
                        "DNI": dni,
                        "CUIT": cuit,
                        "Razón Social": razon_social.upper() if razon_social else "",
                        "Telefono": telefono,
                        "Direccion_1": dir1.upper(),
                        "Direccion_2": dir2.upper(),
                        "Direccion_3": dir3.upper(),
                        "Link_Direccion_1": link1,
                        "Link_Direccion_2": link2,
                        "Link_Direccion_3": link3,
                        "Zona": zona,
                        "Tipo_Cliente": tipo,
                    }

                    usuario_logueado = st.session_state.get(
                        "usuario_actual", "Desconocido"
                    )
                    if ClienteService.crear_cliente(
                        nuevo_cliente, usuario_logueado
                    ):
                        st.success("✅ Cliente cargado!")
                        st.rerun()

    # --- TAB 3: MODIFICAR CLIENTE ---
    if tab_modificar is not None:
        with tab_modificar:
            st.subheader("Modificar Cliente Existente")

            if df_clientes.empty:
                st.warning("No hay clientes registrados para modificar.")
                return

            def obtener_etiqueta_cliente(row):
                razon = limpiar_val(row.get("Razón Social"))
                if razon:
                    return f"{razon} (ID: {row['ID_Cliente']})"
                nombre_c = limpiar_val(row.get("Nombre"))
                apellido_c = limpiar_val(row.get("Apellido"))
                return f"{nombre_c} {apellido_c}".strip() + f" (ID: {row['ID_Cliente']})"

            lista_clientes = df_clientes.apply(obtener_etiqueta_cliente, axis=1)
            seleccion = st.selectbox(
                "Seleccione el cliente",
                [""] + lista_clientes.tolist(),
                key="sel_modificar",
            )

            if seleccion:
                id_modificar = int(
                    seleccion.split("(ID: ")[1].replace(")", "")
                )
                fila = df_clientes[
                    df_clientes["ID_Cliente"].astype(int) == id_modificar
                ].iloc[0]

                # Gift Card
                gc = ClienteService.obtener_gift_card_activa(id_modificar)
                if gc:
                    st.info(f"""
                    **Detalles de Gift Card Activa:**
                    - Saldo Inicial: ${gc['Saldo_Inicial']:,.2f}
                    - Saldo Actual: ${gc['Saldo_Actual']:,.2f}
                    - Pagada con: {gc['Forma_Pago_Adquisicion']}
                    """)

                if rol_usuario == "Administrador":
                    if st.button("🎁 Gestionar Gift Card"):
                        razon_limpia = limpiar_val(fila.get("Razón Social"))
                        nombre_para_gc = (
                            razon_limpia.upper()
                            if razon_limpia
                            else f"{limpiar_val(fila.get('Nombre'))} {limpiar_val(fila.get('Apellido'))}".strip()
                        )
                        if "abrir_asignacion_gift_card" in globals():
                            abrir_asignacion_gift_card(
                                str(id_modificar), nombre_para_gc
                            )
                        else:
                            st.info(
                                f"Gestión de Gift Card para cliente ID {id_modificar} ({nombre_para_gc})."
                            )

                # Formulario Edición
                with st.form("form_datos"):
                    c1, c2 = st.columns(2)
                    with c1:
                        nuevo_nombre = st.text_input(
                            "Nombre", value=limpiar_val(fila.get("Nombre"))
                        )
                        nuevo_apellido = st.text_input(
                            "Apellido", value=limpiar_val(fila.get("Apellido"))
                        )
                        nuevo_dni = st.text_input(
                            "DNI", value=limpiar_val(fila.get("DNI"))
                        )
                        nueva_razon = st.text_input(
                            "Razón Social",
                            value=limpiar_val(fila.get("Razón Social")),
                        )
                        nuevo_cuit = st.text_input(
                            "CUIT", value=limpiar_val(fila.get("CUIT"))
                        )
                        nuevo_telefono = st.text_input(
                            "Teléfono",
                            value=limpiar_val(fila.get("Telefono")),
                            max_chars=10,
                        )

                    with c2:
                        nuevo_dir1 = st.text_input(
                            "Dirección 1",
                            value=limpiar_val(fila.get("Direccion_1")),
                        )
                        nuevo_link1 = st.text_input(
                            "Link Dirección 1",
                            value=limpiar_val(fila.get("Link_Direccion_1")),
                        )
                        nuevo_dir2 = st.text_input(
                            "Dirección 2",
                            value=limpiar_val(fila.get("Direccion_2")),
                        )
                        nuevo_link2 = st.text_input(
                            "Link Dirección 2",
                            value=limpiar_val(fila.get("Link_Direccion_2")),
                        )
                        nuevo_dir3 = st.text_input(
                            "Dirección 3",
                            value=limpiar_val(fila.get("Direccion_3")),
                        )
                        nuevo_link3 = st.text_input(
                            "Link Dirección 3",
                            value=limpiar_val(fila.get("Link_Direccion_3")),
                        )

                    nueva_obs = st.text_area(
                        "Observaciones",
                        value=limpiar_val(fila.get("Observaciones")),
                    )

                    zonas_lista = [
                        "NORTE",
                        "SUR",
                        "CENTRO",
                        "ESTE",
                        "OESTE",
                        "SANLO CHICO",
                    ]
                    idx_zona = (
                        zonas_lista.index(fila.get("Zona"))
                        if fila.get("Zona") in zonas_lista
                        else 0
                    )
                    input_zona = st.selectbox("Zona", zonas_lista, index=idx_zona)

                    tipos_lista = [
                        "CONSUMIDOR FINAL",
                        "MAYORISTA",
                        "EMPRESA/ORGANISMO",
                    ]
                    idx_tipo = (
                        tipos_lista.index(fila.get("Tipo_Cliente"))
                        if fila.get("Tipo_Cliente") in tipos_lista
                        else 0
                    )
                    input_tipo = st.selectbox(
                        "Tipo Cliente", tipos_lista, index=idx_tipo
                    )

                    guardar_btn = st.form_submit_button("Guardar Cambios")

                if guardar_btn:
                    usuario_logueado = st.session_state.get(
                        "usuario_actual", "Desconocido"
                    )

                    razon_final = (
                        nueva_razon.strip().upper()
                        if nueva_razon and nueva_razon.strip().upper() != "NAN"
                        else ""
                    )
                    nombre_final = (
                        nuevo_nombre.strip().upper()
                        if nuevo_nombre and nuevo_nombre.strip().upper() != "NAN"
                        else ""
                    )
                    apellido_final = (
                        nuevo_apellido.strip().upper()
                        if nuevo_apellido and nuevo_apellido.strip().upper() != "NAN"
                        else ""
                    )

                    datos_actualizados = {
                        "Nombre": nombre_final,
                        "Apellido": apellido_final,
                        "DNI": nuevo_dni.strip(),
                        "Razón Social": razon_final,
                        "CUIT": nuevo_cuit.strip(),
                        "Telefono": nuevo_telefono.strip(),
                        "Direccion_1": nuevo_dir1.strip().upper(),
                        "Link_Direccion_1": nuevo_link1.strip(),
                        "Direccion_2": nuevo_dir2.strip().upper(),
                        "Link_Direccion_2": nuevo_link2.strip(),
                        "Direccion_3": nuevo_dir3.strip().upper(),
                        "Link_Direccion_3": nuevo_link3.strip(),
                        "Observaciones": nueva_obs.strip(),
                        "Zona": input_zona,
                        "Tipo_Cliente": input_tipo,
                    }

                    if ClienteService.actualizar_cliente(
                        id_modificar,
                        datos_actualizados,
                        fila.to_dict(),
                        usuario_logueado,
                    ):
                        st.success("Guardado correctamente")
                        st.rerun()

                # Eliminar Cliente
                st.divider()
                if rol_usuario == "Administrador":
                    confirmar_del = st.checkbox(
                        "Confirmar eliminación", key="check_del_final"
                    )
                    if st.button("🗑️ Eliminar Cliente", key="btn_del_final"):
                        if confirmar_del:
                            usuario_logueado = st.session_state.get(
                                "usuario_actual", "Desconocido"
                            )
                            if ClienteService.eliminar_cliente(
                                id_modificar, fila.to_dict(), usuario_logueado
                            ):
                                st.success("🗑️ Cliente eliminado.")
                                st.rerun()
                        else:
                            st.warning(
                                "⚠️ Debes marcar la casilla de confirmación."
                            )
