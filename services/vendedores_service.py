from datetime import datetime
import pandas as pd
from config.database import db


def obtener_vendedores() -> pd.DataFrame:
    """Obtiene el listado completo de vendedores desde Supabase.

    Asegura que existan las columnas mínimas y asigna estado por defecto.
    """
    try:
        response = db.table("VENDEDORES").select("*").execute()
        df_vend = pd.DataFrame(response.data)

        if df_vend.empty:
            df_vend = pd.DataFrame(
                columns=[
                    "ID_Vendedor",
                    "Nombre",
                    "Apellido",
                    "Mail",
                    "Fecha de Nacimiento",
                    "Imagen",
                    "Estado",
                ]
            )

        # Asegurar columnas requeridas
        columnas_necesarias = ["ID_Vendedor", "Nombre", "Apellido", "Estado"]
        for col in columnas_necesarias:
            if col not in df_vend.columns:
                df_vend[col] = None

        df_vend["Estado"] = df_vend["Estado"].fillna("Activo")
        return df_vend
    except Exception as e:
        print(f"Error al obtener vendedores: {e}")
        return pd.DataFrame()


def calcular_siguiente_id(df_vend: pd.DataFrame) -> int:
    """Calcula el siguiente ID secuencial disponible para un nuevo vendedor."""
    if df_vend.empty or "ID_Vendedor" not in df_vend.columns:
        return 1

    ids_numericos = pd.to_numeric(df_vend["ID_Vendedor"], errors="coerce")
    max_id = ids_numericos.max()

    if pd.isna(max_id):
        return 1

    return int(max_id + 1)


def registrar_vendedor(
    nuevo_id: int,
    nombre: str,
    apellido: str,
    mail: str,
    fecha_nac,
    imagen: str = "",
) -> tuple[bool, str]:
    """Registra un nuevo vendedor en la base de datos."""
    try:
        db.table("VENDEDORES").insert({
            "ID_Vendedor": nuevo_id,
            "Nombre": nombre.strip(),
            "Apellido": apellido.strip(),
            "Mail": mail.strip(),
            "Fecha de Nacimiento": str(fecha_nac),
            "Imagen": imagen.strip(),
            "Estado": "Activo",
        }).execute()
        return True, f"¡Vendedor {nombre} registrado exitosamente!"
    except Exception as e:
        return False, f"Error al guardar: {e}"


def actualizar_vendedor(
    id_vendedor: int,
    nombre: str,
    apellido: str,
    mail: str,
    fecha_nac,
    estado: str,
    imagen: str = "",
) -> tuple[bool, str]:
    """Actualiza la información de un vendedor existente."""
    try:
        db.table("VENDEDORES").update({
            "Nombre": nombre.strip(),
            "Apellido": apellido.strip(),
            "Mail": mail.strip(),
            "Fecha de Nacimiento": str(fecha_nac),
            "Imagen": imagen.strip(),
            "Estado": estado,
        }).eq("ID_Vendedor", id_vendedor).execute()
        return True, f"Datos de {nombre} actualizados correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {e}"
