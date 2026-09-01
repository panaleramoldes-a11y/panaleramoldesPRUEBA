import uuid
from datetime import datetime
import streamlit as st
from config.database import db

@st.dialog("➕ Asignar Nueva Gift Card")
def abrir_asignacion_gift_card(id_cliente, nombre_cliente):
    st.write(f"Asignando Gift Card a: **{nombre_cliente}**")
    
    with st.form("form_asignar_gift"):
        monto = st.number_input("Monto inicial de la Gift Card", min_value=0.0, step=100.0)
        
        metodos_db = db.table("FORMAS_PAGO").select("Nombre_Pago").eq("Activo", True).execute()
        opciones = [item['Nombre_Pago'] for item in metodos_db.data] if metodos_db.data else ["Efectivo"]
        forma_pago = st.selectbox("Forma de pago de la Gift Card", opciones)
        
        if st.form_submit_button("Confirmar Emisión"):
            nueva_gc = {
                "ID_GiftCard": str(uuid.uuid4()), 
                "ID_Cliente": int(id_cliente),
                "Saldo_Actual": float(monto),
                "Saldo_Inicial": float(monto),
                "Forma_Pago_Adquisicion": forma_pago,
                "Estado": True,
                "Fecha_Creacion": datetime.now().isoformat()
            }

            try:
                db.table("GIFT_CARDS").insert(nueva_gc).execute()
                st.success(f"✅ Gift Card de ${monto:,.2f} asignada!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar en la base de datos: {e}")
