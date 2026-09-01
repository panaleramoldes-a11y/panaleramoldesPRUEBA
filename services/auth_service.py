from config.database import db

def verificar_credenciales(usuario: str, clave: str):
    """
    Consulta en la tabla USUARIOS si existe la coincidencia de Nombre y Contraseña.
    Devuelve los datos del usuario si es válido, o None en caso contrario.
    """
    try:
        res = db.table("USUARIOS") \
            .select("*") \
            .eq("Nombre", usuario) \
            .eq("Contraseña", clave) \
            .maybe_single() \
            .execute()
        
        return res.data if res else None
    except Exception as e:
        print(f"Error al autenticar: {e}")
        return None
