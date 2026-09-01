import streamlit as st

def resetear_compras():
    """Limpia las variables temporales del módulo de compras de st.session_state."""
    keys_a_limpiar = [
        'carrito_compra', 'oc_en_edicion', 'temp_prov', 
        'temp_pago', 'temp_punto', 'temp_nro', 'prod_compra_key'
    ]
    for key in keys_a_limpiar:
        if key in st.session_state:
            del st.session_state[key]
    
    st.session_state.carrito_compra = []
    st.session_state.txt_barcode = ""
    st.rerun()
