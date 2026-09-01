"""
panaleramoldesprueba.py
Punto de entrada principal de la aplicación Streamlit.
Administra autenticación, enrutamiento por roles y carga de módulos.
"""

import streamlit as st

# Configuración inicial de la página (debe ser la primera orden de Streamlit)
st.set_page_config(
    page_title="Pañalera Moldes - Sistema de Gestión",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# 1. IMPORTACIÓN DE VISTAS (UI VIEWS)
# -----------------------------------------------------------------------------
from ui.views.v_login import render_login_view
from ui.views.v_nueva_venta import render_nueva_venta_view
from ui.views.v_catalogo import render_catalogo_view
from ui.views.v_presupuestos import render_presupuestos_view
from ui.views.v_historial_ventas import render_historial_ventas_view
from ui.views.v_cuentas_corrientes import render_cuentas_corrientes_view
from ui.views.v_caja import render_caja_view
from ui.views.v_productos import render_productos_view
from ui.views.v_clientes import render_clientes_view
from ui.views.v_proveedores import render_proveedores_view
from ui.views.v_compras import render_compras_view
from ui.views.v_vendedores import render_vendedores_view
from ui.views.v_gastos import render_gastos_view
from ui.views.v_repartos import render_repartos_view
from ui.views.v_reportes import render_reportes_view

# -----------------------------------------------------------------------------
# 2. VERIFICACIÓN Y CONTROL DE SESIÓN (AUTH)
# -----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    render_login_view()
    st.stop()

# Datos del usuario autenticado
usuario_actual = st.session_state.get("usuario", "Usuario")
rol_actual = st.session_state.get("rol", "Vendedor")

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (SIDEBAR) & NAVEGACIÓN
# -----------------------------------------------------------------------------
st.sidebar.image("https://via.placeholder.com/150", width=120)  # Reemplazar por logo si aplica
st.sidebar.title("Pañalera Moldes")
st.sidebar.caption(f"👤 **{usuario_actual}** ({rol_actual})")

# Menú según rol de usuario
if rol_actual == "Administrador":
    opciones_menu = [
        "🛒 Nueva Venta",
        "📖 Catalogo de Productos",
        "📄 Presupuestos",
        "📜 Historial de Ventas",
        "🤝 Cuentas Corrientes",
        "💵 Caja Diaria",
        "📦 Productos & Stock",
        "👥 Clientes",
        "🏢 Proveedores",
        "🛍️ Compras",
        "👔 Vendedores",
        "💸 Gastos",
        "🚚 Repartos",
        "📊 Reportes",
    ]
else:
    # Vista restringida para perfil Vendedor
    opciones_menu = [
        "🛒 Nueva Venta",
        "📖 Catalogo de Productos",
        "📄 Presupuestos",
        "📜 Historial de Ventas",
        "🤝 Cuentas Corrientes",
        "🚚 Repartos",
    ]

menu_seleccionado = st.sidebar.radio("Navegación", opciones_menu)

# Botón de cierre de sesión
st.sidebar.divider()
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# -----------------------------------------------------------------------------
# 4. ENRUTADOR PRINCIPAL (ROUTER 14/14 MÓDULOS)
# -----------------------------------------------------------------------------
if menu_seleccionado == "🛒 Nueva Venta":
    render_nueva_venta_view()

elif menu_seleccionado == "📖 Catalogo de Productos":
    render_catalogo_view()

elif menu_seleccionado == "📄 Presupuestos":
    render_presupuestos_view()

elif menu_seleccionado == "📜 Historial de Ventas":
    render_historial_ventas_view()

elif menu_seleccionado == "🤝 Cuentas Corrientes":
    render_cuentas_corrientes_view()

elif menu_seleccionado == "💵 Caja Diaria":
    render_caja_view()

elif menu_seleccionado == "📦 Productos & Stock":
    render_productos_view()

elif menu_seleccionado == "👥 Clientes":
    render_clientes_view()

elif menu_seleccionado == "🏢 Proveedores":
    render_proveedores_view()

elif menu_seleccionado == "🛍️ Compras":
    render_compras_view()

elif menu_seleccionado == "👔 Vendedores":
    render_vendedores_view()

elif menu_seleccionado == "💸 Gastos":
    render_gastos_view()

elif menu_seleccionado == "🚚 Repartos":
    render_repartos_view()

elif menu_seleccionado == "📊 Reportes":
    render_reportes_view()
