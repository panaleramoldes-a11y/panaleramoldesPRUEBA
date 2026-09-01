import streamlit as st
from services.auth_service import verificar_credenciales

def render_login():
    st.title("🔐 Acceso al Sistema - Pañalera Moldes")
    
    with st.form("form_login"):
        usuario_input = st.text_input("Nombre de Usuario")
        password_input = st.text_input("Contraseña", type="password")
        submit_button = st.form_submit_button("Iniciar Sesión", use_container_width=True)

    if submit_button:
        if not usuario_input or not password_input:
            st.warning("⚠️ Por favor ingresa usuario y contraseña.")
            return

        user_data = verificar_credenciales(usuario_input, password_input)

        if user_data:
            st.session_state.autenticado = True
            st.session_state.usuario_actual = user_data.get("Nombre")
            st.session_state.vendedor_id = user_data.get("ID_Usuario")
            st.session_state.rol = user_data.get("Rol", "Vendedor")
            st.success("¡Bienvenido!")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos.")
