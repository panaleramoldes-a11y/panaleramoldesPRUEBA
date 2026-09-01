import streamlit as st
from datetime import datetime
from services.venta_service import VentaService
from database import db

def render_punto_venta():
    st.title("🛒 Punto de Venta")

    # Inicialización de estados de sesión necesarios para el POS
    if "carrito_vta" not in st.session_state:
        st.session_state.carrito_vta = []
    if "pagos_split" not in st.session_state:
        st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
    if "tipo_entrega" not in st.session_state:
        st.session_state.tipo_entrega = "Retiro en Local"
    if "direccion_entrega" not in st.session_state:
        st.session_state.direccion_entrega = ""
    if "link_maps_entrega" not in st.session_state:
        st.session_state.link_maps_entrega = ""
    if "fecha_reparto" not in st.session_state:
        st.session_state.fecha_reparto = datetime.now().date()

    # --- AQUÍ VA EL LAYOUT Y CARRITO DE PRODUCTOS (UI) ---
    st.subheader("Detalle de la Orden")
    
    # Cálculo del Total de la Venta
    total_final_vta = sum(item['subtotal'] for item in st.session_state.carrito_vta)
    st.markdown(f"### **Total: ${total_final_vta:,.2f}**")

    # --- BOTONES DE ACCIÓN: CONFIRMAR VENTA / GUARDAR PENDIENTE ---
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("✅ CONFIRMAR VENTA", use_container_width=True, type="primary"):
            if not st.session_state.carrito_vta:
                st.error("El carrito está vacío.")
            else:
                try:
                    id_v = f"VTA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    f = datetime.now().strftime('%Y-%m-%d')
                    
                    # Recuperación de metadatos de cliente y vendedor
                    id_cliente_final = st.session_state.get('id_cliente_recuperado', 1)
                    vendedor_id_final = st.session_state.get('usuario_id', 1)

                    VentaService.procesar_venta_completa(
                        id_v=id_v,
                        fecha=f,
                        id_cliente=id_cliente_final,
                        vendedor_id=vendedor_id_final,
                        pagos_split=st.session_state.pagos_split,
                        total_vta=total_final_vta,
                        tipo_entrega=st.session_state.tipo_entrega,
                        dir_entrega=st.session_state.direccion_entrega,
                        obs_entrega=st.session_state.get('observaciones_entrega', ''),
                        carrito=st.session_state.carrito_vta,
                        session_usuario=st.session_state.get('usuario_nombre'),
                        gc_activa_id=st.session_state.get('gc_activa_id')
                    )

                    # Si provenía de un pendiente, se remueve el registro previo
                    if 'id_pendiente_cargado' in st.session_state:
                        db.table("VENTAS_PENDIENTES").delete().eq("ID_Pendiente", st.session_state.id_pendiente_cargado).execute()
                        del st.session_state.id_pendiente_cargado

                    st.success(f"✅ Venta {id_v} registrada con éxito.")
                    
                    # Reset del estado del carrito
                    st.session_state.carrito_vta = []
                    st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
                    st.session_state.observaciones_entrega = ""
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al procesar la venta: {e}")

    with col_btn2:
        if st.button("⏳ GUARDAR COMO PENDIENTE", use_container_width=True):
            if not st.session_state.carrito_vta:
                st.error("El carrito está vacío.")
            else:
                try:
                    cliente_nombre_final = st.session_state.get('cliente_nombre_input', 'Consumidor Final')
                    id_cliente_final = st.session_state.get('id_cliente_recuperado', 1)
                    vendedor_id_final = st.session_state.get('usuario_id', 1)

                    payload = {
                        "cliente_nombre": cliente_nombre_final,
                        "id_cliente": id_cliente_final,
                        "vendedor_id": vendedor_id_final,
                        "pagos_split": st.session_state.pagos_split,
                        "carrito": st.session_state.carrito_vta,
                        "tipo_entrega": st.session_state.tipo_entrega,
                        "direccion_entrega": st.session_state.direccion_entrega,
                        "link_maps": st.session_state.link_maps_entrega,
                        "fecha_reparto": st.session_state.fecha_reparto,
                        "observaciones": st.session_state.get('observaciones_entrega', '')
                    }

                    id_pend = st.session_state.get('id_pendiente_cargado')
                    VentaService.guardar_pendiente(payload, id_pendiente_existente=id_pend)

                    st.toast("Venta pendiente guardada correctamente", icon="⏳")
                    
                    # Reset del estado
                    st.session_state.carrito_vta = []
                    st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]
                    st.session_state.observaciones_entrega = ""
                    st.session_state.pop('id_pendiente_cargado', None)
                    st.session_state.pop('id_cliente_recuperado', None)
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al guardar la venta pendiente: {e}")
