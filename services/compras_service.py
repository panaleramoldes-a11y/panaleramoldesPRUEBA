"""
services/compras_service.py
Capa de lógica de negocio y persistencia para el módulo de Compras.
"""

from datetime import datetime
import pandas as pd
from config.database import get_db

MARGENES_RUBROS = {
            "ACEITE": [0.35, 0.35, 0.25, 0.15, 0.0], "ACONDICIONADOR": [0.35, 0.35, 0.25, 0.15, 0.0],
            "ALGODON": [0.35, 0.35, 0.25, 0.15, 0.0], "APOSITOS": [0.35, 0.35, 0.25, 0.15, 0.0],
            "BAÑO LIQUIDO": [0.35, 0.35, 0.25, 0.15, 0.0], "CAMBIADOR": [1.0, 0.5, 0.4, 0.3, 0.0],
            "CHUPETE": [0.35, 0.35, 0.25, 0.15, 0.0], "COLONIA": [0.35, 0.35, 0.25, 0.15, 0.0],
            "CREMA": [0.35, 0.35, 0.25, 0.15, 0.0], "CUCHARAS": [0.35, 0.35, 0.25, 0.15, 0.0],
            "DESCONGESTIONADORES NASALES": [0.35, 0.35, 0.25, 0.15, 0.0], "ESPONJA": [0.35, 0.35, 0.25, 0.15, 0.0],
            "HIGIENE BUCAL": [0.35, 0.35, 0.25, 0.15, 0.0], "HISOPOS": [0.35, 0.35, 0.25, 0.15, 0.0],
            "JABON": [0.35, 0.35, 0.25, 0.15, 0.0], "LECHE": [0.40, 0.15, 0.10, 0.08, 0.0],
            "LIMPIEZA ROPA": [0.35, 0.35, 0.25, 0.15, 0.0], "MAMADERA": [0.35, 0.35, 0.25, 0.15, 0.0],
            "MOCHILA MATERNAL": [0.35, 0.35, 0.25, 0.15, 0.0], "MORDILLOS": [0.35, 0.35, 0.25, 0.15, 0.0],
            "OLEO CALCAREO": [0.35, 0.35, 0.25, 0.15, 0.0], "PAÑALES": [0.20, 0.15, 0.10, 0.08, 0.0],
            "PLATOS": [0.35, 0.35, 0.25, 0.15, 0.0], "PROTECTOR MAMARIO": [0.35, 0.35, 0.25, 0.15, 0.0],
            "SACALECHES": [0.35, 0.35, 0.25, 0.15, 0.0], "SEGURIDAD": [0.35, 0.35, 0.25, 0.15, 0.0],
            "SHAMPOO": [0.35, 0.35, 0.25, 0.15, 0.0], "TALCO": [0.35, 0.35, 0.25, 0.15, 0.0],
            "TETINAS": [0.35, 0.35, 0.25, 0.15, 0.0], "TIJERAS": [0.35, 0.35, 0.25, 0.15, 0.0],
            "TOALLITAS FEMENINAS": [0.35, 0.35, 0.25, 0.15, 0.0], "TOALLITAS HUMEDAS": [0.35, 0.35, 0.25, 0.15, 0.0],
            "VASOS": [0.35, 0.35, 0.25, 0.15, 0.0]
        }

MARGEN_DEFECTO = [1.40, 1.35, 1.30, 1.25, 1.20]


def calcular_precios_sugeridos(costo: float, rubro: str) -> dict:
    """Calcula Precios 1 a 5 sugeridos según costo y rubro."""
    margenes = MARGENES_RUBROS.get(str(rubro).upper(), MARGEN_DEFECTO)
    precios = {}
    for i, mult in enumerate(margenes, start=1):
        precios[f"Precio_{i}"] = round(costo * mult, 2)
    return precios


