from config.database import db

def verificar_credenciales(usuario: str, clave: str):
    """
    Consulta en la tabla USUARIOS si existe la coincidencia de usuario y clave.
    Devuelve los datos del usuario si es válido, o None en caso contrario.
    """
    try:
        res = db.table("USUARIOS").select("*").eq("Usuario", usuario).eq("Clave", clave).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception:
        return None
