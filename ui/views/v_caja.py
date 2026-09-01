from datetime import datetime
import pandas as pd
import streamlit as st

from services.caja_service import (
    obtener_turno_activo,
    iniciar_turno,
    cerrar_turno,
    obtener_movimientos_caja,
    obtener_conceptos_caja,
    registrar_movimiento_manual
)
from utils.formatters import formato_moneda

def mostrar_vista_caja():
    st.title("💰 Gestión de Caja")

    # 1. Obtenemos estado del turno
    turno_actual = obtener_turno_activo()

    # Dos pestañas principales
    tab_turno, tab_explorar = st.tabs(["🕒 Turno Actual", "🔍 Explorador"])

    with tab_turno:
        if turno_actual is None:
            st.warning("⚠️ No hay ningún turno abierto.")
            monto_inicial = st.number_input("Ingrese monto de apertura (efectivo inicial)", min_value=0.0)
            if st.button("🚀 Abrir Turno"):
                usr = st.session_state.get('usuario_actual', 'Martin')
                iniciar_turno(monto_inicial, usr)
                st.rerun()
        else:
            st.success(f"✅ Turno Activo: {turno_actual['ID_Turno']}")

            with st.expander("🔒 Finalizar Turno"):
                with st.form("form_cierre"):
                    monto_cierre = st.number_input("Monto final en caja", min_value=0.0)
                    if st.form_submit_button("Confirmar Cierre"):
                        cerrar_turno(turno_actual['ID_Turno'], monto_cierre)
                        st.success("Turno cerrado correctamente.")
                        st.rerun()

    with tab_explorar:
        df_caja = obtener_movimientos_caja()
        fecha_sel = st.date_input("Consultar fecha", datetime.now())

        if not df_caja.empty:
            df_caja['Fecha'] = pd.to_datetime(df_caja['Fecha'])
            df_filtrado = df_caja[df_caja['Fecha'].dt.date == fecha_sel]
        else:
            df_filtrado = pd.DataFrame()

        # Métricas de Saldo
        if not df_filtrado.empty:
            ingresos = df_filtrado[df_filtrado['Tipo'] == 'Ingreso']['Monto'].sum()
            egresos = df_filtrado[df_filtrado['Tipo'] == 'Egreso']['Monto'].sum()
            saldo_final = ingresos - egresos
        else:
            saldo_final = 0.0

        st.metric("Saldo", formato_moneda(saldo_final))
        st.divider()

        # Tabla de movimientos
        if not df_filtrado.empty:
            columnas_a_mostrar = ['Fecha', 'Tipo', 'Concepto', 'Monto', 'Forma_Pago']
            st.dataframe(
                df_filtrado[columnas_a_mostrar],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay movimientos registrados para la fecha seleccionada.")

        # Formulario de Registro Manual
        with st.expander("➕ Registrar Movimiento Manual"):
            lista_c = obtener_conceptos_caja()

            with st.form("nuevo_movimiento", clear_on_submit=True):
                concepto = st.selectbox("Concepto", lista_c if lista_c else ["GENERAL"])
                tipo = st.radio("Tipo", ["Ingreso", "Egreso"])
                importe = st.number_input("Importe", min_value=0.0)
                forma_pago = st.selectbox("Forma de Pago", ["Efectivo", "Crédito", "Débito", "Transferencia"])

                if st.form_submit_button("Guardar"):
                    id_t = turno_actual['ID_Turno'] if turno_actual else None
                    registrar_movimiento_manual(id_t, tipo, concepto, importe, forma_pago)
                    st.success("✅ Registro realizado.")
                    st.rerun()
