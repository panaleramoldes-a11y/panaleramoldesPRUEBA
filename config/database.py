import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Inicializa y retorna el cliente de Supabase usando los secretos de Streamlit.
    Asegúrate de tener definidas SUPABASE_URL y SUPABASE_KEY en .streamlit/secrets.toml
    """
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# Instancia global reutilizable
db = get_supabase_client()
