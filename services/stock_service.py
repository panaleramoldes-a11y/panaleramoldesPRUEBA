import pandas as pd
from datetime import datetime, timedelta
from config.database import db

def obtener_datos_stock():
    """Obtiene los dataframes de productos y proveedores."""
    try:
        resp_prod = db.table("PRODUCTOS").select("*").execute()
        resp_prov = db.table("PROVEEDORES").select("*").execute()
        
        df_prod = pd.DataFrame(resp_prod.data) if resp_prod.data else pd.DataFrame()
        df_prov = pd.DataFrame(resp_prov.data) if resp_prov.data else pd.DataFrame()
        
        return df_prod, df_prov
    except Exception as e:
        raise Exception(f"Error al obtener datos de productos/proveedores: {e}")

def obtener_ventas_detalle():
    """Obtiene el historial de detalles de venta para el análisis ABC."""
    try:
        res_vd = db.table("VENTAS_DETALLE").select("ID_Producto, Cantidad, Subtotal, Precio_Costo_Unitario").execute()
        return pd.DataFrame(res_vd.data) if res_vd.data else pd.DataFrame()
    except Exception as e:
        raise Exception(f"Error al obtener detalle de ventas: {e}")

def calcular_y_actualizar_stock_automatico(ids_filtrados=None, dias_historia=60):
    """
    Recalcula y actualiza Stock_Min y Stock_Max basándose en las ventas reales 
    de los últimos N días.
    """
    try:
        # Obtener ventas recientes
        fecha_limite = (datetime.now() - timedelta(days=dias_historia)).strftime('%Y-%m-%d')
        resp_v = db.table("VENTAS_CABECERA").select("ID_Venta, Fecha").gte("Fecha", fecha_limite).execute()
        
        if not resp_v.data:
            return False

        df_v = pd.DataFrame(resp_v.data)
        ids_ventas = df_v['ID_Venta'].tolist()

        if not ids_ventas:
            return False

        # Obtener detalle de esas ventas
        resp_vd = db.table("VENTAS_DETALLE").select("ID_Producto, Cantidad").in_("ID_Venta", ids_ventas).execute()
        if not resp_vd.data:
            return False

        df_vd = pd.DataFrame(resp_vd.data)
        df_vd['Cantidad'] = pd.to_numeric(df_vd['Cantidad'], errors='coerce').fillna(0)

        # Filtrar IDs si se pasaron específicamente
        if ids_filtrados:
            ids_str = [str(x) for x in ids_filtrados]
            df_vd = df_vd[df_vd['ID_Producto'].astype(str).isin(ids_str)]

        if df_vd.empty:
            return False

        # Agrupar total vendido por producto
        rotacion = df_vd.groupby('ID_Producto')['Cantidad'].sum().reset_index()

        for _, row in rotacion.iterrows():
            id_p = row['ID_Producto']
            cant_vendida = row['Cantidad']
            
            # Promedio de ventas diarias
            venta_diaria = cant_vendida / dias_historia
            
            # Stock Mínimo = Venta diaria * 15 días (o 1 mínimo si hay ventas)
            stock_min = max(1, round(venta_diaria * 15))
            # Stock Máximo = Stock Mínimo * 2.5
            stock_max = max(stock_min + 1, round(stock_min * 2.5))

            db.table("PRODUCTOS").update({
                "Stock_Min": stock_min,
                "Stock_Max": stock_max
            }).eq("ID_Producto", id_p).execute()

        return True
    except Exception as e:
        raise Exception(f"Error al recalcular stock automático: {e}")
