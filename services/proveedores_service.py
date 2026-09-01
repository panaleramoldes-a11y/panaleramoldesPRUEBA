import re
import pandas as pd
from config.database import db

def obtener_proveedores():
    """Obtiene todos los registros de la tabla PROVEEDORES."""
    try:
        response = db.table("PROVEEDORES").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        raise Exception(f"Error al obtener proveedores: {e}")

def crear_proveedor(data_proveedor, df_prov_existente=None):
    """
    Valida e inserta un nuevo proveedor en la base de datos.
    """
    cuit = data_proveedor.get("CUIT", "")

    # Validaciones
    if not re.match(r'^\d{2}-\d{8}-\d{1}$', cuit):
        raise ValueError("El CUIT debe tener formato XX-XXXXXXXX-X")

    if df_prov_existente is None:
        df_prov_existente = obtener_proveedores()

    if not df_prov_existente.empty and cuit in df_prov_existente['CUIT'].astype(str).values:
        raise ValueError("Ya existe un proveedor con ese CUIT.")

    # Generación de ID sugerido si no viene explícito
    if "ID_Proveedor" not in data_proveedor or not data_proveedor["ID_Proveedor"]:
        data_proveedor["ID_Proveedor"] = str(len(df_prov_existente) + 1).zfill(4)

    try:
        return db.table("PROVEEDORES").insert(data_proveedor).execute()
    except Exception as e:
        raise Exception(f"Error al guardar proveedor: {e}")

def actualizar_proveedor(id_proveedor, data_actualizada):
    """
    Actualiza la información de un proveedor según su ID_Proveedor.
    """
    try:
        return db.table("PROVEEDORES").update(data_actualizada).eq("ID_Proveedor", id_proveedor).execute()
    except Exception as e:
        raise Exception(f"Error al actualizar proveedor: {e}")
