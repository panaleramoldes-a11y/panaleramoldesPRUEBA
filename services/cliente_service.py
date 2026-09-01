import pandas as pd
import streamlit as st
from config.database import db
from services.audit_service import log_auditoria


class ClienteService:

    @staticmethod
    def obtener_todos() -> pd.DataFrame:
        """Obtiene la lista completa de clientes desde la base de datos."""
        try:
            response = db.table("CLIENTES").select("*").execute()
            return pd.DataFrame(response.data) if response.data else pd.DataFrame()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            return pd.DataFrame()

    @staticmethod
    def obtener_gift_card_activa(id_cliente: int):
        """Consulta si el cliente posee una Gift Card activa."""
        try:
            res = (
                db.table("GIFT_CARDS")
                .select("*")
                .eq("ID_Cliente", id_cliente)
                .eq("Estado", True)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            st.error(f"Error al consultar Gift Card: {e}")
            return None

    @staticmethod
    def crear_cliente(datos: dict, usuario: str) -> bool:
        """Inserta un nuevo cliente y registra el evento en auditoría."""
        try:
            resultado = db.table("CLIENTES").insert(datos).execute()
            id_generado = "N/A"
            if resultado.data:
                id_generado = resultado.data[0].get(
                    "ID_Cliente", resultado.data[0].get("id", "N/A")
                )

            log_auditoria(
                tabla="CLIENTES",
                accion="INSERT",
                id_entidad=str(id_generado),
                detalles={
                    "operacion": "Alta de Cliente",
                    "datos_cliente": {
                        "nombre_completo": f"{datos.get('Apellido')}, {datos.get('Nombre')}",
                        "razon_social": datos.get("Razón Social") or "N/A",
                        "telefono": datos.get("Telefono"),
                        "dni_cuit": datos.get("CUIT") or datos.get("DNI"),
                        "zona": datos.get("Zona"),
                        "tipo_cliente": datos.get("Tipo_Cliente"),
                        "direccion_principal": datos.get("Direccion_1"),
                    },
                },
                usuario=usuario,
            )
            return True
        except Exception as e:
            st.error(f"Error al guardar el cliente o registrar auditoría: {e}")
            return False

    @staticmethod
    def actualizar_cliente(
        id_cliente: int, datos: dict, datos_previos: dict, usuario: str
    ) -> bool:
        """Actualiza un cliente existente y registra los cambios previos/posteriores en auditoría."""
        try:
            db.table("CLIENTES").update(datos).eq("ID_Cliente", id_cliente).execute()

            razon_ant = datos_previos.get("Razón Social") or ""
            nombre_ant = (
                razon_ant
                if razon_ant
                else f"{datos_previos.get('Apellido')}, {datos_previos.get('Nombre')}"
            )

            razon_nuev = datos.get("Razón Social") or ""
            nombre_nuev = (
                razon_nuev
                if razon_nuev
                else f"{datos.get('Apellido')}, {datos.get('Nombre')}"
            )

            log_auditoria(
                tabla="CLIENTES",
                accion="UPDATE",
                id_entidad=str(id_cliente),
                detalles={
                    "operacion": "Modificar Cliente",
                    "antes": {
                        "nombre_comercial_o_completo": nombre_ant,
                        "telefono": datos_previos.get("Telefono"),
                        "zona": datos_previos.get("Zona"),
                        "direccion_1": datos_previos.get("Direccion_1"),
                    },
                    "despues": {
                        "nombre_comercial_o_completo": nombre_nuev,
                        "telefono": datos.get("Telefono"),
                        "zona": datos.get("Zona"),
                        "direccion_1": datos.get("Direccion_1"),
                    },
                },
                usuario=usuario,
            )
            return True
        except Exception as e:
            st.error(f"Error al modificar el cliente: {e}")
            return False

    @staticmethod
    def eliminar_cliente(
        id_cliente: int, datos_cliente: dict, usuario: str
    ) -> bool:
        """Elimina físicamente un cliente de la base de datos y audita la acción."""
        try:
            db.table("CLIENTES").delete().eq("ID_Cliente", id_cliente).execute()

            razon = datos_cliente.get("Razón Social") or ""
            identificador = (
                razon
                if razon
                else f"{datos_cliente.get('Apellido')}, {datos_cliente.get('Nombre')}"
            )

            log_auditoria(
                tabla="CLIENTES",
                accion="DELETE",
                id_entidad=str(id_cliente),
                detalles={
                    "operacion": "Eliminar Cliente",
                    "cliente_eliminado": identificador,
                    "dni_cuit": datos_cliente.get("CUIT") or datos_cliente.get("DNI"),
                    "telefono": datos_cliente.get("Telefono"),
                },
                usuario=usuario,
            )
            return True
        except Exception as e:
            st.error(f"Error al eliminar el cliente: {e}")
            return False
