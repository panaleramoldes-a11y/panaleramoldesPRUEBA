import re
import json
from datetime import datetime

class VentaService:
    def __init__(self, db_client):
        self.db = db_client

    # -------------------------------------------------------------------------
    # OBTENCIÓN DE DATOS BÁSICOS
    # -------------------------------------------------------------------------
    def obtener_productos(self):
        """Obtiene la lista de productos activos/disponibles."""
        res = self.db.table("PRODUCTOS").select("*").execute()
        return res.data if res and res.data else []

    def obtener_clientes(self):
        """Obtiene la lista de clientes."""
        res = self.db.table("CLIENTES").select("*").execute()
        return res.data if res and res.data else []

    def obtener_vendedores(self):
        """Obtiene la lista de vendedores/usuarios."""
        res = self.db.table("USUARIOS").select("*").execute()
        return res.data if res and res.data else []

    def obtener_metodos_pago(self):
        """Obtiene la lista de métodos de pago activos."""
        res = self.db.table("METODOS_PAGO").select("*").execute()
        return res.data if res and res.data else []

    def obtener_ventas_pendientes(self):
        """Obtiene la lista de ventas pendientes guardadas."""
        res = self.db.table("VENTAS_PENDIENTES").select("*").order("Fecha", desc=True).execute()
        return res.data if res and res.data else []

    def obtener_turno_abierto(self):
        """Consulta el turno de caja que se encuentra abierto actualmente."""
        res = self.db.table("CONTROL_TURNOS").select("ID_Turno").eq("Estado", "Abierto").maybe_single().execute()
        return res.data['ID_Turno'] if (res and res.data) else "SIN_TURNO"

    # -------------------------------------------------------------------------
    # VALIDACIONES DE STOCK Y GIFT CARD
    # -------------------------------------------------------------------------
    def validar_stock_carrito(self, carrito):
        """Verifica que los productos stockeables del carrito tengan stock suficiente en BD."""
        for item in carrito:
            p_check = self.db.table("PRODUCTOS").select("Nombre", "Stock_Actual", "Es_Stockeable").eq("ID_Producto", str(item["id"])).single().execute()
            if p_check.data:
                es_stockeable = p_check.data.get("Es_Stockeable", True)
                stock_actual = float(p_check.data.get("Stock_Actual", 0))
                cant_solicitada = float(item["cantidad"])

                if es_stockeable and cant_solicitada > stock_actual:
                    nombre_prod = p_check.data.get("Nombre", "Desconocido")
                    return False, f'El artículo "{nombre_prod}" no posee esa cantidad para facturar, revisar código y stock'
        return True, ""

    def validar_saldo_giftcard(self, pagos_split, gc_activa_id):
        """Valida que el saldo real en BD de la Gift Card alcance para los pagos especificados."""
        for pago in pagos_split:
            if "Gift Card" in pago["metodo"]:
                gc_check = self.db.table("GIFT_CARDS").select("Saldo_Actual").eq("ID_GiftCard", gc_activa_id).single().execute()
                saldo_real = float(gc_check.data['Saldo_Actual']) if (gc_check and gc_check.data) else 0.0
                if pago["monto"] > saldo_real:
                    return False, f"❌ ¡Saldo insuficiente en Gift Card! Disponible: ${saldo_real:,.2f}"
        return True, ""

    # -------------------------------------------------------------------------
    # REGISTRO DE VENTA DEFINITIVA
    # -------------------------------------------------------------------------
    def registrar_venta(self, carrito, pagos_split, total_final, tipo_entrega, direccion_entrega, 
                        observaciones_entrega, id_cliente, id_vendedor, usuario_nombre, gc_activa_id=None, id_pendiente=None):
        """
        Registra la venta final en BD: Cabecera, Detalle, Movimientos de Stock, 
        Pagos, Caja, saldo de Gift Card si aplica, y elimina la venta pendiente si existía.
        """
        id_v = datetime.now().strftime("%Y%m%d%H%M%S")
        f = datetime.now().strftime("%Y-%m-%d")
        id_turno_val = self.obtener_turno_abierto()

        # Resolver nombre del vendedor/usuario si no viene especificado
        nombre_usuario_actual = usuario_nombre
        if not nombre_usuario_actual:
            u_res = self.db.table("USUARIOS").select("Nombre").eq("ID_Usuario", id_vendedor).single().execute()
            nombre_usuario_actual = u_res.data.get('Nombre') if (u_res and u_res.data) else str(id_vendedor)

        # 1. Registrar Cabecera
        desglose_pagos = " | ".join([f"{p['metodo']}: ${p['monto']:,.0f}" for p in pagos_split])
        self.db.table("VENTAS_CABECERA").insert({
            "ID_Venta": id_v,
            "Fecha": f,
            "ID_Cliente": id_cliente,
            "ID_Vendedor": id_vendedor, 
            "Forma_Pago": desglose_pagos,
            "Total": total_final,
            "Forma_Entrega": tipo_entrega,
            "Direccion_Entrega": direccion_entrega if tipo_entrega == "Reparto" else "N/A",
            "Observaciones": observaciones_entrega
        }).execute()

        # 2. Registrar Detalle y Actualizar Stock
        for art in carrito:
            prod_data = self.db.table("PRODUCTOS").select("Precio_Costo", "Nombre", "Stock_Actual", "Es_Stockeable").eq("ID_Producto", str(art['id'])).single().execute()
            costo_historico = prod_data.data.get('Precio_Costo', 0) if prod_data.data else 0
            nombre_prod = art.get('nombre') or (prod_data.data.get('Nombre') if prod_data.data else 'Artículo')
            es_stockeable = prod_data.data.get('Es_Stockeable', True) if prod_data.data else True

            self.db.table("VENTAS_DETALLE").insert({
                "ID_Venta": id_v,
                "ID_Producto": str(art['id']),
                "Cantidad": int(art['cantidad']),
                "Precio_Unitario": float(art['precio']),
                "Precio_Costo_Unitario": float(costo_historico),
                "Subtotal": float(art['subtotal'])
            }).execute()

            if es_stockeable and prod_data.data:
                stock_actual = int(prod_data.data.get('Stock_Actual', 0))
                cantidad_vendida = int(art['cantidad'])
                stock_nuevo = stock_actual - cantidad_vendida

                self.db.table("PRODUCTOS").update({"Stock_Actual": stock_nuevo}).eq("ID_Producto", str(art['id'])).execute()

                self.db.table("MOVIMIENTOS_STOCK").insert({
                    "id_producto": str(art['id']),
                    "nombre_producto": nombre_prod,
                    "tipo_movimiento": "VENTA",
                    "cantidad": -cantidad_vendida,
                    "stock_anterior": stock_actual,
                    "stock_nuevo": stock_nuevo,
                    "origen_referencia": f"Venta ID: {id_v}",
                    "usuario": str(nombre_usuario_actual)
                }).execute()

        # 3. Registrar Pagos en VENTAS_PAGOS
        for pago in pagos_split:
            self.db.table("VENTAS_PAGOS").insert({
                "ID_Venta": id_v,
                "Metodo_Pago": pago["metodo"],
                "Monto": float(pago["monto"])
            }).execute()

        # 4. Registrar Movimientos en Caja y Actualización de Gift Card
        for pago in pagos_split:
            metodo = pago["metodo"]
            monto = float(pago["monto"])

            self.db.table("CAJA").insert({
                "ID_Turno": id_turno_val,
                "Fecha": datetime.now().isoformat(),
                "Tipo": "Ingreso",
                "Concepto": f"Venta {id_v} ({metodo})",
                "Monto": monto,
                "Forma_Pago": metodo
            }).execute()

            es_efectivo_reparto = (metodo == "Efectivo" and tipo_entrega == "Reparto")
            es_otro_metodo = (metodo != "Efectivo")

            if es_efectivo_reparto or es_otro_metodo:
                if "Gift Card" in metodo and gc_activa_id:
                    gc_curr = self.db.table("GIFT_CARDS").select("Saldo_Actual").eq("ID_GiftCard", gc_activa_id).single().execute()
                    saldo_base = float(gc_curr.data['Saldo_Actual']) if (gc_curr and gc_curr.data) else 0.0
                    nuevo_saldo = saldo_base - monto

                    self.db.table("GIFT_CARDS").update({"Saldo_Actual": float(nuevo_saldo)}).eq("ID_GiftCard", gc_activa_id).execute()
                    if nuevo_saldo <= 0:
                        self.db.table("GIFT_CARDS").update({"Estado": False}).eq("ID_GiftCard", gc_activa_id).execute()

                self.db.table("CAJA").insert({
                    "ID_Turno": id_turno_val,
                    "Fecha": datetime.now().isoformat(),
                    "Tipo": "Egreso",
                    "Concepto": f"RETIRO PAGO {metodo.upper()} (Venta {id_v})",
                    "Monto": monto,
                    "Forma_Pago": metodo
                }).execute()

        # 5. Borrar de Ventas Pendientes si provenía de allí
        if id_pendiente:
            self.db.table("VENTAS_PENDIENTES").delete().eq("ID_Pendiente", id_pendiente).execute()

        return id_v

    # -------------------------------------------------------------------------
    # GUARDAR / ACTUALIZAR VENTA PENDIENTE
    # -------------------------------------------------------------------------
    def guardar_pendiente(self, carrito, pagos_split, cliente_nombre, id_cliente, vendedor_id, 
                          tipo_entrega, direccion_entrega, link_maps, fecha_reparto, observaciones, id_pendiente_cargado=None):
        """Guarda una nueva venta en estado pendiente o actualiza una existente."""
        lat, lng = None, None
        if link_maps:
            coords = re.findall(r'@(-?\d+\.\d+),(-?\d+\.\d+)', link_maps)
            if coords:
                lat, lng = float(coords[0][0]), float(coords[0][1])

        desglose_pagos = " | ".join([f"{p['metodo']}: ${p['monto']:,.0f}" for p in pagos_split])

        data_to_save = {
            "Fecha": datetime.now().strftime('%Y-%m-%d'),
            "Hora": datetime.now().strftime('%H:%M:%S'),
            "Cliente": cliente_nombre,
            "ID_Cliente_Pendiente": id_cliente,
            "Vendedor": vendedor_id,
            "Metodo_Pago": desglose_pagos,
            "Pagos_JSON": json.dumps(pagos_split),
            "Detalle_JSON": json.dumps(carrito),
            "Forma_Entrega": tipo_entrega,
            "Direccion_Entrega": direccion_entrega,
            "Link_Maps_Entrega": link_maps,
            "Fecha_Entrega": str(fecha_reparto) if fecha_reparto else None,
            "Observaciones": observaciones,
            "Latitud": lat,
            "Longitud": lng
        }

        if id_pendiente_cargado:
            self.db.table("VENTAS_PENDIENTES").update(data_to_save).eq("ID_Pendiente", id_pendiente_cargado).execute()
            return False, "Venta pendiente actualizada"
        else:
            data_to_save["ID_Pendiente"] = f"PEND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.db.table("VENTAS_PENDIENTES").insert(data_to_save).execute()
            return True, "Venta guardada como nuevo pendiente"
