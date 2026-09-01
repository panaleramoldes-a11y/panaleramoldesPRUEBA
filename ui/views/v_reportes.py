"""
ui/views/v_reportes.py
Vista principal para la visualización de tableros de control y reportes de inteligencia de ventas.
"""

from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from services.reportes_service import cargar_datos_reportes


def render_reportes_view():
    """
    Renderiza el panel interactivo de reportes de ventas e inteligencia comercial.
    """
    st.title("📊 Panel de Reportes e Inteligencia de Ventas")

    # --- FILTROS DE FECHA ---
    meses_dict = {
        "Enero": 1,
        "Febrero": 2,
        "Marzo": 3,
        "Abril": 4,
        "Mayo": 5,
        "Junio": 6,
        "Julio": 7,
        "Agosto": 8,
        "Septiembre": 9,
        "Octubre": 10,
        "Noviembre": 11,
        "Diciembre": 12,
    }

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        mes_sel = st.selectbox(
            "Mes", list(meses_dict.keys()), index=datetime.now().month - 1
        )
    with col_f2:
        anio_sel = st.selectbox("Año", [2024, 2025, 2026, 2027], index=2)

    mes_num = meses_dict[mes_sel]

    # --- CARGA DE DATOS DESDE EL SERVICIO ---
    with st.spinner("Consultando base de datos..."):
        datos = cargar_datos_reportes(mes_num, anio_sel)

    if datos is None or datos["cabecera"].empty:
        st.warning(
            f"No hay registros de ventas para el período seleccionado ({mes_sel} {anio_sel})."
        )
        return

    df_cab = datos["cabecera"]
    df_det = datos["detalle"]
    df_pag = datos["pagos"]

    # --- MÉTRICAS PRINCIPALES (KPIs) ---
    ventas_totales = (
        float(df_cab["Total"].sum()) if "Total" in df_cab.columns else 0.0
    )
    total_operaciones = len(df_cab)
    ticket_promedio = (
        ventas_totales / total_operaciones if total_operaciones > 0 else 0.0
    )

    utilidad_total = (
        float(df_det["Ganancia_Bruta"].sum())
        if not df_det.empty and "Ganancia_Bruta" in df_det.columns
        else 0.0
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Ventas Totales", f"${ventas_totales:,.2f}")
    col2.metric("📈 Utilidad Bruta Est.", f"${utilidad_total:,.2f}")
    col3.metric("🧾 Total Operaciones", f"{total_operaciones}")
    col4.metric("🎯 Ticket Promedio", f"${ticket_promedio:,.2f}")

    st.divider()

    # --- SECCIÓN 1: PRODUCTOS MÁS VENDIDOS Y FORMAS DE PAGO ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🔥 Top 10 Productos Más Vendidos")
        if (
            not df_det.empty
            and "Nombre" in df_det.columns
            and "Cantidad" in df_det.columns
        ):
            df_det["Cantidad"] = pd.to_numeric(
                df_det["Cantidad"], errors="coerce"
            ).fillna(0)
            df_det["Nombre"] = df_det["Nombre"].astype(str)

            top_prod = (
                df_det.groupby("Nombre")["Cantidad"]
                .sum()
                .reset_index()
                .sort_values(by="Cantidad", ascending=True)
                .tail(10)
            )

            fig_prod = px.bar(
                top_prod,
                x="Cantidad",
                y="Nombre",
                orientation="h",
                text="Cantidad",
                color_discrete_sequence=["#2E86C1"],
            )
            fig_prod.update_layout(xaxis_title="Unidades Vendidas", yaxis_title="")
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("Sin detalle de productos disponible.")

    with c2:
        st.subheader("💳 Distribución por Formas de Pago")
        if (
            not df_pag.empty
            and "Metodo_Pago" in df_pag.columns
            and "Monto" in df_pag.columns
        ):
            df_pag["Monto"] = pd.to_numeric(
                df_pag["Monto"], errors="coerce"
            ).fillna(0)
            pagos_sum = df_pag.groupby("Metodo_Pago")["Monto"].sum().reset_index()

            fig_pago = px.pie(
                pagos_sum,
                names="Metodo_Pago",
                values="Monto",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(fig_pago, use_container_width=True)
        else:
            st.info("Sin datos de formas de pago.")

    st.divider()

    # --- SECCIÓN 2: MARCAS Y FORMA DE ENTREGA ---
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("🏷️ Top Marcas por Facturación")
        if (
            not df_det.empty
            and "Marca" in df_det.columns
            and "Subtotal" in df_det.columns
        ):
            df_det["Subtotal"] = pd.to_numeric(
                df_det["Subtotal"], errors="coerce"
            ).fillna(0)
            df_det_marca = df_det.dropna(subset=["Marca"])
            top_marcas = (
                df_det_marca.groupby("Marca")["Subtotal"]
                .sum()
                .reset_index()
                .sort_values(by="Subtotal", ascending=False)
                .head(5)
            )

            fig_marcas = px.bar(
                top_marcas,
                x="Marca",
                y="Subtotal",
                text_auto="$.2s",
                color_discrete_sequence=["#28B463"],
            )
            fig_marcas.update_layout(
                yaxis_title="Total Facturado ($)", xaxis_title=""
            )
            st.plotly_chart(fig_marcas, use_container_width=True)
        else:
            st.info("Sin información de marcas.")

    with c4:
        st.subheader("🚚 Ventas: Mostrador vs Reparto")
        if "Forma_Entrega" in df_cab.columns:
            entrega_df = df_cab["Forma_Entrega"].value_counts().reset_index()
            entrega_df.columns = ["Forma_Entrega", "Cantidad"]
            fig_entrega = px.pie(
                entrega_df,
                names="Forma_Entrega",
                values="Cantidad",
                color_discrete_sequence=["#F39C12", "#8E44AD"],
            )
            st.plotly_chart(fig_entrega, use_container_width=True)
        else:
            st.info("Sin datos sobre forma de entrega.")

    st.divider()

    # --- SECCIÓN 3: RANKING DE VENDEDORES Y TOP CLIENTES ---
    c5, c6 = st.columns(2)

    with c5:
        st.subheader("👥 Ranking de Vendedores")
        if "Vendedor_Nombre" in df_cab.columns and "Total" in df_cab.columns:
            df_cab["Total"] = pd.to_numeric(
                df_cab["Total"], errors="coerce"
            ).fillna(0)
            vend_df = (
                df_cab.groupby("Vendedor_Nombre")["Total"]
                .sum()
                .reset_index()
                .sort_values(by="Total", ascending=False)
            )

            fig_vend = px.bar(
                vend_df,
                x="Vendedor_Nombre",
                y="Total",
                text_auto="$.2s",
                color_discrete_sequence=["#16A085"],
            )
            fig_vend.update_layout(xaxis_title="", yaxis_title="Total Vendido ($)")
            st.plotly_chart(fig_vend, use_container_width=True)
        else:
            st.info("Sin información de vendedores.")

    with c6:
        st.subheader("⭐ Top 10 Clientes del Mes")
        if "Cliente_Nombre" in df_cab.columns:
            cli_df = df_cab[df_cab["Cliente_Nombre"] != "Cliente General"]
            if not cli_df.empty:
                top_cli = (
                    cli_df.groupby("Cliente_Nombre")["Total"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Total", ascending=False)
                    .head(10)
                )
                st.dataframe(
                    top_cli.rename(
                        columns={
                            "Cliente_Nombre": "Cliente",
                            "Total": "Total Comprado ($)",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "Todas las ventas del mes fueron registradas a Cliente General / Mostrador."
                )

    st.divider()

    # --- SECCIÓN 4: MATRIZ DE MARGEN Y RENTABILIDAD POR PRODUCTO ---
    st.subheader("📊 Matriz de Rentabilidad por Producto")
    if not df_det.empty and "Ganancia_Bruta" in df_det.columns:
        rent_df = (
            df_det.groupby("Nombre")
            .agg(
                Unidades_Vendidas=("Cantidad", "sum"),
                Facturacion_Total=("Subtotal", "sum"),
                Ganancia_Total=("Ganancia_Bruta", "sum"),
            )
            .reset_index()
        )

        rent_df["Margen_%"] = (
            rent_df["Ganancia_Total"] / rent_df["Facturacion_Total"] * 100
        ).round(2)
        rent_df = rent_df.sort_values(by="Ganancia_Total", ascending=False)

        st.dataframe(
            rent_df.style.format(
                {
                    "Facturacion_Total": "${:,.2f}",
                    "Ganancia_Total": "${:,.2f}",
                    "Margen_%": "{:.2f}%",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
