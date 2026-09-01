import streamlit as st
from services import config_pagos_service

def render():
    st.subheader("⚙️ Configuración de Formas de Pago")

    # 1. Formulario para agregar nuevo medio de pago
    with st.form("nuevo_pago", clear_on_submit=True):
        nuevo_pago = st.text_input("Nombre del nuevo medio de pago", placeholder="Ej: Transferencia Mercado Pago")
        submitted = st.form_submit_button("➕ Agregar Medio de Pago")
        
        if submitted:
            if nuevo_pago:
                try:
                    config_pagos_service.agregar_forma_pago(nuevo_pago)
                    st.success(f"✅ Se agregó '{nuevo_pago.strip().upper()}' correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al agregar: {e}")
            else:
                st.warning("⚠️ Debe ingresar un nombre válido.")

    st.divider()

    # 2. Listado y gestión de medios de pago existentes
    st.markdown("### Medios de Pago Registrados")
    
    try:
        pagos = config_pagos_service.obtener_formas_pago()
    except Exception as e:
        st.error(f"Error al cargar las formas de pago: {e}")
        return

    if not pagos:
        st.info("No hay formas de pago registradas.")
        return

    # Contenedor para alinear la lista
    for p in pagos:
        col1, col2, col3 = st.columns([3, 1.5, 1.5])
        
        id_pago = p.get('ID_Pago')
        nombre = p.get('Nombre_Pago', 'Sin Nombre')
        activo = p.get('Activo', False)

        with col1:
            st.write(f"**{nombre}**")

        with col2:
            if activo:
                st.caption("🟢 Activo")
            else:
                st.caption("🔴 Inactivo")

        with col3:
            if activo:
                if st.button("Desactivar", key=f"desact_{id_pago}"):
                    try:
                        config_pagos_service.cambiar_estado_pago(id_pago, False)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                if st.button("Activar", key=f"act_{id_pago}"):
                    try:
                        config_pagos_service.cambiar_estado_pago(id_pago, True)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# Aliases requeridos por ejecutar_vista() en app.py
mostrar_vista_config_pagos = render
render_config_pagos_view = render
main = render
