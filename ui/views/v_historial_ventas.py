import streamlit as st
import pandas as pd
from services.historial_ventas_service import obtener_historial_ventas, anular_venta

def render():
    st.header("📋 Historial de Ventas")

    # 1. Cargar Datos
    try:
        df_ventas, df_prod = obtener_historial_ventas()
    except Exception as e:
        st.error(str(e))
        st.stop()

    if df_ventas.empty:
        st.info("No hay registros de ventas disponibles.")
        return

    st.caption(f"Filas totales cargadas: {len(df_ventas)}")

    # 2. Filtros
    c1, c2, c3, c4 = st.columns(4)
    min_fecha = df_ventas['Fecha'].min()
    max_fecha = df_ventas['Fecha'].max()

    with c1:
        rango_fechas = st.date_input("Rango de fechas", value=(min_fecha, max_fecha))
    with c2:
        lista_clientes = ["Todos"] + sorted(list(df_ventas['Cliente_Full'].dropna().unique()))
        cliente_filtro = st.selectbox("Cliente", lista_clientes)
    with c3:
        lista_vendedores = ["Todos"] + sorted(list(df_ventas['Vendedor_Full'].dropna().unique()))
        vendedor_filtro = st.selectbox("Vendedor", lista_vendedores)
    with c4:
        lista_pagos = ["Todos"] + sorted(list(df_ventas['Forma_Pago'].dropna().unique()))
        pago_filtro = st.selectbox("Pago", lista_pagos)

    # 3. Aplicar Filtros
    df_f = df_ventas.copy()

    if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
        df_f = df_f[(df_f['Fecha'] >= rango_fechas[0]) & (df_f['Fecha'] <= rango_fechas[1])]
    
    if cliente_filtro != "Todos":
        df_f = df_f[df_f['Cliente_Full'] == cliente_filtro]
    if vendedor_filtro != "Todos":
        df_f = df_f[df_f['Vendedor_Full'] == vendedor_filtro]
    if pago_filtro != "Todos":
        df_f = df_f[df_f['Forma_Pago'] == pago_filtro]

    # Auditoría
    st.divider()
    st.subheader("🔍 Auditoría de Diferencias")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Total en Historial Completo", f"${df_ventas['Total'].sum():,.2f}")
    with col_b:
        st.metric("Total Filtrado", f"${df_f['Total'].sum():,.2f}")
    
    st.caption(f"Filas totales: {len(df_ventas)} | Filas tras filtros: {len(df_f)}")

    # 4. Tabla Principal
    columnas_visibles = ['ID_Venta', 'Fecha', 'Cliente_Full', 'Vendedor_Full', 'Total', 'Forma_Pago', 'Estado']
    st.dataframe(df_f[columnas_visibles], use_container_width=True)

    # 5. Detalle de Venta
    st.divider()
    st.subheader("Detalle de Venta Seleccionada")
    id_sel = st.text_input("Ingrese ID de Venta para ver detalle:")

    if id_sel:
        venta_sel = df_ventas[df_ventas['ID_Venta'].astype(str) == id_sel.strip()]

        if not venta_sel.empty:
            fila_venta = venta_sel.iloc[0]
            detalles = fila_venta.get('VENTAS_DETALLE', [])
            
            if detalles:
                df_det = pd.DataFrame(detalles)
                if not df_prod.empty and 'ID_Producto' in df_det.columns:
                    df_det = df_det.merge(df_prod, on="ID_Producto", how="left")
                
                cols_mostrar = [c for c in ['ID_Venta', 'Nombre', 'Precio_Unitario', 'Cantidad', 'Subtotal'] if c in df_det.columns]
                st.table(df_det[cols_mostrar])

                total_detalle = df_det['Subtotal'].sum() if 'Subtotal' in df_det.columns else 0.0
                st.markdown(f"### **Total de la Venta {id_sel}: ${total_detalle:,.2f}**")

            # Botón de Anulación
            estado_actual = fila_venta.get('Estado', 'ACTIVA')
            if estado_actual != "ANULADA":
                if st.button("🚫 ANULAR ESTA VENTA", type="primary"):
                    usuario_actual = st.session_state.get('usuario_actual', 'Desconocido')
                    try:
                        anular_venta(id_sel, usuario_actual)
                        st.success("✅ Venta anulada con éxito.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al anular: {e}")
            else:
                st.warning("⚠️ Esta venta ya se encuentra ANULADA.")
        else:
            st.error("Venta no encontrada.")

# Aliases de compatibilidad para ejecutar_vista
mostrar_ventas = render
main = render
