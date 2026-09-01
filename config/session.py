import streamlit as st

def init_session_state():
    """Inicializa los valores por defecto del estado de sesión."""
    if "logeado" not in st.session_state:
        st.session_state.logeado = False

    if "usuario_actual" not in st.session_state:
        st.session_state.usuario_actual = None

    if "rol" not in st.session_state:
        st.session_state.rol = None

    if "lista_global_vta" not in st.session_state:
        st.session_state.lista_global_vta = []

    if "carrito_compra" not in st.session_state:
        st.session_state.carrito_compra = []

    if "txt_barcode" not in st.session_state:
        st.session_state.txt_barcode = ""
