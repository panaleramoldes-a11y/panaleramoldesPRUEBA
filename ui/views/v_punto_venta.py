import json
import streamlit as st
from datetime import datetime
from services.venta_service import VentaService

def render_punto_venta(db):
    st.title("🛒 Punto de Venta (POS)")
    
    # Instancia de servicio
    venta_service = VentaService(db)

    # -------------------------------------------------------------------------
    # INITIALIZE SESSION STATES
    # -------------------------------------------------------------------------
    if 'carrito_vta' not in st.session_state:
        st.session_state.carrito_vta = []
    if 'pagos_split' not in st.session_state:
        st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
    if 'tipo_entrega' not in st.session_state:
        st.session_state.tipo_entrega = "Retiro en Local"
    if 'direccion_entrega' not in st.session_state:
        st.session_state.direccion_entrega = ""
    if 'link_maps_entrega' not in st.session_state:
        st.session_state.link_maps_entrega = ""
    if 'fecha_reparto' not in st.session_state:
        st.session_state.fecha_reparto = datetime.now().date()
    if 'observaciones_entrega' not in st.session_state:
        st.session_state.observaciones_entrega = ""

    # Cargar Catálogos
    df_prod = venta_service.obtener_productos()
    df_cli = venta_service.obtener_clientes()
    df_vend = venta_service.obtener_vendedores()
    df_metodos = venta_service.obtener_metodos_pago()
    metodos_pago_base = [m.get("Nombre_Metodo") for m in df_metodos if m.get("Nombre_Metodo")] if df_metodos else ["Efectivo", "Transferencia", "Débito", "Crédito"]

    # -------------------------------------------------------------------------
    # RECUPERAR VENTAS PENDIENTES (EXPANDER)
    # -------------------------------------------------------------------------
    with st.expander("⏳ Cargar o Recuperar Venta Pendiente", expanded=False):
        pendientes = venta_service.obtener_ventas_pendientes()
        if pendientes:
            opciones_pend = {f"{p['ID_Pendiente']} - {p['Cliente']} (${p.get('Fecha')})": p for p in pendientes}
            seleccion_pend = st.selectbox("Seleccionar Venta Pendiente", ["-- Seleccionar --"] + list(opciones_pend.keys()))
            
            if seleccion_pend != "-- Seleccionar --":
                p_data = opciones_pend[seleccion_pend]
                if st.button("📥 CARGAR ESTA VENTA AL CARRITO", type="primary"):
                    try:
                        st.session_state.carrito_vta = json.loads(p_data["Detalle_JSON"]) if p_data.get("Detalle_JSON") else []
                        st.session_state.pagos_split = json.loads(p_data["Pagos_JSON"]) if p_data.get("Pagos_JSON") else [{"metodo": "Efectivo", "monto": 0.0}]
                        st.session_state.tipo_entrega = p_data.get("Forma_Entrega", "Retiro en Local")
                        st.session_state.direccion_entrega = p_data.get("Direccion_Entrega", "")
                        st.session_state.link_maps_entrega = p_data.get("Link_Maps_Entrega", "")
                        st.session_state.observaciones_entrega = p_data.get("Observaciones", "")
                        
                        f_ent = p_data.get("Fecha_Entrega")
                        if f_ent:
                            try:
                                st.session_state.fecha_reparto = datetime.strptime(f_ent, '%Y-%m-%d').date()
                            except:
                                pass
                                
                        st.session_state.id_pendiente_cargado = p_data["ID_Pendiente"]
                        st.session_state.id_cliente_recuperado = p_data.get("ID_Cliente_Pendiente")
                        st.success(f"Venta {p_data['ID_Pendiente']} cargada correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al reconstruir el carrito: {e}")
        else:
            st.info("No hay ventas pendientes guardadas.")

    st.divider()

    # -------------------------------------------------------------------------
    # SECCIÓN DE CLIENTE Y VENDEDOR
    # -------------------------------------------------------------------------
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        dict_clientes = {f"{c.get('Nombre', '')} (ID: {c.get('ID_Cliente')})": c.get('ID_Cliente') for c in df_cli} if df_cli else {}
        idx_cli = 0
        if 'id_cliente_recuperado' in st.session_state:
            for i, val in enumerate(dict_clientes.values()):
                if val == st.session_state.id_cliente_recuperado:
                    idx_cli = i
                    break

        cliente_sel = st.selectbox("👤 Cliente", list(dict_clientes.keys()) if dict_clientes else ["Consumidor Final"], index=idx_cli)
        id_cliente_final = dict_clientes.get(cliente_sel, "CF")
        cliente_nombre_final = cliente_sel.split(" (ID:")[0] if " (ID:" in cliente_sel else cliente_sel

    with col_c2:
        dict_vend = {f"{v.get('Nombre', '')}": v.get('ID_Usuario') for v in df_vend} if df_vend else {}
        vendedor_sel = st.selectbox("👨‍💼 Vendedor", list(dict_vend.keys()) if dict_vend else ["General"])
        vendedor_id_final = dict_vend.get(vendedor_sel, "1")

    # -------------------------------------------------------------------------
    # BÚSQUEDA Y SELECCIÓN DE PRODUCTOS
    # -------------------------------------------------------------------------
    st.subheader("🛍️ Agregar Productos")
    dict_prod = {f"{p.get('Nombre')} - [${p.get('Precio_Venta', 0):,.0f}] (Stock: {p.get('Stock_Actual', 0)})": p for p in df_prod} if df_prod else {}
    
    col_p1, col_p2, col_p3 = st.columns([3, 1, 1])
    with col_p1:
        prod_seleccionado_str = st.selectbox("Buscar Producto", ["-- Seleccionar --"] + list(dict_prod.keys()))
    with col_p2:
        cant_agregar = st.number_input("Cantidad", min_value=1, value=1, step=1)
    with col_p3:
        st.write("")
        st.write("")
        if st.button("➕ Agregar", width='stretch'):
            if prod_seleccionado_str != "-- Seleccionar --":
                prod_obj = dict_prod[prod_seleccionado_str]
                item_id = prod_obj.get("ID_Producto")
                
                # Revisar si ya está en el carrito
                encontrado = False
                for item in st.session_state.carrito_vta:
                    if item["id"] == item_id:
                        item["cantidad"] += cant_agregar
                        item["subtotal"] = item["cantidad"] * item["precio"]
                        encontrado = True
                        break
                
                if not encontrado:
                    precio = float(prod_obj.get("Precio_Venta", 0))
                    st.session_state.carrito_vta.append({
                        "id": item_id,
                        "nombre": prod_obj.get("Nombre"),
                        "cantidad": cant_agregar,
                        "precio": precio,
                        "subtotal": cant_agregar * precio
                    })
                st.rerun()

    # -------------------------------------------------------------------------
    # VISUALIZACIÓN Y GESTIÓN DEL CARRITO
    # -------------------------------------------------------------------------
    st.subheader("🛒 Carrito de Compras")
    subtotal_bruto = 0.0

    if st.session_state.carrito_vta:
        for idx, item in enumerate(st.session_state.carrito_vta):
            col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns([3, 1, 1, 1, 0.5])
            with col_i1:
                st.write(f"**{item['nombre']}**")
            with col_i2:
                nueva_cant = st.number_input(f"Cant", min_value=1, value=int(item['cantidad']), key=f"cant_{idx}")
                if nueva_cant != item['cantidad']:
                    item['cantidad'] = nueva_cant
                    item['subtotal'] = nueva_cant * item['precio']
                    st.rerun()
            with col_i3:
                st.write(f"${item['precio']:,.2f}")
            with col_i4:
                st.write(f"**${item['subtotal']:,.2f}**")
            with col_i5:
                if st.button("❌", key=f"del_{idx}"):
                    st.session_state.carrito_vta.pop(idx)
                    st.rerun()
            subtotal_bruto += item['subtotal']
            st.divider()
    else:
        st.info("El carrito está vacío.")

    total_final_vta = subtotal_bruto

    # -------------------------------------------------------------------------
    # FORMA DE ENTREGA Y DETALLES
    # -------------------------------------------------------------------------
    st.subheader("🚚 Forma de Entrega")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.session_state.tipo_entrega = st.radio("Tipo de Entrega", ["Retiro en Local", "Reparto"], index=0 if st.session_state.tipo_entrega == "Retiro en Local" else 1, horizontal=True)
    
    if st.session_state.tipo_entrega == "Reparto":
        with col_e2:
            st.session_state.fecha_reparto = st.date_input("Fecha de Reparto", value=st.session_state.fecha_reparto)
        
        col_dir1, col_dir2 = st.columns(2)
        with col_dir1:
            st.session_state.direccion_entrega = st.text_input("Dirección de Entrega", value=st.session_state.direccion_entrega)
        with col_dir2:
            st.session_state.link_maps_entrega = st.text_input("Link Google Maps", value=st.session_state.link_maps_entrega)
            
    st.session_state.observaciones_entrega = st.text_area("Observaciones de la Entrega", value=st.session_state.observaciones_entrega)

    # -------------------------------------------------------------------------
    # PAGOS DIVIDIDOS (SPLIT PAYMENTS)
    # -------------------------------------------------------------------------
    st.subheader("💳 Formas de Pago")
    
    # Agregar método de Gift Card si se activa alguna
    metodos_disponibles = list(metodos_pago_base)
    if st.session_state.get('gc_activa_id'):
        metodos_disponibles.append(f"Gift Card ({st.session_state.get('gc_activa_id')})")

    for idx, pago in enumerate(st.session_state.pagos_split):
        col_m1, col_m2, col_m3 = st.columns([2, 2, 0.5])
        with col_m1:
            m_idx = metodos_disponibles.index(pago["metodo"]) if pago["metodo"] in metodos_disponibles else 0
            pago["metodo"] = st.selectbox(f"Método #{idx+1}", metodos_disponibles, index=m_idx, key=f"metodo_{idx}")
        with col_m2:
            pago["monto"] = st.number_input(f"Monto #{idx+1}", min_value=0.0, value=float(pago["monto"]), step=100.0, key=f"monto_{idx}")
        with col_m3:
            st.write("")
            st.write("")
            if len(st.session_state.pagos_split) > 1 and st.button("❌", key=f"del_pago_{idx}"):
                st.session_state.pagos_split.pop(idx)
                st.rerun()

    if st.button("➕ Agregar otro método de pago"):
        st.session_state.pagos_split.append({"metodo": "Efectivo", "monto": 0.0})
        st.rerun()

    # Resumen de Totales
    suma_pagos = sum(float(p["monto"]) for p in st.session_state.pagos_split)
    diferencia = total_final_vta - suma_pagos

    st.markdown(f"### **TOTAL VENTA: ${total_final_vta:,.2f}**")
    if abs(diferencia) > 0.01:
        st.warning(f"Falta cubrir / Excedente: **${diferencia:,.2f}** (Suma cargada: ${suma_pagos:,.2f})")
    else:
        st.success("✅ El total coincide perfectamente con la suma de los pagos.")

    # -------------------------------------------------------------------------
    # 6. BOTONES DE CIERRE (Solo visibles si hay productos en el carrito)
    # -------------------------------------------------------------------------
    if st.session_state.carrito_vta:
        st.divider()
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            if st.button("🏁 FINALIZAR Y REGISTRAR VENTA", width='stretch', type="primary"):
                # 0. Verificación de sumas de pago
                if abs(suma_pagos - total_final_vta) > 0.01:
                    st.error(f"¡Error! La suma de los pagos (${suma_pagos:.2f}) no coincide con el total (${total_final_vta:.2f})")
                else:
                    # 1. Validación de stock real
                    ok_stock, err_stock = venta_service.validar_stock_carrito(st.session_state.carrito_vta)
                    if not ok_stock:
                        st.error(err_stock)
                    else:
                        # 2. Validación de Gift Card
                        gc_id_activa = st.session_state.get('gc_activa_id')
                        ok_gc, err_gc = venta_service.validar_saldo_giftcard(st.session_state.pagos_split, gc_id_activa)
                        if not ok_gc:
                            st.error(err_gc)
                        else:
                            # 3. Procesar venta sin errores
                            try:
                                id_pend = st.session_state.get('id_pendiente_cargado')
                                usr_nom = st.session_state.get('usuario_nombre')
                                
                                venta_service.registrar_venta(
                                    carrito=st.session_state.carrito_vta,
                                    pagos_split=st.session_state.pagos_split,
                                    total_final=total_final_vta,
                                    tipo_entrega=st.session_state.tipo_entrega,
                                    direccion_entrega=st.session_state.direccion_entrega,
                                    observaciones_entrega=st.session_state.get('observaciones_entrega', ''),
                                    id_cliente=id_cliente_final,
                                    id_vendedor=vendedor_id_final,
                                    usuario_nombre=usr_nom,
                                    gc_activa_id=gc_id_activa,
                                    id_pendiente=id_pend
                                )

                                # Limpieza del Estado de Sesión tras éxito
                                if 'id_pendiente_cargado' in st.session_state:
                                    del st.session_state.id_pendiente_cargado

                                st.success("✅ Venta registrada correctamente!")
                                st.session_state.carrito_vta = []
                                st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
                                st.session_state.observaciones_entrega = ""
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error al registrar: {e}")

        with col_f2:
            if st.button("⏳ GUARDAR COMO PENDIENTE", width='stretch'):
                try:
                    id_pend_cargado = st.session_state.get('id_pendiente_cargado')
                    es_nuevo, msg = venta_service.guardar_pendiente(
                        carrito=st.session_state.carrito_vta,
                        pagos_split=st.session_state.pagos_split,
                        cliente_nombre=cliente_nombre_final,
                        id_cliente=id_cliente_final,
                        vendedor_id=vendedor_id_final,
                        tipo_entrega=st.session_state.tipo_entrega,
                        direccion_entrega=st.session_state.direccion_entrega,
                        link_maps=st.session_state.link_maps_entrega,
                        fecha_reparto=st.session_state.fecha_reparto,
                        observaciones=st.session_state.get('observaciones_entrega', ''),
                        id_pendiente_cargado=id_pend_cargado
                    )

                    st.toast(msg, icon="🔄" if not es_nuevo else "⏳")

                    # Limpieza tras guardar pendiente
                    st.session_state.carrito_vta = []
                    st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
                    st.session_state.observaciones_entrega = ""
                    if 'id_pendiente_cargado' in st.session_state:
                        del st.session_state.id_pendiente_cargado
                    if 'id_cliente_recuperado' in st.session_state:
                        del st.session_state.id_cliente_recuperado
                        
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al guardar pendiente: {e}")
    else:
        st.info("El carrito está vacío.")
