import streamlit as st
import pandas as pd
from services.productos_service import ProductosService


def render_productos_view():
    st.title("📦 Gestión de Productos")

    # 1. CARGA INICIAL DE DATOS
    try:
        if 'df_prod' not in st.session_state:
            st.session_state.df_prod = ProductosService.obtener_productos()
        df_prod = st.session_state.df_prod
        lista_proveedores = ProductosService.obtener_proveedores()
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        st.stop()

    # 2. PESTAÑAS DINÁMICAS SEGÚN ROL
    es_admin = st.session_state.get('rol') == "Administrador"
    usuario_actual = st.session_state.get('usuario_nombre') or st.session_state.get('usuario_actual', 'Usuario')

    if es_admin:
        tabs = st.tabs(["🔍 Buscar", "➕ Alta", "✏️ Modificar", "🔄 Cambios", "✂️ Divisor", "📋 Inventario", "📥 Importar", "📜 Histórico"])
        tab_buscar, tab_alta, tab_modificar, tab_cambios, tab_divisor, tab_inventario, tab_importar, tab_historico = tabs
    else:
        tabs = st.tabs(["🔍 Buscar", "🔄 Cambios", "✂️ Divisor", "📋 Inventario"])
        tab_buscar, tab_cambios, tab_divisor, tab_inventario = tabs
        tab_alta, tab_modificar, tab_importar, tab_historico = None, None, None, None

    # --- PESTAÑA BUSCAR ---
    with tab_buscar:
        st.subheader("🔍 Buscador de Productos")
        c_chk1, c_chk2 = st.columns(2)
        solo_con_stock = c_chk1.checkbox("📦 Solo productos con Stock > 0", value=True, key="chk_solo_con_stock")
        mostrar_inactivos = False
        if es_admin:
            mostrar_inactivos = c_chk2.checkbox("👁️ Mostrar productos INACTIVOS", value=False, key="chk_inactivos")

        busqueda_texto = st.text_input("Escriba para filtrar por nombre o código:", placeholder="Ej: pampers, toallitas...", key="busqueda_tab_buscar")

        c1, c2 = st.columns(2)
        rubros = ["Todos"] + [r for r in df_prod['Rubro'].dropna().unique().tolist() if r]
        marcas = ["Todos"] + [m for m in df_prod['Marca'].dropna().unique().tolist() if m]

        filtro_rubro = c1.selectbox("Filtrar por Rubro", rubros, key="filtro_rubro_tab")
        filtro_marca = c2.selectbox("Filtrar por Marca", marcas, key="filtro_marca_tab")

        df_filtrado = df_prod.copy()

        if 'Estado' in df_filtrado.columns and not mostrar_inactivos:
            df_filtrado = df_filtrado[df_filtrado['Estado'] != 'INACTIVO']

        if solo_con_stock and 'Stock_Actual' in df_filtrado.columns:
            df_filtrado['Stock_Actual'] = pd.to_numeric(df_filtrado['Stock_Actual'], errors='coerce').fillna(0)
            df_filtrado = df_filtrado[df_filtrado['Stock_Actual'] > 0]

        if busqueda_texto:
            busqueda_texto = busqueda_texto.lower()
            mask = df_filtrado['Nombre'].str.lower().str.contains(busqueda_texto, na=False) | \
                   df_filtrado['ID_Producto'].astype(str).str.lower().str.contains(busqueda_texto, na=False)
            df_filtrado = df_filtrado[mask]

        if filtro_rubro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Rubro'] == filtro_rubro]
        if filtro_marca != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Marca'] == filtro_marca]

        if 'Nombre' in df_filtrado.columns:
            df_filtrado = df_filtrado.sort_values(by='Nombre', key=lambda col: col.str.lower(), ascending=True)

        df_para_wsp = df_filtrado.copy()

        if not es_admin:
            cols_vendedor = ['Nombre', 'Precio_1', 'Precio_2', 'Precio_3']
            df_filtrado = df_filtrado[[c for c in cols_vendedor if c in df_filtrado.columns]]

        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

        st.markdown("---")
        if st.button("💬 Generar Respuesta para WhatsApp", type="primary", key="btn_wsp_precios_prod"):
            msg_precios_wsp = ProductosService.generar_mensaje_whatsapp(df_para_wsp)
            if not msg_precios_wsp:
                st.warning("⚠️ No hay productos seleccionados para generar la respuesta.")
            else:
                st.text_area("Copiar respuesta para WhatsApp:", value=msg_precios_wsp, height=250, key="txt_area_wsp_precios")

    # --- PESTAÑA CAMBIOS ---
    with tab_cambios:
        st.subheader("🔄 Gestión de Cambios y Devoluciones")

        if es_admin:
            st.divider()
            st.subheader("🛡️ Panel de Supervisión (Admin)")
            pendientes = ProductosService.obtener_pre_cambios_pendientes()

            if pendientes:
                for p in pendientes:
                    with st.container(border=True):
                        st.markdown(f"**Producto:** {p['Nombre']} | **Solicitante:** {p['Usuario']}")
                        st.caption(f"Motivo: {p['Descripción']}")

                        with st.form(f"form_admin_{p['id']}"):
                            col_a, col_b, col_c = st.columns(3)
                            new_cant = col_a.number_input("Cantidad:", value=max(p['Entra'], p['Sale']), key=f"cant_{p['id']}")
                            new_tipo = col_b.selectbox("Tipo:", ["ENTRA", "SALE"], index=0 if p['Entra'] > 0 else 1, key=f"tipo_{p['id']}")
                            new_desc = col_c.text_input("Motivo editado:", value=p['Descripción'], key=f"desc_{p['id']}")

                            btn_col1, btn_col2 = st.columns(2)
                            if btn_col1.form_submit_button("💾 Aprobar y Procesar", use_container_width=True):
                                try:
                                    ProductosService.procesar_aprobacion_cambio(p['id'], p['Código'], p['Nombre'], new_cant, new_tipo, new_desc, usuario_actual)
                                    st.success("✅ Cambio procesado con éxito.")
                                    if 'df_prod' in st.session_state:
                                        del st.session_state['df_prod']
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                            if btn_col2.form_submit_button("❌ Rechazar", use_container_width=True):
                                ProductosService.rechazar_pre_cambio(p['id'])
                                st.rerun()
            else:
                st.info("No hay cambios pendientes.")
            st.divider()

        if 'lista_cambios' not in st.session_state:
            st.session_state.lista_cambios = []

        opciones_productos = (df_prod['Nombre'] + " (ID: " + df_prod['ID_Producto'].astype(str) + ")").tolist()
        prod_seleccionado = st.selectbox("Buscar producto", options=opciones_productos, index=None, placeholder="Escriba para buscar...", key="buscador_cambios")

        if prod_seleccionado:
            nombre_real = prod_seleccionado.split(" (ID: ")[0]
            id_real = prod_seleccionado.split("(ID: ")[1].replace(")", "")

            c1, c2 = st.columns(2)
            cant_sel = c1.number_input("Cantidad:", min_value=1, value=1, key="cant_input")
            tipo_sel = c2.radio("Tipo:", ["ENTRA", "SALE"], horizontal=True, key="tipo_input")

            if st.button("➕ Añadir a la lista"):
                st.session_state.lista_cambios.append({"ID": id_real, "Producto": nombre_real, "Cantidad": cant_sel, "Tipo": tipo_sel})
                st.rerun()

        if st.session_state.lista_cambios:
            st.write("Resumen del movimiento:")
            st.table(pd.DataFrame(st.session_state.lista_cambios))

            if st.button("❌ Limpiar lista"):
                st.session_state.lista_cambios = []
                st.rerun()

            motivo = st.text_input("Motivo del cambio:")
            if st.button("📤 Enviar Pre-cambio a Revisión"):
                try:
                    ProductosService.enviar_pre_cambio(st.session_state.lista_cambios, motivo, usuario_actual)
                    st.success("✅ Enviado a revisión.")
                    st.session_state.lista_cambios = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- PESTAÑA DIVISOR ---
    with tab_divisor:
        st.subheader("✂️ Divisor de Fardos")

        if st.session_state.get('msg_division_exitosa'):
            st.success(st.session_state.msg_division_exitosa)
            st.toast("✅ ¡División procesada correctamente!", icon="🎉")
            del st.session_state['msg_division_exitosa']

        regex_patron = '|'.join([r'\bx12\b', r'\bx24\b', r'\bx30\b', r'\bX12\b', r'\bX24\b', r'\bX30\b'])
        df_filtrado_div = df_prod[
            (df_prod['Rubro'] == 'LECHE') & 
            (df_prod['Stock_Actual'] > 0) & 
            (df_prod['Nombre'].str.contains(regex_patron, regex=True, na=False))
        ].copy()

        if df_filtrado_div.empty:
            st.warning("No hay productos de 'LECHE' identificados como fardos (x12, x24, x30) con stock disponible.")
        else:
            opciones_prod = (df_filtrado_div['ID_Producto'].astype(str) + " - " + df_filtrado_div['Nombre']).tolist()
            id_fardo_sel = st.selectbox("Seleccionar Fardo a dividir:", [""] + opciones_prod, key="div_fardo")

            if id_fardo_sel:
                id_fardo = id_fardo_sel.split(" - ")[0]
                fila_fardo = df_filtrado_div[df_filtrado_div['ID_Producto'].astype(str) == id_fardo].iloc[0]

                st.info(f"Fardo: {fila_fardo['Nombre']} | Stock actual: {fila_fardo['Stock_Actual']} unidades")

                with st.form("form_divisor"):
                    c1, c2 = st.columns(2)
                    unidades = c1.number_input("¿Cuántas unidades trae el fardo?", min_value=1, value=24)
                    id_cajita = c2.text_input("Código de la Cajita Individual:")

                    costo_fardo = float(fila_fardo['Precio_Costo']) if fila_fardo['Precio_Costo'] else 0.0
                    costo_unitario = costo_fardo / unidades if unidades > 0 else 0
                    precio_sugerido = ((int((costo_unitario * 1.40) // 100) + 1) * 100)

                    st.write(f"Costo unitario: `${costo_unitario:,.2f}` | Precio Sugerido: `${precio_sugerido:,.0f}`")

                    if st.form_submit_button("🚀 Confirmar División"):
                        if int(fila_fardo['Stock_Actual']) <= 0:
                            st.error(f"⚠️ El fardo '{fila_fardo['Nombre']}' no cuenta con existencias.")
                        elif not id_cajita.strip():
                            st.error("⚠️ Debe ingresar el código de la cajita individual.")
                        else:
                            st.session_state.pending_division = {
                                "id_fardo": id_fardo, "fila_fardo": fila_fardo,
                                "unidades": int(unidades), "id_cajita": id_cajita.strip()
                            }
                            st.rerun()

                if "pending_division" in st.session_state:
                    p = st.session_state.pending_division
                    st.markdown("---")
                    st.warning(f"⚠️ **¿Confirmar división del fardo?**\n\n- **Fardo:** {p['fila_fardo']['Nombre']}\n- **Cajita:** {p['id_cajita']} (+{p['unidades']} unidades)")

                    col_conf1, col_conf2 = st.columns(2)
                    if col_conf1.button("✅ Sí, Ejecutar División", type="primary", key="btn_confirm_div_yes"):
                        try:
                            nombre_cajita = ProductosService.ejecutar_division_fardo(
                                p['id_fardo'], p['fila_fardo'], p['unidades'], p['id_cajita'], usuario_actual
                            )
                            st.session_state.msg_division_exitosa = f"🎉 **¡División Exitosa!** Se descontó 1 fardo y se acreditaron {p['unidades']} unidades a '{nombre_cajita}'."
                            del st.session_state['pending_division']
                            if 'df_prod' in st.session_state:
                                del st.session_state['df_prod']
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al procesar la división: {e}")

                    if col_conf2.button("❌ Cancelar", key="btn_confirm_div_no"):
                        del st.session_state['pending_division']
                        st.rerun()
