import streamlit as st
import services.venta_service as venta_service
# Importar la conexión a BD definida en la configuración global
from config.database import db 

def render_punto_venta_view():
    """
    Punto de entrada invocado dinámicamente por ejecutar_vista(v_punto_venta)
    """
    # 1. Obtención de datos de sesión y cálculo de variables locales
    vendedor_id_final = st.session_state.get("usuario_id")
    cliente_nombre_final = st.session_state.get("cliente_actual_nombre", "Consumidor Final")
    id_cliente_final = st.session_state.get("cliente_actual_id", 1)
    
    # Renderizado de UI, tablas, selectores...
    
    total_final_vta = sum(art['subtotal'] for art in st.session_state.get("carrito_vta", []))

    # --- BOTONES DE CIERRE Y PROCESAMIENTO ---
    if st.session_state.carrito_vta:
        st.divider()
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            if st.button("🏁 FINALIZAR Y REGISTRAR VENTA", width='stretch', type="primary"):
                suma_pagos = sum(float(p["monto"]) for p in st.session_state.pagos_split)
                if abs(suma_pagos - total_final_vta) > 0.01:
                    st.error(f"¡Error! La suma de los pagos (${suma_pagos:.2f}) no coincide con el total (${total_final_vta:.2f})")
                else:
                    ok_stock, msg_stock = venta_service.verificar_stock_suficiente(db, st.session_state.carrito_vta)
                    if not ok_stock:
                        st.error(msg_stock)
                    else:
                        ok_gc, msg_gc = venta_service.verificar_saldo_giftcards(
                            db, 
                            st.session_state.pagos_split, 
                            st.session_state.get('gc_activa_id')
                        )
                        if not ok_gc:
                            st.error(msg_gc)
                        else:
                            try:
                                venta_service.registrar_venta_completa(
                                    db, 
                                    st.session_state, 
                                    id_cliente_final, 
                                    vendedor_id_final, 
                                    total_final_vta
                                )
                                st.success("✅ Venta registrada correctamente!")
                                st.session_state.carrito_vta = []
                                st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
                                st.session_state.observaciones_entrega = ""
                                if 'id_pendiente_cargado' in st.session_state:
                                    del st.session_state.id_pendiente_cargado
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al registrar: {e}")

        with col_f2:
            if st.button("⏳ GUARDAR COMO PENDIENTE", width='stretch'):
                try:
                    res = venta_service.guardar_venta_pendiente(
                        db, 
                        st.session_state, 
                        cliente_nombre_final, 
                        id_cliente_final, 
                        vendedor_id_final
                    )
                    
                    if res == "actualizado":
                        st.toast("Venta pendiente actualizada", icon="🔄")
                    else:
                        st.toast("Venta guardada como nuevo pendiente", icon="⏳")

                    st.session_state.carrito_vta = []
                    st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
                    st.session_state.observaciones_entrega = ""
                    if 'id_pendiente_cargado' in st.session_state:
                        del st.session_state.id_pendiente_cargado
                    if 'id_cliente_recuperado' in st.session_state:
                        del st.session_state.id_cliente_recuperado

                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar pendiente: {e}")
    else:
        st.info("El carrito está vacío.")
