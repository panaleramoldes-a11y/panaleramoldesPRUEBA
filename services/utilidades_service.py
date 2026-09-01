"""
services/utilidades_service.py
Capa de servicio para la extracción y procesamiento del Reporte de Utilidades / Rentabilidad.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
from config.database import db


def obtener_datos_utilidad_base() -> pd.DataFrame:
    """Extrae las tablas necesarias de Supabase, las combina y calcula la Utilidad Bruta por item.

    Returns:
        pd.DataFrame: DataFrame consolidado con datos de ventas y utilidad, o DataFrame vacío si no hay datos.
    """
    try:
        res_vd = (
            db.table("VENTAS_DETALLE")
            .select(
                "ID_Venta, ID_Producto, Cantidad, Precio_Unitario,"
                " Precio_Costo_Unitario"
            )
            .execute()
        )
        res_vc = (
            db.table("VENTAS_CABECERA").select("ID_Venta, Fecha").execute()
        )
        res_p = (
            db.table("PRODUCTOS")
            .select("ID_Producto, Nombre, Rubro, Marca")
            .execute()
        )

        ventas_det = res_vd.data or []
        ventas_cab = res_vc.data or []
        prods = res_p.data or []

        if not ventas_det or not ventas_cab or not prods:
            return pd.DataFrame()

        df_vd = pd.DataFrame(ventas_det)
        df_vc = pd.DataFrame(ventas_cab)
        df_p = pd.DataFrame(prods)

        # Merge de tablas
        df = df_vd.merge(df_vc, on="ID_Venta").merge(df_p, on="ID_Producto")

        if df.empty:
            return pd.DataFrame()

        df["Fecha"] = pd.to_datetime(df["Fecha"])
        df["Utilidad_Bruta"] = df["Cantidad"] * (
            df["Precio_Unitario"] - df["Precio_Costo_Unitario"]
        )

        return df

    except Exception as e:
        print(f"Error al obtener datos de utilidad: {e}")
        return pd.DataFrame()


def filtrar_utilidades(
    df: pd.DataFrame,
    fecha_inicio,
    fecha_fin,
    rubros: Optional[List[str]] = None,
    marcas: Optional[List[str]] = None,
    nombres: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Aplica los filtros de rango de fechas y selectores múltiples al DataFrame base."""
    if df.empty:
        return df

    mask = (df["Fecha"].dt.date >= fecha_inicio) & (
        df["Fecha"].dt.date <= fecha_fin
    )

    if rubros:
        mask &= df["Rubro"].isin(rubros)
    if marcas:
        mask &= df["Marca"].isin(marcas)
    if nombres:
        mask &= df["Nombre"].isin(nombres)

    return df[mask]
