"""
ui/views/v_compras.py
Vista principal de Compras (Gestión de Stock, Costos, Precios y Órdenes).
"""

from datetime import datetime
import streamlit as st
import pandas as pd

from services.compras_service import (
    obtener_historial_compras,
    obtener_detalle_compra,
    obtener_ordenes_compra,
    obtener_detalle_orden,
    activar_producto,
    registrar_orden_compra,
    eliminar_orden_compra,
    registrar_compra_y_cargar_stock,
    calcular_precios_sugeridos,
    generar_texto_whatsapp_precios
)
from services.productos_service import ProductosService
obtener_productos = ProductosService.obtener_productos
from services.proveedores_service import obtener_proveedores


# --- MODALES Y DIÁLOGOS ---
@st.dialog("⚠️ Producto Inactivo Detectado")
def dialog_producto_inactivo(prod_row):
    st.warning(f"El producto **{prod_row['Nombre']}** (ID: {prod_row['ID_Producto']}) está deshabilitado.")
    st.write("¿Deseas reactivarlo e ingresarlo al carrito?")
    col1, col2 = st.columns(2)
    if col1.button("✅ Reactivar e Ingresar", type="primary", use_container_width=True):
        activar_producto(str(prod_row['ID_Producto']))
        st.session_state.prod_a_reactivar = prod_row
        st.rerun()
    if col2.button("❌ Cancelar", use_container_width=True):
        st.rerun()