def obtener_historial_compras() -> pd.DataFrame:
    """Obtiene todas las cabeceras de compras registradas."""
    db = get_db()
    res = db.table("COMPRAS_CABECERA").select("*").order("Fecha", desc=True).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def obtener_detalle_compra(id_compra: str) -> pd.DataFrame:
    """Obtiene el detalle de ítems de una compra específica con nombre de producto."""
    db = get_db()
    res = db.table("DETALLE_COMPRAS").select("*, PRODUCTOS(Nombre)").eq("ID_Compra", id_compra).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        if 'PRODUCTOS' in df.columns:
            df['Nombre'] = df['PRODUCTOS'].apply(lambda x: x.get('Nombre', '') if isinstance(x, dict) else '')
        return df
    return pd.DataFrame()


def obtener_ordenes_compra() -> pd.DataFrame:
    """Obtiene todas las órdenes de compra activas."""
    db = get_db()
    res = db.table("ORDENES_COMPRA").select("*").order("Fecha", desc=True).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()


def obtener_detalle_orden(id_compra: str) -> list:
    """Obtiene el detalle de una Orden de Compra para cargarla en el carrito."""
    db = get_db()
    res = db.table("DETALLE_ORDENES").select("*, PRODUCTOS(*)").eq("ID_Compra", id_compra).execute()
    carrito = []
    if res.data:
        for row in res.data:
            prod = row.get("PRODUCTOS", {}) or {}
            carrito.append({
                "id": str(row["ID_Producto"]),
                "nombre": prod.get("Nombre", "Desconocido"),
                "cantidad": int(row.get("Cantidad", 1)),
                "costo": float(row.get("Precio_Costo_Unitario", 0.0)),
                "subtotal": float(row.get("Subtotal", 0.0)),
                "Precio_1": float(prod.get("Precio_1", 0.0)),
                "Precio_2": float(prod.get("Precio_2", 0.0)),
                "Precio_3": float(prod.get("Precio_3", 0.0)),
                "Precio_4": float(prod.get("Precio_4", 0.0)),
                "Precio_5": float(prod.get("Precio_5", 0.0)),
                "rubro": prod.get("Rubro", "GENERAL")
            })
    return carrito


def activar_producto(id_producto: str):
    """Activa un producto inactivo."""
    db = get_db()
    db.table("PRODUCTOS").update({"Estado": True}).eq("ID_Producto", id_producto).execute()


def registrar_orden_compra(proveedor: str, fecha: str, metodo_pago: str, total: float, carrito: list) -> str:
    """Guarda o actualiza una Orden de Compra y sus detalles."""
    db = get_db()
    id_c = f"OC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Insertar Cabecera
    db.table("ORDENES_COMPRA").insert({
        "ID_Compra": id_c,
        "Fecha": str(fecha),
        "Proveedor": proveedor,
        "Metodo_Pago": metodo_pago,
        "Total_Compra": float(total)
    }).execute()

    # Insertar Detalles
    for item in carrito:
        db.table("DETALLE_ORDENES").insert({
            "ID_Compra": id_c,
            "ID_Producto": str(item['id']),
            "Cantidad": int(item['cantidad']),
            "Precio_Costo_Unitario": float(item['costo']),
            "Subtotal": float(item['subtotal'])
        }).execute()

    return id_c


def eliminar_orden_compra(id_compra: str):
    """Elimina una Orden de Compra y su detalle asociado."""
    db = get_db()
    db.table("DETALLE_ORDENES").delete().eq("ID_Compra", id_compra).execute()
    db.table("ORDENES_COMPRA").delete().eq("ID_Compra", id_compra).execute()


