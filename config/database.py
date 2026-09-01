import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Inicializa y retorna el cliente de Supabase usando los secretos de Streamlit.
    Lee específicamente la sección [produccion] definida en .streamlit/secrets.toml
    """
    try:
        url: str = st.secrets["desarrollo"]["SUPABASE_URL"]
        key: str = st.secrets["desarrollo"]["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"❌ Error en la configuración de secrets.toml: Falta la clave {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error al conectar con Supabase: {e}")
        st.stop()

# Instancia global reutilizable para los servicios
db = get_supabase_client()
