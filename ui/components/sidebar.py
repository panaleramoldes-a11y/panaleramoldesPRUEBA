import streamlit as st

def render_sidebar():
    """
    Renderiza la barra lateral con el diseño clásico (selectbox) y retorna la vista seleccionada.
    """
    with st.sidebar:
        st.title("🛡️ Pañalera Moldes")
        
        usuario = st.session_state.get("usuario_actual", "Usuario")
        rol = st.session_state.get("rol", "Vendedor")
        
        st.write(f"👤 Usuario: {usuario}")
        st.write(f"💼 Rol: {rol}")
        
        # Definición de opciones según el rol
        opciones_disponibles = ["💰 Caja"]
        
        if rol == "Administrador":
            opciones_disponibles.extend([
                "🛒 Punto de Venta", 
                "👥 Clientes", 
                "📜 Historial de Ventas", 
                "⚙️ Config. Pagos", 
                "📦 Productos",
                "📊 Control de Stock", 
                "🏢 Proveedores", 
                "🛍️ Compras", 
                "👔 Vendedores", 
                "📋 Auditoría", 
                "💰 Utilidades", 
                "🚚 Repartos", 
                "📈 Reportes"
            ])
        elif rol == "Vendedor":
            opciones_disponibles.extend([
                "🛒 Punto de Venta", 
                "🚚 Repartos", 
                "📦 Productos", 
                "👥 Clientes"
            ])
        
        # Desplegable del menú principal
        menu_seleccionado = st.selectbox("Menú Principal", opciones_disponibles)
        
        st.divider()
        
        # Botón para cerrar sesión
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.clear()
            st.session_state.autenticado = False
            st.rerun()
            
    return menu_seleccionado
