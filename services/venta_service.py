import json
import re
from datetime import datetime
import pandas as pd
import streamlit as st
from config.database import db
from services.audit_service import log_auditoria


class VentaService:

    # ==========================================
    # 1. FUNCIONES EXISTENTES (HISTORIAL Y ANULACIÓN)
    # ==========================================

    @staticmethod
    def obtener_ventas_completas() -> pd.DataFrame:
        """Obtiene el historial completo de ventas asociando clientes, vendedores y pagos."""
        try:
            res = (
                db.table("VENTAS")
                .select(
                    "*, CLIENTES(Nombre, Apellido, Razón Social), VENDEDORES(Nombre)"
                )
                .order("ID_Venta", desc=True)
                .execute()
            )
            return pd.DataFrame(res.data) if res.data else pd.DataFrame()
        except Exception as e:
            st.error(f"Error al cargar historial de ventas: {e}")
            return pd.DataFrame()

    @staticmethod
    def anular_venta(id_vta_a_anular: str) -> bool:
        """Procesa la anulación completa de una venta y revierte sus efectos."""
        try:
            res_vta = (
                db.table("VENTAS")
                .select("*")
                .eq("ID_Venta", id_vta_a_anular)
                .execute()
            )
            if not res_vta.data:
                st.error("No se encontró la venta especificada.")
                return False

            vta_data = res_vta.data[0]
            if vta_data.get("Estado") == "ANULADA":
                st.warning("Esta venta ya fue anulada previamente.")
                return False

            # 1. Devolver Stock
            res_detalles = (
                db.table("VENTAS_DETALLE")
                .select("*")
                .eq("ID_Venta", id_vta_a_anular)
                .execute()
            )
            if res_detalles.data:
                for item in res_detalles.data:
                    prod_id = item.get("ID_Producto")
                    cant = item.get("Cantidad", 0)
                    if prod_id and cant > 0:
                        res_prod = (
                            db.table("PRODUCTOS")
                            .select("Stock_Actual")
                            .eq("ID_Producto", prod_id)
                            .execute()
                        )
                        if res_prod.data:
                            stock_actual = res_prod.data[0].get(
                                "Stock_Actual", 0
                            )
                            nuevo_stock = stock_actual + cant
                            db.table("PRODUCTOS").update(
                                {"Stock_Actual": nuevo_stock}
                            ).eq("ID_Producto", prod_id).execute()

            # 2. Revertir Pagos de Gift Card
            res_pagos = (
                db.table("VENTAS_PAGOS")
                .select("*")
                .eq("ID_Venta", id_vta_a_anular)
                .execute()
            )
            if res_pagos.data:
                for pago in res_pagos.data:
                    id_gc = pago.get("ID_GiftCard")
                    monto_pagado = pago.get("Monto_Pagado", 0)
                    if id_gc and monto_pagado > 0:
                        res_gc = (
                            db.table("GIFT_CARDS")
                            .select("Saldo_Actual")
                            .eq("ID_GiftCard", id_gc)
                            .execute()
                        )
                        if res_gc.data:
                            saldo_act = res_gc.data[0].get("Saldo_Actual", 0)
                            db.table("GIFT_CARDS").update(
                                {"Saldo_Actual": saldo_act + monto_pagado}
                            ).eq("ID_GiftCard", id_gc).execute()

            # 3. Cambiar estado de la Venta
            db.table("VENTAS").update({"Estado": "ANULADA"}).eq(
                "ID_Venta", id_vta_a_anular
            ).execute()

            # 4. Registrar Auditoría
            usr = st.session_state.get("usuario_actual", "Sistema")
            log_auditoria(
                tabla="VENTAS",
                accion="UPDATE",
                id_entidad=str(id_vta_a_anular),
                detalles={
                    "operacion": "Anulación de Venta",
                    "monto_total": vta_data.get("Monto_Total"),
                },
                usuario=usr,
            )

            st.success(
                f"✅ Venta N° {id_vta_a_anular} anulada exitosamente."
            )
            return True

        except Exception as e:
            st.error(f"Error al anular la venta: {e}")
            return False

    # ==========================================
    # 2. NUEVAS FUNCIONES DE NUEVA VENTA Y PENDIENTES
    # ==========================================

    @staticmethod
    def obtener_turno_y_usuario(vendedor_id: int, session_usuario: str):
        """Obtiene el turno abierto actual y resuelve el nombre del usuario/vendedor."""
        turno_res = (
            db.table("CONTROL_TURNOS")
            .select("ID_Turno")
            .eq("Estado", "Abierto")
            .maybe_single()
            .execute()
        )
        id_turno = (
            turno_res.data["ID_Turno"]
            if (turno_res and turno_res.data)
            else "SIN_TURNO"
        )

        nombre_usuario = session_usuario
        if not nombre_usuario:
            u_res = (
                db.table("USUARIOS")
                .select("Nombre")
                .eq("ID_Usuario", vendedor_id)
                .single()
                .execute()
            )
            nombre_usuario = (
                u_res.data.get("Nombre")
                if (u_res and u_res.data)
                else str(vendedor_id)
            )

        return id_turno, nombre_usuario

    @staticmethod
    def procesar_venta_completa(
        id_v: str,
        fecha: str,
        id_cliente: int,
        vendedor_id: int,
        pagos_split: list,
        total_vta: float,
        tipo_entrega: str,
        dir_entrega: str,
        obs_entrega: str,
        carrito: list,
        session_usuario: str,
        gc_activa_id: str = None,
    ):
        """Ejecuta el cierre de venta completo: Cabecera, Detalle, Stock, Pagos y Caja/GiftCards."""
        id_turno, nombre_usuario = VentaService.obtener_turno_y_usuario(
            vendedor_id, session_usuario
        )
        desglose_pagos = " | ".join(
            [f"{p['metodo']}: ${p['monto']:,.0f}" for p in pagos_split]
        )

        # 1. Cabecera de Venta
        db.table("VENTAS_CABECERA").insert({
            "ID_Venta": id_v,
            "Fecha": fecha,
            "ID_Cliente": id_cliente,
            "ID_Vendedor": vendedor_id,
            "Forma_Pago": desglose_pagos,
            "Total": total_vta,
            "Forma_Entrega": tipo_entrega,
            "Direccion_Entrega": (
                dir_entrega if tipo_entrega == "Reparto" else "N/A"
            ),
            "Observaciones": obs_entrega,
        }).execute()

        # 2. Detalle de Venta y Ajuste de Stock
        for art in carrito:
            prod_data = (
                db.table("PRODUCTOS")
                .select("Precio_Costo", "Nombre", "Stock_Actual", "Es_Stockeable")
                .eq("ID_Producto", str(art["id"]))
                .single()
                .execute()
            )

            costo = (
                prod_data.data.get("Precio_Costo", 0) if prod_data.data else 0
            )
            nombre_prod = art.get("nombre") or (
                prod_data.data.get("Nombre") if prod_data.data else "Artículo"
            )
            es_stockeable = (
                prod_data.data.get("Es_Stockeable", True)
                if prod_data.data
                else True
            )

            db.table("VENTAS_DETALLE").insert({
                "ID_Venta": id_v,
                "ID_Producto": str(art["id"]),
                "Cantidad": int(art["cantidad"]),
                "Precio_Unitario": float(art["precio"]),
                "Precio_Costo_Unitario": float(costo),
                "Subtotal": float(art["subtotal"]),
            }).execute()

            if es_stockeable and prod_data.data:
                stock_actual = int(prod_data.data.get("Stock_Actual", 0))
                cant = int(art["cantidad"])
                stock_nuevo = stock_actual - cant

                db.table("PRODUCTOS").update(
                    {"Stock_Actual": stock_nuevo}
                ).eq("ID_Producto", str(art["id"])).execute()
                db.table("MOVIMIENTOS_STOCK").insert({
                    "id_producto": str(art["id"]),
                    "nombre_producto": nombre_prod,
                    "tipo_movimiento": "VENTA",
                    "cantidad": -cant,
                    "stock_anterior": stock_actual,
                    "stock_nuevo": stock_nuevo,
                    "origen_referencia": f"Venta ID: {id_v}",
                    "usuario": str(nombre_usuario),
                }).execute()

        # 3. Registros de Pagos Desglosados
        for pago in pagos_split:
            db.table("VENTAS_PAGOS").insert({
                "ID_Venta": id_v,
                "Metodo_Pago": pago["metodo"],
                "Monto": float(pago["monto"]),
            }).execute()

        # 4. Impacto en Caja y Consumo de Gift Cards
        for pago in pagos_split:
            metodo, monto = pago["metodo"], float(pago["monto"])
            db.table("CAJA").insert({
                "ID_Turno": id_turno,
                "Fecha": datetime.now().isoformat(),
                "Tipo": "Ingreso",
                "Concepto": f"Venta {id_v} ({metodo})",
                "Monto": monto,
                "Forma_Pago": metodo,
            }).execute()

            if (metodo == "Efectivo" and tipo_entrega == "Reparto") or (
                metodo != "Efectivo"
            ):
                if "Gift Card" in metodo and gc_activa_id:
                    gc_curr = (
                        db.table("GIFT_CARDS")
                        .select("Saldo_Actual")
                        .eq("ID_GiftCard", gc_activa_id)
                        .single()
                        .execute()
                    )
                    saldo_base = (
                        float(gc_curr.data["Saldo_Actual"])
                        if (gc_curr and gc_curr.data)
                        else 0.0
                    )
                    nuevo_saldo = saldo_base - monto
                    db.table("GIFT_CARDS").update(
                        {"Saldo_Actual": float(nuevo_saldo)}
                    ).eq("ID_GiftCard", gc_activa_id).execute()
                    if nuevo_saldo <= 0:
                        db.table("GIFT_CARDS").update({"Estado": False}).eq(
                            "ID_GiftCard", gc_activa_id
                        ).execute()

                db.table("CAJA").insert({
                    "ID_Turno": id_turno,
                    "Fecha": datetime.now().isoformat(),
                    "Tipo": "Egreso",
                    "Concepto": f"RETIRO PAGO {metodo.upper()} (Venta {id_v})",
                    "Monto": monto,
                    "Forma_Pago": metodo,
                }).execute()

        # Registrar Auditoría
        log_auditoria(
            tabla="VENTAS_CABECERA",
            accion="INSERT",
            id_entidad=str(id_v),
            detalles={
                "operacion": "Alta de Venta POS",
                "monto_total": total_vta,
            },
            usuario=nombre_usuario,
        )

    @staticmethod
    def guardar_pendiente(payload: dict, id_pendiente_existente: str = None):
        """Crea o actualiza una venta pendiente procesando coordenadas de Google Maps."""
        lat, lng = None, None
        link = payload.get("link_maps")
        if link:
            coords = re.findall(r"@(-?\d+\.\d+),(-?\d+\.\d+)", link)
            if coords:
                lat, lng = float(coords[0][0]), float(coords[0][1])

        desglose_pagos = " | ".join(
            [f"{p['metodo']}: ${p['monto']:,.0f}" for p in payload["pagos_split"]]
        )

        data_to_save = {
            "Fecha": datetime.now().strftime("%Y-%m-%d"),
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Cliente": payload["cliente_nombre"],
            "ID_Cliente_Pendiente": payload["id_cliente"],
            "Vendedor": payload["vendedor_id"],
            "Metodo_Pago": desglose_pagos,
            "Pagos_JSON": json.dumps(payload["pagos_split"]),
            "Detalle_JSON": json.dumps(payload["carrito"]),
            "Forma_Entrega": payload["tipo_entrega"],
            "Direccion_Entrega": payload["direccion_entrega"],
            "Link_Maps_Entrega": link,
            "Fecha_Entrega": str(payload["fecha_reparto"]),
            "Observaciones": payload["observaciones"],
            "Latitud": lat,
            "Longitud": lng,
        }

        if id_pendiente_existente:
            db.table("VENTAS_PENDIENTES").update(data_to_save).eq(
                "ID_Pendiente", id_pendiente_existente
            ).execute()
        else:
            data_to_save["ID_Pendiente"] = (
                f"PEND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            db.table("VENTAS_PENDIENTES").insert(data_to_save).execute()
