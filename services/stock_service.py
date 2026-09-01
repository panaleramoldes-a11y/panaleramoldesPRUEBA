import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config.database import db

def calcular_y_actualizar_stock_automatico(ids_filtrados: list = None):
    """
    Calcula el promedio diario de ventas de los últimos 60 días
    y actualiza Stock_Min y Stock_Max en la base de datos.
    """
    try:
        fecha_hace_60_dias = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        # Consultar detalle de ventas de los últimos 60 días
        res_ventas = db.table("VENTAS_DETALLE") \
            .select("ID_Producto, Cantidad, VENTAS!inner(Fecha, Estado)") \
            .gte("VENTAS.Fecha", fecha_hace_60_dias) \
            .eq("VENTAS.Estado", "COMPLETADA") \
            .execute()
        
        if not res_ventas.data:
            st.warning("No hay suficientes datos de ventas en los últimos 60 días para calcular los rangos.")
            return

        df_v = pd.DataFrame(res_ventas.data)
        if ids_filtrados:
            df_v = df_v[df_v['ID_Producto'].isin(ids_filtrados)]

        if df_v.empty:
            st.info("No se encontraron movimientos para los productos seleccionados.")
            return

        # Agrupar total de unidades vendidas por producto en 60 días
        resumen_ventas = df_v.groupby("ID_Producto")["Cantidad"].sum().reset_index()
        
        actualizados = 0
        for _, row in resumen_ventas.iterrows():
            prod_id = row["ID_Producto"]
            cant_total = float(row["Cantidad"])
            
            promedio_diario = cant_total / 60.0
            stock_min = int(round(promedio_diario * 7))   # Cobertura de 7 días
            stock_max = int(round(promedio_diario * 21))  # Cobertura de 21 días
            
            db.table("PRODUCTOS").update({
                "Stock_Min": stock_min,
                "Stock_Max": stock_max
            }).eq("ID_Producto", prod_id).execute()
            
            actualizados += 1

        st.success(f"✅ Se actualizaron los stock Mínimos y Máximos para {actualizados} productos.")
        if 'df_prod' in st.session_state:
            del st.session_state['df_prod']

    except Exception as e:
        st.error(f"Error al calcular stock automático: {e}")

def actualizar_estados_productos(db_client):
    """
    Regla:
    - INACTIVO: Si Stock_Min es NULL / None / 0 Y Stock_Actual es 0.
    - ACTIVO: Cualquier otro caso (incluye productos con stock > 0).
    """
    try:
        prods = db_client.table("PRODUCTOS").select("ID_Producto, Stock_Actual, Stock_Min, Estado").execute().data
        
        prods_a_inactivar = []
        prods_a_activar = []
        
        for p in prods:
            cod = p.get("ID_Producto")
            stock = int(p.get("Stock_Actual") or 0)
            stock_min = p.get("Stock_Min")
            estado_actual = p.get("Estado", "ACTIVO")
            
            sin_stock_min = (stock_min is None or str(stock_min).strip() in ["", "0", "None"])
            
            if sin_stock_min and stock == 0:
                if estado_actual != "INACTIVO":
                    prods_a_inactivar.append(cod)
            else:
                if estado_actual != "ACTIVO":
                    prods_a_activar.append(cod)
                    
        for cod in prods_a_inactivar:
            db_client.table("PRODUCTOS").update({"Estado": "INACTIVO"}).eq("ID_Producto", cod).execute()
            
        for cod in prods_a_activar:
            db_client.table("PRODUCTOS").update({"Estado": "ACTIVO"}).eq("ID_Producto", cod).execute()
            
        st.success(f"✅ Estados actualizados: {len(prods_a_inactivar)} inhabilitados, {len(prods_a_activar)} reactivados.")
        
        if 'df_prod' in st.session_state:
            del st.session_state['df_prod']
            
    except Exception as e:
        st.error(f"Error al actualizar estados: {e}")