# --- VISTA PRINCIPAL ---
def render_compras_view():
    st.title("📦 Módulo de Compras e Inventario")

    # Inicialización de Estados
    if "carrito_compra" not in st.session_state:
        st.session_state.carrito_compra = []

    # Cargar datos base
    df_prod = obtener_productos()
    list_prov = obtener_proveedores()

    # --- 1. GABINETE DE HISTORIAL Y ÓRDENES ---
    with st.expander("📁 Gabinete Histórico (Facturas y Órdenes)", expanded=False):
        tab_fact, tab_ord = st.tabs(["📄 Facturas Registradas", "📋 Órdenes de Compra"])

        with tab_fact:
            df_fact = obtener_historial_compras()
            if not df_fact.empty:
                st.dataframe(df_fact, use_container_width=True)
                id_fact_sel = st.selectbox("Ver detalle de Factura:", df_fact["ID_Compra"].unique(), key="sel_fact")
                if id_fact_sel:
                    df_det = obtener_detalle_compra(id_fact_sel)
                    st.dataframe(df_det, use_container_width=True)
            else:
                st.info("No hay facturas registradas.")

        with tab_ord:
            df_ord = obtener_ordenes_compra()
            if not df_ord.empty:
                st.dataframe(df_ord, use_container_width=True)
                col_o1, col_o2 = st.columns(2)
                id_ord_sel = col_o1.selectbox("Seleccionar Orden de Compra:", df_ord["ID_Compra"].unique(), key="sel_ord")

                if col_o2.button("📥 Cargar Orden al Carrito", type="primary"):
                    st.session_state.carrito_compra = obtener_detalle_orden(id_ord_sel)
                    st.session_state.oc_en_edicion = id_ord_sel
                    st.success(f"Orden {id_ord_sel} cargada en el carrito.")
                    st.rerun()

                if col_o2.button("🗑️ Eliminar Orden", type="secondary"):
                    eliminar_orden_compra(id_ord_sel)
                    st.success(f"Orden {id_ord_sel} eliminada.")
                    st.rerun()
            else:
                st.info("No hay órdenes de compra registradas.")

    st.divider()

    # --- 2. REGISTRO / BÚSQUEDA DE PRODUCTOS ---
    st.subheader("🔍 Agregar Productos al Carrito")

    if not df_prod.empty:
        opciones_prod = df_prod.apply(lambda x: f"{x['ID_Producto']} - {x['Nombre']}", axis=1).tolist()
        prod_seleccionado_str = st.selectbox("Buscar por Nombre o Código (EAN/SKU):", [""] + opciones_prod)

        if prod_seleccionado_str:
            id_p = prod_seleccionado_str.split(" - ")[0]
            prod_row = df_prod[df_prod["ID_Producto"].astype(str) == str(id_p)].iloc[0]

            # Verificar si está activo
            if not bool(prod_row.get("Estado", True)):
                dialog_producto_inactivo(prod_row)

            # Agregar si es reactivado o activo
            if bool(prod_row.get("Estado", True)) or st.session_state.get("prod_a_reactivar"):
                if "prod_a_reactivar" in st.session_state:
                    del st.session_state.prod_a_reactivar

                # Formulario simple de inserción rápida
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                cant = c1.number_input("Cantidad:", min_value=1, value=1, step=1)
                costo = c2.number_input("Costo Unitario ($):", min_value=0.0, value=float(prod_row.get("Precio_Costo", 0.0)), step=10.0)

                if c4.button("➕ Agregar", type="primary"):
                    # Verificar si ya existe en carrito
                    existe = False
                    for item in st.session_state.carrito_compra:
                        if str(item['id']) == str(id_p):
                            item['cantidad'] += cant
                            item['costo'] = costo
                            item['subtotal'] = item['cantidad'] * item['costo']
                            existe = True
                            break

                    if not existe:
                        rubro = prod_row.get("Rubro", "GENERAL")
                        sugeridos = calcular_precios_sugeridos(costo, rubro)
                        st.session_state.carrito_compra.append({
                            "id": str(id_p),
                            "nombre": prod_row["Nombre"],
                            "cantidad": cant,
                            "costo": costo,
                            "subtotal": cant * costo,
                            "Precio_1": float(prod_row.get("Precio_1", sugeridos["Precio_1"])),
                            "Precio_2": float(prod_row.get("Precio_2", sugeridos["Precio_2"])),
                            "Precio_3": float(prod_row.get("Precio_3", sugeridos["Precio_3"])),
                            "Precio_4": float(prod_row.get("Precio_4", sugeridos["Precio_4"])),
                            "Precio_5": float(prod_row.get("Precio_5", sugeridos["Precio_5"])),
                            "rubro": rubro
                        })
                    st.rerun()

    # --- 3. EDICIÓN DEL CARRITO Y PRECIOS ---
    st.subheader("🛒 Carrito de Compras y Actualización de Precios")

    if st.session_state.carrito_compra:
        items_a_eliminar = []

        for idx, item in enumerate(st.session_state.carrito_compra):
            with st.expander(f"📦 {item['nombre']} (Cant: {item['cantidad']}) - Subtotal: ${item['subtotal']:,.2f}", expanded=True):
                c_c1, c_c2, c_c3, c_c4 = st.columns([1, 1, 1, 1])
                item['cantidad'] = c_c1.number_input("Cantidad", min_value=1, value=int(item['cantidad']), key=f"cant_{idx}")
                item['costo'] = c_c2.number_input("Costo U.", min_value=0.0, value=float(item['costo']), key=f"costo_{idx}")
                item['subtotal'] = item['cantidad'] * item['costo']

                # Recalcular Precios con botón si es necesario
                if c_c3.button("🔄 Recalcular Sugeridos", key=f"recalc_{idx}"):
                    sug = calcular_precios_sugeridos(item['costo'], item.get('rubro', 'GENERAL'))
                    item['Precio_1'] = sug['Precio_1']
                    item['Precio_2'] = sug['Precio_2']
                    item['Precio_3'] = sug['Precio_3']
                    item['Precio_4'] = sug['Precio_4']
                    item['Precio_5'] = sug['Precio_5']
                    st.rerun()

                if c_c4.button("❌ Eliminar", key=f"del_{idx}"):
                    items_a_eliminar.append(idx)

                # Edición Precios 1 a 5
                st.caption("Precios de Venta P1 a P5:")
                cp1, cp2, cp3, cp4, cp5 = st.columns(5)
                item['Precio_1'] = cp1.number_input("Precio 1", value=float(item.get('Precio_1', 0.0)), key=f"p1_{idx}")
                item['Precio_2'] = cp2.number_input("Precio 2", value=float(item.get('Precio_2', 0.0)), key=f"p2_{idx}")
                item['Precio_3'] = cp3.number_input("Precio 3", value=float(item.get('Precio_3', 0.0)), key=f"p3_{idx}")
                item['Precio_4'] = cp4.number_input("Precio 4", value=float(item.get('Precio_4', 0.0)), key=f"p4_{idx}")
                item['Precio_5'] = cp5.number_input("Precio 5", value=float(item.get('Precio_5', 0.0)), key=f"p5_{idx}")

        # Aplicar borrados
        for idx in reversed(items_a_eliminar):
            st.session_state.carrito_compra.pop(idx)
            st.rerun()

        # Totales
        total_final = sum(item['subtotal'] for item in st.session_state.carrito_compra)
        st.markdown(f"### **TOTAL COMPRA: ${total_final:,.2f}**")

        st.divider()

        # --- DATOS DE LA COMPRA / ORDEN ---
        st.subheader("📑 Datos del Comprobante")
        f1, f2, f3, f4 = st.columns(4)

        prov_sel = f1.selectbox("Proveedor:", list_prov if list_prov else ["General"])
        fecha_factura = f2.date_input("Fecha:", datetime.now())
        pago_compra = f3.selectbox("Método de Pago:", ["Efectivo", "Transferencia", "Cuenta Corriente", "Cheque"])
        nro_fact = f4.text_input("N° Factura / Remito:")

        # Exportar Lista de Precios
        with st.expander("📲 Compartir Precios por WhatsApp"):
            texto_wa = generar_texto_whatsapp_precios(st.session_state.carrito_compra)
            st.text_area("Texto Formateado:", value=texto_wa, height=150)

        # --- BOTONES DE ACCIÓN ---
        col_reg1, col_reg2, col_reg3 = st.columns([1, 1.5, 1])

        # 1. Borrar Carrito
        if col_reg1.button("🗑️ Vaciar Carrito", use_container_width=True):
            st.session_state.carrito_compra = []
            if "oc_en_edicion" in st.session_state:
                del st.session_state.oc_en_edicion
            st.rerun()

        # 2. Guardar Orden de Compra
        if col_reg3.button("📋 Guardar como Órden", use_container_width=True):
            id_oc = registrar_orden_compra(prov_sel, str(fecha_factura), pago_compra, total_final, st.session_state.carrito_compra)
            st.success(f"Orden de Compra {id_oc} registrada con éxito.")
            st.session_state.carrito_compra = []
            if "oc_en_edicion" in st.session_state:
                del st.session_state.oc_en_edicion
            st.rerun()

        # 3. Registrar Compra y Cargar Stock (Lógica solicitada en Parte 2)
        if col_reg2.button("💾 REGISTRAR Y CARGAR STOCK", type="primary", use_container_width=True):
            # Validaciones básicas
            if not nro_fact.strip():
                st.error("⚠️ El N° de Factura / Remito es obligatorio para registrar el stock.")
            else:
                usuario_act = st.session_state.get("usuario_actual", "Admin")
                oc_edicion = st.session_state.get("oc_en_edicion", None)

                registrar_compra_y_cargar_stock(
                    fecha_factura=fecha_factura,
                    proveedor=prov_sel,
                    nro_factura=nro_fact,
                    metodo_pago=pago_compra,
                    total_final=total_final,
                    carrito=st.session_state.carrito_compra,
                    df_prod=df_prod,
                    usuario_logueado=usuario_act,
                    oc_en_edicion=oc_edicion
                )

                # Limpieza local
                if "oc_en_edicion" in st.session_state:
                    del st.session_state.oc_en_edicion

                st.success("¡Compra registrada, stock cargado y Kardex actualizado correctamente!")
                st.session_state.carrito_compra = []
                st.rerun()

    else:
        st.info("El carrito de compras está vacío.")
