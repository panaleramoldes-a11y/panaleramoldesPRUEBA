from datetime import datetime
import pandas as pd
from config.database import db
from utils.audit_logger import log_auditoria


class ProductosService:

    @staticmethod
    def obtener_productos():
        """Obtiene el listado completo de productos."""
        try:
            data = db.table("PRODUCTOS").select("*").execute().data
            df_prod = pd.DataFrame(data)

            columnas_requeridas = [
                'ID_Producto', 'Nombre', 'Rubro', 'ID_Proveedor', 'Marca',
                'Stock_Actual', 'Stock_Min', 'Stock_Max', 'Precio_Costo',
                'Precio_1', 'Precio_2', 'Precio_3', 'Precio_4', 'Precio_5',
                'Imagen'
            ]
            if df_prod.empty:
                df_prod = pd.DataFrame(columns=columnas_requeridas)

            return df_prod
        except Exception as e:
            raise Exception(f"Error al cargar productos: {e}")

    @staticmethod
    def obtener_proveedores():
        """Obtiene la lista de razones sociales de proveedores."""
        try:
            df_prov = pd.DataFrame(
                db.table("PROVEEDORES").select("Razon_Social").execute().data
            )
            return (df_prov['Razon_Social'].tolist()
                    if not df_prov.empty else ["Sin proveedores"])
        except Exception:
            return ["Sin proveedores"]

    @staticmethod
    def generar_mensaje_whatsapp(df_productos):
        """Genera el texto formateado con las reglas de precios para enviar por WhatsApp."""
        if df_productos.empty:
            return ""

        lineas_mensaje = []
        for _, prod in df_productos.iterrows():
            nombre = str(prod.get('Nombre', '')).strip()

            try:
                p1 = int(float(prod.get('Precio_1', 0)))
                p2 = int(float(prod.get('Precio_2', 0)))
                p3 = int(float(prod.get('Precio_3', 0)))
            except (ValueError, TypeError):
                p1, p2, p3 = 0, 0, 0

            # Aplicación de Reglas de precios
            if p1 == p2:
                linea = f"• *{nombre}* ${p1}"
            elif p1 != p2 and p2 == p3:
                linea = f"• *{nombre}* ${p1} x1 o ${p2} cada uno llevando 2"
            elif p2 != p3:
                linea = f"• *{nombre}* ${p1} x1 o ${p3} cada uno llevando 3"
            else:
                linea = f"• *{nombre}* ${p1}"

            lineas_mensaje.append(linea)

        return "\n".join(lineas_mensaje)

    @staticmethod
    def obtener_pre_cambios_pendientes():
        """Obtiene las solicitudes de pre-cambio pendientes."""
        return db.table("PRE_CAMBIOS").select("*").eq("Estado", "PENDIENTE").execute().data

    @staticmethod
    def procesar_aprobacion_cambio(p_id, p_codigo, p_nombre, new_cant, new_tipo, new_desc, usuario_admin):
        """Aprueba un pre-cambio, actualiza el stock, registra en CAMBIOS y KARDEX."""
        prod_data = db.table("PRODUCTOS").select("Stock_Actual", "Nombre").eq("ID_Producto", p_codigo).execute().data
        if not prod_data:
            raise Exception("El producto no existe en la base de datos.")

        stock_viejo = int(prod_data[0]['Stock_Actual'])
        nombre_kardex = prod_data[0].get('Nombre', p_nombre)
        cantidad_mov = int(new_cant) if new_tipo == 'ENTRA' else -int(new_cant)
        stock_nuevo = stock_viejo + cantidad_mov

        # 1. Actualizar Stock
        db.table("PRODUCTOS").update({"Stock_Actual": stock_nuevo}).eq("ID_Producto", p_codigo).execute()

        # 2. Registrar en CAMBIOS
        db.table("CAMBIOS").insert({
            "Fecha": datetime.now().isoformat(),
            "Usuario": usuario_admin,
            "Código": p_codigo,
            "Nombre": p_nombre,
            "Descripción": new_desc,
            "Entra": int(new_cant) if new_tipo == 'ENTRA' else 0,
            "Sale": int(new_cant) if new_tipo == 'SALE' else 0,
            "existencia_ant": stock_viejo,
            "existencia_actual": stock_nuevo
        }).execute()

        # 3. Registrar KARDEX
        tipo_mov_kardex = "DEVOLUCIÓN ENTRADA" if new_tipo == 'ENTRA' else "CAMBIO SALIDA"
        db.table("MOVIMIENTOS_STOCK").insert({
            "id_producto": str(p_codigo),
            "nombre_producto": nombre_kardex,
            "tipo_movimiento": tipo_mov_kardex,
            "cantidad": cantidad_mov,
            "stock_anterior": stock_viejo,
            "stock_nuevo": stock_nuevo,
            "origen_referencia": f"Cambio/Devolución ID: {p_id} - Motivo: {new_desc}",
            "usuario": str(usuario_admin)
        }).execute()

        # 4. Cambiar estado
        db.table("PRE_CAMBIOS").update({"Estado": "PROCESADO"}).eq("id", p_id).execute()

    @staticmethod
    def rechazar_pre_cambio(p_id):
        """Marca una solicitud de cambio como RECHAZADO."""
        db.table("PRE_CAMBIOS").update({"Estado": "RECHAZADO"}).eq("id", p_id).execute()

    @staticmethod
    def enviar_pre_cambio(lista_cambios, motivo, usuario):
        """Crea registros de solicitudes de pre-cambio enviadas por usuarios/vendedores."""
        for item in lista_cambios:
            db.table("PRE_CAMBIOS").insert({
                "Fecha": datetime.now().isoformat(),
                "Código": item['ID'],
                "Nombre": item['Producto'],
                "Descripción": motivo,
                "Entra": int(item['Cantidad']) if item['Tipo'] == 'ENTRA' else 0,
                "Sale": int(item['Cantidad']) if item['Tipo'] == 'SALE' else 0,
                "Estado": "PENDIENTE",
                "Usuario": str(usuario)
            }).execute()

    @staticmethod
    def ejecutar_division_fardo(id_fardo, fila_fardo, unidades, id_cajita, usuario):
        """Ejecuta la división de fardo descontando 1 fardo e incrementando la cajita."""
        prod_cajita = db.table("PRODUCTOS").select("Stock_Actual", "Nombre").eq("ID_Producto", id_cajita).execute().data
        if not prod_cajita:
            raise Exception("El código de la cajita no existe en la base de datos.")

        # Descuento del Fardo
        stock_fardo_old = int(fila_fardo['Stock_Actual'])
        nuevo_stock_fardo = stock_fardo_old - 1
        db.table("PRODUCTOS").update({"Stock_Actual": nuevo_stock_fardo}).eq("ID_Producto", id_fardo).execute()

        # Incremento de Cajita
        stock_cajita_old = int(prod_cajita[0]['Stock_Actual'])
        nombre_cajita = prod_cajita[0].get('Nombre', 'Cajita Individual')
        nuevo_stock_cajita = stock_cajita_old + unidades
        db.table("PRODUCTOS").update({"Stock_Actual": nuevo_stock_cajita}).eq("ID_Producto", id_cajita).execute()

        fecha_iso = datetime.now().isoformat()

        # Auditorías y Cambios (Fardo y Cajita)
        db.table("CAMBIOS").insert({
            "Fecha": fecha_iso, "Usuario": str(usuario), "Código": id_fardo,
            "Nombre": fila_fardo['Nombre'],
            "Descripción": f"División de fardo: Se transformó en {unidades} unidades de {id_cajita}",
            "Entra": 0, "Sale": 1, "existencia_ant": stock_fardo_old, "existencia_actual": nuevo_stock_fardo
        }).execute()

        db.table("CAMBIOS").insert({
            "Fecha": fecha_iso, "Usuario": str(usuario), "Código": id_cajita,
            "Nombre": nombre_cajita,
            "Descripción": f"Ingreso por división de fardo {id_fardo}",
            "Entra": unidades, "Sale": 0, "existencia_ant": stock_cajita_old, "existencia_actual": nuevo_stock_cajita
        }).execute()

        # Kardex
        db.table("MOVIMIENTOS_STOCK").insert({
            "id_producto": str(id_fardo), "nombre_producto": str(fila_fardo['Nombre']),
            "tipo_movimiento": "DIVISIÓN FARDO (SALIDA)", "cantidad": -1,
            "stock_anterior": stock_fardo_old, "stock_nuevo": nuevo_stock_fardo,
            "origen_referencia": f"División en {unidades} uds de Cajita (ID: {id_cajita})",
            "usuario": str(usuario)
        }).execute()

        db.table("MOVIMIENTOS_STOCK").insert({
            "id_producto": str(id_cajita), "nombre_producto": str(nombre_cajita),
            "tipo_movimiento": "DIVISIÓN FARDO (ENTRADA)", "cantidad": unidades,
            "stock_anterior": stock_cajita_old, "stock_nuevo": nuevo_stock_cajita,
            "origen_referencia": f"Ingreso por división de Fardo (ID: {id_fardo})",
            "usuario": str(usuario)
        }).execute()

        # Log Auditoría
        log_auditoria(
            tabla="PRODUCTOS", accion="UPDATE", id_entidad=id_fardo,
            detalles={
                "operacion": "Divisor de Fardos",
                "fardo": {"id": id_fardo, "nombre": fila_fardo['Nombre'], "stock_nuevo": nuevo_stock_fardo},
                "cajita": {"id": id_cajita, "nombre": nombre_cajita, "unidades_ingresadas": unidades, "stock_nuevo": nuevo_stock_cajita}
            },
            usuario=usuario
        )

        return nombre_cajita
