# services/stock_service.py
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st


def obtener_datos_stock_base(db):
    """Consulta los productos y proveedores desde Supabase."""
    res_prod = db.table("PRODUCTOS").select("*").execute()
    res_prov = db.table("PROVEEDORES").select("*").execute()

    df_prod = (
        pd.DataFrame(res_prod.data) if res_prod.data else pd.DataFrame()
    )
    df_prov = (
        pd.DataFrame(res_prov.data) if res_prov.data else pd.DataFrame()
    )

    return df_prod, df_prov


def obtener_detalle_ventas(db):
    """Obtiene el historial de ventas necesario para el análisis ABC."""
    res_vd = (
        db.table("VENTAS_DETALLE")
        .select("ID_Producto, Cantidad, Subtotal, Precio_Costo_Unitario")
        .execute()
        .data
    )
    return pd.DataFrame(res_vd) if res_vd else pd.DataFrame()


def calcular_y_actualizar_stock_automatico(db, ids_filtrados: list = None):
    """Calcula el promedio diario de ventas de los últimos 60 días

    y actualiza Stock_Min y Stock_Max en la base de datos.
    """
    try:
        fecha_hace_60_dias = (datetime.now() - timedelta(days=60)).strftime(
            "%Y-%m-%d"
        )

        res_ventas = (
            db.table("VENTAS_DETALLE")
            .select("ID_Producto, Cantidad, VENTAS!inner(Fecha, Estado)")
            .gte("VENTAS.Fecha", fecha_hace_60_dias)
            .eq("VENTAS.Estado", "COMPLETADA")
            .execute()
        )

        if not res_ventas.data:
            st.warning(
                "No hay suficientes datos de ventas en los últimos 60 días para calcular los rangos."
            )
            return False

        df_v = pd.DataFrame(res_ventas.data)
        if ids_filtrados:
            df_v = df_v[df_v["ID_Producto"].isin(ids_filtrados)]

        if df_v.empty:
            st.info(
                "No se encontraron movimientos para los productos seleccionados."
            )
            return False

        resumen_ventas = (
            df_v.groupby("ID_Producto")["Cantidad"].sum().reset_index()
        )

        actualizados = 0
        for _, row in resumen_ventas.iterrows():
            prod_id = row["ID_Producto"]
            cant_total = float(row["Cantidad"])

            promedio_diario = cant_total / 60.0
            stock_min = int(
                round(promedio_diario * 7)
            )  # Cobertura de 7 días
            stock_max = int(
                round(promedio_diario * 21)
            )  # Cobertura de 21 días

            db.table("PRODUCTOS").update(
                {"Stock_Min": stock_min, "Stock_Max": stock_max}
            ).eq("ID_Producto", prod_id).execute()

            actualizados += 1

        if "df_prod" in st.session_state:
            del st.session_state["df_prod"]

        return actualizados

    except Exception as e:
        st.error(f"Error al calcular stock automático: {e}")
        return False


def actualizar_estados_productos(db_client):
    """Regla:

    - INACTIVO: Si Stock_Min es NULL / None / 0 Y Stock_Actual es 0.
    - ACTIVO: Cualquier otro caso.
    """
    try:
        prods = (
            db_client.table("PRODUCTOS")
            .select("ID_Producto, Stock_Actual, Stock_Min, Estado")
            .execute()
            .data
        )

        prods_a_inactivar = []
        prods_a_activar = []

        for p in prods:
            cod = p.get("ID_Producto")
            stock = int(p.get("Stock_Actual") or 0)
            stock_min = p.get("Stock_Min")
            estado_actual = p.get("Estado", "ACTIVO")

            sin_stock_min = stock_min is None or str(
                stock_min
            ).strip() in ["", "0", "None"]

            if sin_stock_min and stock == 0:
                if estado_actual != "INACTIVO":
                    prods_a_inactivar.append(cod)
            else:
                if estado_actual != "ACTIVO":
                    prods_a_activar.append(cod)

        for cod in prods_a_inactivar:
            db_client.table("PRODUCTOS").update({"Estado": "INACTIVO"}).eq(
                "ID_Producto", cod
            ).execute()

        for cod in prods_a_activar:
            db_client.table("PRODUCTOS").update({"Estado": "ACTIVO"}).eq(
                "ID_Producto", cod
            ).execute()

        st.success(
            f"✅ Estados actualizados: {len(prods_a_inactivar)} inhabilitados, {len(prods_a_activar)} reactivados."
        )

        if "df_prod" in st.session_state:
            del st.session_state["df_prod"]

    except Exception as e:
        st.error(f"Error al actualizar estados: {e}")


