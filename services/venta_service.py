from datetime import datetime
import json
import re


def validar_stock_carrito(db, carrito):
    """
    Verifica que el stock de los productos stockeables sea suficiente antes de procesar.
    Retorna (True, None) si es correcto o (False, mensaje_error).
    """
    for item in carrito:
        p_check = (
            db.table("PRODUCTOS")
            .select("Nombre", "Stock_Actual", "Es_Stockeable")
            .eq("ID_Producto", str(item["id"]))
            .single()
            .execute()
        )

        if p_check.data:
            es_stockeable = p_check.data.get("Es_Stockeable", True)
            stock_actual = float(p_check.data.get("Stock_Actual", 0))
            cant_solicitada = float(item["cantidad"])

            if es_stockeable and cant_solicitada > stock_actual:
                nombre_prod = p_check.data.get("Nombre", "Desconocido")
                return (
                    False,
                    f'El artículo "{nombre_prod}" no posee esa cantidad para facturar, revisar código y stock.',
                )

    return True, None


def validar_saldo_giftcard(db, pagos_split, gc_activa_id):
    """
    Valida el saldo real disponible en la base de datos si se usa Gift Card.
    Retorna (True, None) si es correcto o (False, mensaje_error).
    """
    for pago in pagos_split:
        if "Gift Card" in pago["metodo"]:
            gc_check = (
                db.table("GIFT_CARDS")
                .select("Saldo_Actual")
                .eq("ID_GiftCard", gc_activa_id)
                .single()
                .execute()
            )

            saldo_real = (
                float(gc_check.data["Saldo_Actual"])
                if (gc_check and gc_check.data)
                else 0.0
            )

            if pago["monto"] > saldo_real:
                return (
                    False,
                    f"❌ ¡Saldo insuficiente en Gift Card! Disponible: ${saldo_real:,.2f}",
                )

    return True, None


def obtener_turno_abierto(db):
    """Retorna el ID del turno abierto actual o 'SIN_TURNO'."""
    turno_res = (
        db.table("CONTROL_TURNOS")
        .select("ID_Turno")
        .eq("Estado", "Abierto")
        .maybe_single()
        .execute()
    )
    return (
        turno_res.data["ID_Turno"]
        if (turno_res and turno_res.data)
        else "SIN_TURNO"
    )


def obtener_nombre_usuario(db, vendedor_id, usuario_nombre_session=None):
    """Retorna el nombre del usuario asignado."""
    if usuario_nombre_session:
        return usuario_nombre_session

    u_res = (
        db.table("USUARIOS")
        .select("Nombre")
        .eq("ID_Usuario", vendedor_id)
        .single()
        .execute()
    )
    return (
        u_res.data.get("Nombre")
        if (u_res and u_res.data)
        else str(vendedor_id)
    )


