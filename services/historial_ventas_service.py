import pandas as pd
from config.database import db
from services.audit_service import log_auditoria

def obtener_historial_ventas():
    try:
        # Carga de ventas principales con su detalle
        resp_ventas = db.table("VENTAS_CABECERA")\
            .select("ID_Venta, Fecha, ID_Cliente, ID_Vendedor, Total, Forma_Pago, Estado, VENTAS_DETALLE(*)")\
            .limit(100000)\
            .execute()
        
        df_ventas = pd.DataFrame(resp_ventas.data)
        if df_ventas.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Limpieza y normalización de la columna Total
        df_ventas['Total'] = (df_ventas['Total']
                            .astype(str)
                            .str.replace(',', '', regex=False)
                            .str.replace(',', '.', regex=False)
                            .apply(pd.to_numeric, errors='coerce')
                            .fillna(0))

        # Tablas auxiliares para cruce de datos
        df_clientes = pd.DataFrame(db.table("CLIENTES").select("ID_Cliente, Nombre, Apellido").execute().data)
        df_prod = pd.DataFrame(db.table("PRODUCTOS").select("ID_Producto, Nombre").execute().data)
        df_vend = pd.DataFrame(db.table("VENDEDORES").select("ID_Vendedor, Nombre, Apellido").execute().data)

        # Normalización de claves foráneas para merges precisos
        df_ventas['ID_Cliente'] = df_ventas['ID_Cliente'].astype(str)
        df_ventas['ID_Vendedor'] = df_ventas['ID_Vendedor'].astype(str)

        if not df_clientes.empty:
            df_clientes['ID_Cliente'] = df_clientes['ID_Cliente'].astype(str)
            df_ventas = df_ventas.merge(df_clientes, on="ID_Cliente", how="left")
            df_ventas['Cliente_Full'] = df_ventas['Nombre'].fillna("Sin Nombre") + " " + df_ventas['Apellido'].fillna("")
        else:
            df_ventas['Cliente_Full'] = "Sin Nombre"

        if not df_vend.empty:
            df_vend['ID_Vendedor'] = df_vend['ID_Vendedor'].astype(str)
            df_ventas = df_ventas.merge(df_vend, on="ID_Vendedor", how="left", suffixes=('_vta', '_vend'))
            df_ventas['Vendedor_Full'] = df_ventas['Nombre_vend'].fillna("Sin Vendedor") + " " + df_ventas['Apellido_vend'].fillna("")
        else:
            df_ventas['Vendedor_Full'] = "Sin Vendedor"

        # Conversión de fechas a formato date de Python
        df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha']).dt.date

        return df_ventas, df_prod

    except Exception as e:
        raise Exception(f"Error al obtener el historial de ventas: {e}")


def anular_venta(id_venta, usuario_logueado):
    try:
        # 1. Obtener detalles de la venta para reversar stock si aplica
        venta_resp = db.table("VENTAS_CABECERA").select("*, VENTAS_DETALLE(*)").eq("ID_Venta", int(id_venta)).execute()
        if not venta_resp.data:
            raise Exception("Venta no encontrada.")
        
        datos_venta = venta_resp.data[0]

        # 2. Revertir el estado de la venta
        db.table("VENTAS_CABECERA").update({"Estado": "ANULADA"}).eq("ID_Venta", int(id_venta)).execute()

        # 3. Log de Auditoría
        log_auditoria(
            tabla="VENTAS_CABECERA",
            accion="UPDATE",
            id_entidad=str(id_venta),
            detalles={
                "operacion": "Anulación de Venta",
                "monto_revertido": datos_venta.get("Total"),
                "cliente_id": datos_venta.get("ID_Cliente")
            },
            usuario=usuario_logueado
        )
        return True
    except Exception as e:
        raise Exception(f"Error en la anulación de la venta: {e}")
