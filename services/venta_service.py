import streamlit as st
import pandas as pd
from config.database import db
from services.audit_service import log_auditoria

def obtener_ventas_completas():
    """Obtiene el historial completo de ventas asociando clientes, vendedores y pagos."""
    try:
        res = db.table("VENTAS").select("*, CLIENTES(Nombre, Apellido, Razón Social), VENDEDORES(Nombre)").order("ID_Venta", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar historial de ventas: {e}")
        return pd.DataFrame()

def anular_venta(id_vta_a_anular):
    """Procesa la anulación completa de una venta y revierte sus efectos."""
    try:
        res_vta = db.table("VENTAS").select("*").eq("ID_Venta", id_vta_a_anular).execute()
        if not res_vta.data:
            st.error("No se encontró la venta especificada.")
            return False

        vta_data = res_vta.data[0]
        if vta_data.get("Estado") == "ANULADA":
            st.warning("Esta venta ya fue anulada previamente.")
            return False

        # 1. Devolver Stock
        res_detalles = db.table("VENTAS_DETALLE").select("*").eq("ID_Venta", id_vta_a_anular).execute()
        if res_detalles.data:
            for item in res_detalles.data:
                prod_id = item.get("ID_Producto")
                cant = item.get("Cantidad", 0)
                if prod_id and cant > 0:
                    res_prod = db.table("PRODUCTOS").select("Stock_Actual").eq("ID_Producto", prod_id).execute()
                    if res_prod.data:
                        stock_actual = res_prod.data[0].get("Stock_Actual", 0)
                        nuevo_stock = stock_actual + cant
                        db.table("PRODUCTOS").update({"Stock_Actual": nuevo_stock}).eq("ID_Producto", prod_id).execute()

        # 2. Revertir Pagos de Gift Card
        res_pagos = db.table("VENTAS_PAGOS").select("*").eq("ID_Venta", id_vta_a_anular).execute()
        if res_pagos.data:
            for pago in res_pagos.data:
                id_gc = pago.get("ID_GiftCard")
                monto_pagado = pago.get("Monto_Pagado", 0)
                if id_gc and monto_pagado > 0:
                    res_gc = db.table("GIFT_CARDS").select("Saldo_Actual").eq("ID_GiftCard", id_gc).execute()
                    if res_gc.data:
                        saldo_act = res_gc.data[0].get("Saldo_Actual", 0)
                        db.table("GIFT_CARDS").update({"Saldo_Actual": saldo_act + monto_pagado}).eq("ID_GiftCard", id_gc).execute()

        # 3. Cambiar estado de la Venta
        db.table("VENTAS").update({"Estado": "ANULADA"}).eq("ID_Venta", id_vta_a_anular).execute()

        # 4. Registrar Auditoría
        usr = st.session_state.get('usuario_actual', 'Sistema')
        log_auditoria(
            tabla="VENTAS",
            accion="UPDATE",
            id_entidad=str(id_vta_a_anular),
            detalles={"operacion": "Anulación de Venta", "monto_total": vta_data.get("Monto_Total")},
            usuario=usr
        )

        st.success(f"✅ Venta N° {id_vta_a_anular} anulada exitosamente.")
        return True

    except Exception as e:
        st.error(f"Error al anular la venta: {e}")
        return False
