"""
services/reportes_service.py
Capa de servicio para la extracción, cruce y procesamiento de datos analíticos.
"""

from typing import Dict, Optional
import pandas as pd
import streamlit as st
from config.database import db


def cargar_datos_reportes(mes_num: int, anio_num: int) -> Optional[Dict[str, pd.DataFrame]]:
    """
    Carga y procesa los datos desde Supabase para el mes y año seleccionados.

    Args:
        mes_num (int): Número del mes (1-12).
        anio_num (int): Año a consultar.

    Returns:
        Optional[Dict[str, pd.DataFrame]]: Diccionario con DataFrames 'cabecera', 'detalle' y 'pagos',
        o None en caso de error/sin datos.
    """
    try:
        # Definir rango de fechas para el mes seleccionado
        fecha_inicio = f"{anio_num}-{mes_num:02d}-01"
        if mes_num == 12:
            fecha_fin = f"{anio_num + 1}-01-01"
        else:
            fecha_fin = f"{anio_num}-{mes_num + 1:02d}-01"

        # 1. Obtener VENTAS_CABECERA del mes
        res_cab = (
            db.table("VENTAS_CABECERA")
            .select("*")
            .gte("Fecha", fecha_inicio)
            .lt("Fecha", fecha_fin)
            .neq("Estado", "Anulada")
            .execute()
        )
        df_cabecera = pd.DataFrame(res_cab.data or [])

        if df_cabecera.empty:
            return None

        ids_ventas = df_cabecera["ID_Venta"].tolist()

        # 2. Obtener VENTAS_DETALLE para los IDs del mes
        res_det = (
            db.table("VENTAS_DETALLE")
            .select("*")
            .in_("ID_Venta", ids_ventas)
            .execute()
        )
        df_detalle = pd.DataFrame(res_det.data or [])

        # 3. Obtener VENTAS_PAGOS para los IDs del mes
        res_pagos = (
            db.table("VENTAS_PAGOS")
            .select("*")
            .in_("ID_Venta", ids_ventas)
            .execute()
        )
        df_pagos = pd.DataFrame(res_pagos.data or [])

        # 4. Obtener PRODUCTOS
        res_prod = db.table("PRODUCTOS").select("ID_Producto, Nombre, Marca, Rubro").execute()
        df_productos = pd.DataFrame(res_prod.data or [])

        # 5. Obtener CLIENTES
        res_cli = db.table("CLIENTES").select("*").execute()
        df_clientes = pd.DataFrame(res_cli.data or [])

        # 6. Obtener VENDEDORES
        res_vend = db.table("VENDEDORES").select("ID_Vendedor, Nombre, Apellido").execute()
        df_vendedores = pd.DataFrame(res_vend.data or [])

        # --- ENSAMBLADO Y CRUCES DE DATOS ---

        # Merge de Detalle con Productos
        if not df_detalle.empty and not df_productos.empty:
            df_detalle = df_detalle.merge(df_productos, on="ID_Producto", how="left")
            df_detalle["Nombre"] = df_detalle["Nombre"].fillna(df_detalle["ID_Producto"])
            df_detalle["Precio_Costo_Unitario"] = df_detalle["Precio_Costo_Unitario"].fillna(0)
            df_detalle["Costo_Total"] = df_detalle["Cantidad"] * df_detalle["Precio_Costo_Unitario"]
            df_detalle["Ganancia_Bruta"] = df_detalle["Subtotal"] - df_detalle["Costo_Total"]

        # Merge Cabecera con Clientes
        if not df_clientes.empty and "ID_Cliente" in df_cabecera.columns:
            col_razon = "Razón Social" if "Razón Social" in df_clientes.columns else "RazónSocial"

            df_clientes["Cliente_Nombre"] = df_clientes.apply(
                lambda r: r[col_razon]
                if col_razon in r and pd.notnull(r[col_razon]) and str(r[col_razon]).strip() != ""
                else f"{r.get('Nombre', '') or ''} {r.get('Apellido', '') or ''}".strip(),
                axis=1,
            )
            df_cabecera = df_cabecera.merge(
                df_clientes[["ID_Cliente", "Cliente_Nombre"]],
                on="ID_Cliente",
                how="left",
            )
            df_cabecera["Cliente_Nombre"] = df_cabecera["Cliente_Nombre"].fillna("Cliente General")

        # Merge Cabecera con Vendedores
        if not df_vendedores.empty and "ID_Vendedor" in df_cabecera.columns:
            df_vendedores["Vendedor_Nombre"] = (
                df_vendedores["Nombre"].fillna("") + " " + df_vendedores["Apellido"].fillna("")
            ).str.strip()
            df_cabecera = df_cabecera.merge(
                df_vendedores[["ID_Vendedor", "Vendedor_Nombre"]],
                on="ID_Vendedor",
                how="left",
            )
            df_cabecera["Vendedor_Nombre"] = df_cabecera["Vendedor_Nombre"].fillna(
                df_cabecera["ID_Vendedor"]
            )

        return {
            "cabecera": df_cabecera,
            "detalle": df_detalle,
            "pagos": df_pagos,
        }

    except Exception as e:
        st.error(f"Error cargando datos de Supabase para reportes: {e}")
        return None
