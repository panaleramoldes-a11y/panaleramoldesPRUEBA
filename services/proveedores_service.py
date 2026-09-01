# services/proveedores_service.py
import re
import pandas as pd


def obtener_proveedores(db):
    """Consulta todos los registros de la tabla PROVEEDORES en Supabase."""
    response = db.table("PROVEEDORES").select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


def validar_cuit_formato(cuit: str) -> bool:
    """Valida que el CUIT tenga el formato XX-XXXXXXXX-X."""
    return bool(re.match(r"^\d{2}-\d{8}-\d{1}$", cuit.strip()))


def generar_siguiente_id_proveedor(df_prov: pd.DataFrame) -> str:
    """Genera un nuevo ID con formato '0001', '0002', etc."""
    return str(len(df_prov) + 1).zfill(4)


def guardar_proveedor(db, datos_prov: dict, df_prov: pd.DataFrame):
    """Aplica validaciones de negocio e inserta un nuevo proveedor en Supabase.

    Retorna tuple: (bool_exito, mensaje_resultado)
    """
    cuit = datos_prov.get("CUIT", "").strip()

    # 1. Validación de formato de CUIT
    if not validar_cuit_formato(cuit):
        return False, "Error: El CUIT debe tener el formato XX-XXXXXXXX-X."

    # 2. Validación de CUIT duplicado
    if not df_prov.empty and "CUIT" in df_prov.columns:
        cuits_existentes = df_prov["CUIT"].astype(str).str.strip().values
        if cuit in cuits_existentes:
            return False, "Error: Ya existe un proveedor registrado con ese CUIT."

    # 3. Guardado en BD
    try:
        db.table("PROVEEDORES").insert(datos_prov).execute()
        return True, "¡Proveedor cargado exitosamente!"
    except Exception as e:
        return False, f"Error al guardar el proveedor: {e}"


def actualizar_proveedor(db, id_proveedor: str, datos_actualizados: dict):
    """Actualiza la información de un proveedor existente por su ID_Proveedor.

    Retorna tuple: (bool_exito, mensaje_resultado)
    """
    try:
        db.table("PROVEEDORES").update(datos_actualizados).eq(
            "ID_Proveedor", id_proveedor
        ).execute()
        return True, "Datos actualizados correctamente."
    except Exception as e:
        return False, f"Error al actualizar el proveedor: {e}"
