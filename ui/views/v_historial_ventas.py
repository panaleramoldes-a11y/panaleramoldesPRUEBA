import pandas as pd
import streamlit as st
from services.historial_ventas_service import HistorialVentasService


def render_historial_ventas():
    st.header("📋 Historial de Ventas")

    # 1. Cargar datos mediante el servicio
    df_ventas = HistorialVentasService.cargar_datos_historial()

    if df_ventas.empty:
        st.info("No hay ventas registradas o no se pudieron cargar los datos.")
        return

    st.write(f"Filas totales cargadas: {len(df_ventas)}")

    # 2. Filtros UI
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        min_date = df_ventas["Fecha"].min()
        max_date = df_ventas["Fecha"].max()
        rango_fechas = st.date_input(
            "Rango de fechas", value=(min_date, max_date)
        )
    with c2:
        clientes_opts = ["Todos"] + sorted(
            df_ventas["Cliente_Full"].dropna().unique().tolist()
        )
        cliente_filtro = st.selectbox("Cliente", clientes_opts)
    with c3:
        vendedores_opts = ["Todos"] + sorted(
            df_ventas["Vendedor_Full"].dropna().unique().tolist()
        )
        vendedor_filtro = st.selectbox("Vendedor", vendedores_opts)
    with c4:
        pagos_opts = ["Todos"] + sorted(
            df_ventas["Forma_Pago"].dropna().unique().tolist()
        )
        pago_filtro = st.selectbox("Pago", pagos_opts)

    # 3. Aplicar Filtros
    df_f = df_ventas.copy()

    if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
        df_f = df_f[
            (df_f["Fecha"] >= rango_fechas[0])
            & (df_f["Fecha"] <= rango_fechas[1])
        ]

    if cliente_filtro != "Todos":
        df_f = df_f[df_f["Cliente_Full"] == cliente_filtro]
    if vendedor_filtro != "Todos":
        df_f = df_f[df_f["Vendedor_Full"] == vendedor_filtro]
    if pago_filtro != "Todos":
        df_f = df_f[df_f["Forma_Pago"] == pago_filtro]

    # --- AUDITORÍA DE DATOS ---
    st.divider()
    st.subheader("🔍 Auditoría de Diferencias")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(
            "Total en DF_Ventas (Original)", f"${df_ventas['Total'].sum():,.2f}"
        )
    with col_b:
        st.metric("Total en DF_F (Filtrado)", f"${df_f['Total'].sum():,.2f}")

    st.write(
        f"Filas totales: {len(df_ventas)} | Filas tras filtros: {len(df_f)}"
    )

    sin_nombre_cnt = (
        df_f["Cliente_Full"].str.contains("Sin Nombre", na=False).sum()
    )
    if sin_nombre_cnt > 0:
        st.warning(
            f"¡Atención! Hay {sin_nombre_cnt} ventas con 'Sin Nombre'. Esto puede estar afectando tus filtros."
        )

    # 4. Mostrar Tabla Principal y Sumatoria
    cols_mostrar = [
        "ID_Venta",
        "Fecha",
        "Cliente_Full",
        "Vendedor_Full",
        "Total",
        "Forma_Pago",
    ]
    cols_existentes = [c for c in cols_mostrar if c in df_f.columns]
    st.dataframe(df_f[cols_existentes], use_container_width=True)
    st.metric("Total Acumulado Filtrado", f"${df_f['Total'].sum():,.2f}")

    # 5. Detalle de Venta
    st.subheader("Detalle de Venta Seleccionada")
    id_sel = st.text_input("Ingrese ID de Venta para ver detalle:")

    if id_sel:
        venta_sel = df_ventas[df_ventas["ID_Venta"].astype(str) == id_sel.strip()]

        if not venta_sel.empty:
            detalles = venta_sel.iloc[0].get("VENTAS_DETALLE", [])
            df_det = pd.DataFrame(detalles)

            if not df_det.empty:
                df_prod = HistorialVentasService.obtener_cat_productos()
                if not df_prod.empty and "ID_Producto" in df_det.columns:
                    df_det = df_det.merge(df_prod, on="ID_Producto", how="left")

                columnas_ordenadas = [
                    c
                    for c in [
                        "ID_Venta",
                        "Nombre",
                        "Precio_Unitario",
                        "Cantidad",
                        "Subtotal",
                    ]
                    if c in df_det.columns
                ]
                st.table(df_det[columnas_ordenadas])

                if "Subtotal" in df_det.columns:
                    total_detalle = df_det["Subtotal"].sum()
                    st.markdown(
                        f"### **Total de la Venta {id_sel}: ${total_detalle:,.2f}**"
                    )
            else:
                st.info("Esta venta no cuenta con ítems detallados.")

            # BOTÓN DE ANULACIÓN
            estado_actual = venta_sel.iloc[0].get("Estado", "ACTIVA")

            if estado_actual != "ANULADA":
                if st.button("🚫 ANULAR ESTA VENTA", type="primary"):
                    usuario_actual = st.session_state.get(
                        "usuario_actual", "Desconocido"
                    )
                    if HistorialVentasService.anular_venta_proceso(
                        id_sel, usuario_actual
                    ):
                        st.success(
                            "✅ Venta anulada, stock devuelto y caja ajustada correctamente."
                        )
                        st.rerun()
            else:
                st.warning("⚠️ Esta venta ya se encuentra ANULADA.")
        else:
            st.error("Venta no encontrada.")


def modulo_ventas():
    """Función wrapper de compatibilidad."""
    render_historial_ventas()
