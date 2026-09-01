import streamlit as st
from services.venta_service import registrar_venta, guardar_venta_pendiente


def render_botones_cierre(
    db, total_final_vta, id_cliente_final, cliente_nombre_final, vendedor_id_final
):
    """Renderiza los botones de acción para procesar o guardar la venta pendiente."""
    if not st.session_state.get("carrito_vta"):
        st.info("El carrito está vacío.")
        return

    st.divider()
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        if st.button(
            "🏁 FINALIZAR Y REGISTRAR VENTA",
            use_container_width=True,
            type="primary",
        ):
            suma_pagos = sum(
                float(p["monto"])
                for p in st.session_state.get("pagos_split", [])
            )

            if abs(suma_pagos - total_final_vta) > 0.01:
                st.error(
                    f"¡Error! La suma de los pagos (${suma_pagos:.2f}) no coincide con el total (${total_final_vta:.2f})"
                )
            else:
                try:
                    id_venta_registrada = registrar_venta(
                        db=db,
                        carrito=st.session_state.carrito_vta,
                        pagos_split=st.session_state.pagos_split,
                        total_final=total_final_vta,
                        cliente_id=id_cliente_final,
                        vendedor_id=vendedor_id_final,
                        tipo_entrega=st.session_state.get(
                            "tipo_entrega", "Mostrador"
                        ),
                        direccion_entrega=st.session_state.get(
                            "direccion_entrega", ""
                        ),
                        observaciones=st.session_state.get(
                            "observaciones_entrega", ""
                        ),
                        gc_activa_id=st.session_state.get("gc_activa_id"),
                        usuario_nombre=st.session_state.get("usuario_nombre"),
                        id_pendiente_cargado=st.session_state.get(
                            "id_pendiente_cargado"
                        ),
                    )

                    st.success(
                        f"✅ Venta {id_venta_registrada} registrada correctamente!"
                    )

                    st.session_state.carrito_vta = []
                    st.session_state.pagos_split = [
                        {"metodo": "Efectivo", "monto": 0.0}
                    ]
                    st.session_state.observaciones_entrega = ""
                    if "id_pendiente_cargado" in st.session_state:
                        del st.session_state.id_pendiente_cargado

                    st.rerun()

                except Exception as e:
                    st.error(f"Error al registrar: {e}")

    with col_f2:
        if st.button("⏳ GUARDAR COMO PENDIENTE", use_container_width=True):
            try:
                resultado = guardar_venta_pendiente(
                    db=db,
                    carrito=st.session_state.carrito_vta,
                    pagos_split=st.session_state.pagos_split,
                    cliente_nombre=cliente_nombre_final,
                    cliente_id=id_cliente_final,
                    vendedor_id=vendedor_id_final,
                    tipo_entrega=st.session_state.get(
                        "tipo_entrega", "Mostrador"
                    ),
                    direccion_entrega=st.session_state.get(
                        "direccion_entrega", ""
                    ),
                    link_maps=st.session_state.get("link_maps_entrega", ""),
                    fecha_reparto=st.session_state.get("fecha_reparto"),
                    observaciones=st.session_state.get(
                        "observaciones_entrega", ""
                    ),
                    id_pendiente_cargado=st.session_state.get(
                        "id_pendiente_cargado"
                    ),
                )

                if resultado == "actualizado":
                    st.toast("Venta pendiente actualizada", icon="🔄")
                else:
                    st.toast(
                        "Venta guardada como nuevo pendiente", icon="⏳"
                    )

                st.session_state.carrito_vta = []
                st.session_state.pagos_split = [
                    {"metodo": "Efectivo", "monto": 0.0}
                ]
                st.session_state.observaciones_entrega = ""

                if "id_pendiente_cargado" in st.session_state:
                    del st.session_state.id_pendiente_cargado
                if "id_cliente_recuperado" in st.session_state:
                    del st.session_state.id_cliente_recuperado

                st.rerun()

            except Exception as e:
                st.error(f"Error al guardar pendiente: {e}")


def render(db=None):
    """Punto de entrada compatible con invocación sin argumentos desde 'ejecutar_vista'."""
    # Recuperar conexión db de la sesión si no se pasó como parámetro
    if db is None:
        db = st.session_state.get("db") or st.session_state.get("supabase")

    st.title("🛒 Punto de Venta")

    if "carrito_vta" not in st.session_state:
        st.session_state.carrito_vta = []
    if "pagos_split" not in st.session_state:
        st.session_state.pagos_split = [{"metodo": "Efectivo", "monto": 0.0}]

    total_venta = sum(
        item.get("subtotal", 0.0) for item in st.session_state.carrito_vta
    )
    id_cliente = st.session_state.get("id_cliente", "CLI-000")
    nombre_cliente = st.session_state.get("nombre_cliente", "Consumidor Final")
    id_vendedor = st.session_state.get("id_usuario", "USER-001")

    render_botones_cierre(
        db=db,
        total_final_vta=total_venta,
        id_cliente_final=id_cliente,
        cliente_nombre_final=nombre_cliente,
        vendedor_id_final=id_vendedor,
    )


# Alias de soporte
main = render
