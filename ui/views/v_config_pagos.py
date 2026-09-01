import streamlit as st
from services.config_pagos_service import ConfigPagosService


def render_config_pagos():
    st.subheader("⚙️ Configuración de Formas de Pago")

    usuario_actual = st.session_state.get("usuario_actual", "Desconocido")

    # Formulario para agregar nuevo medio de pago
    with st.form("nuevo_pago", clear_on_submit=True):
        nuevo_pago = st.text_input("Nombre del nuevo medio de pago")
        submitted = st.form_submit_button("Agregar")

        if submitted:
            if ConfigPagosService.agregar_forma_pago(nuevo_pago, usuario_actual):
                st.success(f"Medio de pago '{nuevo_pago}' agregado con éxito.")
                st.rerun()

    st.divider()
    st.write("### Formas de Pago Registradas")

    # Listar formas de pago existentes
    pagos = ConfigPagosService.obtener_formas_pago()

    if not pagos:
        st.info("No hay formas de pago registradas.")
        return

    for p in pagos:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        # Nombre y Estado actual
        estado_txt = "🟢 Activo" if p.get("Activo", True) else "🔴 Inactivo"
        col1.write(f"**{p['Nombre_Pago']}** ({estado_txt})")

        # Botón para activar/desactivar dinámicamente
        es_activo = p.get("Activo", True)
        label_btn = "Desactivar" if es_activo else "Activar"
        
        if col2.button(label_btn, key=f"btn_pago_{p['ID_Pago']}"):
            if ConfigPagosService.cambiar_estado_pago(p["ID_Pago"], not es_activo, usuario_actual):
                st.rerun()


def modulo_config_pagos():
    """Función wrapper de compatibilidad para menú principal."""
    render_config_pagos()
