import pandas as pd
import streamlit as st
from config.constants import LISTA_RUBROS
from services import proveedores_service

def render():
    st.title("🚚 Gestión de Proveedores")

    # Carga de datos desde la capa de servicio
    try:
        df_prov = proveedores_service.obtener_proveedores()
    except Exception as e:
        st.error(f"Error al cargar proveedores: {e}")
        return

    tab1, tab2, tab3 = st.tabs(["🔍 Explorador", "➕ Nuevo Proveedor", "✏️ Modificar"])

    # -----------------------------------------------------------------
    # TAB 1: EXPLORADOR
    # -----------------------------------------------------------------
    with tab1:
        st.subheader("Lista de Proveedores")
        busqueda_prov = st.text_input("🔍 Filtrar por Nombre, CUIT o Rubro:")

        df_filtrado = df_prov.copy()
        if busqueda_prov and not df_prov.empty:
            b_txt = busqueda_prov.lower()
            mask = df_prov.apply(
                lambda row: b_txt in str(row.get('Razon_Social', '')).lower() or
                            b_txt in str(row.get('CUIT', '')).lower() or
                            b_txt in str(row.get('Rubros_Asociados', '')).lower(),
                axis=1
            )
            df_filtrado = df_prov[mask]

        st.dataframe(df_filtrado, use_container_width=True)

    # -----------------------------------------------------------------
    # TAB 2: NUEVO PROVEEDOR
    # -----------------------------------------------------------------
    with tab2:
        with st.form("nuevo_prov", clear_on_submit=True):
            nuevo_id = str(len(df_prov) + 1).zfill(4)
            st.info(f"ID Sugerido: {nuevo_id}")

            col1, col2 = st.columns(2)
            with col1:
                razon_social = st.text_input("Razón Social")
                cuit = st.text_input("CUIT (Formato: XX-XXXXXXXX-X)")
                direccion = st.text_input("Dirección")
            with col2:
                telefono = st.text_input("Teléfono")
                condicion = st.selectbox("Condición Fiscal", ["Responsable Inscripto", "Monotributo", "Exento"])

            rubros_seleccionados = st.multiselect("Asociar Rubros", LISTA_RUBROS)

            btn_guardar = st.form_submit_button("Guardar Proveedor")

            if btn_guardar:
                data_nuevo = {
                    "ID_Proveedor": nuevo_id,
                    "Razon_Social": razon_social,
                    "Rubros_Asociados": ", ".join(rubros_seleccionados),
                    "CUIT": cuit,
                    "Condicion_Fiscal": condicion,
                    "Direccion": direccion,
                    "Telefono": telefono
                }
                
                try:
                    proveedores_service.crear_proveedor(data_nuevo, df_prov)
                    st.success("¡Proveedor cargado exitosamente!")
                    st.rerun()
                except ValueError as ve:
                    st.error(f"Error de validación: {ve}")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # -----------------------------------------------------------------
    # TAB 3: MODIFICAR
    # -----------------------------------------------------------------
    with tab3:
        if not df_prov.empty and 'Razon_Social' in df_prov.columns:
            lista_opciones = df_prov['Razon_Social'].dropna().tolist()
            prov_seleccionado = st.selectbox("Seleccionar proveedor a editar", lista_opciones)

            if prov_seleccionado:
                datos = df_prov[df_prov['Razon_Social'] == prov_seleccionado].iloc[0]

                with st.form("modificar_prov"):
                    col1, col2 = st.columns(2)
                    with col1:
                        razon_social_mod = st.text_input("Razón Social", value=datos.get('Razon_Social', ''))
                        cuit_mod = st.text_input("CUIT", value=datos.get('CUIT', ''))
                        direccion_mod = st.text_input("Dirección", value=datos.get('Direccion', ''))
                    with col2:
                        telefono_mod = st.text_input("Teléfono", value=datos.get('Telefono', ''))
                        
                        cond_actual = datos.get('Condicion_Fiscal', 'Responsable Inscripto')
                        opciones_cond = ["Responsable Inscripto", "Monotributo", "Exento"]
                        idx_cond = opciones_cond.index(cond_actual) if cond_actual in opciones_cond else 0
                        condicion_mod = st.selectbox("Condición Fiscal", opciones_cond, index=idx_cond)

                        # Recuperar rubros guardados asegurando coincidencia con LISTA_RUBROS
                        raw_rubros = str(datos.get('Rubros_Asociados', '')) if pd.notna(datos.get('Rubros_Asociados')) else ""
                        rubros_defecto = [r.strip() for r in raw_rubros.split(",") if r.strip() in LISTA_RUBROS]
                        rubros_mod = st.multiselect("Rubros", LISTA_RUBROS, default=rubros_defecto)

                    btn_mod = st.form_submit_button("Actualizar Proveedor")

                    if btn_mod:
                        data_update = {
                            "Razon_Social": razon_social_mod,
                            "Rubros_Asociados": ", ".join(rubros_mod),
                            "CUIT": cuit_mod,
                            "Condicion_Fiscal": condicion_mod,
                            "Direccion": direccion_mod,
                            "Telefono": telefono_mod
                        }
                        try:
                            proveedores_service.actualizar_proveedor(datos['ID_Proveedor'], data_update)
                            st.success("Datos actualizados correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")
        else:
            st.info("No hay proveedores registrados para modificar.")

# Aliases de compatibilidad requeridos por ejecutar_vista
mostrar_vista_proveedores = render
render_proveedores_view = render
main = render
