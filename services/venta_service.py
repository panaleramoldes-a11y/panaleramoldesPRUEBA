import json
import re
from datetime import datetime

def verificar_stock_suficiente(db, carrito):
    """
    Valida si hay stock suficiente en la BD antes de confirmar.
    Retorna (True, None) o (False, mensaje_error).
    """
    for item in carrito:
        p_check = db.table("PRODUCTOS").select("Nombre", "Stock_Actual", "Es_Stockeable").eq("ID_Producto", str(item["id"])).single().execute()
        if p_check.data:
            es_stockeable = p_check.data.get("Es_Stockeable", True)
            stock_actual = float(p_check.data.get("Stock_Actual", 0))
            cant_solicitada = float(item["cantidad"])

            if es_stockeable and cant_solicitada > stock_actual:
                nombre_prod = p_check.data.get("Nombre", "Desconocido")
                return False, f'El artículo "{nombre_prod}" no posee esa cantidad para facturar, revisar código y stock'
    return True, None

def verificar_saldo_giftcards(db, pagos_split, gc_activa_id):
    """
    Valida que el saldo real en BD cubra los pagos hechos con Gift Card.
    Retorna (True, None) o (False, mensaje_error).
    """
    for pago in pagos_split:
        if "Gift Card" in pago["metodo"]:
            gc_check = db.table("GIFT_CARDS").select("Saldo_Actual").eq("ID_GiftCard", gc_activa_id).single().execute()
            saldo_real = float(gc_check.data['Saldo_Actual']) if (gc_check and gc_check.data) else 0.0
            
            if pago["monto"] > saldo_real:
                return False, f"❌ ¡Saldo insuficiente en Gift Card! Disponible: ${saldo_real:,.2f}"
    return True, None

