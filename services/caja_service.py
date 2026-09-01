from datetime import datetime
import pandas as pd
import streamlit as st
from config.database import db

def obtener_turno_activo():
    """Retorna el turno de caja abierto (Estado == True)."""
    try:
        res = db.table("CAJA_TURNOS").select("*").eq("Estado", True).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception:
        return None

def iniciar_turno(monto_inicial: float, usuario: str = "Martin"):
    """Abre un nuevo turno de caja."""
    nuevo_turno = {
        "Monto_Inicial": float(monto_inicial),
        "Usuario_Apertura": usuario,
        "Fecha_Apertura": datetime.now().isoformat(),
        "Estado": True
    }
    return db.table("CAJA_TURNOS").insert(nuevo_turno).execute()

def cerrar_turno(id_turno: str, monto_cierre: float):
    """Cierra el turno actual y genera el egreso de cierre en la tabla CAJA."""
    # A. Cerrar turno en CONTROL_TURNOS
    db.table("CONTROL_TURNOS").update({
        "Fecha_Hora_Cierre": datetime.now().isoformat(),
        "Monto_Cierre_Declarado": float(monto_cierre),
        "Estado": "Cerrado"
    }).eq("ID_Turno", id_turno).execute()

    # B. Registrar egreso en CAJA
    db.table("CAJA").insert({
        "Fecha": datetime.now().isoformat(),
        "Tipo": "Egreso",
        "Concepto": "CIERRE CAJA DIARIO",
        "Monto": float(monto_cierre),
        "Forma_Pago": "Efectivo",
        "ID_Turno": id_turno
    }).execute()

def obtener_movimientos_caja():
    """Obtiene todos los movimientos de la tabla CAJA."""
    try:
        res = db.table("CAJA").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def obtener_conceptos_caja():
    """Obtiene el listado de conceptos para los movimientos manuales."""
    try:
        data = db.table("LISTA_CONCEPTOS").select("CONCEPTO").execute().data
        return [c['CONCEPTO'] for c in data] if data else []
    except Exception:
        return []

def registrar_movimiento_manual(id_turno: str, tipo: str, concepto: str, importe: float, forma_pago: str):
    """Registra un movimiento manual de caja (Ingreso/Egreso) y su contraasiento si corresponde."""
    id_t = id_turno if id_turno else "SIN_TURNO"
    
    db.table("CAJA").insert({
        "ID_Turno": id_t,
        "Fecha": datetime.now().isoformat(),
        "Tipo": tipo,
        "Concepto": concepto,
        "Monto": float(importe),
        "Forma_Pago": forma_pago
    }).execute()

    # Contraasiento automático para ingresos que no son efectivo
    if tipo == "Ingreso" and forma_pago != "Efectivo":
        db.table("CAJA").insert({
            "ID_Turno": id_t,
            "Fecha": datetime.now().isoformat(),
            "Tipo": "Egreso",
            "Concepto": f"RETIRO PAGO {forma_pago.upper()}",
            "Monto": float(importe),
            "Forma_Pago": forma_pago
        }).execute()