def registrar_compra_y_cargar_stock(
    fecha_factura,
    proveedor: str,
    nro_factura: str,
    metodo_pago: str,
    total_final: float,
    carrito: list,
    df_prod: pd.DataFrame,
    usuario_logueado: str = "Admin",
    oc_en_edicion: str = None
) -> str:
    """
    1. Registra cabecera de compra.
    2. Actualiza costos y precios P1-P5 en PRODUCTOS.
    3. Si es stockeable, incrementa Stock_Actual.
    4. Registra en DETALLE_COMPRAS.
    5. Genera movimiento Kardex en MOVIMIENTOS_STOCK.
    6. Elimina Orden de Compra previa si provino de una edición.
    """
    db = get_db()
    id_c = f"COM-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 1. Guardar Cabecera de Compra
    db.table("COMPRAS_CABECERA").insert({
        "ID_Compra": id_c,
        "Fecha": str(fecha_factura),
        "Proveedor": proveedor,
        "Nro_Factura": nro_factura,
        "Metodo_Pago": metodo_pago,
        "Total_Compra": float(total_final)
    }).execute()

    # 2. Procesar detalle de carrito
    for item in carrito:
        id_p_str = str(item['id'])
        cant_comprada = int(item['cantidad'])

        data_update = {
            "Precio_Costo": float(item['costo']),
            "Precio_1": float(item.get('Precio_1', 0)),
            "Precio_2": float(item.get('Precio_2', 0)),
            "Precio_3": float(item.get('Precio_3', 0)),
            "Precio_4": float(item.get('Precio_4', 0)),
            "Precio_5": float(item.get('Precio_5', 0))
        }

        # Obtener información del producto
        prod_info = df_prod[df_prod['ID_Producto'].astype(str) == id_p_str] if not df_prod.empty else pd.DataFrame()

        es_stockeable = False
        stock_anterior = 0
        stock_nuevo = 0
        nombre_producto = item.get('nombre', '')

        if not prod_info.empty:
            fila_p = prod_info.iloc[0]
            es_stockeable = bool(fila_p.get('Es_Stockeable', False))
            stock_anterior = int(fila_p.get('Stock_Actual', 0) or 0)
            if not nombre_producto:
                nombre_producto = str(fila_p.get('Nombre', ''))

        if es_stockeable:
            stock_nuevo = stock_anterior + cant_comprada
            data_update["Stock_Actual"] = stock_nuevo

        # Update a PRODUCTOS
        db.table("PRODUCTOS").update(data_update).eq("ID_Producto", id_p_str).execute()

        # Detalle de Compra
        db.table("DETALLE_COMPRAS").insert({
            "ID_Compra": id_c,
            "ID_Producto": id_p_str,
            "Cantidad": cant_comprada,
            "Precio_Costo_Unitario": float(item['costo']),
            "Subtotal": float(item['subtotal'])
        }).execute()

        # KARDEX (MOVIMIENTOS_STOCK)
        if es_stockeable:
            db.table("MOVIMIENTOS_STOCK").insert({
                "id_producto": id_p_str,
                "nombre_producto": str(nombre_producto),
                "tipo_movimiento": "COMPRA (ENTRADA)",
                "cantidad": cant_comprada,
                "stock_anterior": float(stock_anterior),
                "stock_nuevo": float(stock_nuevo),
                "origen_referencia": f"Ingreso por Compra (ID: {id_c} - Factura: {nro_factura})",
                "usuario": str(usuario_logueado)
            }).execute()

    # 3. Eliminar OC previa si correspondía
    if oc_en_edicion:
        eliminar_orden_compra(oc_en_edicion)

    return id_c


def generar_texto_whatsapp_precios(carrito: list) -> str:
    """Genera una lista formateada de precios para compartir por WhatsApp."""
    if not carrito:
        return "El carrito está vacío."

    lineas = ["📋 *LISTA DE PRECIOS ACTUALIZADA*\n"]
    for item in carrito:
        lineas.append(f"🔹 *{item.get('nombre', 'Producto')}*")
        lineas.append(f"   • P1: ${item.get('Precio_1', 0):,.2f}")
        lineas.append(f"   • P2: ${item.get('Precio_2', 0):,.2f}")
        lineas.append(f"   • P3: ${item.get('Precio_3', 0):,.2f}")
        lineas.append(f"   • P4: ${item.get('Precio_4', 0):,.2f}")
        lineas.append(f"   • P5: ${item.get('Precio_5', 0):,.2f}\n")

    return "\n".join(lineas)