def registrar_venta(
    db,
    carrito,
    pagos_split,
    total_final,
    cliente_id,
    vendedor_id,
    tipo_entrega,
    direccion_entrega,
    observaciones,
    gc_activa_id=None,
    usuario_nombre=None,
    id_pendiente_cargado=None,
):
    """
    Registra la venta completa en Supabase (Cabecera, Detalle, Stock, Pagos, Caja y consumo GC).
    """
    # 1. Validaciones previas
    val_stock, err_stock = validar_stock_carrito(db, carrito)
    if not val_stock:
        raise Exception(err_stock)

    val_gc, err_gc = validar_saldo_giftcard(db, pagos_split, gc_activa_id)
    if not val_gc:
        raise Exception(err_gc)

    # 2. Generar IDs y variables de sesión
    id_v = datetime.now().strftime("%Y%m%d%H%M%S")
    f = datetime.now().strftime("%Y-%m-%d")
    id_turno_val = obtener_turno_abierto(db)
    nombre_usuario_actual = obtener_nombre_usuario(
        db, vendedor_id, usuario_nombre
    )

    # 3. Registrar Cabecera
    desglose_pagos = " | ".join(
        [f"{p['metodo']}: ${p['monto']:,.0f}" for p in pagos_split]
    )
    db.table("VENTAS_CABECERA").insert(
        {
            "ID_Venta": id_v,
            "Fecha": f,
            "ID_Cliente": cliente_id,
            "ID_Vendedor": vendedor_id,
            "Forma_Pago": desglose_pagos,
            "Total": total_final,
            "Forma_Entrega": tipo_entrega,
            "Direccion_Entrega": (
                direccion_entrega if tipo_entrega == "Reparto" else "N/A"
            ),
            "Observaciones": observaciones,
        }
    ).execute()

    # 4. Registrar Detalle y Actualizar Inventario
    for art in carrito:
        prod_data = (
            db.table("PRODUCTOS")
            .select("Precio_Costo", "Nombre", "Stock_Actual", "Es_Stockeable")
            .eq("ID_Producto", str(art["id"]))
            .single()
            .execute()
        )

        costo_historico = (
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

        db.table("VENTAS_DETALLE").insert(
            {
                "ID_Venta": id_v,
                "ID_Producto": str(art["id"]),
                "Cantidad": int(art["cantidad"]),
                "Precio_Unitario": float(art["precio"]),
                "Precio_Costo_Unitario": float(costo_historico),
                "Subtotal": float(art["subtotal"]),
            }
        ).execute()

        # Descontar stock si es stockeable
        if es_stockeable and prod_data.data:
            stock_actual = int(prod_data.data.get("Stock_Actual", 0))
            cantidad_vendida = int(art["cantidad"])
            stock_nuevo = stock_actual - cantidad_vendida

            db.table("PRODUCTOS").update({"Stock_Actual": stock_nuevo}).eq(
                "ID_Producto", str(art["id"])
            ).execute()

            db.table("MOVIMIENTOS_STOCK").insert(
                {
                    "id_producto": str(art["id"]),
                    "nombre_producto": nombre_prod,
                    "tipo_movimiento": "VENTA",
                    "cantidad": -cantidad_vendida,
                    "stock_anterior": stock_actual,
                    "stock_nuevo": stock_nuevo,
                    "origen_referencia": f"Venta ID: {id_v}",
                    "usuario": str(nombre_usuario_actual),
                }
            ).execute()

    # 5. Registrar Pagos en VENTAS_PAGOS
    for pago in pagos_split:
        db.table("VENTAS_PAGOS").insert(
            {
                "ID_Venta": id_v,
                "Metodo_Pago": pago["metodo"],
                "Monto": float(pago["monto"]),
            }
        ).execute()

    # 6. Registrar en Caja y procesar Gift Cards
    for pago in pagos_split:
        metodo = pago["metodo"]
        monto = float(pago["monto"])

        db.table("CAJA").insert(
            {
                "ID_Turno": id_turno_val,
                "Fecha": datetime.now().isoformat(),
                "Tipo": "Ingreso",
                "Concepto": f"Venta {id_v} ({metodo})",
                "Monto": monto,
                "Forma_Pago": metodo,
            }
        ).execute()

        es_efectivo_reparto = (
            metodo == "Efectivo" and tipo_entrega == "Reparto"
        )
        es_otro_metodo = metodo != "Efectivo"

        if es_efectivo_reparto or es_otro_metodo:
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

            db.table("CAJA").insert(
                {
                    "ID_Turno": id_turno_val,
                    "Fecha": datetime.now().isoformat(),
                    "Tipo": "Egreso",
                    "Concepto": f"RETIRO PAGO {metodo.upper()} (Venta {id_v})",
                    "Monto": monto,
                    "Forma_Pago": metodo,
                }
            ).execute()

    # 7. Eliminar de pendientes si venía de un pedido pendiente
    if id_pendiente_cargado:
        db.table("VENTAS_PENDIENTES").delete().eq(
            "ID_Pendiente", id_pendiente_cargado
        ).execute()

    return id_v


def guardar_venta_pendiente(
    db,
    carrito,
    pagos_split,
    cliente_nombre,
    cliente_id,
    vendedor_id,
    tipo_entrega,
    direccion_entrega,
    link_maps,
    fecha_reparto,
    observaciones,
    id_pendiente_cargado=None,
):
    """
    Guarda o actualiza una venta en la tabla VENTAS_PENDIENTES.
    """
    lat, lng = None, None
    if link_maps:
        coords = re.findall(r"@(-?\d+\.\d+),(-?\d+\.\d+)", link_maps)
        if coords:
            lat, lng = float(coords[0][0]), float(coords[0][1])

    desglose_pagos = " | ".join(
        [f"{p['metodo']}: ${p['monto']:,.0f}" for p in pagos_split]
    )

    data_to_save = {
        "Fecha": datetime.now().strftime("%Y-%m-%d"),
        "Hora": datetime.now().strftime("%H:%M:%S"),
        "Cliente": cliente_nombre,
        "ID_Cliente_Pendiente": cliente_id,
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
        "Longitud": lng,
    }

    if id_pendiente_cargado:
        db.table("VENTAS_PENDIENTES").update(data_to_save).eq(
            "ID_Pendiente", id_pendiente_cargado
        ).execute()
        return "actualizado"
    else:
        data_to_save["ID_Pendiente"] = (
            f"PEND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        db.table("VENTAS_PENDIENTES").insert(data_to_save).execute()
        return "creado"


def anular_venta(db, id_venta, motivo, usuario_actual):
    """
    Anula una venta, restituye el stock de productos stockeables y registra contramovimientos.
    """
    venta = (
        db.table("VENTAS_CABECERA")
        .select("*")
        .eq("ID_Venta", id_venta)
        .single()
        .execute()
    )
    if not venta or not venta.data:
        raise Exception("La venta especificada no existe.")

    detalles = (
        db.table("VENTAS_DETALLE")
        .select("*")
        .eq("ID_Venta", id_venta)
        .execute()
    )

    # Revertir stock
    for det in detalles.data:
        prod = (
            db.table("PRODUCTOS")
            .select("Stock_Actual", "Es_Stockeable", "Nombre")
            .eq("ID_Producto", str(det["ID_Producto"]))
            .single()
            .execute()
        )
        if prod.data and prod.data.get("Es_Stockeable", True):
            stock_act = int(prod.data.get("Stock_Actual", 0))
            cant_devolucion = int(det["Cantidad"])
            stock_nuevo = stock_act + cant_devolucion

            db.table("PRODUCTOS").update({"Stock_Actual": stock_nuevo}).eq(
                "ID_Producto", str(det["ID_Producto"])
            ).execute()

            db.table("MOVIMIENTOS_STOCK").insert(
                {
                    "id_producto": str(det["ID_Producto"]),
                    "nombre_producto": prod.data.get("Nombre", "Artículo"),
                    "tipo_movimiento": "ANULACIÓN VENTA",
                    "cantidad": cant_devolucion,
                    "stock_anterior": stock_act,
                    "stock_nuevo": stock_nuevo,
                    "origen_referencia": (
                        f"Anulación Venta ID: {id_venta} - Motivo: {motivo}"
                    ),
                    "usuario": str(usuario_actual),
                }
            ).execute()

    # Marcar venta como anulada
    db.table("VENTAS_CABECERA").update(
        {
            "Observaciones": f"[ANULADA: {motivo}] "
            + str(venta.data.get("Observaciones", ""))
        }
    ).eq("ID_Venta", id_venta).execute()

    return True
