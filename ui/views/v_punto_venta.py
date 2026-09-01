import streamlit as st
import services.venta_service as venta_service

def render_punto_venta(db, total_final_vta, vendedor_id_final, cliente_nombre_final, id_cliente_final):
    """
    Vista del Punto de Venta.
    Recibe la conexión a la base de datos y las variables calculadas en las Secciones 1 a 5.
    """
    
    # --- [SECCIONES 1 A 5 DENTRO DE LA VISTA] ---
    # Aquí va el renderizado de selección de productos, carrito, totales, etc.
    
    # --- 6. BOTONES DE CIERRE (Solo visibles si hay productos en el carrito) ---
    if st.session_state.carrito_vta:
        st.divider()
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            if st.button("🏁 FINALIZAR Y REGISTRAR VENTA", width='stretch', type="primary"):
                # 0. Verificación de sumas de pago
                suma_pagos = sum(float(p["monto"]) for p in st.session_state.pagos_split)
                if abs(suma_pagos - total_final_vta) > 0.01:
                    st.error(f"¡Error! La suma de los pagos (${suma_pagos:.2f}) no coincide con el total (${total_final_vta:.2f})")
                else:
                    # Validaciones en BD a través del servicio
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
                            # Procesar Venta
                            try:
                                venta_service.registrar_venta_completa(
                                    db, 
                                    st.session_state, 
                                    id_cliente_final, 
                                    vendedor_id_final, 
                                    total_final_vta
                                )
                                st.success("✅ Venta registrada correctamente!")
                                
                                # Limpieza del Estado
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

                    # Limpieza del Estado
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
