import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (CARD-STYLE DASHBOARD)
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Reportes Pañalera Moldes")

# CSS personalizado para replicar el estilo visual de la imagen
custom_css = """
<style>
    /* Fondo principal claro */
    .stApp {
        background-color: #f4f6f9;
    }
    
    /* Ocultar padding superior por defecto */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* Estilo para las Tarjetas (Cards) con bordes redondeados y sombra sutil */
    .dashboard-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 15px;
        height: 100%;
    }

    /* Encabezado superior */
    .header-title {
        font-size: 24px;
        font-weight: 800;
        color: #1a2530;
        border-left: 5px solid #2b5c8f;
        padding-left: 12px;
        margin-bottom: 0px;
    }
    
    .header-actions {
        text-align: right;
        color: #6c757d;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
    }

    /* Textos de KPIs */
    .kpi-title {
        font-size: 12px;
        font-weight: 700;
        color: #1a2530;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #1a2530;
        margin-bottom: 2px;
    }

    .kpi-subtext {
        font-size: 11px;
        color: #8c98a4;
        margin-bottom: 8px;
    }

    /* Badges de variación */
    .badge-positive {
        background-color: #d4edda;
        color: #155724;
        font-size: 12px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 10px;
        display: inline-block;
    }

    .badge-negative {
        background-color: #f8d7da;
        color: #721c24;
        font-size: 12px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 10px;
        display: inline-block;
    }

    /* Encabezados de Paneles */
    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .panel-title {
        font-size: 13px;
        font-weight: 700;
        color: #1a2530;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .panel-dots {
        color: #a0aec0;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
    }

    /* Tablas personalizadas */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }

    .custom-table th {
        background-color: #e9ecef;
        color: #495057;
        font-weight: 700;
        text-align: left;
        padding: 8px;
    }

    .custom-table td {
        padding: 8px;
        border-bottom: 1px solid #f1f3f5;
        color: #212529;
    }

    /* Barras de progreso simples para marcas */
    .progress-bg {
        background-color: #e9ecef;
        border-radius: 6px;
        height: 8px;
        width: 100%;
        margin-top: 4px;
    }
    
    .progress-bar-fill {
        height: 100%;
        border-radius: 6px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. SECCIÓN A: ENCABEZADO SUPERIOR
# -----------------------------------------------------------------------------
col_title, col_actions = st.columns([3, 1])

with col_title:
    st.markdown('<p class="header-title">REPORTES PAÑALERA MOLDES</p>', unsafe_allow_html=True)

with col_actions:
    st.markdown('<div class="header-actions">⬇️ exportar &nbsp;&nbsp;&nbsp;&nbsp; ⚙️ configurar</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 3. SECCIÓN B: PRIMERA FILA DE KPIS Y SELECTOR
# -----------------------------------------------------------------------------
col_b1, col_b2, col_b3 = st.columns([1.2, 1.2, 1.6])

with col_b1:
    st.markdown("""
        <div class="dashboard-card">
            <div class="kpi-title">CANTIDAD DE REPARTOS</div>
            <div class="kpi-value">29</div>
            <hr style="margin: 12px 0; border: 0; border-top: 1px solid #e9ecef;">
            <div class="kpi-title">REPARTOS % VENTAS</div>
            <div class="kpi-value">77.5%</div>
        </div>
    """, unsafe_allow_html=True)

with col_b2:
    # Card con selector interactivo
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="kpi-title">PERÍODO</div>', unsafe_allow_html=True)
    opcion_mes = st.selectbox(
        "Seleccionar Mes", 
        ["Seleccionar Mes", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto"],
        index=0,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_b3:
    st.markdown("""
        <div class="dashboard-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="kpi-title">VENTAS TOTALES</div>
                    <div class="kpi-value">$1,250,000</div>
                </div>
                <span class="badge-positive">▲ +12.5%</span>
            </div>
            <div class="kpi-subtext">Variación % mes anterior</div>
            <hr style="margin: 8px 0; border: 0; border-top: 1px solid #e9ecef;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="kpi-title">UTILIDAD</div>
                    <div class="kpi-value">$1,900,000</div>
                </div>
                <span class="badge-negative">▼ -2.1%</span>
            </div>
            <div class="kpi-subtext">Variación % mes anterior</div>
        </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 4. SECCIÓN C: SEGUNDA FILA (BARRAS TOP 10 Y DONUT FORMAS DE PAGO)
