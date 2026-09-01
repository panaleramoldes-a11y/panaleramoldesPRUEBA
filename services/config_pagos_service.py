import pandas as pd
import streamlit as st
from config.database import db
from services.audit_service import log_auditoria


class ConfigPagosService:

    @staticmethod
    def obtener_formas_pago() -> list:
        """Obtiene todas las formas de pago registradas."""
        try:
            response = db.table("FORMAS_PAGO").select("*").execute()
            return response.data if response.data else []
        except Exception as e:
            st.error(f"Error al cargar las formas de pago: {e}")
            return []

    @staticmethod
    def agregar_forma_pago(nombre_pago: str, usuario: str) -> bool:
        """Inserta un nuevo medio de pago activo y registra auditoría."""
        if not nombre_pago.strip():
            st.warning("El nombre del medio de pago no puede estar vacío.")
            return False

        try:
            res = (
                db.table("FORMAS_PAGO")
                .insert({"Nombre_Pago": nombre_pago.strip(), "Activo": True})
                .execute()
            )

            if res.data:
                id_creado = res.data[0].get("ID_Pago", "N/A")
                log_auditoria(
                    tabla="FORMAS_PAGO",
                    accion="INSERT",
                    id_entidad=str(id_creado),
                    detalles={
                        "operacion": "Agregar Forma de Pago",
                        "nombre": nombre_pago.strip(),
                    },
                    usuario=usuario,
                )
                return True
            return False
        except Exception as e:
            st.error(f"Error al agregar forma de pago: {e}")
            return False

    @staticmethod
    def cambiar_estado_pago(id_pago: int, activo: bool, usuario: str) -> bool:
        """Activa o desactiva un medio de pago según su ID."""
        try:
            db.table("FORMAS_PAGO").update({"Activo": activo}).eq(
                "ID_Pago", id_pago
            ).execute()

            log_auditoria(
                tabla="FORMAS_PAGO",
                accion="UPDATE",
                id_entidad=str(id_pago),
                detalles={
                    "operacion": "Cambio de Estado Pago",
                    "nuevo_estado": activo,
                },
                usuario=usuario,
            )
            return True
        except Exception as e:
            st.error(f"Error al actualizar la forma de pago: {e}")
            return False
