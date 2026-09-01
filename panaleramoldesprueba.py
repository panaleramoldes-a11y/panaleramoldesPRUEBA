"""
panaleramoldesprueba.py
Punto de entrada principal de la aplicación Streamlit alineado con la estructura real de views/.
"""

import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Pañalera Moldes - Sistema de Gestión",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# 1. IMPORTACIÓN DE VISTAS (Basado en la estructura real de views/)
# -----------------------------------------------------------------------------
from views.v_auditoria import render_auditoria_view
from views.v_caja import render_caja_view
from views.v_clientes import render_clientes_view
from views.v_compras import render_compras_view
from views.v_config_pagos import render_config_pagos_view
from views.v_historial_ventas import render_historial_ventas_view
from views.v_productos import render_productos_view
from views.v_proveedores import render_proveedores_view
from views.v_punto_venta import render_punto_venta_view
from views.v_repartos import render_repartos_view
from views.v_reportes import render_reportes_view
from views.v_stock import render_stock_view
from views.v_utilidades import render_utilidades_view
from views.v_vendedores import render_vendedores_view

# -----------------------------------------------------------------------------
# 2. CONTROL DE SESIÓN
# -----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = True  # O tu lógica de autenticación

usuario_actual = st.session_state.get("usuario", "Usuario")
rol_actual = st.session_state.get("rol", "Administrador")

# -----------------------------------------------------------------------------
# 3. NAVEGACIÓN Y MENÚ
# -----------------------------------------------------------------------------
st.sidebar.title("Pañalera Moldes")
st.sidebar.caption(f"👤 **{usuario_actual}** ({rol_actual})")

if rol_actual == "Administrador":
    opciones_menu = [
        "🛒 Punto de Venta",
        "📜 Historial de Ventas",
        "📦 Productos",
        "📊 Control de Stock",
        "👥 Clientes",
        "🏢 Proveedores",
        "🛍️ Compras",
        "👔 Vendedores",
        "💵 Caja",
        "🚚 Repartos",
        "📈 Reportes",
        "💰 Utilidades",
        "⚙️ Config. Pagos",
        "📋 Auditoría",
    ]
else:
    opciones_menu = [
        "🛒 Punto de Venta",
        "📜 Historial de Ventas",
        "📦 Productos",
        "🚚 Repartos",
    ]

menu_seleccionado = st.sidebar.radio("Navegación", opciones_menu)

st.sidebar.divider()
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# -----------------------------------------------------------------------------
# 4. ENRUTADOR DE VISTAS
# -----------------------------------------------------------------------------
if menu_seleccionado == "🛒 Punto de Venta":
    render_punto_venta_view()

elif menu_seleccionado == "📜 Historial de Ventas":
    render_historial_ventas_view()

elif menu_seleccionado == "📦 Productos":
    render_productos_view()

elif menu_seleccionado == "📊 Control de Stock":
    render_stock_view()

elif menu_seleccionado == "👥 Clientes":
    render_clientes_view()

elif menu_seleccionado == "🏢 Proveedores":
    render_proveedores_view()

elif menu_seleccionado == "🛍️ Compras":
    render_compras_view()

elif menu_seleccionado == "👔 Vendedores":
    render_vendedores_view()

elif menu_seleccionado == "💵 Caja":
    render_caja_view()

elif menu_seleccionado == "🚚 Repartos":
    render_repartos_view()

elif menu_seleccionado == "📈 Reportes":
    render_reportes_view()

elif menu_seleccionado == "💰 Utilidades":
    render_utilidades_view()

elif menu_seleccionado == "⚙️ Config. Pagos":
    render_config_pagos_view()

elif menu_seleccionado == "📋 Auditoría":
    render_auditoria_view()