# -----------------------------------------------------------------------------
col_c1, col_c2 = st.columns([2.2, 1.3])

# Paleta de colores consistente con la interfaz gráfica
color_palette = ['#2b5c8f', '#4682b4', '#5c9ce6', '#4fa8d1', '#38b6ff', '#20c997', '#48c774', '#5cd65c', '#7ada7a', '#9ae69a']

with col_c1:
    st.markdown("""
        <div class="dashboard-card">
            <div class="panel-header">
                <span class="panel-title">TOP 10 ARTÍCULOS VENDIDOS</span>
                <span style="font-size: 12px; color: #6c757d;">⬇️ exportar &nbsp; ⚙️</span>
            </div>
    """, unsafe_allow_html=True)
    
    # Datos del gráfico de barras Top 10
    df_top10 = pd.DataFrame({
        'Producto': [f'Producto {i}' for i in range(1, 10)] + ['Fardos'],
        'Cantidad': [10342, 7288, 6958, 5534, 4477, 4485, 2276, 2013, 1500, 1278]
    })

    fig_bar = px.bar(
        df_top10, 
        x='Producto', 
        y='Cantidad',
        text='Cantidad',
        color='Producto',
        color_discrete_sequence=color_palette
    )
    
    fig_bar.update_traces(
        texttemplate='%{text:,}', 
        textposition='outside',
        cliponaxis=False
    )
    
    fig_bar.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=10, r=10, t=30, b=10),
        height=280,
        xaxis=dict(title="", tickangle=-35),
        yaxis=dict(title="", showgrid=True, gridcolor='#f0f0f0')
    )
    
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_c2:
    st.markdown("""
        <div class="dashboard-card">
            <div class="panel-header">
                <span class="panel-title">FORMAS DE PAGO</span>
                <span class="panel-dots">⋮</span>
            </div>
    """, unsafe_allow_html=True)

    # Datos gráfico dónut
    df_pago = pd.DataFrame({
        'Forma': ['Efectivo', 'Transferencia', 'Tarjeta Débito', 'Tarjeta Crédito', 'Otros'],
        'Porcentaje': [55.0, 27.0, 18.0, 3.0, 1.0]
    })

    fig_donut = px.pie(
        df_pago, 
        values='Porcentaje', 
        names='Forma', 
        hole=0.6,
        color_discrete_sequence=['#2b5c8f', '#4682b4', '#20c997', '#495057', '#adb5bd']
    )
    
    fig_donut.update_traces(textinfo='none')
    fig_donut.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=280,
        paper_bgcolor='white'
    )

    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 5. SECCIÓN D: TERCERA FILA (TOP MARCAS, DETALLE DE PAGO Y TOP CLIENTES)
# -----------------------------------------------------------------------------
col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])

