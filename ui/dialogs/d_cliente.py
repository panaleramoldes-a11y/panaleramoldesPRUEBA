import streamlit as st
from config.database import db
from services.audit_service import log_auditoria

@st.dialog("➕ Nuevo Cliente Rápido")
def abrir_alta_cliente_rapida():
    with st.form("form_nuevo_cliente_rapido"):
        nombre = st.text_input("Nombre")
        apellido = st.text_input("Apellido")
        razon_social = st.text_input("Razón Social")
        telefono = st.text_input("Teléfono* (10 dígitos)", max_chars=10)
        dir1 = st.text_input("Dirección 1*")
        link1 = st.text_input("Link Dirección 1 (Google Maps)")
        zona = st.selectbox("Zona*", ["NORTE", "SUR", "CENTRO", "ESTE", "OESTE", "SANLO CHICO"])
        
        submitted = st.form_submit_button("Guardar Cliente")
        if submitted:
            tiene_datos_persona = bool(nombre and apellido)
            tiene_razon_social = bool(razon_social)
            
            if not (tiene_datos_persona or tiene_razon_social):
                st.error("⚠️ Debes completar obligatoriamente el 'Nombre y Apellido' o la 'Razón Social'.")
            elif not all([telefono, dir1]):
                st.error("⚠️ El 'Teléfono' y la 'Dirección 1' son campos obligatorios.")
            else:
                try:
                    existe_telefono = db.table("CLIENTES").select("ID_Cliente").eq("Telefono", str(telefono)).execute().data
                    
                    if existe_telefono:
                        st.error("⚠️ Ya existe un cliente con este teléfono!")
                    else:
                        tipo_detectado = "EMPRESA/ORGANISMO" if tiene_razon_social else "CONSUMIDOR FINAL"
                        
                        nuevo_cliente = {
                            "Nombre": nombre.upper() if nombre else "N/A", 
                            "Apellido": apellido.upper() if apellido else "N/A",
                            "Razón Social": razon_social.upper() if razon_social else "",
                            "Telefono": telefono, 
                            "Direccion_1": dir1.upper(),
                            "Link_Direccion_1": link1,
                            "Zona": zona, 
                            "Tipo_Cliente": tipo_detectado
                        }
                        
                        resultado = db.table("CLIENTES").insert(nuevo_cliente).execute()
                        
                        id_cliente_generado = "N/A"
                        if resultado.data:
                            id_cliente_generado = resultado.data[0].get('ID_Cliente', resultado.data[0].get('id', 'N/A'))
                        
                        usuario_logueado = st.session_state.get('usuario_actual', 'Desconocido')
                        
                        log_auditoria(
                            tabla="CLIENTES",
                            accion="INSERT",
                            id_entidad=id_cliente_generado,
                            detalles={
                                "operacion": "Alta de Cliente Rápida",
                                "datos_cliente": {
                                    "nombre_completo": f"{apellido.upper()}, {nombre.upper()}" if tiene_datos_persona else "N/A",
                                    "razon_social": razon_social.upper() if razon_social else "N/A",
                                    "telefono": telefono,
                                    "zona": zona,
                                    "tipo_cliente": tipo_detectado,
                                    "direccion_principal": dir1.upper()
                                }
                            },
                            usuario=usuario_logueado
                        )
                        
                        st.success("✅ Cliente guardado!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error al procesar la solicitud: {e}")