def calcular_ranking_abc(df_prod, df_prov, df_vd, filtros):
    """Calcula el ranking de priorización comercial (ABC) y el nivel de urgencia."""
    df_ranking = df_prod.copy()

    if df_ranking.empty:
        return pd.DataFrame()

    if "Estado" in df_ranking.columns:
        df_ranking = df_ranking[df_ranking["Estado"] != "INACTIVO"]

    if "Es_Stockeable" in df_ranking.columns:
        df_ranking = df_ranking[df_ranking["Es_Stockeable"] == True]

    if "Rubro" in df_ranking.columns and "Nombre" in df_ranking.columns:
        es_leche = df_ranking["Rubro"].astype(str).str.upper() == "LECHE"
        contiene_bulto = df_ranking["Nombre"].astype(str).str.contains(
            " x12| x24| x30| x400| x800| x1000| x1200", case=False, na=False
        )
        df_ranking = df_ranking[~es_leche | contiene_bulto]

    df_ranking["Stock_Actual"] = (
        pd.to_numeric(df_ranking["Stock_Actual"], errors="coerce")
        .fillna(0)
    )
    df_ranking["Stock_Min"] = (
        pd.to_numeric(df_ranking["Stock_Min"], errors="coerce").fillna(0)
    )
    df_ranking["Stock_Max"] = (
        pd.to_numeric(df_ranking["Stock_Max"], errors="coerce").fillna(0)
    )

    busqueda_abc = filtros.get("busqueda_abc")
    if busqueda_abc:
        b_txt = busqueda_abc.lower()
        mask_abc = (
            df_ranking["Nombre"]
            .astype(str)
            .str.lower()
            .str.contains(b_txt, na=False)
        ) | (
            df_ranking["ID_Producto"]
            .astype(str)
            .str.lower()
            .str.contains(b_txt, na=False)
        )
        df_ranking = df_ranking[mask_abc]

    if filtros.get("p_rubro") and filtros["p_rubro"] != "Todos":
        df_ranking = df_ranking[df_ranking["Rubro"] == filtros["p_rubro"]]

    if filtros.get("p_marca") and filtros["p_marca"] != "Todos":
        df_ranking = df_ranking[df_ranking["Marca"] == filtros["p_marca"]]

    if filtros.get("p_prov") and filtros["p_prov"] != "Todos":
        if "Proveedor" in df_ranking.columns:
            df_ranking = df_ranking[
                df_ranking["Proveedor"] == filtros["p_prov"]
            ]
        elif "ID_Proveedor" in df_ranking.columns and not df_prov.empty:
            prov_sel = df_prov[df_prov["Razon_Social"] == filtros["p_prov"]]
            if not prov_sel.empty:
                id_p = prov_sel.iloc[0]["ID_Proveedor"]
                df_ranking = df_ranking[df_ranking["ID_Proveedor"] == id_p]

    if df_ranking.empty:
        return pd.DataFrame()

    if not df_vd.empty:
        df_vd["Cantidad"] = (
            pd.to_numeric(df_vd["Cantidad"], errors="coerce").fillna(0)
        )
        df_vd["Subtotal"] = (
            pd.to_numeric(df_vd["Subtotal"], errors="coerce").fillna(0)
        )
        df_vd["Precio_Costo_Unitario"] = (
            pd.to_numeric(df_vd["Precio_Costo_Unitario"], errors="coerce")
            .fillna(0)
        )
        df_vd["Ganancia_Real"] = df_vd["Subtotal"] - (
            df_vd["Cantidad"] * df_vd["Precio_Costo_Unitario"]
        )

        agrupado = (
            df_vd.groupby("ID_Producto")
            .agg(
                {
                    "Cantidad": "sum",
                    "Subtotal": "sum",
                    "Ganancia_Real": "sum",
                }
            )
            .reset_index()
            .rename(
                columns={
                    "Cantidad": "Rotacion_Unid",
                    "Subtotal": "Facturacion_Total",
                    "Ganancia_Real": "Ganancia_Total",
                }
            )
        )

        df_ranking["ID_Producto"] = df_ranking["ID_Producto"].astype(str)
        agrupado["ID_Producto"] = agrupado["ID_Producto"].astype(str)
        df_ranking = pd.merge(
            df_ranking, agrupado, on="ID_Producto", how="left"
        )
    else:
        df_ranking["Rotacion_Unid"] = 0
        df_ranking["Facturacion_Total"] = 0.0
        df_ranking["Ganancia_Total"] = 0.0

    df_ranking["Rotacion_Unid"] = df_ranking["Rotacion_Unid"].fillna(0)
    df_ranking["Facturacion_Total"] = df_ranking["Facturacion_Total"].fillna(
        0.0
    )
    df_ranking["Ganancia_Total"] = df_ranking["Ganancia_Total"].fillna(0.0)

    max_rot = df_ranking["Rotacion_Unid"].max()
    max_fact = df_ranking["Facturacion_Total"].max()
    max_gan = df_ranking["Ganancia_Total"].max()

    norm_rot = (
        (df_ranking["Rotacion_Unid"] / max_rot * 100) if max_rot > 0 else 0
    )
    norm_fact = (
        (df_ranking["Facturacion_Total"] / max_fact * 100)
        if max_fact > 0
        else 0
    )
    norm_gan = (
        (df_ranking["Ganancia_Total"] / max_gan * 100) if max_gan > 0 else 0
    )

    df_ranking["Score_Comercial"] = (
        (0.40 * norm_fact) + (0.35 * norm_rot) + (0.25 * norm_gan)
    )

    p70 = df_ranking["Score_Comercial"].quantile(0.70)
    p30 = df_ranking["Score_Comercial"].quantile(0.30)

    def asignar_categoria(score):
        if score >= p70 and score > 0:
            return "🟢 Categoría A"
        elif score >= p30 and score > 0:
            return "🟡 Categoría B"
        else:
            return "🔴 Categoría C"

    df_ranking["Categoria_ABC"] = df_ranking["Score_Comercial"].apply(
        asignar_categoria
    )

    df_ranking["Faltante_Min"] = (
        df_ranking["Stock_Min"] - df_ranking["Stock_Actual"]
    ).clip(lower=0)

    def calc_urgencia(row):
        if row["Stock_Min"] > 0 and row["Faltante_Min"] > 0:
            return (row["Faltante_Min"] / row["Stock_Min"]) * 100
        return 0.0

    df_ranking["Urgencia_%"] = df_ranking.apply(calc_urgencia, axis=1)

    df_ranking["Orden_Cat"] = df_ranking["Categoria_ABC"].map(
        {
            "🟢 Categoría A": 1,
            "🟡 Categoría B": 2,
            "🔴 Categoría C": 3,
        }
    )

    df_ranking = df_ranking.sort_values(
        by=["Orden_Cat", "Urgencia_%", "Score_Comercial"],
        ascending=[True, False, False],
    ).reset_index(drop=True)

    df_ranking["Pedir"] = df_ranking["Urgencia_%"] > 0
    return df_ranking
