import streamlit as st

def render_sidebar():
    """
    Renderiza el menú lateral de navegación y gestiona las restricciones de acceso por rol.
    Retorna el nombre del módulo seleccionado.
    """
    st.sidebar.title("🛡️ Pañalera Moldes ERP")
    
    # Información del Usuario Logueado
    usuario = st.session_state.get("usuario_actual", "Usuario")
    rol = st.session_state.get("rol", "Vendedor")
    
    st.sidebar.markdown(f"👤 **{usuario}**  \n🏷️ *Rol: {rol}*")
    
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.logeado = False
        st.session_state.usuario_actual = None
        st.session_state.rol = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Navegación")

    # Definición de Módulos según Rol
    if rol == "Administrador":
        opciones = [
            "🛒 Punto de Venta",
            "📜 Historial de Ventas",
            "📊 Reporte de Rentabilidad",
            "📦 Compras y Stock",
            "👥 Clientes y Gift Cards",
            "🚚 Optimización de Rutas",
            "⚙️ Configuración y Pagos"
        ]
    else:
        # Rol Vendedor: Acceso restringido a tareas operativas del día
        opciones = [
            "🛒 Punto de Venta",
            "📜 Historial de Ventas",
            "📦 Compras y Stock",
            "👥 Clientes y Gift Cards"
        ]

    opcion_seleccionada = st.sidebar.radio("Ir a:", opciones)
    
    st.sidebar.markdown("---")
    st.sidebar.caption("ERP Pañalera Moldes v2.0")
    
    return opcion_seleccionada
