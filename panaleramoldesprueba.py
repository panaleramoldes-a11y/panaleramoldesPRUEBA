"""
app.py
Punto de entrada principal con enrutamiento dinámico y control de acceso.
"""

import sys
from pathlib import Path
import streamlit as st

# --- CONFIGURACIÓN DE RUTAS DEL PROYECTO ---
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Configuración inicial de la página
st.set_page_config(
    page_title="Pañalera Moldes - Sistema de Gestión",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- IMPORTACIÓN DE VISTAS Y COMPONENTES ---
from ui.views.v_login import render_login
from ui.components.sidebar import render_sidebar
from ui.views import (
    v_auditoria,
    v_caja,
    v_clientes,
    v_compras,
    v_config_pagos,
    v_historial_ventas,
    v_productos,
    v_proveedores,
    v_punto_venta,
    v_repartos,
    v_reportes,
    v_stock,
    v_utilidades,
    v_vendedores,
)

# -----------------------------------------------------------------------------
# 1. EJECUTOR FLEXIBLE DE VISTAS
# -----------------------------------------------------------------------------
def ejecutar_vista(modulo):
    """
    Busca y ejecuta dinámicamente la función principal dentro de cada módulo de vista.
    """
    nombre_modulo = modulo.__name__.split(".")[-1]   # ej: v_caja
    nombre_limpio = nombre_modulo.replace("v_", "") # ej: caja

    nombres_posibles = [
        f"mostrar_vista_{nombre_limpio}",
        f"render_{nombre_modulo}_view",
        f"render_{nombre_limpio}_view",
        "render",
        "main",
    ]

    for fn in nombres_posibles:
        if hasattr(modulo, fn):
            getattr(modulo, fn)()
            return

    st.error(f"No se encontró una función de renderizado válida en `{nombre_modulo}.py`.")

# -----------------------------------------------------------------------------
# 2. INICIALIZACIÓN Y CONTROL DE SESIÓN
# -----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Si NO está autenticado, detiene la ejecución mostrando solo la vista de Login
if not st.session_state.autenticado:
    render_login()
    st.stop()

# -----------------------------------------------------------------------------
# 3. RENDERIZADO DEL SIDEBAR
# -----------------------------------------------------------------------------
if 'lista_global_vta' not in st.session_state:
    st.session_state.lista_global_vta = "Automática (P1/P2)"

menu_seleccionado = render_sidebar()

# -----------------------------------------------------------------------------
# 4. ENRUTADOR PRINCIPAL
# -----------------------------------------------------------------------------
if menu_seleccionado == "🛒 Punto de Venta":
    ejecutar_vista(v_punto_venta)

elif menu_seleccionado == "📜 Historial de Ventas":
    ejecutar_vista(v_historial_ventas)

elif menu_seleccionado == "📦 Productos":
    ejecutar_vista(v_productos)

elif menu_seleccionado == "📊 Control de Stock":
    ejecutar_vista(v_stock)

elif menu_seleccionado == "👥 Clientes":
    ejecutar_vista(v_clientes)

elif menu_seleccionado == "🏢 Proveedores":
    ejecutar_vista(v_proveedores)

elif menu_seleccionado == "🛍️ Compras":
    ejecutar_vista(v_compras)

elif menu_seleccionado == "👔 Vendedores":
    ejecutar_vista(v_vendedores)

elif menu_seleccionado == "💰 Caja":
    ejecutar_vista(v_caja)

elif menu_seleccionado == "🚚 Repartos":
    ejecutar_vista(v_repartos)

elif menu_seleccionado == "📈 Reportes":
    ejecutar_vista(v_reportes)

elif menu_seleccionado == "💰 Utilidades":
    ejecutar_vista(v_utilidades)

elif menu_seleccionado == "⚙️ Config. Pagos":
    ejecutar_vista(v_config_pagos)

elif menu_seleccionado == "📋 Auditoría":
    ejecutar_vista(v_auditoria)
