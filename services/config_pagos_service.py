from config.database import db

def obtener_formas_pago():
    """Obtiene todos los medios de pago registrados."""
    try:
        response = db.table("FORMAS_PAGO").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        raise Exception(f"Error al obtener las formas de pago: {e}")

def agregar_forma_pago(nombre_pago):
    """Agrega un nuevo medio de pago activo."""
    if not nombre_pago or not nombre_pago.strip():
        raise ValueError("El nombre de la forma de pago no puede estar vacío.")
    
    try:
        data = {
            "Nombre_Pago": nombre_pago.strip().upper(),
            "Activo": True
        }
        return db.table("FORMAS_PAGO").insert(data).execute()
    except Exception as e:
        raise Exception(f"Error al guardar la forma de pago: {e}")

def cambiar_estado_pago(id_pago, nuevo_estado):
    """Activa o desactiva un medio de pago según su ID."""
    try:
        return db.table("FORMAS_PAGO").update({"Activo": nuevo_estado}).eq("ID_Pago", id_pago).execute()
    except Exception as e:
        raise Exception(f"Error al actualizar el estado de la forma de pago: {e}")