def registrar_venta_completa(db, session_state, id_cliente_final, vendedor_id_final, total_final_vta):
    """
    Procesa el registro completo de la venta en las tablas correspondientes.
    """
    id_v = datetime.now().strftime("%Y%m%d%H%M%S")
    f = datetime.now().strftime("%Y-%m-%d")

    # 1. Obtener Turno y Nombre de Usuario
    turno_res = db.table("CONTROL_TURNOS").select("ID_Turno").eq("Estado", "Abierto").maybe_single().execute()
    id_turno_val = turno_res.data['ID_Turno'] if (turno_res and turno_res.data) else "SIN_TURNO"

    nombre_usuario_actual = session_state.get('usuario_nombre')
    if not nombre_usuario_actual:
        u_res = db.table("USUARIOS").select("Nombre").eq("ID_Usuario", vendedor_id_final).single().execute()
        nombre_usuario_actual = u_res.data.get('Nombre') if (u_res and u_res.data) else str(vendedor_id_final)

    # 2. Registrar Cabecera
    desglose_pagos = " | ".join([f"{p['metodo']}: ${p['monto']:,.0f}" for p in session_state.pagos_split])
    db.table("VENTAS_CABECERA").insert({
        "ID_Venta": id_v,
        "Fecha": f,
        "ID_Cliente": id_cliente_final,
        "ID_Vendedor": vendedor_id_final, 
        "Forma_Pago": desglose_pagos,
        "Total": total_final_vta,
        "Forma_Entrega": session_state.tipo_entrega,
        "Direccion_Entrega": session_state.direccion_entrega if session_state.tipo_entrega == "Reparto" else "N/A",
        "Observaciones": session_state.get('observaciones_entrega', '')
    }).execute()

    # 3. Registrar Detalle y Actualizar Stock
    for art in session_state.carrito_vta:
        prod_data = db.table("PRODUCTOS").select("Precio_Costo", "Nombre", "Stock_Actual", "Es_Stockeable").eq("ID_Producto", str(art['id'])).single().execute()
        
        costo_historico = prod_data.data.get('Precio_Costo', 0) if prod_data.data else 0
        nombre_prod = art.get('nombre') or (prod_data.data.get('Nombre') if prod_data.data else 'Artículo')
        es_stockeable = prod_data.data.get('Es_Stockeable', True) if prod_data.data else True

        db.table("VENTAS_DETALLE").insert({
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

            db.table("PRODUCTOS").update({"Stock_Actual": stock_nuevo}).eq("ID_Producto", str(art['id'])).execute()

            db.table("MOVIMIENTOS_STOCK").insert({
                "id_producto": str(art['id']),
                "nombre_producto": nombre_prod,
                "tipo_movimiento": "VENTA",
                "cantidad": -cantidad_vendida,
                "stock_anterior": stock_actual,
                "stock_nuevo": stock_nuevo,
                "origen_referencia": f"Venta ID: {id_v}",
                "usuario": str(nombre_usuario_actual)
            }).execute()

    # 4. Registrar Pagos en VENTAS_PAGOS
    for pago in session_state.pagos_split:
        db.table("VENTAS_PAGOS").insert({
            "ID_Venta": id_v,
            "Metodo_Pago": pago["metodo"],
            "Monto": float(pago["monto"])
        }).execute()

    # 5. Registrar en Caja y procesar Gift Cards
    for pago in session_state.pagos_split:
        metodo = pago["metodo"]
        monto = float(pago["monto"])

        db.table("CAJA").insert({
            "ID_Turno": id_turno_val,
            "Fecha": datetime.now().isoformat(),
            "Tipo": "Ingreso",
            "Concepto": f"Venta {id_v} ({metodo})",
            "Monto": monto,
            "Forma_Pago": metodo
        }).execute()

        es_efectivo_reparto = (metodo == "Efectivo" and session_state.tipo_entrega == "Reparto")
        es_otro_metodo = (metodo != "Efectivo")

        if es_efectivo_reparto or es_otro_metodo:
            if "Gift Card" in metodo:
                gc_id = session_state.get('gc_activa_id')
                gc_curr = db.table("GIFT_CARDS").select("Saldo_Actual").eq("ID_GiftCard", gc_id).single().execute()
                saldo_base = float(gc_curr.data['Saldo_Actual']) if (gc_curr and gc_curr.data) else 0.0
                nuevo_saldo = saldo_base - monto

                db.table("GIFT_CARDS").update({"Saldo_Actual": float(nuevo_saldo)}).eq("ID_GiftCard", gc_id).execute()
                if nuevo_saldo <= 0:
                    db.table("GIFT_CARDS").update({"Estado": False}).eq("ID_GiftCard", gc_id).execute()

            db.table("CAJA").insert({
                "ID_Turno": id_turno_val,
                "Fecha": datetime.now().isoformat(),
                "Tipo": "Egreso",
                "Concepto": f"RETIRO PAGO {metodo.upper()} (Venta {id_v})",
                "Monto": monto,
                "Forma_Pago": metodo
            }).execute()

    # 6. Si provenía de pendientes, eliminar registro previo
    if 'id_pendiente_cargado' in session_state:
        db.table("VENTAS_PENDIENTES").delete().eq("ID_Pendiente", session_state.id_pendiente_cargado).execute()

def guardar_venta_pendiente(db, session_state, cliente_nombre_final, id_cliente_final, vendedor_id_final):
    """
    Serializa y guarda la venta actual en la tabla VENTAS_PENDIENTES.
    """
    lat, lng = None, None
    link = session_state.link_maps_entrega
    if link:
        coords = re.findall(r'@(-?\d+\.\d+),(-?\d+\.\d+)', link)
        if coords:
            lat, lng = float(coords[0][0]), float(coords[0][1])

    desglose_pagos = " | ".join([f"{p['metodo']}: ${p['monto']:,.0f}" for p in session_state.pagos_split])

    data_to_save = {
        "Fecha": datetime.now().strftime('%Y-%m-%d'),
        "Hora": datetime.now().strftime('%H:%M:%S'),
        "Cliente": cliente_nombre_final,
        "ID_Cliente_Pendiente": id_cliente_final,
        "Vendedor": vendedor_id_final,
        "Metodo_Pago": desglose_pagos,
        "Pagos_JSON": json.dumps(session_state.pagos_split),
        "Detalle_JSON": json.dumps(session_state.carrito_vta),
        "Forma_Entrega": session_state.tipo_entrega,
        "Direccion_Entrega": session_state.direccion_entrega,
        "Link_Maps_Entrega": link,
        "Fecha_Entrega": session_state.fecha_reparto,
        "Observaciones": session_state.get('observaciones_entrega', ''),
        "Latitud": lat,
        "Longitud": lng
    }

    if 'id_pendiente_cargado' in session_state and session_state.id_pendiente_cargado:
        db.table("VENTAS_PENDIENTES").update(data_to_save).eq("ID_Pendiente", session_state.id_pendiente_cargado).execute()
        return "actualizado"
    else:
        data_to_save["ID_Pendiente"] = f"PEND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db.table("VENTAS_PENDIENTES").insert(data_to_save).execute()
        return "nuevo"
