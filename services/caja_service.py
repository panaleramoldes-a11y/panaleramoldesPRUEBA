from config.database import db
from datetime import datetime

def obtener_turno_activo():
    """Retorna el turno de caja que se encuentra abierto actualmente (Estado == True)."""
    try:
        res = db.table("CAJA_TURNOS").select("*").eq("Estado", True).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception:
        return None

def iniciar_turno(monto_inicial: float, usuario: str):
    """Abre un nuevo turno de caja con el monto inicial indicado."""
    nuevo_turno = {
        "Monto_Inicial": float(monto_inicial),
        "Usuario_Apertura": usuario,
        "Fecha_Apertura": datetime.now().isoformat(),
        "Estado": True
    }
    return db.table("CAJA_TURNOS").insert(nuevo_turno).execute()
