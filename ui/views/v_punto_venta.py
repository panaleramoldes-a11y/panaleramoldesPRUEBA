import streamlit as st
import pandas as pd
from datetime import datetime
import json
import re

from config.database import db
import services.venta_service as venta_service

def render_punto_venta_view():
    st.markdown("### 🛒 Punto de Venta")

    # --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
    if "carrito_vta" not in st.session_state:
        st.session_state.carrito_vta = []
    if "pagos_split" not in st.session_state:
        st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
    if "tipo_entrega" not in st.session_state:
        st.session_state.tipo_entrega = "Retira en Local"
    if "direccion_entrega" not in st.session_state:
        st.session_state.direccion_entrega = ""
    if "link_maps_entrega" not in st.session_state:
        st.session_state.link_maps_entrega = ""
    if "fecha_reparto" not in st.session_state:
        st.session_state.fecha_reparto = datetime.now().strftime("%Y-%m-%d")

    # ==========================================
    # 1. SECCIÓN VENDEDOR Y CLIENTE
    # ==========================================
    col_vended, col_cli = st.columns(2)

    with col_vended:
        res_vendedores = db.table("USUARIOS").select("ID_Usuario, Nombre").execute()
        dict_vendedores = {v['Nombre']: v['ID_Usuario'] for v in res_vendedores.data} if res_vendedores.data else {}
        
        lista_nombres_v = list(dict_vendedores.keys())
        idx_def_v = 0
        if "usuario_nombre" in st.session_state and st.session_state.usuario_nombre in lista_nombres_v:
            idx_def_v = lista_nombres_v.index(st.session_state.usuario_nombre)

        vendedor_sel = st.selectbox("👔 Vendedor", options=lista_nombres_v, index=idx_def_v)
        vendedor_id_final = dict_vendedores.get(vendedor_sel)

    with col_cli:
        res_clientes = db.table("CLIENTES").select("ID_Cliente, Nombre, Telefono, Direccion, Link_GoogleMaps").execute()
        dict_clientes = {c['Nombre']: c for c in res_clientes.data} if res_clientes.data else {}
        
        lista_nombres_c = list(dict_clientes.keys())
        idx_cli_def = 0
        
        if 'id_cliente_recuperado' in st.session_state:
            for i, n in enumerate(lista_nombres_c):
                if dict_clientes[n]['ID_Cliente'] == st.session_state.id_cliente_recuperado:
                    idx_cli_def = i
                    break

        cliente_sel = st.selectbox("👤 Cliente", options=lista_nombres_c, index=idx_cli_def)
        cliente_obj = dict_clientes.get(cliente_sel, {})
        id_cliente_final = cliente_obj.get('ID_Cliente')
        cliente_nombre_final = cliente_sel

    st.divider()

    # ==========================================
    # 2. BÚSQUEDA Y SELECCIÓN DE PRODUCTOS
    # ==========================================
    st.subheader("🔍 Seleccionar Productos")
    
    col_busqueda, col_cant = st.columns([3, 1])

    with col_busqueda:
        res_prods = db.table("PRODUCTOS").select("ID_Producto, Nombre, Precio_Venta, Stock_Actual, Es_Stockeable").execute()
        
        dict_prods = {}
        opciones_prods = []
        if res_prods.data:
            for p in res_prods.data:
                label = f"{p['ID_Producto']} - {p['Nombre']} (${p['Precio_Venta']:,.2f})"
                dict_prods[label] = p
                opciones_prods.append(label)

        prod_seleccionado_label = st.selectbox("Buscar por código o nombre:", options=[""] + opciones_prods, index=0)

    with col_cant:
        cantidad_ingresada = st.number_input("Cantidad:", min_value=1, value=1, step=1)

    if st.button("➕ Agregar al Carrito", type="secondary", width='stretch'):
        if prod_seleccionado_label and prod_seleccionado_label in dict_prods:
            p_data = dict_prods[prod_seleccionado_label]
            
            # Verificar si ya existe en el carrito
            existe = False
            for item in st.session_state.carrito_vta:
                if item["id"] == p_data["ID_Producto"]:
                    item["cantidad"] += cantidad_ingresada
                    item["subtotal"] = item["cantidad"] * item["precio"]
                    existe = True
                    break

            if not existe:
                st.session_state.carrito_vta.append({
                    "id": p_data["ID_Producto"],
                    "nombre": p_data["Nombre"],
                    "precio": float(p_data["Precio_Venta"]),
                    "cantidad": int(cantidad_ingresada),
                    "subtotal": float(p_data["Precio_Venta"]) * int(cantidad_ingresada)
                })
            st.toast(f"Agregado: {p_data['Nombre']}", icon="🛒")
            st.rerun()

    # ==========================================
    # 3. DETALLE DEL CARRITO
    # ==========================================
    st.divider()
    st.subheader("🛒 Carrito de Compras")

    if st.session_state.carrito_vta:
        df_carrito = pd.DataFrame(st.session_state.carrito_vta)
        
        # Tabla interactiva con opción de eliminar
        for idx, row in df_carrito.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([1, 3, 2, 2, 2, 1])
            c1.write(f"**{row['id']}**")
            c2.write(row['nombre'])
            c3.write(f"${row['precio']:,.2f}")
            c4.write(f"Cant: {row['cantidad']}")
            c5.write(f"**${row['subtotal']:,.2f}**")
            if c6.button("❌", key=f"del_{idx}"):
                st.session_state.carrito_vta.pop(idx)
                st.rerun()

        subtotal_vta = sum(item["subtotal"] for item in st.session_state.carrito_vta)
        st.markdown(f"#### **Subtotal: ${subtotal_vta:,.2f}**")
    else:
        st.info("El carrito está vacío.")
        subtotal_vta = 0.0

    # ==========================================
    # 4. ENTREGA Y REPARTO
    # ==========================================
    st.divider()
    st.subheader("🚚 Modulo de Entrega")
    
    col_ent1, col_ent2 = st.columns(2)
    with col_ent1:
        st.session_state.tipo_entrega = st.radio("Tipo de Entrega:", ["Retira en Local", "Reparto"], horizontal=True)

    if st.session_state.tipo_entrega == "Reparto":
        with col_ent2:
            st.session_state.fecha_reparto = st.date_input("Fecha de Reparto:", value=datetime.now()).strftime("%Y-%m-%d")
        
        dir_def = cliente_obj.get("Direccion", "") if cliente_obj else ""
        maps_def = cliente_obj.get("Link_GoogleMaps", "") if cliente_obj else ""

        col_dir1, col_dir2 = st.columns(2)
        with col_dir1:
            st.session_state.direccion_entrega = st.text_input("Dirección de Entrega:", value=dir_def)
        with col_dir2:
            st.session_state.link_maps_entrega = st.text_input("Link de Google Maps:", value=maps_def)

        st.session_state.observaciones_entrega = st.text_area("Observaciones para la Entrega:", value=st.session_state.get('observaciones_entrega', ''))

    # ==========================================
    # 5. FORMA DE PAGO
    # ==========================================
    st.divider()
    st.subheader("💳 Formas de Pago")

    res_metodos = db.table("CONFIG_PAGOS").select("Metodo, Recargo_Porcentaje").eq("Activo", True).execute()
    dict_metodos = {m['Metodo']: float(m['Recargo_Porcentaje']) for m in res_metodos.data} if res_metodos.data else {"Efectivo": 0.0}

    total_recargos = 0.0
    nuevos_pagos = []

    for i, pago in enumerate(st.session_state.pagos_split):
        col_p1, col_p2, col_p3, col_p4 = st.columns([3, 2, 2, 1])
        
        with col_p1:
            lista_m = list(dict_metodos.keys())
            idx_m = lista_m.index(pago["metodo"]) if pago["metodo"] in lista_m else 0
            metodo_sel = st.selectbox(f"Método #{i+1}", options=lista_m, index=idx_m, key=f"metodo_{i}")
        
        with col_p2:
            monto_val = st.number_input(f"Monto #{i+1}", min_value=0.0, value=float(pago["monto"]), step=100.0, key=f"monto_{i}")

        recargo_pct = dict_metodos.get(metodo_sel, 0.0)
        recargo_monto = monto_val * (recargo_pct / 100.0)
        total_recargos += recargo_monto

        with col_p3:
            st.write(f"Recargo ({recargo_pct}%): **${recargo_monto:,.2f}**")

        with col_p4:
            if len(st.session_state.pagos_split) > 1:
                if st.button("🗑️", key=f"del_pago_{i}"):
                    st.session_state.pagos_split.pop(i)
                    st.rerun()

        nuevos_pagos.append({"metodo": metodo_sel, "monto": monto_val})

    st.session_state.pagos_split = nuevos_pagos

    if st.button("➕ Agregar otro método de pago"):
        st.session_state.pagos_split.append({"metodo": "Efectivo", "monto": 0.0})
        st.rerun()

    # Manejo de Gift Card activa
    has_gc = any("Gift Card" in p["metodo"] for p in st.session_state.pagos_split)
    if has_gc:
        gc_input = st.text_input("🔑 Ingrese el ID de la Gift Card:")
        if gc_input:
            st.session_state.gc_activa_id = gc_input

    total_final_vta = subtotal_vta + total_recargos
    st.markdown(f"### 💵 **TOTAL A PAGAR: ${total_final_vta:,.2f}**")

    # ==========================================
    # 6. BOTONES DE CIERRE DE LA VENTA
    # ==========================================
    if st.session_state.carrito_vta:
        st.divider()
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            if st.button("🏁 FINALIZAR Y REGISTRAR VENTA", width='stretch', type="primary"):
                suma_pagos = sum(float(p["monto"]) for p in st.session_state.pagos_split)
                if abs(suma_pagos - total_final_vta) > 0.01:
                    st.error(f"¡Error! La suma de los pagos (${suma_pagos:,.2f}) no coincide con el total (${total_final_vta:,.2f})")
                else:
                    ok_stock, msg_stock = venta_service.verificar_stock_suficiente(db, st.session_state.carrito_vta)
                    if not ok_stock:
                        st.error(msg_stock)
                    else:
                        ok_gc, msg_gc = venta_service.verificar_saldo_giftcards(
                            db, 
                            st.session_state.pagos_split, 
                            st.session_state.get('gc_activa_id')
                        )
                        if not ok_gc:
                            st.error(msg_gc)
                        else:
                            try:
                                venta_service.registrar_venta_completa(
                                    db, 
                                    st.session_state, 
                                    id_cliente_final, 
                                    vendedor_id_final, 
                                    total_final_vta
                                )
                                st.success("✅ Venta registrada correctamente!")
                                
                                # Limpieza completa del estado
                                st.session_state.carrito_vta = []
                                st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
                                st.session_state.observaciones_entrega = ""
                                if 'id_pendiente_cargado' in st.session_state:
                                    del st.session_state.id_pendiente_cargado
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error al registrar venta: {e}")

        with col_f2:
            if st.button("⏳ GUARDAR COMO PENDIENTE", width='stretch'):
                try:
                    res = venta_service.guardar_venta_pendiente(
                        db, 
                        st.session_state, 
                        cliente_nombre_final, 
                        id_cliente_final, 
                        vendedor_id_final
                    )
                    
                    if res == "actualizado":
                        st.toast("Venta pendiente actualizada", icon="🔄")
                    else:
                        st.toast("Venta guardada como nuevo pendiente", icon="⏳")

                    # Limpieza del estado
                    st.session_state.carrito_vta = []
                    st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
                    st.session_state.observaciones_entrega = ""
                    if 'id_pendiente_cargado' in st.session_state:
                        del st.session_state.id_pendiente_cargado
                    if 'id_cliente_recuperado' in st.session_state:
                        del st.session_state.id_cliente_recuperado

                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar venta pendiente: {e}")
