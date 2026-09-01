"""
ui/views/v_utilidades.py
Vista para la consulta y análisis de rentabilidad / reporte de utilidades.
"""

from datetime import date
import streamlit as st
from services.utilidades_service import (
    filtrar_utilidades,
    obtener_datos_utilidad_base,
)


def render_utilidades_view():
    st.title("📈 Reporte de Utilidades")
    st.subheader("Reporte de Rentabilidad Detallado")

    df_base = obtener_datos_utilidad_base()

    if df_base.empty:
        st.info("No hay registros de ventas o productos para calcular la utilidad.")
        return

    st.write("---")

    # Rango de fechas por defecto
    min_fecha = df_base["Fecha"].min().date()
    max_fecha = df_base["Fecha"].max().date()

    c1, c2 = st.columns(2)
    with c1:
        fecha_inicio = st.date_input("Desde", min_fecha)
    with c2:
        fecha_fin = st.date_input("Hasta", max_fecha)

    # Filtros multiselección
    opciones_rubros = sorted(df_base["Rubro"].dropna().unique().tolist())
    opciones_marcas = sorted(df_base["Marca"].dropna().unique().tolist())
    opciones_nombres = sorted(df_base["Nombre"].dropna().unique().tolist())

    rubros_sel = st.multiselect("Filtrar por Rubro", opciones_rubros)
    marcas_sel = st.multiselect("Filtrar por Marca", opciones_marcas)
    nombres_sel = st.multiselect("Filtrar por Producto", opciones_nombres)

    # Aplicación de filtros
    df_filtrado = filtrar_utilidades(
        df=df_base,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        rubros=rubros_sel,
        marcas=marcas_sel,
        nombres=nombres_sel,
    )

    # Métricas y tabla de resultados
    utilidad_total = (
        df_filtrado["Utilidad_Bruta"].sum() if not df_filtrado.empty else 0.0
    )
    st.metric("💰 Utilidad Total Filtrada", f"${utilidad_total:,.2f}")

    if not df_filtrado.empty:
        # Formateo de fecha para render
        df_display = df_filtrado.copy()
        df_display["Fecha"] = df_display["Fecha"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        columnas_mostrar = [
            "Fecha",
            "Nombre",
            "Rubro",
            "Marca",
            "Cantidad",
            "Utilidad_Bruta",
        ]

        st.dataframe(
            df_display[columnas_mostrar],
            hide_index=True,
            use_container_width=True,
            column_config={
                "Utilidad_Bruta": st.column_config.NumberColumn(
                    "Utilidad Bruta", format="$ %.2f"
                ),
                "Cantidad": st.column_config.NumberColumn(
                    "Cantidad", format="%d"
                ),
            },
        )
    else:
        st.warning(
            "No se encontraron registros con los filtros seleccionados."
        )