with col_d1:
    st.markdown("""
        <div class="dashboard-card">
            <div class="panel-header">
                <span class="panel-title">TOP 3 MARCAS</span>
                <span class="panel-dots">⋮</span>
            </div>
            <div style="margin-bottom: 12px;">
                <div style="display:flex; justify-between; font-weight:600; font-size:12px;">Pampers</div>
                <div class="progress-bg"><div class="progress-bar-fill" style="width: 85%; background-color: #2b5c8f;"></div></div>
            </div>
            <div style="margin-bottom: 12px;">
                <div style="display:flex; justify-between; font-weight:600; font-size:12px;">Huggies</div>
                <div class="progress-bg"><div class="progress-bar-fill" style="width: 65%; background-color: #4682b4;"></div></div>
            </div>
            <div style="margin-bottom: 12px;">
                <div style="display:flex; justify-between; font-weight:600; font-size:12px;">Babysec</div>
                <div class="progress-bg"><div class="progress-bar-fill" style="width: 35%; background-color: #495057;"></div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_d2:
    st.markdown("""
        <div class="dashboard-card">
            <div class="panel-header">
                <span class="panel-title">FORMAS DE PAGO</span>
                <span class="panel-dots">⋮</span>
            </div>
            <table class="custom-table">
                <tr><td><span style="color:#2b5c8f;">■</span> Efectivo</td><td style="text-align:right; font-weight:bold;">55.0%</td></tr>
                <tr><td><span style="color:#4682b4;">■</span> Transferencia</td><td style="text-align:right; font-weight:bold;">27.0%</td></tr>
                <tr><td><span style="color:#20c997;">■</span> Tarjeta Débito</td><td style="text-align:right; font-weight:bold;">18.0%</td></tr>
                <tr><td><span style="color:#495057;">■</span> Tarjeta Crédito</td><td style="text-align:right; font-weight:bold;">3.0%</td></tr>
                <tr><td><span style="color:#adb5bd;">■</span> Otros</td><td style="text-align:right; font-weight:bold;">1.0%</td></tr>
            </table>
        </div>
    """, unsafe_allow_html=True)

with col_d3:
    st.markdown("""
        <div class="dashboard-card">
            <div class="panel-header">
                <span class="panel-title">TOP 10 CLIENTES</span>
                <span class="panel-dots">⋮</span>
            </div>
            <table class="custom-table">
                <thead>
                    <tr><th>Cliente</th><th style="text-align:right;">Ventas</th></tr>
                </thead>
                <tbody>
                    <tr><td>Farmacia San Martin</td><td style="text-align:right;">$20,000</td></tr>
                    <tr><td>Distribuidora Norte</td><td style="text-align:right;">$20,000</td></tr>
                    <tr><td>Pérez María</td><td style="text-align:right;">$13,000</td></tr>
                    <tr><td>Gómez Roberto</td><td style="text-align:right;">$10,500</td></tr>
                    <tr><td>Minimarket Italia</td><td style="text-align:right;">$8,100</td></tr>
                    <tr><td>Pañalera Belgrano</td><td style="text-align:right;">$5,500</td></tr>
                </tbody>
            </table>
        </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. SECCIÓN E: CUARTA FILA (RANKING VENDEDORES Y MATRIZ RENTABILIDAD)
# -----------------------------------------------------------------------------
col_e1, col_e2 = st.columns([1.3, 2.2])

with col_e1:
    st.markdown("""
        <div class="dashboard-card">
            <div class="panel-header">
                <span class="panel-title">RANKING VENDEDORES</span>
                <span class="panel-dots">⋮</span>
            </div>
    """, unsafe_allow_html=True)

    # Datos para barras apiladas de vendedores
    vendedores = ['1', '2', '3', '4', '5', '6']
    fig_vend = go.Figure(data=[
        go.Bar(name='Meta', x=vendedores, y=[60000, 40000, 35000, 45000, 40000, 35000], marker_color='#495057'),
        go.Bar(name='Venta Directa', x=vendedores, y=[30000, 25000, 18000, 20000, 25000, 20000], marker_color='#4682b4'),
        go.Bar(name='Comisión', x=vendedores, y=[30000, 40000, 40000, 45000, 45000, 35000], marker_color='#20c997')
    ])

    fig_vend.update_layout(
        barmode='stack',
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
    )

    st.plotly_chart(fig_vend, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_e2:
    st.markdown("""
        <div class="dashboard-card">
            <div class="panel-header">
                <span class="panel-title">TOP 10 ART. + RENTABILIDAD</span>
                <span class="panel-dots">⋮</span>
            </div>
            <div style="overflow-x: auto;">
                <table class="custom-table" style="text-align: center;">
                    <thead>
                        <tr>
                            <th style="text-align:left;">Producto</th>
                            <th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="text-align:left; font-weight:600;">Ventas ($)</td>
                            <td>130.000</td><td>122.000</td><td>67.000</td><td>26.000</td><td>16.000</td><td>12.000</td>
                        </tr>
                        <tr>
                            <td style="text-align:left; font-weight:600;">Rentabilidad %</td>
                            <td style="background-color:#d4edda; color:#155724;">+12.5%</td>
                            <td style="background-color:#d4edda; color:#155724;">+38.6%</td>
                            <td>12.6%</td><td>18.7%</td><td>17.4%</td><td>7.9%</td>
                        </tr>
                        <tr>
                            <td style="text-align:left; font-weight:600;">Margen %</td>
                            <td style="background-color:#d4edda; color:#155724;">+2.1%</td>
                            <td style="background-color:#d4edda; color:#155724;">+2.6%</td>
                            <td>+6.6%</td><td>12.2%</td><td>12.9%</td><td>0.0%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    """, unsafe_allow_html=True)
